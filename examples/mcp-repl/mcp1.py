#!/usr/bin/env python3
# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""
MCP Server 1 - Calculator Tools

Simple MCP server providing calculator operations using FastMCP
with Streamable HTTP transport (MCP specification 2025-06-18).
"""

from typing import Annotated
from pydantic import Field
from mcp.server import FastMCP


# Create FastMCP server
mcp = FastMCP(name="Calculator Server")


@mcp.tool()
async def add(
    a: Annotated[float, Field(description="First number")],
    b: Annotated[float, Field(description="Second number")],
) -> float:
    """Add two numbers together"""
    return a + b


@mcp.tool()
async def subtract(
    a: Annotated[float, Field(description="First number")],
    b: Annotated[float, Field(description="Second number")],
) -> float:
    """Subtract b from a"""
    return a - b


@mcp.tool()
async def multiply(
    a: Annotated[float, Field(description="First number")],
    b: Annotated[float, Field(description="Second number")],
) -> float:
    """Multiply two numbers"""
    return a * b


@mcp.tool()
async def divide(
    a: Annotated[float, Field(description="Numerator")],
    b: Annotated[float, Field(description="Denominator")],
) -> float:
    """Divide a by b"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Calculator MCP Server on http://localhost:8001")
    print("   MCP endpoint: http://localhost:8001/mcp (Streamable HTTP)")
    print("   Tools: add, subtract, multiply, divide")
    print("")
    
    # Get the Starlette app with Streamable HTTP transport
    app = mcp.streamable_http_app()
    
    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


