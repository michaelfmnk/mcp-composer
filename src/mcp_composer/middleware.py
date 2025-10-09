import logging

from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.tools import Tool
from mcp import McpError, ErrorData, types as mt

from mcp_composer.db import mongodb_client


# not for production. for tool segregation purposes only
class SecurityFilterMiddleware(Middleware):
    async def on_list_tools(
            self,
            context: MiddlewareContext[mt.ListToolsRequest],
            call_next: CallNext[mt.ListToolsRequest, list[Tool]],
    ) -> list[Tool]:
        from fastmcp.server.dependencies import get_access_token
        email = get_access_token().claims.get("email")

        config = mongodb_client.get_user_config(email)
        if not config:
            logging.warning("Unauthorized access attempt by %s;", email)
            raise McpError(ErrorData(
                code=32000,
                message="User is not authorized to access this MCP.",
            ))

        tools = await call_next(context)
        filtered_tools = []
        for tool in tools:
            owner_email = tool._client.owner_email
            print(owner_email)
            if owner_email == email:
                filtered_tools.append(tool)

        return filtered_tools
