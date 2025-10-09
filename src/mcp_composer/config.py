"""Application configuration management."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoConfig(BaseSettings):
    """MongoDB connection configuration."""

    model_config = SettingsConfigDict(env_prefix="MONGODB_")

    connection_string: str = Field(alias="uri")
    database_name: str = Field(default="mcp_composer", alias="database")


class GoogleOAuthConfig(BaseSettings):
    """Google OAuth configuration."""

    model_config = SettingsConfigDict(env_prefix="GOOGLE_")

    client_id: str
    client_secret: str


class MCPServerConfig(BaseSettings):
    """MCP server configuration."""

    model_config = SettingsConfigDict(env_prefix="MCP_")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    transport: str = Field(default="http")


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    base_url: str = Field(alias="BASE_URL")

    # Google OAuth configuration
    google_client_id: str = Field(alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(alias="GOOGLE_CLIENT_SECRET")

    # MCP server configuration
    mcp_host: str = Field(default="0.0.0.0", alias="MCP_HOST")
    mcp_port: int = Field(default=8000, alias="MCP_PORT")
    mcp_transport: str = Field(default="http", alias="MCP_TRANSPORT")

    # MongoDB configuration
    mongodb_uri: str = Field(alias="MONGODB_URI")
    mongodb_database: str = Field(default="mcp_composer", alias="MONGODB_DATABASE")

    @property
    def google(self) -> GoogleOAuthConfig:
        """Get Google OAuth configuration as a nested config object."""
        return GoogleOAuthConfig(
            client_id=self.google_client_id,
            client_secret=self.google_client_secret
        )

    @property
    def mcp(self) -> MCPServerConfig:
        """Get MCP server configuration as a nested config object."""
        return MCPServerConfig(
            host=self.mcp_host,
            port=self.mcp_port,
            transport=self.mcp_transport
        )

    @property
    def mongo(self) -> MongoConfig:
        """Get MongoDB configuration as a nested config object."""
        return MongoConfig(
            uri=self.mongodb_uri,
            database=self.mongodb_database,
            collection=self.mongodb_collection
        )