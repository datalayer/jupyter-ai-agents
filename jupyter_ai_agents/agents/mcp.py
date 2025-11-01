# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""MCP (Model Context Protocol) tools integration."""

import httpx
from typing import Any, Dict, List

from jupyter_ai_agents.agents.models import MCPServer


class MCPClient:
    """Client for communicating with MCP servers."""
    
    def __init__(self, server_url: str):
        """
        Initialize MCP client.
        
        Args:
            server_url: URL of the MCP server
        """
        self.server_url = server_url.rstrip('/')
        # Create a long-lived HTTP client with appropriate settings
        # matching the settings used in tools.py for consistency
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=300.0,  # Long timeout for LLM responses
                write=10.0,
                pool=5.0
            ),
            http2=False,  # Disable HTTP/2 for better compatibility
            follow_redirects=True,
            limits=httpx.Limits(
                max_keepalive_connections=5,  # Reduced to avoid exhaustion
                max_connections=10,  # Reduced to avoid exhaustion
                keepalive_expiry=60.0  # Longer keepalive
            )
        )
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            response = await self.client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error listing tools from {self.server_url}: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        try:
            response = await self.client.post(
                f"{self.server_url}/tools/{tool_name}",
                json={"arguments": arguments}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class MCPToolManager:
    """Manage MCP tools and servers."""
    
    def __init__(self):
        """Initialize MCP tool manager."""
        self.servers: Dict[str, MCPServer] = {}
        self.clients: Dict[str, MCPClient] = {}
    
    def add_server(self, server: MCPServer):
        """
        Add an MCP server.
        
        Args:
            server: MCP server configuration
        """
        self.servers[server.id] = server
        if server.enabled:
            self.clients[server.id] = MCPClient(server.url)
    
    def remove_server(self, server_id: str):
        """
        Remove an MCP server.
        
        Args:
            server_id: ID of the server to remove
        """
        if server_id in self.servers:
            del self.servers[server_id]
        if server_id in self.clients:
            del self.clients[server_id]
    
    def update_server(self, server_id: str, server: MCPServer):
        """
        Update an MCP server configuration.
        
        Args:
            server_id: ID of the server to update
            server: New server configuration
        """
        self.servers[server_id] = server
        if server.enabled and server_id not in self.clients:
            self.clients[server_id] = MCPClient(server.url)
        elif not server.enabled and server_id in self.clients:
            del self.clients[server_id]
    
    def get_servers(self) -> List[MCPServer]:
        """
        Get all MCP servers.
        
        Returns:
            List of MCP server configurations
        """
        return list(self.servers.values())
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get all available tools from enabled MCP servers.
        
        Returns:
            List of tool definitions with server information
        """
        all_tools = []
        for server_id, client in self.clients.items():
            server = self.servers[server_id]
            if server.enabled:
                tools = await client.list_tools()
                for tool in tools:
                    tool['mcp_server_id'] = server_id
                    tool['mcp_server_name'] = server.name
                    all_tools.append(tool)
        return all_tools
    
    def register_with_agent(self, agent: Any):
        """
        Register MCP tools with Pydantic AI agent.
        
        Args:
            agent: The Pydantic AI agent
        """
        # TODO: Implement dynamic tool registration
        # This will be implemented when we add MCP tool calling support
        pass
    
    async def close_all(self):
        """Close all MCP clients."""
        for client in self.clients.values():
            await client.close()
