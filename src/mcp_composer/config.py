import os
from dotenv import load_dotenv


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self):
        self.google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        self.base_url = os.environ.get("BASE_URL")
        self.fmcp_port = int(os.environ.get("FMCP_PORT", "8000"))

        # MongoDB configuration
        self.mongodb_uri = os.environ.get("MONGODB_URI")
        self.mongodb_database = os.environ.get("MONGODB_DATABASE", "fmcp")
        self.mongodb_collection = os.environ.get("MONGODB_COLLECTION", "mcp_configs")

    def validate(self):
        """Validate that required configuration is present."""
        required_fields = [
            ("GOOGLE_CLIENT_ID", self.google_client_id),
            ("GOOGLE_CLIENT_SECRET", self.google_client_secret),
            ("BASE_URL", self.base_url),
            ("MONGODB_URI", self.mongodb_uri),
        ]

        missing_fields = [
            field_name for field_name, field_value in required_fields
            if not field_value
        ]

        if missing_fields:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")


# Global config instance
load_dotenv()
config = Config()