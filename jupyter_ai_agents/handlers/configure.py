# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tornado handlers for chat API compatible with Vercel AI SDK."""

import json
import tornado.web

from jupyter_server.base.handlers import APIHandler

from jupyter_ai_agents.agents.pydantic.models import (
    FrontendConfig,
    AIModel,
    BuiltinTool,
)


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
            
            # Define available models.
            models = [
                AIModel(
                    id="anthropic:claude-sonnet-4-5",
                    name="Claude Sonnet 4.0",
                    builtin_tools=["jupyter_execute", "jupyter_read", "jupyter_files"]
                )
            ]
            
            # Define builtin tools.
            builtin_tools = [
                BuiltinTool(
                    id="jupyter_execute",
                    name="Execute Code",
                    description="Execute Python code in the active kernel"
                ),
                BuiltinTool(
                    id="jupyter_read",
                    name="Read Notebook",
                    description="Read a Jupyter notebook file"
                ),
                BuiltinTool(
                    id="jupyter_files",
                    name="List Files",
                    description="List files in the workspace"
                )
            ]
            
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
            
            self.finish(config.model_dump_json())
            
        except Exception as e:
            self.log.error(f"Error in configure handler: {e}", exc_info=True)
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
