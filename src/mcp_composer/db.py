import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from .config import config
from .models import UserMCPConfig

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client for MCP configuration storage."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None

    async def connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(config.mongodb_uri)
            self.db = self.client[config.mongodb_database]
            self.collection = self.db[config.mongodb_collection]
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {config.mongodb_database}.{config.mongodb_collection}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    async def get_user_config(self, email: str) -> Optional[UserMCPConfig]:
        """
        Get MCP configuration for a specific user by email.

        Args:
            email: User's email address

        Returns:
            UserMCPConfig object or None if not found
        """
        try:
            document = await self.collection.find_one({"_id": email})
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
            cursor = self.collection.find({})
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
            document = user_config.to_document()
            await self.collection.update_one(
                {"_id": document["_id"]},
                {"$set": {"mcpServers": document["mcpServers"]}},
                upsert=True
            )
            logger.info(f"Updated configuration for user: {user_config.email}")
        except Exception as e:
            logger.error(f"Error setting config for {user_config.email}: {e}")
            raise


# Global MongoDB client instance
mongodb_client = MongoDBClient()
