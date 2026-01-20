"""MCP server lifecycle and management."""
import logging

from fastmcp import FastMCP
from fastmcp.server.auth import AuthProvider
from key_value.aio.stores.mongodb import MongoDBStore

from mcp_composer.auth.middleware import SecurityFilterMiddleware
from mcp_composer.auth.providers import create_google_auth_provider
from mcp_composer.config import AuthProviderType
from mcp_composer.config import Config
from mcp_composer.database import UserConfigRepository
from mcp_composer.server import CustomProxyClient
from pymongo import AsyncMongoClient
from fastmcp.server import create_proxy

logger = logging.getLogger(__name__)


class MCPServerManager:
    """
    Manages the lifecycle of the FastMCP server.

    This class handles server creation, configuration, user server mounting,
    and startup/shutdown operations. It coordinates authentication providers
    and security middleware based on configuration.
    """

    def __init__(self,
                 config: Config,
                 mongo_client: AsyncMongoClient,
                 user_config_repository: UserConfigRepository):
        """
        Initialize server manager with dependencies.

        Args:
            config: Application configuration containing auth, MCP, and MongoDB settings.
            mongo_client: Async MongoDB client for OAuth client storage.
            user_config_repository: Repository for accessing user MCP configurations.
        """
        self.mcp: FastMCP | None = None
        self.config: Config = config
        self.mongo_client = mongo_client
        self.user_config_repository = user_config_repository

    async def _create_mcp_server(self) -> FastMCP:
        """
        Create and configure the FastMCP server.

        Returns:
            Configured FastMCP server instance
        """

        auth_provider_type = self.config.auth_provider
        auth_provider: AuthProvider | None = None

        if auth_provider_type == AuthProviderType.GOOGLE:
            db_store = MongoDBStore(client=self.mongo_client)

            # noinspection PyTypeChecker
            auth_provider = create_google_auth_provider(
                base_url=self.config.base_url,
                config=self.config.google,
                client_storage=db_store
            )
            logger.info("Google OAuth authentication enabled")
        elif auth_provider_type == AuthProviderType.NONE:
            logger.info("Authentication disabled")
        else:
            raise ValueError(f"Unsupported auth provider: {auth_provider_type}")

        logger.info(f"Using auth provider: {auth_provider}")
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
                mcp.mount(create_proxy(client))

                logger.info(f"Mounted (live) servers for {user_config.email}")

            except Exception as e:
                logger.error(f"Failed to import servers for {user_config.email}: {e}")

    async def start_mcp(self) -> None:
        """Initialize and run the MCP server with all user configurations."""
        # Create server
        self.mcp = await self._create_mcp_server()

        # Import user servers
        await self._mount_user_servers(self.mcp)

        # await self._print_tools(self.mcp)

        # Start server
        mcp_config = self.config.mcp
        logger.info(f"Starting MCP Composer on {mcp_config.transport}://{mcp_config.host}:{mcp_config.port}")
        await self.mcp.run_async(
            transport=mcp_config.transport, host=mcp_config.host, port=8001,
            stateless_http=True
        )

    @staticmethod
    async def _print_tools(mcp: FastMCP) -> None:
        """Print available tools in the MCP server."""
        tools = await mcp.list_tools()

        if not tools:
            logger.warning("No tools available in the MCP server.")
            return

        logger.info("Available tools:")
        for tool in tools:
            logger.info(f"- {tool.name}: {tool.description}")
