.PHONY: help install mcp1 mcp2 repl1 repl2 clean

# Default target
# anthropic:claude-sonnet-4-20250514
# azure-openai:gpt-4o-mini
help:
	@echo "Simple MCP Example - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install  - Install dependencies (mcp, uvicorn, starlette, sse-starlette, jupyter-ai-agents)"
	@echo "  mcp1     - Start MCP server 1 (Calculator) on http://localhost:8001"
	@echo "  mcp2     - Start MCP server 2 (Echo) on http://localhost:8002"
	@echo "  repl1    - Start jupyter-ai-agents REPL connected to MCP server 1"
	@echo "  repl2    - Start jupyter-ai-agents REPL connected to MCP server 2"
	@echo "  clean    - Clean up temporary files"
	@echo ""
	@echo "Usage:"
	@echo "  Terminal 1: make mcp1     # Start calculator server on port 8001"
	@echo "  Terminal 2: make repl1    # Connect REPL to calculator server"
	@echo ""
	@echo "  Or:"
	@echo "  Terminal 1: make mcp2     # Start echo server on port 8002"
	@echo "  Terminal 2: make repl2    # Connect REPL to echo server"
	@echo ""
	@echo "Note: These MCP servers use SSE transport (HTTP/SSE)"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install mcp uvicorn starlette sse-starlette
	pip install -e ../..
	@echo ""
	@echo "✓ Installation complete!"
	@echo ""
	@echo "Available MCP servers:"
	@echo "  • mcp1.py - Calculator tools (add, subtract, multiply, divide) on port 8001"
	@echo "  • mcp2.py - Echo tools (ping, echo, reverse, uppercase, etc.) on port 8002"
	@echo ""
	@echo "These servers use SSE transport (HTTP/SSE) compatible with jupyter-ai-agents"
	@echo ""

# Start MCP server 1 (Calculator)
mcp1:
	@echo "🚀 Starting MCP Server 1 (Calculator) on http://localhost:8001"
	@echo ""
	@echo "Available tools:"
	@echo "  • add(a, b) - Add two numbers"
	@echo "  • subtract(a, b) - Subtract two numbers"
	@echo "  • multiply(a, b) - Multiply two numbers"
	@echo "  • divide(a, b) - Divide two numbers"
	@echo ""
	@echo "MCP Endpoint (Streamable HTTP):"
	@echo "  • http://localhost:8001/mcp"
	@echo ""
	python mcp1.py

# Start MCP server 2 (Echo)
mcp2:
	@echo "🚀 Starting MCP Server 2 (Echo) on http://localhost:8002"
	@echo ""
	@echo "Available tools:"
	@echo "  • ping() - Test server connectivity"
	@echo "  • echo(message) - Echo back the message"
	@echo "  • reverse(text) - Reverse the text"
	@echo "  • uppercase(text) - Convert to uppercase"
	@echo "  • lowercase(text) - Convert to lowercase"
	@echo "  • count_words(text) - Count words in text"
	@echo ""
	@echo "MCP Endpoint (Streamable HTTP):"
	@echo "  • http://localhost:8002/mcp"
	@echo ""
	python mcp2.py

# Start REPL connected to MCP server 1 (Calculator)
repl1:
	@echo "🤖 Starting jupyter-ai-agents REPL connected to Calculator Server"
	@echo "   MCP Endpoint: http://localhost:8001/mcp"
	@echo ""
	@echo "Make sure the calculator server is running first (make mcp1 in another terminal)"
	@echo ""
	jupyter-ai-agents repl \
	  --verbose \
	  --mcp-servers http://localhost:8001/mcp \
	  --model azure-openai:gpt-4o-mini

# Start REPL connected to MCP server 2 (Echo)
repl2:
	@echo "🤖 Starting jupyter-ai-agents REPL connected to Echo Server"
	@echo "   MCP Endpoint: http://localhost:8002/mcp"
	@echo ""
	@echo "Make sure the echo server is running first (make mcp2 in another terminal)"
	@echo ""
	jupyter-ai-agents repl \
	  --verbose \
	  --mcp-servers http://localhost:8002/mcp \
	  --model azure-openai:gpt-4o-mini

# Clean up
clean:
	@echo "Cleaning up..."
	@rm -f *.log nohup.out
	@rm -rf __pycache__
	@echo "✓ Cleanup complete"
