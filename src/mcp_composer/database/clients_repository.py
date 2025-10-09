"""Repository for OAuth client data storage."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ClientsRepository:
    """Repository for managing OAuth client data in MongoDB."""

    def __init__(self, db_client, collection_name: str = "clients"):
        """
        Initialize clients repository with database client.

        Args:
            db_client: MongoDBClient instance
            collection_name: Name of the MongoDB collection for client data
        """
        self.db_client = db_client
        self.collection_name = collection_name

    def _get_collection(self):
        """Get the clients collection."""
        return self.db_client.get_collection(self.collection_name)

    async def get_client(self, client_id: str) -> Optional[dict]:
        """
        Get OAuth client data by client ID.

        Args:
            client_id: Client identifier

        Returns:
            Client data dictionary or None if not found
        """
        try:
            collection = self._get_collection()
            document = await collection.find_one({"_id": client_id})
            if document:
                # Remove MongoDB's _id field before returning
                document.pop("_id", None)
                return document
            return None
        except Exception as e:
            logger.error(f"Error retrieving client data for {client_id}: {e}")
            return None

    async def set_client(self, client_id: str, client_data: dict) -> None:
        """
        Store or update OAuth client data.

        Args:
            client_id: Client identifier
            client_data: Client data dictionary to store
        """
        try:
            collection = self._get_collection()
            await collection.update_one(
                {"_id": client_id},
                {"$set": client_data},
                upsert=True
            )
            logger.info(f"Stored client data for: {client_id}")
        except Exception as e:
            logger.error(f"Error storing client data for {client_id}: {e}")
            raise

    async def delete_client(self, client_id: str) -> None:
        """
        Delete OAuth client data by client ID.

        Args:
            client_id: Client identifier
        """
        try:
            collection = self._get_collection()
            result = await collection.delete_one({"_id": client_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted client data for: {client_id}")
            else:
                logger.warning(f"No client data found to delete for: {client_id}")
        except Exception as e:
            logger.error(f"Error deleting client data for {client_id}: {e}")
            raise
