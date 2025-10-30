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
) -> tuple[MCPServerStreamableHTTP, httpx.AsyncClient | None]:
    """
    Create an MCP server connection to jupyter-mcp-server.
    
    The jupyter-mcp-server runs on the same Jupyter server and exposes
    tools via the MCP protocol over HTTP.
    
    Args:
        base_url: Jupyter server base URL (e.g., "http://localhost:8888")
        token: Authentication token for Jupyter server
        
    Returns:
        Tuple of (MCPServerStreamableHTTP instance, httpx.AsyncClient or None)
        The http_client must be kept alive for the lifetime of the server
        and should be properly closed when no longer needed.
    """
    # Construct the MCP endpoint URL
    # jupyter-mcp-server typically runs at /mcp endpoint
    mcp_url = urljoin(base_url.rstrip('/') + '/', 'mcp')
    
    logger.info(f"Creating MCP server connection to {mcp_url}")
    
    # Create HTTP client with authentication if token is provided
    if token:
        # Create a long-lived HTTP client with appropriate settings
        # This client must be kept alive for the entire session
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=300.0,  # Long timeout for LLM responses
                write=10.0,
                pool=5.0
            ),
            headers={"Authorization": f"token {token}"},
            http2=False,  # Disable HTTP/2 for better compatibility
            follow_redirects=True,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0  # Keep connections alive
            )
        )
        server = MCPServerStreamableHTTP(mcp_url, http_client=http_client)
        logger.info("MCP server connection created successfully with authenticated client")
        return server, http_client
    else:
        server = MCPServerStreamableHTTP(mcp_url)
        logger.info("MCP server connection created successfully without authentication")
        return server, None


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
    http_client = None
    try:
        server, http_client = create_mcp_server(base_url, token)
        
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
    finally:
        # Clean up the HTTP client after this one-time query
        if http_client:
            await http_client.aclose()


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
