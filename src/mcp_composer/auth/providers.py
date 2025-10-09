"""OAuth authentication providers."""
from fastmcp.server.auth.providers.google import GoogleProvider

from mcp_composer.config import Config
from mcp_composer.database.storage import MongoClientStorage


def create_google_auth_provider(config: Config, clients_repository) -> GoogleProvider:
    """
    Create and configure Google OAuth provider.

    Args:
        config: Application configuration
        clients_repository: ClientsRepository instance for OAuth token storage

    Returns:
        Configured GoogleProvider instance
    """
    google_config = config.google
    return GoogleProvider(
        client_id=google_config.client_id,
        client_secret=google_config.client_secret,
        base_url=config.base_url,
        required_scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        client_storage=MongoClientStorage(clients_repository)
    )
