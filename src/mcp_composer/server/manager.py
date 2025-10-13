"""MCP server lifecycle and management."""
import logging

from fastmcp import FastMCP
from fastmcp.prompts import Prompt

from mcp_composer.auth.middleware import SecurityFilterMiddleware
from mcp_composer.auth.providers import create_google_auth_provider
from mcp_composer.server import CustomProxyClient

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages the lifecycle of the FastMCP server."""

    def __init__(self, config, clients_repository, user_config_repository):
        """
        Initialize server manager with dependencies.

        Args:
            config: Application configuration
            clients_repository: Repository for OAuth client data
            user_config_repository: Repository for user configurations
        """
        self.mcp = None
        self.config = config
        self.clients_repository = clients_repository
        self.user_config_repository = user_config_repository

    async def _create_mcp_server(self) -> FastMCP:
        """
        Create and configure the FastMCP server.

        Returns:
            Configured FastMCP server instance
        """
        auth_provider = create_google_auth_provider(self.config, self.clients_repository)
        mcp = FastMCP(name="Swarmnetics MCP")
        # mcp.add_middleware(SecurityFilterMiddleware(self.user_config_repository))
        return mcp

    def _attach_prompts_to_proxy(self, proxy: FastMCP, user_config) -> None:
        """
        Attach prompts from user configuration to a proxy.

        Args:
            proxy: FastMCP proxy instance to attach prompts to
            user_config: UserMCPConfig containing prompt configurations
        """
        # Add default owner prompt
        proxy.add_prompt(Prompt.from_function(
            lambda: f"This is a tool owned by {user_config.email}.",
            name="/owner",
            description="Indicates the owner of this tool."
        ))

        # Add custom prompts from config
        if user_config.prompts:
            for prompt_config in user_config.prompts:
                if prompt_config.enabled:
                    proxy.add_prompt(prompt_config.to_prompt())
                    logger.info(f"Added prompt '{prompt_config.name}' for {user_config.email}")

    async def _mount_user_servers(self, mcp: FastMCP) -> None:
        """
        Import MCP servers for each user and mount them as proxy clients.

        Args:
            mcp: FastMCP server instance to mount clients to
        """
        user_configs = await self.user_config_repository.get_all_user_configs()
        print(f"Found {len(user_configs)} user configurations to import.")
        for user_config in user_configs:
            try:
                client = CustomProxyClient(
                    user_config.to_client_config(),
                    owner_email=str(user_config.email)
                )
                await client.__aenter__()
                proxy = FastMCP.as_proxy(client)
                self._attach_prompts_to_proxy(proxy, user_config)
                mcp.mount(proxy)

                logger.info(f"Imported servers for {user_config.email}")
            except Exception as e:
                logger.error(f"Failed to import servers for {user_config.email}: {e}")

    async def start_mcp(self) -> None:
        """Initialize and run the MCP server with all user configurations."""
        # Create server
        self.mcp = await self._create_mcp_server()

        # Import user servers
        await self._mount_user_servers(self.mcp)

        await self._print_tools(self.mcp)

        # Start server
        mcp_config = self.config.mcp
        logger.info(f"Starting MCP Composer on {mcp_config.transport}://{mcp_config.host}:{mcp_config.port}")
        await self.mcp.run_async(transport=mcp_config.transport, host=mcp_config.host, port=mcp_config.port)

    @staticmethod
    async def _print_tools(mcp: FastMCP) -> None:
        """Print available tools in the MCP server."""
        tools = await mcp.get_tools()
        if tools:
            logger.info("Available tools:")
            for _, tool in tools.items():
                logger.info(f"- {tool.name}: {tool.description}")
        else:
            logger.warning("No tools available in the MCP server.")
