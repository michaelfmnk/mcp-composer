"""Main entry point for MCP Composer server."""
import asyncio
import logging

from mcp_composer.app import McpComposerApp
from mcp_composer.config import Config

logging.basicConfig(level=logging.INFO)


def main() -> None:
    """Main entry point for the application."""
    # Load and validate configuration (Pydantic validates automatically)
    config = Config()

    # Create application instance
    app = McpComposerApp(config)

    # Run the application
    asyncio.run(app.run())


if __name__ == "__main__":
    main()