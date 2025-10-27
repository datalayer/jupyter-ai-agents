# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tools integration for Jupyter AI Agents."""

import logging
from typing import Any

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


async def get_available_tools(
    base_url: str,
    token: str | None = None,
    enabled_only: bool = True,
) -> list[dict[str, Any]]:
    """
    Get available tools from jupyter-mcp-tools extension.
    
    Args:
        base_url: Jupyter server base URL
        token: Authentication token for Jupyter server
        enabled_only: Whether to return only enabled tools
        
    Returns:
        List of tool dictionaries with name, description, and inputSchema
    """
    try:
        from jupyter_mcp_tools import get_tools
        
        logger.info(f"Querying jupyter-mcp-tools at {base_url}, enabled_only={enabled_only}")
        
        # Define specific tools we want to load
        allowed_tools = [
            "docmanager_open",
            "docmanager_new-untitled",
            "notebook_insert-cell-above",
            "notebook_insert-cell-below",
        ]
        
        # Query for specific tools (comma-separated list)
        search_query = ",".join(allowed_tools)
        logger.info(f"Querying jupyter-mcp-tools with specific tools: {search_query}")
        
        tools_data = await get_tools(
            base_url=base_url,
            token=token,
            query=search_query,
            enabled_only=enabled_only
        )
        
        logger.info(f"Query returned {len(tools_data)} tools: {[t.get('id') for t in tools_data]}")
        
        # If no tools found with enabled_only=True, try with enabled_only=False
        if not tools_data and enabled_only:
            logger.info("No enabled tools found, trying with enabled_only=False")
            tools_data = await get_tools(
                base_url=base_url,
                token=token,
                query=search_query,
                enabled_only=False
            )
            logger.info(f"Query with enabled_only=False returned {len(tools_data)} tools")
        
        # Convert jupyter-mcp-tools format to pydantic-ai compatible format
        converted_tools = []
        for tool_data in tools_data:
            tool_name = tool_data.get('id', '')
            logger.debug(f"Processing tool: {tool_name}, data: {tool_data}")
            
            # Create tool dictionary with MCP protocol fields
            tool_dict = {
                "name": tool_name,
                "description": tool_data.get('caption', tool_data.get('label', '')),
            }
            
            # Convert parameters to inputSchema
            params = tool_data.get('parameters', {})
            if params:
                tool_dict["inputSchema"] = {
                    "type": "object",
                    "properties": params.get('properties', {}),
                    "required": params.get('required', []),
                }
            else:
                tool_dict["inputSchema"] = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
            
            converted_tools.append(tool_dict)
        
        logger.info(f"Successfully converted {len(converted_tools)} tools from jupyter-mcp-tools")
        return converted_tools
        
    except ImportError as e:
        logger.warning(f"jupyter-mcp-tools not installed: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error querying jupyter-mcp-tools: {e}", exc_info=True)
        return []


def tools_to_builtin_list(tools: list[dict[str, Any]]) -> list[str]:
    """
    Extract tool names from tools list.
    
    Args:
        tools: List of tool dictionaries
        
    Returns:
        List of tool names/IDs
    """
    return [tool.get('name', '') for tool in tools if tool.get('name')]
