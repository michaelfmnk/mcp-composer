import logging

from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider

from mcp_composer.mcp_client import CustomProxyClient
from mcp_composer.middleware import SecurityFilterMiddleware
from .client_storage import MongoClientStorage
from .config import config
from .db import mongodb_client
from .models import UserMCPConfig

logging.basicConfig(level=logging.INFO)

config.validate()


async def load_user_configs() -> list[UserMCPConfig]:
    """Load all MCP configurations from MongoDB."""
    await mongodb_client.connect()
    user_configs = await mongodb_client.get_all_user_configs()
    return user_configs


async def import_user_servers(mcp: FastMCP, user_configs: list[UserMCPConfig]) -> None:
    """Import MCP servers for each user and tag their tools."""
    for user_config in user_configs:
        try:
            client = CustomProxyClient(user_config.to_client_config(), owner_email=str(user_config.email))
            await client.__aenter__()
            mcp.mount(FastMCP.as_proxy(client))
            logging.info(f"Imported servers for {user_config.email}")
        except Exception as e:
            logging.error(f"Failed to import servers for {user_config.email}: {e}")


async def print_tools(mcp: FastMCP) -> None:
    """Print all available tools with their tags."""
    tools = await mcp.get_tools()
    for k, v in tools.items():
        print("Tool:", v.name, "Tags:", v.tags)


async def start() -> None:
    auth_provider = GoogleProvider(
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        base_url=config.base_url,
        required_scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        client_storage=MongoClientStorage(mongodb_client)
    )
    mcp = FastMCP(name="Swarmnetics MCP", auth=auth_provider)
    mcp.add_middleware(SecurityFilterMiddleware())

    # Import servers
    user_configs: list[UserMCPConfig] = await load_user_configs()
    await import_user_servers(mcp, user_configs)
    await print_tools(mcp)

    print("Starting FMCP on port", config.fmcp_port)
    await mcp.run_async(transport="http", host="0.0.0.0", port=config.fmcp_port)


def main() -> None:
    import asyncio
    asyncio.run(start())

if __name__ == "__main__":
    main()