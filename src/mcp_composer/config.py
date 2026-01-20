"""Application configuration management."""
from enum import Enum
from typing import Optional, Literal

from fastmcp.server.server import Transport
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthProviderType(str, Enum):
    """Authentication provider type."""
    GOOGLE = "google"
    NONE = "none"


class MongoConfig(BaseSettings):
    """
    MongoDB connection configuration.

    Attributes:
        connection_string: MongoDB connection URI (e.g., 'mongodb://localhost:27017').
        database_name: Name of the database to use for storing MCP configurations.
    """

    model_config = SettingsConfigDict(env_prefix="MONGODB_")

    connection_string: str = Field(alias="uri")
    database_name: str = Field(default="mcp_composer", alias="database")


class GoogleOAuthConfig(BaseSettings):
    """
    Google OAuth configuration for authentication.

    Attributes:
        client_id: Google OAuth 2.0 client ID from Google Cloud Console.
        client_secret: Google OAuth 2.0 client secret from Google Cloud Console.
    """

    model_config = SettingsConfigDict(env_prefix="GOOGLE_")

    client_id: str
    client_secret: str


class MCPServerConfig(BaseSettings):
    """
    MCP server configuration for network binding.

    Attributes:
        host: Host address to bind the server to (default: '0.0.0.0').
        port: Port number to listen on (default: 8000).
        transport: Transport protocol type (options: 'stdio', 'http', 'sse', 'streamable-http').
    """

    model_config = SettingsConfigDict(env_prefix="MCP_")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    transport: Transport = Field(default="http")


class Config(BaseSettings):
    """
    Main application configuration loaded from environment variables.

    This class aggregates all configuration settings and provides nested config
    objects via properties for Google OAuth, MCP server, and MongoDB settings.

    Attributes:
        base_url: Base URL for the application (used for OAuth callbacks).
        auth_provider: Authentication provider type ('google' or 'none').
        google_client_id: Google OAuth client ID (required when auth_provider is 'google').
        google_client_secret: Google OAuth client secret (required when auth_provider is 'google').
        mcp_host: Host address for the MCP server.
        mcp_port: Port number for the MCP server.
        mcp_transport: Transport protocol for MCP communication.
        mongodb_uri: MongoDB connection URI.
        mongodb_database: MongoDB database name.
    """

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