"""OAuth authentication providers."""
from fastmcp.server.auth.providers.google import GoogleProvider
from key_value.aio.protocols import AsyncKeyValue

from mcp_composer.config import GoogleOAuthConfig


def create_google_auth_provider(
        base_url: str,
        config: GoogleOAuthConfig,
        client_storage: AsyncKeyValue | None = None,
) -> GoogleProvider:
    """
    Create and configure Google OAuth provider.

    Args:
        base_url: Base URL for OAuth callbacks (e.g., 'http://localhost:8000').
        config: Google OAuth configuration containing client_id and client_secret.
        client_storage: Optional async key-value store for persisting OAuth client data.

    Returns:
        Configured GoogleProvider instance with offline access and consent prompt.
    """
    provider = GoogleProvider(
        client_id=config.client_id,
        client_secret=config.client_secret,
        base_url=base_url,
        required_scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", ],
        client_storage=client_storage,
        require_authorization_consent=False
    )
    provider._extra_authorize_params = {
        "access_type": "offline",
        "prompt": "consent"
    }
    return provider
