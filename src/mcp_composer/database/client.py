"""MongoDB client connection management."""
import logging
from typing import Optional, Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from mcp_composer.config import MongoConfig

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client for database connection management."""

    def __init__(self, mongo_config: MongoConfig):
        """
        Initialize MongoDB client with configuration.

        Args:
            mongo_config: MongoDB configuration
        """
        self.config = mongo_config
        self.client: Optional[AsyncMongoClient[dict[str, Any]]] = None
        self.db: Optional[AsyncDatabase[dict[str, Any]]] = None

    async def connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncMongoClient(self.config.connection_string)
            self.db = self.client[self.config.database_name]
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.config.database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            await self.client.close()
            logger.info("MongoDB connection closed")

    def get_collection(self, collection_name: str):
        """Get a MongoDB collection by name."""
        if self.db is None:
            raise RuntimeError("MongoDB client not connected. Call connect() first.")
        return self.db[collection_name]
