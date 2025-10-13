from typing import Any

from fastmcp import MCPPrompt, MCPPromptArgument
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class MCPPromptArgumentConfig(BaseModel):
    """Configuration for a single argument of an MCP prompt."""
    model_config = ConfigDict(extra='forbid')

    name: str = Field(..., description="The argument name")
    description: str = Field(..., description="Description of the argument")
    required: bool = Field(False, description="Whether the argument is required")

class PromptConfig(BaseModel):
    """Configuration for a prompt to be attached to an MCP server."""
    model_config = ConfigDict(extra='forbid')

    message: str = Field(..., description="The prompt message/content to return")
    name: str = Field(..., description="The prompt name (e.g., '/owner')")
    title: str | None = Field(None, description="Optional prompt title")
    description: str = Field(..., description="Description of what this prompt provides")
    enabled: bool = Field(True, description="Whether this prompt is enabled")
    arguments: list[MCPPromptArgumentConfig] | None = Field([], description="List of arguments for the prompt")

    def to_mcp_prompt(self) -> MCPPrompt:
        """Convert to MCPPrompt for use with FastMCP."""

        return MCPPrompt(
            name=self.name,
            arguments=arguments,
            title=self.title,
            description=[
                MCPPromptArgument(
                    name=arg.name,
                    description=arg.description,
                    required=arg.required,
                )
                for arg in self.arguments or []
            ],
        )


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
    prompts: list[PromptConfig] | None = None

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "UserMCPConfig":
        """Create from MongoDB document."""
        # Convert prompts list to PromptConfig objects if present
        prompts = None
        if "prompts" in document and document["prompts"] is not None:
            prompts = [
                PromptConfig(**prompt) if isinstance(prompt, dict) else prompt
                for prompt in document["prompts"]
            ]

        return cls(
            _id=document["_id"],
            mcpServers=MCPServersConfig.from_mcp_servers_dict(document.get("mcpServers", {})),
            prompts=prompts
        )

    def to_document(self) -> dict[str, Any]:
        """Convert to MongoDB document format."""
        doc = {
            "_id": self.email,
            "mcpServers": self.mcp_servers.to_mcp_servers_dict()
        }
        if self.prompts is not None:
            doc["prompts"] = [prompt.model_dump(exclude_none=True) for prompt in self.prompts]
        return doc

    def to_client_config(self) -> dict[str, Any]:
        """Convert to FastMCP Client config format."""
        return {
            "mcpServers": self.mcp_servers.to_mcp_servers_dict()
        }
