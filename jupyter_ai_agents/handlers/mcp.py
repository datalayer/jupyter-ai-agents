# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tornado handlers for chat API compatible with Vercel AI SDK."""

import json

import tornado.web

from jupyter_server.base.handlers import APIHandler


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
            from ..agents.models import MCPServer
            
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
            from ..agents.models import MCPServer
            
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
