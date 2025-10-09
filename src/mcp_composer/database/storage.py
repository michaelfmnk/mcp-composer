"""MongoDB-based storage adapter for OAuth tokens and client data."""
import logging

from fastmcp.utilities.storage import KVStorage

logger = logging.getLogger(__name__)


class MongoClientStorage(KVStorage):
    """
    Storage adapter for OAuth tokens and client data.

    Adapts ClientsRepository to the KVStorage interface required by FastMCP.
    """

    def __init__(self, clients_repository):
        """
        Initialize MongoDB client storage with repository.

        Args:
            clients_repository: ClientsRepository instance for data access
        """
        self.clients_repository = clients_repository

    async def get(self, key: str) -> dict | None:
        """
        Retrieve client data by key.

        Args:
            key: Client identifier

        Returns:
            Client data dictionary or None if not found
        """
        return await self.clients_repository.get_client(key)

    async def set(self, key: str, value: dict) -> None:
        """
        Store or update client data.

        Args:
            key: Client identifier
            value: Client data dictionary to store
        """
        await self.clients_repository.set_client(key, value)

    async def delete(self, key: str) -> None:
        """
        Delete client data by key.

        Args:
            key: Client identifier
        """
        await self.clients_repository.delete_client(key)
