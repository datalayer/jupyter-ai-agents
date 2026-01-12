# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Config handler."""

import json

import tornado

from jupyter_server.base.handlers import APIHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyter_ai_agents.__version__ import __version__


class ConfigHandler(ExtensionHandlerMixin, APIHandler):
    """The handler for configurations.
    
    Returns the agent configuration including available models and tools.
    This endpoint is queried by the agent-runtimes Chat component.
    """

    @tornado.web.authenticated
    def get(self):
        """Returns the configuration for the chat agent.
        
        Returns a JSON object with:
        - models: List of available models
        - builtinTools: List of built-in tools
        - mcpServers: List of MCP servers (optional)
        """
        # Build model list based on available API keys
        models = []
        
        # Check for Anthropic
        import os
        if os.environ.get("ANTHROPIC_API_KEY"):
            models.append({
                "id": "anthropic:claude-sonnet-4-20250514",
                "name": "Claude Sonnet 4",
                "isAvailable": True,
            })
            models.append({
                "id": "anthropic:claude-3-5-sonnet-latest",
                "name": "Claude 3.5 Sonnet",
                "isAvailable": True,
            })
        
        # Check for OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            models.append({
                "id": "openai:gpt-4o",
                "name": "GPT-4o",
                "isAvailable": True,
            })
            models.append({
                "id": "openai:gpt-4o-mini",
                "name": "GPT-4o Mini",
                "isAvailable": True,
            })
        
        # If no models available, add a placeholder
        if not models:
            models.append({
                "id": "none",
                "name": "No models available",
                "isAvailable": False,
            })
        
        # Get MCP servers if configured
        mcp_servers = []
        toolsets = self.settings.get("chat_toolsets", [])
        # TODO: Add MCP server enumeration from toolsets
        
        res = json.dumps({
            "models": models,
            "builtinTools": [],  # No builtin tools for now
            "mcpServers": mcp_servers,
        })
        self.finish(res)
