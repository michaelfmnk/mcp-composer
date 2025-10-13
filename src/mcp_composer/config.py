"""Application configuration management."""
from enum import Enum
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MountMode(str, Enum):
    """Downstream MCP server mount mode."""
    LIVE = "live"
    STATIC = "static"


class AuthProviderType(str, Enum):
    """Authentication provider type."""
    GOOGLE = "google"
    NONE = "none"


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

    # Authentication configuration
    auth_provider: AuthProviderType = Field(
        default=AuthProviderType.GOOGLE,
        alias="AUTH_PROVIDER",
        description="Authentication provider: 'google' for Google OAuth, 'none' to disable auth"
    )

    # Google OAuth configuration (optional when auth_provider is 'none')
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")

    # MCP server configuration
    mcp_host: str = Field(default="0.0.0.0", alias="MCP_HOST")
    mcp_port: int = Field(default=8000, alias="MCP_PORT")
    mcp_transport: str = Field(default="http", alias="MCP_TRANSPORT")

    # MongoDB configuration
    mongodb_uri: str = Field(alias="MONGODB_URI")
    mongodb_database: str = Field(default="mcp_composer", alias="MONGODB_DATABASE")

    # MCP composition mode
    mcp_composition_mode: MountMode = Field(
        default=MountMode.LIVE,
        alias="MCP_COMPOSITION_MODE",
        description="Composition mode for downstream MCP servers: 'live' uses mcp.mount(), 'static' uses mcp.import_server()"
    )

    @field_validator("google_client_id", "google_client_secret")
    @classmethod
    def validate_google_credentials(cls, v, info):
        """Validate that Google credentials are provided when auth_provider is GOOGLE."""
        # Check if auth_provider field exists in values
        auth_provider = info.data.get("auth_provider")

        # If auth_provider is GOOGLE, credentials are required
        if auth_provider == AuthProviderType.GOOGLE and v is None:
            field_name = info.field_name
            raise ValueError(
                f"{field_name} is required when AUTH_PROVIDER is 'google'"
            )
        return v

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
        )