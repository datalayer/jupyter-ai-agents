# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tools integration for Jupyter AI Agents using MCP (Model Context Protocol)."""

import logging
from typing import Any
from urllib.parse import urljoin

import httpx
from pydantic_ai.mcp import MCPServerStreamableHTTP

logger = logging.getLogger(__name__)


def generate_name_from_id(tool_id: str) -> str:
    """
    Generate a display name from a tool ID.
    
    Replaces underscores with spaces and capitalizes the first letter.
    
    Args:
        tool_id: Tool identifier (e.g., "notebook_run-all-cells")
        
    Returns:
        Formatted name (e.g., "Notebook run-all-cells")
    """
    if not tool_id:
        return ""
    
    # Replace underscores with spaces
    name = tool_id.replace('_', ' ')
    
    # Capitalize first letter
    if name:
        name = name[0].upper() + name[1:]
    
    return name


def create_mcp_server(
    base_url: str,
    token: str | None = None,
) -> MCPServerStreamableHTTP:
    """
    Create an MCP server connection to jupyter-mcp-server.
    
    The jupyter-mcp-server runs on the same Jupyter server and exposes
    tools via the MCP protocol over HTTP.
    
    Args:
        base_url: Jupyter server base URL (e.g., "http://localhost:8888")
        token: Authentication token for Jupyter server
        
    Returns:
        MCPServerStreamableHTTP instance connected to jupyter-mcp-server
    """
    # Construct the MCP endpoint URL
    # jupyter-mcp-server typically runs at /mcp endpoint
    mcp_url = urljoin(base_url.rstrip('/') + '/', 'mcp')
    
    logger.info(f"Creating MCP server connection to {mcp_url}")
    
    # Create MCP server with authentication headers if token is provided
    if token:
        headers = {"Authorization": f"token {token}"}
        server = MCPServerStreamableHTTP(mcp_url, headers=headers)
        logger.info("MCP server connection created successfully with authentication")
    else:
        server = MCPServerStreamableHTTP(mcp_url)
        logger.info("MCP server connection created successfully without authentication")
    
    return server


async def get_available_tools_from_mcp(
    base_url: str,
    token: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get available tools from jupyter-mcp-server via MCP protocol.
    
    This replaces the previous jupyter-mcp-tools direct query approach.
    Now we connect to the MCP server using pydantic-ai's MCP client
    and query tools through the standard MCP protocol.
    
    Args:
        base_url: Jupyter server base URL
        token: Authentication token for Jupyter server
        
    Returns:
        List of tool dictionaries with name, description, and inputSchema
    """
    try:
        server = create_mcp_server(base_url, token)
        
        # Use the MCP server as a context manager to connect and disconnect
        async with server:
            # List all available tools from the MCP server
            logger.info("Listing tools from MCP server...")
            tools = await server.list_tools()
            
            logger.info(f"MCP server returned {len(tools)} tools")
            
            # Convert MCP tool definitions to our internal format
            converted_tools = []
            for tool in tools:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description or "",
                }
                
                # Include inputSchema if available
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    tool_dict["inputSchema"] = tool.inputSchema
                else:
                    tool_dict["inputSchema"] = {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                
                converted_tools.append(tool_dict)
                logger.debug(f"Converted tool: {tool.name}")
            
            logger.info(f"Successfully retrieved {len(converted_tools)} tools from MCP server")
            return converted_tools
            
    except Exception as e:
        logger.error(f"Error connecting to MCP server at {base_url}: {e}", exc_info=True)
        return []


# Alias for backward compatibility
async def get_available_tools(
    base_url: str,
    token: str | None = None,
    enabled_only: bool = True,
) -> list[dict[str, Any]]:
    """
    Get available tools (backward compatible wrapper).
    
    Args:
        base_url: Jupyter server base URL
        token: Authentication token for Jupyter server
        enabled_only: Ignored (kept for backward compatibility)
        
    Returns:
        List of tool dictionaries
    """
    # Note: enabled_only is ignored as MCP server manages this internally
    return await get_available_tools_from_mcp(base_url, token)


def tools_to_builtin_list(tools: list[dict[str, Any]]) -> list[str]:
    """
    Extract tool names from tools list.
    
    Args:
        tools: List of tool dictionaries
        
    Returns:
        List of tool names/IDs
    """
    return [tool.get('name', '') for tool in tools if tool.get('name')]
