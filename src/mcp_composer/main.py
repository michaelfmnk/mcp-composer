"""Main entry point for MCP Composer server."""
import asyncio
import logging
import signal

from mcp_composer.app import McpComposerApp
from mcp_composer.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run(app: McpComposerApp) -> None:
    """Run the application with proper signal handling."""
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def signal_handler():
        """Handle shutdown signals."""
        logger.info("Received shutdown signal, initiating graceful shutdown...")
        shutdown_event.set()

    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # Initialize the app
        await app.initialize()

        # Start the server in a task
        server_task = asyncio.create_task(app.start())

        # Wait for shutdown signal
        await shutdown_event.wait()

        # Cancel the server task
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    finally:
        await app.shutdown()


def main() -> None:
    """Main entry point for the application."""
    # Load and validate configuration (Pydantic validates automatically)
    config = Config()

    # Create application instance
    app = McpComposerApp(config)

    # Run the application with signal handling
    asyncio.run(run(app))


if __name__ == "__main__":
    main()