from .agent import create_chat_agent
from .mcp import MCPToolManager
from .config import ChatConfig

"""
Chat functionality for Jupyter AI Agents.

This package provides:
- Pydantic AI agent for chat
- MCP (Model Context Protocol) integration
- Configuration management
"""

__all__ = [
    'create_chat_agent',
    'MCPToolManager',
    'ChatConfig',
]
