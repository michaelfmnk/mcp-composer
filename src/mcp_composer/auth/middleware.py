"""Security middleware for tool filtering and authorization."""
import logging

from fastmcp.prompts import Prompt
from fastmcp.resources import Resource
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.tools import Tool
from mcp import McpError, ErrorData, types as mt

logger = logging.getLogger(__name__)


# not for production. for tool segregation purposes only
class SecurityFilterMiddleware(Middleware):
    """
    Middleware that filters MCP resources based on authenticated user's ownership.

    This middleware intercepts list requests for tools, prompts, and resources,
    filtering them to only return items owned by the currently authenticated user.
    Ownership is determined by checking the owner_email attribute on proxy clients
    or by matching tool tags against the user's email.

    Note:
        This middleware is intended for development and tool segregation purposes.
        Additional security measures may be needed for production deployments.
    """

    def __init__(self, user_config_repository):
        """
        Initialize middleware with user config repository.

        Args:
            user_config_repository: Repository for validating user authorization
                and accessing user MCP configurations.
        """
        super().__init__()
        self.user_config_repository = user_config_repository

    async def on_list_tools(
            self,
            context: MiddlewareContext[mt.ListToolsRequest],
            call_next: CallNext[mt.ListToolsRequest, list[Tool]],
    ) -> list[Tool]:
        """
        Filter tools to only show those owned by the authenticated user.

        Args:
            context: Middleware context containing the request
            call_next: Callback to invoke next middleware or handler

        Returns:
            Filtered list of tools owned by the user

        Raises:
            McpError: If user is not authorized
        """
        from fastmcp.server.dependencies import get_access_token
        email = get_access_token().claims.get("email")

        config = await self.user_config_repository.get_user_config(email)
        if not config:
            logger.warning(f"Unauthorized access attempt by {email}")
            raise McpError(ErrorData(
                code=32000,
                message="User is not authorized to access this MCP.",
            ))

        tools: list[Tool] = await call_next(context)
        filtered_tools = []
        for tool in tools:
            if email in tool.tags:
                filtered_tools.append(tool)

        logger.info(f"Filtered {len(filtered_tools)}/{len(tools)} tools for {email}")
        return filtered_tools

    async def on_list_prompts(
        self,
        context: MiddlewareContext[mt.ListPromptsRequest],
        call_next: CallNext[mt.ListPromptsRequest, list[Prompt]],
    ) -> list[Prompt]:
        """
        Filter prompts to only show those owned by the authenticated user.

        Args:
            context: Middleware context containing the request
            call_next: Callback to invoke next middleware or handler

        Returns:
            Filtered list of prompts owned by the user

        Raises:
            McpError: If user is not authorized
        """
        from fastmcp.server.dependencies import get_access_token
        email = get_access_token().claims.get("email")

        config = await self.user_config_repository.get_user_config(email)
        if not config:
            logger.warning(f"Unauthorized access attempt by {email}")
            raise McpError(ErrorData(
                code=32000,
                message="User is not authorized to access this MCP.",
            ))

        prompts = await call_next(context)
        filtered_prompts = []
        for prompt in prompts:
            owner_email = prompt._client.owner_email
            logger.debug(f"Prompt {prompt.name} owned by {owner_email}")
            if owner_email == email:
                filtered_prompts.append(prompt)

        logger.info(f"Filtered {len(filtered_prompts)}/{len(prompts)} prompts for {email}")
        return filtered_prompts

    async def on_list_resources(
        self,
        context: MiddlewareContext[mt.ListResourcesRequest],
        call_next: CallNext[mt.ListResourcesRequest, list[Resource]],
    ) -> list[Resource]:
        """
        Filter resources to only show those owned by the authenticated user.

        Args:
            context: Middleware context containing the request
            call_next: Callback to invoke next middleware or handler

        Returns:
            Filtered list of resources owned by the user

        Raises:
            McpError: If user is not authorized
        """
        from fastmcp.server.dependencies import get_access_token
        email = get_access_token().claims.get("email")

        config = await self.user_config_repository.get_user_config(email)
        if not config:
            logger.warning(f"Unauthorized access attempt by {email}")
            raise McpError(ErrorData(
                code=32000,
                message="User is not authorized to access this MCP.",
            ))

        resources = await call_next(context)
        filtered_resources = []
        for resource in resources:
            owner_email = resource._client.owner_email
            logger.debug(f"Resource {resource.name} owned by {owner_email}")
            if owner_email == email:
                filtered_resources.append(resource)

        logger.info(f"Filtered {len(filtered_resources)}/{len(resources)} resources for {email}")
        return filtered_resources