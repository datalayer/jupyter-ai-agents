# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Pydantic models for chat functionality."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AIModel(BaseModel):
    """Configuration for an AI model."""
    
    id: str = Field(..., description="Model identifier (e.g., 'anthropic:claude-sonnet-4-5')")
    name: str = Field(..., description="Display name for the model")
    builtin_tools: List[str] = Field(default_factory=list, description="List of builtin tool IDs")


class BuiltinTool(BaseModel):
    """Configuration for a builtin tool."""
    
    id: str = Field(..., description="Tool identifier")
    name: str = Field(..., description="Display name for the tool")
    description: Optional[str] = Field(None, description="Tool description")


class MCPServer(BaseModel):
    """Configuration for an MCP server."""
    
    id: str = Field(..., description="Unique server identifier")
    name: str = Field(..., description="Display name for the server")
    url: str = Field(..., description="Server URL")
    enabled: bool = Field(default=True, description="Whether the server is enabled")
    tools: List[str] = Field(default_factory=list, description="List of available tool names")


class FrontendConfig(BaseModel):
    """Configuration returned to frontend."""
    
    models: List[AIModel] = Field(default_factory=list, description="Available AI models")
    builtin_tools: List[BuiltinTool] = Field(default_factory=list, description="Available builtin tools")
    mcp_servers: List[MCPServer] = Field(default_factory=list, description="Configured MCP servers")
