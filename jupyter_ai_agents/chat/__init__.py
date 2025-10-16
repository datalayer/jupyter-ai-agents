"""
Chat functionality for Jupyter AI Agents.

This package provides:
- Pydantic AI agent for chat
- Tornado handlers for Vercel AI protocol
- MCP (Model Context Protocol) integration
- Configuration management
"""

__all__ = [
    'create_chat_agent',
    'ChatHandler',
    'ConfigureHandler',
    'MCPToolManager',
    'ChatConfig',
]

from .agent import create_chat_agent
from .mcp_tools import MCPToolManager
from .config import ChatConfig
