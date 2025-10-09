"""Custom proxy client with ownership tracking."""
from fastmcp.server.proxy import ProxyClient


class CustomProxyClient(ProxyClient):
    """
    Custom proxy client that tracks the owner email for tool filtering.

    Extends FastMCP's ProxyClient to add owner_email attribute which is used
    by SecurityFilterMiddleware to filter tools per user.
    """

    def __init__(self, *args, owner_email: str, **kwargs):
        """
        Initialize custom proxy client.

        Args:
            owner_email: Email of the user who owns this MCP server
            *args: Positional arguments for ProxyClient
            **kwargs: Keyword arguments for ProxyClient
        """
        self.owner_email = owner_email
        super().__init__(*args, **kwargs)
