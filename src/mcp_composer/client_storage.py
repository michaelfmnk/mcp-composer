import logging

from fastmcp.utilities.storage import KVStorage

from mcp_composer.db import mongodb_client

logger = logging.getLogger(__name__)


class MongoClientStorage(KVStorage):
    """MongoDB-based client storage for OAuth tokens and client data."""

    def __init__(self, mongodb_client):
        """
        Initialize MongoDB client storage.

        Args:
            mongodb_client: MongoDBClient instance with connection to MongoDB
        """
        self.mongodb_client = mongodb_client
        self._clients_collection = None

    def _get_collection(self):
        """Get the clients collection."""
        if self._clients_collection is None:
            if self.mongodb_client.db is None:
                raise RuntimeError("MongoDB client not connected. Call mongodb_client.connect() first.")
            self._clients_collection = self.mongodb_client.db["clients"]
        return self._clients_collection

    async def get(self, key: str) -> dict | None:
        """
        Retrieve client data by key.

        Args:
            key: Client identifier

        Returns:
            Client data dictionary or None if not found
        """
        try:
            collection = self._get_collection()
            document = await collection.find_one({"_id": key})
            if document:
                # Remove MongoDB's _id field before returning
                document.pop("_id", None)
                return document
            return None
        except Exception as e:
            logger.error(f"Error retrieving client data for key {key}: {e}")
            return None

    async def set(self, key: str, value: dict) -> None:
        """
        Store or update client data.

        Args:
            key: Client identifier
            value: Client data dictionary to store
        """
        try:
            collection = self._get_collection()
            await collection.update_one(
                {"_id": key},
                {"$set": value},
                upsert=True
            )
            logger.info(f"Stored client data for key: {key}")
        except Exception as e:
            logger.error(f"Error storing client data for key {key}: {e}")
            raise

    async def delete(self, key: str) -> None:
        """
        Delete client data by key.

        Args:
            key: Client identifier
        """
        try:
            collection = self._get_collection()
            result = await collection.delete_one({"_id": key})
            if result.deleted_count > 0:
                logger.info(f"Deleted client data for key: {key}")
            else:
                logger.warning(f"No client data found to delete for key: {key}")
        except Exception as e:
            logger.error(f"Error deleting client data for key {key}: {e}")
            raise
