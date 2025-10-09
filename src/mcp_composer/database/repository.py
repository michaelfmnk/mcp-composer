"""Repository pattern for user MCP configurations."""
import logging
from typing import Optional

from mcp_composer.models import UserMCPConfig

logger = logging.getLogger(__name__)


class UserConfigRepository:
    """Repository for managing user MCP configurations in MongoDB."""

    def __init__(self, db_client, collection_name: str = "mcp_configs"):
        """
        Initialize repository with database client.

        Args:
            db_client: MongoDBClient instance
            collection_name: Name of the MongoDB collection
        """
        self.db_client = db_client
        self.collection_name = collection_name

    def _get_collection(self):
        """Get the user configs collection."""
        return self.db_client.get_collection(self.collection_name)

    async def get_user_config(self, email: str) -> Optional[UserMCPConfig]:
        """
        Get MCP configuration for a specific user by email.

        Args:
            email: User's email address

        Returns:
            UserMCPConfig object or None if not found
        """
        try:
            collection = self._get_collection()
            document = await collection.find_one({"_id": email})
            if document:
                return UserMCPConfig.from_document(document)
            logger.warning(f"No configuration found for user: {email}")
            return None
        except Exception as e:
            logger.error(f"Error fetching config for {email}: {e}")
            return None

    async def get_all_user_configs(self) -> list[UserMCPConfig]:
        """
        Get all user configurations.

        Returns:
            List of UserMCPConfig objects
        """
        try:
            configs: list[UserMCPConfig] = []
            collection = self._get_collection()
            cursor = collection.find({})
            async for document in cursor:
                try:
                    config = UserMCPConfig.from_document(document)
                    configs.append(config)
                except Exception as e:
                    logger.error(f"Error parsing config document: {e}")
                    continue
            logger.info(f"Loaded configurations for {len(configs)} users")
            return configs
        except Exception as e:
            logger.error(f"Error fetching all configs: {e}")
            return []

    async def set_user_config(self, user_config: UserMCPConfig) -> None:
        """
        Set or update MCP configuration for a user.

        Args:
            user_config: UserMCPConfig object
        """
        try:
            collection = self._get_collection()
            document = user_config.to_document()
            await collection.update_one(
                {"_id": document["_id"]},
                {"$set": {"mcpServers": document["mcpServers"]}},
                upsert=True
            )
            logger.info(f"Updated configuration for user: {user_config.email}")
        except Exception as e:
            logger.error(f"Error setting config for {user_config.email}: {e}")
            raise
