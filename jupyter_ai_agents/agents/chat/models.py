# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Pydantic models for chat functionality."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request from frontend."""
    
    model: Optional[str] = Field(None, description="Model to use for this request")
    builtin_tools: List[str] = Field(default_factory=list, description="Enabled builtin tools")
    messages: List[dict] = Field(default_factory=list, description="Conversation messages")
