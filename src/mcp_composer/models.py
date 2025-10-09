from typing import Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    model_config = ConfigDict(extra='allow')

    url: str | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None


class MCPServersConfig(BaseModel):
    """Container for multiple MCP server configurations."""
    model_config = ConfigDict(extra='forbid')

    servers: dict[str, MCPServerConfig] = Field(default_factory=dict)

    @classmethod
    def from_mcp_servers_dict(cls, mcp_servers: dict[str, Any]) -> "MCPServersConfig":
        """Create from the mcpServers dictionary format."""
        servers = {
            name: MCPServerConfig(**config)
            for name, config in mcp_servers.items()
        }
        return cls(servers=servers)

    def to_mcp_servers_dict(self) -> dict[str, Any]:
        """Convert to mcpServers dictionary format for FastMCP Client."""
        return {
            name: server.model_dump(exclude_none=True)
            for name, server in self.servers.items()
        }


class UserMCPConfig(BaseModel):
    """User's MCP configuration document stored in MongoDB."""
    model_config = ConfigDict(extra='forbid')

    email: EmailStr = Field(alias="_id")
    mcp_servers: MCPServersConfig = Field(alias="mcpServers")

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "UserMCPConfig":
        """Create from MongoDB document."""
        return cls(
            _id=document["_id"],
            mcpServers=MCPServersConfig.from_mcp_servers_dict(document.get("mcpServers", {}))
        )

    def to_document(self) -> dict[str, Any]:
        """Convert to MongoDB document format."""
        return {
            "_id": self.email,
            "mcpServers": self.mcp_servers.to_mcp_servers_dict()
        }

    def to_client_config(self) -> dict[str, Any]:
        """Convert to FastMCP Client config format."""
        return {
            "mcpServers": self.mcp_servers.to_mcp_servers_dict()
        }
