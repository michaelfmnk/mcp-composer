"""Main application class for MCP Composer."""
import logging

from pymongo.asynchronous.mongo_client import AsyncMongoClient

from mcp_composer.config import Config
from mcp_composer.database.client import MongoDBClient
from mcp_composer.database.repository import UserConfigRepository
from mcp_composer.database.tokens_repository import TokensRepository
from mcp_composer.server.manager import MCPServerManager

logger = logging.getLogger(__name__)


class McpComposerApp:
    """
    Main application class that manages all components and dependencies.

    This class eliminates global state by managing all component instances
    and their dependencies through dependency injection.
    """

    def __init__(self, config: Config):
        """
        Initialize the application with configuration.

        Args:
            config: Application configuration
        """
        self.config = config

        # Initialize database components
        self.db_client = MongoDBClient(config.mongo)
        self.user_config_repository = UserConfigRepository(self.db_client)
        self.tokens_repository = TokensRepository(self.db_client)

        # Initialize server components
        self.server_manager = MCPServerManager(
            config=self.config,
            db_client=self.db_client,
            user_config_repository=self.user_config_repository,
            tokens_repository=self.tokens_repository
        )

    async def initialize(self) -> None:
        """Initialize the application and connect to dependencies."""
        logger.info("Initializing MCP Composer...")
        await self.db_client.connect()
        logger.info("MCP Composer initialized successfully")

    async def start(self) -> None:
        """Start the MCP server."""
        await self.server_manager.start_mcp()

    async def shutdown(self) -> None:
        """Shutdown the application and cleanup resources."""
        logger.info("Shutting down MCP Composer...")
        await self.server_manager.dump_auth_state()
        await self.db_client.close()
        logger.info("MCP Composer shutdown complete")
