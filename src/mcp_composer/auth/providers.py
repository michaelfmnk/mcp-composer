"""OAuth authentication providers."""
from typing import Any

from fastmcp.server.auth.providers.google import GoogleProvider
from key_value.aio.stores.mongodb.store import MongoDBStore
from pymongo.asynchronous.mongo_client import AsyncMongoClient

from mcp_composer.config import Config


async def create_google_auth_provider(config: Config, db_client: AsyncMongoClient[dict[str, Any]]) -> GoogleProvider:
    """
    Create and configure Google OAuth provider.

    Args:
        config: Application configuration
        db_client: MongoDBClient instance with established connection

    Returns:
        Configured GoogleProvider instance
    """
    # Create MongoDB store using the shared MongoDB client
    client_storage = MongoDBStore(
        client=db_client,
        db_name=config.mongodb_database,
        default_collection="oauth_clients"
    )

    provider = GoogleProvider(
        client_id=config.google.client_id,
        client_secret=config.google.client_secret,
        base_url=config.base_url,
        require_authorization_consent=False,
        required_scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],
        client_storage=client_storage
    )
    provider._extra_authorize_params = {
        "access_type": "offline",
        "prompt": "consent"
    }
    return provider
