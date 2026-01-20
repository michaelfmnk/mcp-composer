"""Custom proxy client with ownership tracking for multi-tenant tool isolation."""

import mcp
from fastmcp.server.providers.proxy import ProxyClient


class CustomProxyClient(ProxyClient):
    """
    Extended ProxyClient that tracks ownership for multi-tenant isolation.

    Each user's MCP servers are wrapped in this client, which injects the
    owner's email into tool metadata for filtering by SecurityFilterMiddleware.

    Attributes:
        owner_email: Email address of the user who owns this MCP server configuration.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize custom proxy client with owner tracking.

        Args:
            *args: Positional arguments passed to ProxyClient (typically client config).
            **kwargs: Keyword arguments for ProxyClient. Must include 'owner_email'
                to identify the user who owns this server configuration.
        """
        super().__init__(*args, **kwargs)

    async def list_tools(self: "CustomProxyClient") -> list[mcp.types.Tool]:
        """
        List tools available in the proxied MCP server with ownership tags.

        Overrides ProxyClient's list_tools to inject owner_email into each tool's
        metadata tags, enabling SecurityFilterMiddleware to filter tools by owner.

        Returns:
            List of MCP tools with owner_email added to their fastmcp tags.
        """
        tools = await super().list_tools()
        for tool in tools:
            if tool.meta is None:
                tool.meta = {'fastmcp': {'tags': []}}
            tool.meta['fastmcp']['tags'].append(self.owner_email)

        return tools
