<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.io)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# Simple MCP Server Examples

This directory contains two simple MCP servers that demonstrate how to create and use MCP servers with jupyter-ai-agents.

## 🎯 Overview

This example demonstrates standalone MCP servers using **FastMCP** with **Streamable HTTP transport** (MCP specification 2025-06-18):

1. **Calculator Server** (`mcp1.py`) - Math operations on port 8001
2. **Echo Server** (`mcp2.py`) - String operations on port 8002

Both servers use **FastMCP** (from the standard MCP SDK) which automatically handles:
- HTTP/SSE transport complexity
- GET (SSE streaming) and POST (JSON-RPC messages) at `/mcp` endpoint
- Tool registration and execution
- Input/output schema validation

This is the same pattern used by `jupyter-mcp-server`, providing a clean, high-level abstraction for MCP server development.

## 📋 MCP Servers

### Calculator Server (mcp1.py) - Port 8001
- `add(a, b)` - Add two numbers
- `subtract(a, b)` - Subtract two numbers  
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide two numbers

### Echo Server (mcp2.py) - Port 8002
- `ping()` - Test connectivity
- `echo(message)` - Echo back message
- `reverse(text)` - Reverse string
- `uppercase(text)` - Convert to uppercase
- `lowercase(text)` - Convert to lowercase
- `count_words(text)` - Count words

## 🚀 Quick Start

**1. Install:**
```bash
make install
```

**2. Terminal 1 - Start server:**
```bash
make mcp1  # or make mcp2
```

**3. Terminal 2 - Connect REPL:**
```bash
make repl1  # or make repl2
```

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make mcp1` | Start Calculator (8001) |
| `make mcp2` | Start Echo (8002) |
| `make repl1` | Connect to Calculator |
| `make repl2` | Connect to Echo |
| `make clean` | Clean temp files |

## 📝 Manual Usage

If you want to run commands manually:

**Start servers:**
```bash
python mcp1.py  # Calculator on port 8001
python mcp2.py  # Echo on port 8002
```

**Connect REPL (using the `/mcp` endpoint):**
```bash
# Single server
jupyter-ai-agents repl --mcp-servers http://localhost:8001/mcp

# Multiple servers
jupyter-ai-agents repl --mcp-servers "http://localhost:8001/mcp,http://localhost:8002/mcp"
```

**Important:** The MCP servers use Streamable HTTP transport with a single `/mcp` endpoint that handles both GET (for SSE streaming) and POST (for JSON-RPC messages) requests, as defined in the [MCP specification 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#streamable-http).

## �💬 REPL Examples

```
> Add 5 and 7
> What is 15 divided by 3?
> Reverse the text "jupyter"
> Count words in "hello world"
```

## 📚 Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [Pydantic AI](https://ai.pydantic.dev/)
- [Jupyter AI Agents](https://github.com/datalayer/jupyter-ai-agents)

---
**Made with ❤️ by [Datalayer](https://datalayer.io)**
