# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

.PHONY: help jupyterlab repl clean

# Default target
# anthropic:claude-sonnet-4-20250514
# azure-openai:gpt-4o-mini
help:
	@echo "Jupyter MCP Example - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  jupyterlab  - Start JupyterLab server on http://localhost:8888"
	@echo "  repl        - Start jupyter-ai-agents REPL connected to Jupyter MCP server"
	@echo "  clean       - Clean up temporary files"
	@echo ""
	@echo "Usage:"
	@echo "  Terminal 1: make jupyterlab    # Start JupyterLab with MCP server"
	@echo "  Terminal 2: make repl          # Connect REPL to Jupyter MCP server"
	@echo ""
	@echo "Note: The REPL connects to jupyter-mcp-server at http://localhost:8888/mcp"
	@echo ""

jupyterlab: ## jupyterlab
	jupyter lab \
		--port 8888 \
		--ServerApp.root_dir ./../../dev/content \
		--IdentityProvider.token=

# Start REPL connected to MCP Jupyter
repl:
	@echo "🤖 Starting jupyter-ai-agents REPL connected to Jupyter Server"
	@echo "Make sure the Jupyter server is running first (make jupyterlab in another terminal)"
	@echo ""
	jupyter-ai-agents repl \
	  --verbose \
	  --mcp-servers http://localhost:8888/mcp \
	  --model anthropic:claude-sonnet-4-20250514
