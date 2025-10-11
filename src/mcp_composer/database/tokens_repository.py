import logging

from mcp.server.auth.provider import AccessToken, RefreshToken
from mcp_composer.models import OAuthToken, TokenType

logger = logging.getLogger(__name__)


class TokensRepository:
    def __init__(self, db_client, collection_name: str = "tokens"):
        """
        Initialize tokens repository with database client.

        Args:
            db_client: MongoDBClient instance
            collection_name: Name of the MongoDB collection for tokens
        """
        self.db_client = db_client
        self.collection_name = collection_name

    async def delete_all(self):
        """Delete all tokens from the collection."""
        collection = self._get_collection()
        await collection.delete_many({})
        logger.info("Deleted all tokens from the collection")

    async def save_all(self, tokens: list[OAuthToken]):
        """Delete all tokens from the collections and save new ones."""
        collection = self._get_collection()
        await collection.delete_many({})
        if tokens:
            documents = [token.to_document() for token in tokens]
            await collection.insert_many(documents)
            logger.info(f"Saved {len(tokens)} tokens to the collection")
        else:
            logger.info("No tokens to save; collection cleared")

    async def get_access_token_relations(self) -> dict[str, AccessToken]:
        """Get a mapping of access tokens to their token strings."""
        collection = self._get_collection()
        cursor = collection.find({"type": TokenType.ACCESS.value})

        result = {}
        async for document in cursor:
            oauth_token: OAuthToken = OAuthToken.from_document(document)
            if oauth_token and oauth_token.access_token:
                result[oauth_token.token] = oauth_token.access_token
        return result

    async def get_refresh_token_relations(self) -> dict[str, RefreshToken]:
        """Get a mapping of refresh tokens to their token strings."""
        collection = self._get_collection()
        cursor = collection.find({"type": TokenType.REFRESH.value})

        result = {}
        async for document in cursor:
            oauth_token: OAuthToken = OAuthToken.from_document(document)
            if oauth_token and oauth_token.refresh_token:
                result[oauth_token.token] = oauth_token.refresh_token
        return result

    def _get_collection(self):
        """Get the tokens collection."""
        return self.db_client.get_collection(self.collection_name)
