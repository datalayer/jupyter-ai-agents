# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Config handler."""

import json
import logging
import os

import tornado
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from jupyter_server.base.handlers import APIHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyter_ai_agents.__version__ import __version__


logger = logging.getLogger(__name__)


class ConfigHandler(ExtensionHandlerMixin, APIHandler):
    """The handler for configurations.
    
    Returns the agent configuration including available models and tools.
    This endpoint is queried by the agent-runtimes Chat component.
    """

    async def _fetch_mcp_tools(self, mcp_url: str, token: str | None) -> list[dict]:
        """Fetch tools from the MCP server using JSON-RPC protocol.
        
        Args:
            mcp_url: URL of the MCP server endpoint
            token: Authentication token
            
        Returns:
            List of tool dictionaries with name, description
        """
        try:
            client = AsyncHTTPClient()
            
            # Prepare JSON-RPC request for tools/list
            request_body = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            })
            
            headers = {
                "Content-Type": "application/json",
            }
            if token:
                headers["Authorization"] = f"token {token}"
            
            request = HTTPRequest(
                mcp_url,
                method="POST",
                headers=headers,
                body=request_body,
                request_timeout=5.0,  # Short timeout for config query
            )
            
            response = await client.fetch(request, raise_error=False)
            
            if response.code == 200:
                result = json.loads(response.body.decode("utf-8"))
                if "result" in result and "tools" in result["result"]:
                    tools = []
                    for tool in result["result"]["tools"]:
                        tools.append({
                            "name": tool.get("name", ""),
                            "description": tool.get("description", ""),
                            "enabled": True,  # Enable by default
                        })
                    logger.info(f"Discovered {len(tools)} tools from MCP server")
                    return tools
                elif "error" in result:
                    logger.warning(f"MCP server returned error: {result['error']}")
            else:
                logger.warning(f"MCP server returned status {response.code}")
                
        except Exception as e:
            logger.warning(f"Failed to fetch MCP tools: {e}")
        
        return []

    @tornado.web.authenticated
    async def get(self):
        """Returns the configuration for the chat agent.
        
        Returns a JSON object with:
        - models: List of available models
        - builtinTools: List of built-in tools
        - mcpServers: List of MCP servers (optional)
        """
        # Build model list based on available API keys
        models = []
        
        # Check for Anthropic
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
        
        # Build MCP servers list
        mcp_servers = []
        base_url = self.settings.get("chat_base_url", "")
        token = self.settings.get("chat_token")
        
        # Try to discover tools from jupyter-mcp-server
        mcp_url = f"{base_url.rstrip('/')}/mcp" if base_url else ""
        tools = []
        is_available = False
        
        if mcp_url:
            tools = await self._fetch_mcp_tools(mcp_url, token)
            is_available = len(tools) > 0
        
        mcp_servers.append({
            "id": "jupyter-mcp-server",
            "name": "Jupyter MCP Server",
            "description": "MCP tools for interacting with Jupyter notebooks (read/write cells, execute code, etc.)",
            "url": mcp_url,
            "isAvailable": is_available,
            "enabled": is_available,  # Auto-enable if available
            "tools": tools,
        })
        
        res = json.dumps({
            "models": models,
            "builtinTools": [],  # No builtin tools for now
            "mcpServers": mcp_servers,
        })
        self.finish(res)
