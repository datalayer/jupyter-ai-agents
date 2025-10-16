"""Tornado handlers for chat API compatible with Vercel AI SDK."""

import json
import tornado.web
from jupyter_server.base.handlers import APIHandler

from ..chat.models import FrontendConfig, AIModel, BuiltinTool


class ChatHandler(APIHandler):
    """
    Handler for /api/chat endpoint.
    
    This handler implements the Vercel AI protocol for streaming chat responses.
    It receives chat messages and streams back AI responses with support for:
    - Text responses
    - Tool calls
    - Reasoning steps
    - Source citations
    """
    
    @tornado.web.authenticated
    async def post(self):
        """Handle chat POST request with streaming."""
        try:
            # Get agent from application settings
            agent = self.settings.get('chat_agent')
            if not agent:
                self.set_status(500)
                self.finish(json.dumps({"error": "Chat agent not initialized"}))
                return
            
            # Parse request body
            body = json.loads(self.request.body.decode('utf-8'))
            messages = body.get('messages', [])
            model = body.get('model')
            builtin_tools = body.get('builtinTools', [])
            
            # Set up streaming response headers
            self.set_header('Content-Type', 'text/event-stream')
            self.set_header('Cache-Control', 'no-cache')
            self.set_header('Connection', 'keep-alive')
            self.set_header('Access-Control-Allow-Origin', '*')
            
            # TODO: Implement proper Vercel AI protocol streaming
            # For now, send a simple response
            response = {
                "role": "assistant",
                "content": "Chat streaming not yet fully implemented. Your message: " + 
                          (messages[-1].get('content', '') if messages else ''),
            }
            
            # Send as SSE event
            event_data = f"data: {json.dumps(response)}\n\n"
            self.write(event_data)
            await self.flush()
            
            # Send done event
            self.write("data: [DONE]\n\n")
            await self.flush()
            
        except Exception as e:
            self.log.error(f"Error in chat handler: {e}", exc_info=True)
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
    
    @tornado.web.authenticated
    async def options(self):
        """Handle OPTIONS request for CORS."""
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')
        self.set_status(204)
        self.finish()


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
            # Get MCP manager from settings
            mcp_manager = self.settings.get('mcp_manager')
            
            # Define available models
            models = [
                AIModel(
                    id="anthropic:claude-sonnet-4.0",
                    name="Claude Sonnet 4.0",
                    builtin_tools=["jupyter_execute", "jupyter_read", "jupyter_files"]
                )
            ]
            
            # Define builtin tools
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
            
            # Get MCP servers
            mcp_servers = []
            if mcp_manager:
                mcp_servers = mcp_manager.get_servers()
            
            # Create response
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


class MCPServersHandler(APIHandler):
    """Handler for MCP server CRUD operations."""
    
    @tornado.web.authenticated
    async def get(self):
        """Get all MCP servers."""
        try:
            mcp_manager = self.settings.get('mcp_manager')
            if not mcp_manager:
                self.finish(json.dumps([]))
                return
            
            servers = mcp_manager.get_servers()
            self.finish(json.dumps([s.model_dump() for s in servers]))
            
        except Exception as e:
            self.log.error(f"Error getting MCP servers: {e}", exc_info=True)
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
    
    @tornado.web.authenticated
    async def post(self):
        """Add a new MCP server."""
        try:
            from ..chat.models import MCPServer
            
            data = json.loads(self.request.body.decode('utf-8'))
            server = MCPServer(**data)
            
            mcp_manager = self.settings.get('mcp_manager')
            config = self.settings.get('chat_config')
            
            if mcp_manager:
                mcp_manager.add_server(server)
            
            if config:
                servers = mcp_manager.get_servers() if mcp_manager else [server]
                config.save_mcp_servers(servers)
            
            self.finish(server.model_dump_json())
            
        except Exception as e:
            self.log.error(f"Error adding MCP server: {e}", exc_info=True)
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))


class MCPServerHandler(APIHandler):
    """Handler for individual MCP server operations."""
    
    @tornado.web.authenticated
    async def put(self, server_id: str):
        """Update MCP server."""
        try:
            from ..chat.models import MCPServer
            
            data = json.loads(self.request.body.decode('utf-8'))
            server = MCPServer(**data)
            
            mcp_manager = self.settings.get('mcp_manager')
            config = self.settings.get('chat_config')
            
            if mcp_manager:
                mcp_manager.update_server(server_id, server)
            
            if config:
                servers = mcp_manager.get_servers() if mcp_manager else []
                config.save_mcp_servers(servers)
            
            self.finish(server.model_dump_json())
            
        except Exception as e:
            self.log.error(f"Error updating MCP server: {e}", exc_info=True)
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
    
    @tornado.web.authenticated
    async def delete(self, server_id: str):
        """Delete MCP server."""
        try:
            mcp_manager = self.settings.get('mcp_manager')
            config = self.settings.get('chat_config')
            
            if mcp_manager:
                mcp_manager.remove_server(server_id)
            
            if config:
                servers = mcp_manager.get_servers() if mcp_manager else []
                config.save_mcp_servers(servers)
            
            self.set_status(204)
            self.finish()
            
        except Exception as e:
            self.log.error(f"Error deleting MCP server: {e}", exc_info=True)
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))
