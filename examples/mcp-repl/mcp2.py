#!/usr/bin/env python3
# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""
MCP Server 2 - Echo Tools

Simple MCP server providing string manipulation tools using FastMCP
with Streamable HTTP transport (MCP specification 2025-06-18).
"""

from typing import Annotated
from pydantic import Field
from mcp.server import FastMCP


# Create FastMCP server
mcp = FastMCP(name="Echo Server")


@mcp.tool()
async def ping() -> str:
    """Simple ping tool to test connectivity"""
    return "pong"


@mcp.tool()
async def echo(
    message: Annotated[str, Field(description="Message to echo back")]
) -> str:
    """Echo back a message"""
    return message


@mcp.tool()
async def reverse(
    text: Annotated[str, Field(description="Text to reverse")]
) -> str:
    """Reverse a string"""
    return text[::-1]


@mcp.tool()
async def uppercase(
    text: Annotated[str, Field(description="Text to convert to uppercase")]
) -> str:
    """Convert text to uppercase"""
    return text.upper()


@mcp.tool()
async def lowercase(
    text: Annotated[str, Field(description="Text to convert to lowercase")]
) -> str:
    """Convert text to lowercase"""
    return text.lower()


@mcp.tool()
async def count_words(
    text: Annotated[str, Field(description="Text to count words in")]
) -> int:
    """Count the number of words in text"""
    return len(text.split())


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Echo MCP Server on http://localhost:8002")
    print("   MCP endpoint: http://localhost:8002/mcp (Streamable HTTP)")
    print("   Tools: ping, echo, reverse, uppercase, lowercase, count_words")
    print("")
    
    # Get the Starlette app with Streamable HTTP transport
    app = mcp.streamable_http_app()
    
    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
import uvicorn


# Create MCP server
server = Server("echo-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available string manipulation tools."""
    return [
        Tool(
            name="ping",
            description="Simple ping that returns 'pong'",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="echo",
            description="Echo back the provided message",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo back"},
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="reverse",
            description="Reverse a string",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to reverse"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="uppercase",
            description="Convert text to uppercase",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to convert"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="lowercase",
            description="Convert text to lowercase",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to convert"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="count_words",
            description="Count the number of words in text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                },
                "required": ["text"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "ping":
        return [TextContent(type="text", text="pong")]
    elif name == "echo":
        message = arguments.get("message", "")
        return [TextContent(type="text", text=message)]
    elif name == "reverse":
        text = arguments.get("text", "")
        return [TextContent(type="text", text=text[::-1])]
    elif name == "uppercase":
        text = arguments.get("text", "")
        return [TextContent(type="text", text=text.upper())]
    elif name == "lowercase":
        text = arguments.get("text", "")
        return [TextContent(type="text", text=text.lower())]
    elif name == "count_words":
        text = arguments.get("text", "")
        word_count = len(text.split())
        return [TextContent(type="text", text=str(word_count))]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# Create SSE transport for the single MCP endpoint
sse = SseServerTransport("/mcp")


async def handle_mcp_endpoint(request):
    """
    Handle the MCP endpoint according to Streamable HTTP transport specification.
    
    This single endpoint handles both:
    - POST requests: Client sends JSON-RPC messages
    - GET requests: Client opens SSE stream for server messages
    """
    if request.method == "GET":
        # GET request: Open SSE stream for server-to-client messages
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
    elif request.method == "POST":
        # POST request: Client sends JSON-RPC message
        # handle_post_message handles the response internally via ASGI callbacks
        await sse.handle_post_message(
            request.scope, request.receive, request._send
        )
    else:
        # Method not allowed
        return Response(status_code=405)


# Create Starlette app with single MCP endpoint
app = Starlette(
    routes=[
        Route("/mcp", endpoint=handle_mcp_endpoint, methods=["GET", "POST"]),
    ]
)


if __name__ == "__main__":
    print("🚀 Starting Echo MCP Server on http://localhost:8002")
    print("   MCP endpoint: http://localhost:8002/mcp (Streamable HTTP)")
    print("   Supports: GET (SSE stream) and POST (JSON-RPC messages)")
    print("")
    print("   Tools: ping, echo, reverse, uppercase, lowercase, count_words")
    uvicorn.run(app, host="0.0.0.0", port=8002)


