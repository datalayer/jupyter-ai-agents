# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tornado handlers for chat API compatible with Vercel AI SDK."""

import json
import logging
import tornado.web

from jupyter_server.base.handlers import APIHandler

from jupyter_ai_agents.agents.models import (
    FrontendConfig,
    AIModel,
    BuiltinTool,
)
from jupyter_ai_agents.tools import get_available_tools, generate_name_from_id

logger = logging.getLogger(__name__)


class ConfigureHandler(APIHandler):
    """
    Handler for /api/configure endpoint.
    
    Returns configuration information for the frontend:
    - Available models
    - Builtin tools
    - MCP servers
    """
    
    @tornado.web.authenticated
    async def get(self):
        """Return configuration for frontend."""
        try:
            # Get MCP manager from settings.
            mcp_manager = self.settings.get('mcp_manager')
            
            # Get Jupyter server connection details
            serverapp = self.settings.get('serverapp')
            if serverapp:
                base_url = serverapp.connection_url
                token = serverapp.token
                logger.info(f"Using Jupyter ServerApp connection URL: {base_url}")
            else:
                # Fallback to localhost
                base_url = "http://localhost:8888"
                token = None
                logger.warning("ServerApp not found in settings, using localhost")
            
            # Fetch available tools from jupyter-mcp-tools
            # Try with enabled_only=False first to see all available tools
            logger.info("Fetching tools from jupyter-mcp-tools...")
            available_tools = await get_available_tools(
                base_url=base_url,
                token=token,
                enabled_only=False  # Get all tools, not just enabled ones
            )
            logger.info(f"Fetched {len(available_tools)} tools from jupyter-mcp-tools: {[t.get('name') for t in available_tools]}")
            
            # Convert tools to BuiltinTool format
            builtin_tools = []
            for tool in available_tools:
                tool_id = tool.get('name', '')
                tool_name = tool.get('description', '')
                
                # If name is empty, generate from ID
                if not tool_name or not tool_name.strip():
                    tool_name = generate_name_from_id(tool_id)
                
                builtin_tools.append(
                    BuiltinTool(
                        id=tool_id,
                        name=tool_name
                    )
                )
            
            logger.info(f"Converted to {len(builtin_tools)} BuiltinTool objects")
            
            # Define available models with tool associations
            tool_ids = [tool.id for tool in builtin_tools]
            models = [
                AIModel(
                    id="anthropic:claude-sonnet-4-5",
                    name="Claude Sonnet 4.5",
                    builtin_tools=tool_ids  # Associate all available tools
                )
            ]
            logger.info(f"Created model with {len(tool_ids)} associated tools")
            
            # Get MCP servers.
            mcp_servers = []
            if mcp_manager:
                mcp_servers = mcp_manager.get_servers()
            
            # Create response.
            config = FrontendConfig(
                models=models,
                builtin_tools=builtin_tools,
                mcp_servers=mcp_servers
            )
            
            logger.info(f"Returning config with {len(builtin_tools)} builtin_tools")
            self.finish(config.model_dump_json(by_alias=True))
            
        except Exception as e:
            self.log.error(f"Error in configure handler: {e}", exc_info=True)
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
