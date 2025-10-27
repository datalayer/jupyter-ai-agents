# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

from .chat.agent import create_chat_agent
from .mcp import MCPToolManager
from .chat.config import ChatConfig

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
