"""MCP server lifecycle and management."""
import logging

from fastmcp import FastMCP
from fastmcp.server.auth import AuthProvider
from fastmcp.server.auth import OAuthProxy
from mcp.server.auth.provider import AccessToken, RefreshToken
from mcp_composer.database.tokens_repository import TokensRepository

from mcp_composer.auth.middleware import SecurityFilterMiddleware
from mcp_composer.auth.providers import create_google_auth_provider
from mcp_composer.config import AuthProviderType, MountMode
from mcp_composer.config import Config
from mcp_composer.database import ClientsRepository, UserConfigRepository
from mcp_composer.models import OAuthToken, TokenType
from mcp_composer.server import CustomProxyClient

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages the lifecycle of the FastMCP server."""

    def __init__(self,
                 config: Config,
                 tokens_repository: TokensRepository,
                 clients_repository: ClientsRepository,
                 user_config_repository: UserConfigRepository):
        """
        Initialize server manager with dependencies.

        Args:
            config: Application configuration
            tokens_repository: Repository for OAuth tokens
            clients_repository: Repository for OAuth client data
            user_config_repository: Repository for user configurations
        """
        self.mcp: FastMCP | None = None
        self.config: Config = config
        self.clients_repository = clients_repository
        self.user_config_repository = user_config_repository
        self.tokens_repository = tokens_repository

    async def _create_mcp_server(self) -> FastMCP:
        """
        Create and configure the FastMCP server.

        Returns:
            Configured FastMCP server instance
        """

        auth_provider_type = self.config.auth_provider
        auth_provider: AuthProvider | None = None

        if auth_provider_type == AuthProviderType.GOOGLE:
            auth_provider = create_google_auth_provider(self.config, self.clients_repository)
            logger.info("Google OAuth authentication enabled")
        elif auth_provider_type == AuthProviderType.NONE:
            logger.info("Authentication disabled")
        else:
            raise ValueError(f"Unsupported auth provider: {auth_provider_type}")

        mcp = FastMCP(name="Swarmnetics MCP", auth=auth_provider)
        if auth_provider_type != AuthProviderType.NONE:
            mcp.add_middleware(SecurityFilterMiddleware(self.user_config_repository))

        return mcp

    async def _mount_user_servers(self, mcp: FastMCP) -> None:
        """
        Import MCP servers for each user and mount them as proxy clients.

        Args:
            mcp: FastMCP server instance to mount clients to
        """
        user_configs = await self.user_config_repository.get_all_user_configs()
        logger.info(f"Found {len(user_configs)} user configurations to import.")
        for user_config in user_configs:
            try:
                client = CustomProxyClient(
                    user_config.to_client_config(),
                    owner_email=str(user_config.email)
                )
                await client.__aenter__()
                proxy = FastMCP.as_proxy(client)

                # Mount or import based on configuration
                mount_mode = self.config.mcp_composition_mode
                if mount_mode == MountMode.LIVE:
                    mcp.mount(proxy)
                    logger.info(f"Mounted (live) servers for {user_config.email}")
                elif mount_mode == MountMode.STATIC:
                    await mcp.import_server(proxy)
                    logger.info(f"Imported (static) servers for {user_config.email}")
                else:
                    raise ValueError(f"Unsupported mount mode: {mount_mode}")
            except Exception as e:
                logger.error(f"Failed to import servers for {user_config.email}: {e}")

    async def start_mcp(self) -> None:
        """Initialize and run the MCP server with all user configurations."""
        # Create server
        self.mcp = await self._create_mcp_server()
        await self.restore_auth_state()

        # Import user servers
        await self._mount_user_servers(self.mcp)

        await self._print_tools(self.mcp)

        # Start server
        mcp_config = self.config.mcp
        logger.info(f"Starting MCP Composer on {mcp_config.transport}://{mcp_config.host}:{mcp_config.port}")
        await self.mcp.run_async(transport=mcp_config.transport, host=mcp_config.host, port=mcp_config.port)

    async def dump_auth_state(self):
        """Dump the current authentication state of the MCP server."""
        if self.mcp is None:
            logger.warning("MCP server is not running. Cannot dump auth state.")
            return
        # if self.mcp.auth is type of OAuthProxy
        if isinstance(self.mcp.auth, OAuthProxy):
            access_tokens: dict[str, AccessToken] = self.mcp.auth._access_tokens
            refresh_tokens: dict[str, RefreshToken] = self.mcp.auth._refresh_tokens

            oauth_tokens = []
            for token_str, access_token in access_tokens.items():
                oauth_tokens.append(OAuthToken(
                    _id=token_str,
                    type=TokenType.ACCESS,
                    accessToken=access_token,
                    refreshToken=None
                ))

            for token_str, refresh_token in refresh_tokens.items():
                oauth_tokens.append(OAuthToken(
                    _id=token_str,
                    type=TokenType.REFRESH,
                    accessToken=None,
                    refreshToken=refresh_token
                ))

            await self.tokens_repository.save_all(oauth_tokens)
            logger.info(f"Dumped {len(oauth_tokens)} OAuth tokens to database")

    async def restore_auth_state(self):
        """Restore the authentication state of the MCP server from the database."""
        if self.mcp is None:
            logger.warning("MCP server is not running. Cannot restore auth state.")
            return

        if isinstance(self.mcp.auth, OAuthProxy):
            access_tokens = await self.tokens_repository.get_access_token_relations()
            refresh_tokens = await self.tokens_repository.get_refresh_token_relations()

            self.mcp.auth._access_tokens = access_tokens
            self.mcp.auth._refresh_tokens = refresh_tokens

            logger.info(f"Restored {len(access_tokens)} access tokens and {len(refresh_tokens)} refresh tokens from database")

    async def _print_tools(self, mcp: FastMCP) -> None:
        """Print available tools in the MCP server."""
        tools = await mcp.get_tools()
        if tools:
            logger.info("Available tools:")
            for _, tool in tools.items():
                logger.info(f"- {tool.name}: {tool.description}")
        else:
            logger.warning("No tools available in the MCP server.")
