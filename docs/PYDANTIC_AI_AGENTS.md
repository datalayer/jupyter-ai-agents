# Pydantic AI Agents with MCP Integration

This document describes the new pydantic-ai based agents that use the Model Context Protocol (MCP) for Jupyter integration.

## Overview

The pydantic-ai agents represent a modern approach to AI-powered Jupyter notebook manipulation:

- **Technology Stack**: Built with [pydantic-ai](https://ai.pydantic.dev/), a Python agent framework
- **Communication Protocol**: Uses [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) for tool integration
- **Architecture**: Direct server-to-server communication (no RTC/nbmodel client needed)
- **CLI Support**: Includes pydantic-ai's built-in interactive CLI

## Architecture Comparison

### Legacy LangChain Architecture
```
CLI Tool → NbModel Client → RTC (WebSocket) → Jupyter Server → Notebook
         → Kernel Client → Kernel → Execution
```

### New Pydantic AI Architecture  
```
CLI Tool → MCP Client → HTTP/SSE → jupyter-mcp-server → Jupyter Server → Notebook
                                                        → Kernel → Execution
```

## Key Benefits

1. **Simplified Communication**: Direct HTTP communication instead of WebSocket RTC
2. **Standard Protocol**: MCP is becoming the standard for tool integration with AI
3. **Better Tool Discovery**: MCP provides automatic tool discovery and schema validation
4. **Modern Framework**: pydantic-ai offers better type safety and async support
5. **Interactive Mode**: Built-in CLI with conversation history and markdown rendering

## Available Agents

### 1. Prompt Agent

Creates and executes code based on natural language instructions.

**Features**:
- Breaks down complex requests into steps
- Installs required packages automatically
- Adds explanatory markdown cells
- Executes code to verify it works
- Maintains cell indexing and execution flow

**Usage**:
```bash
jupyter-ai-agents-pydantic prompt \
  --url http://localhost:8888 \
  --token YOUR_TOKEN \
  --model-provider openai \
  --model-name gpt-4o \
  --path notebook.ipynb \
  --input "Create a pandas dataframe and plot it with matplotlib"
```

**Options**:
- `--url`: Jupyter server URL
- `--token`: Authentication token
- `--path`: Notebook path
- `--input`: User instruction
- `--model-provider`: AI provider (openai, anthropic, azure-openai, etc.)
- `--model-name`: Model identifier
- `--current-cell-index`: Where user made the request (default: -1)
- `--full-context`: Include full notebook content in context
- `--verbose`: Enable debug logging

### 2. Explain Error Agent

Analyzes errors in notebooks and provides fixes.

**Features**:
- Parses error tracebacks
- Explains the root cause
- Inserts corrected code cells
- Executes fixes to verify they work
- Adds explanatory comments

**Usage**:
```bash
jupyter-ai-agents-pydantic explain-error \
  --url http://localhost:8888 \
  --token YOUR_TOKEN \
  --model-provider openai \
  --model-name gpt-4o \
  --path notebook.ipynb \
  --current-cell-index 5
```

**Options**:
- `--current-cell-index`: Cell with error (-1 to find first error)
- Other options same as prompt agent

### 3. Interactive Mode

Conversational interface for notebook manipulation.

**Usage**:
```bash
jupyter-ai-agents-pydantic interactive \
  --url http://localhost:8888 \
  --token YOUR_TOKEN \
  --model-provider openai \
  --model-name gpt-4o \
  --path notebook.ipynb
```

**Special Commands**:
- `/exit`: Exit the session
- `/markdown`: Show last response in markdown
- `/multiline`: Toggle multiline input mode (use Ctrl+D to submit)
- `/cp`: Copy last response to clipboard

## Model Providers

### OpenAI
```bash
export OPENAI_API_KEY='your-key'
jupyter-ai-agents-pydantic prompt \
  --model-provider openai \
  --model-name gpt-4o \
  ...
```

### Anthropic
```bash
export ANTHROPIC_API_KEY='your-key'
jupyter-ai-agents-pydantic prompt \
  --model-provider anthropic \
  --model-name claude-sonnet-4-0 \
  ...
```

### Azure OpenAI
```bash
export AZURE_OPENAI_API_KEY='your-key'
export AZURE_OPENAI_ENDPOINT='https://your-endpoint.openai.azure.com/'
jupyter-ai-agents-pydantic prompt \
  --model-provider azure-openai \
  --model-name gpt-4o \
  ...
```

### GitHub Copilot
```bash
export GITHUB_TOKEN='your-github-token'
jupyter-ai-agents-pydantic prompt \
  --model-provider github-copilot \
  --model-name gpt-4o \
  ...
```

## MCP Tools Available

The agents have access to the following tools through jupyter-mcp-server:

### Notebook Tools
- `notebook_insert_cell`: Insert a new cell at a specific index
- `notebook_insert_code_cell`: Insert and optionally execute a code cell
- `notebook_insert_markdown_cell`: Insert a markdown cell
- `notebook_get_cell`: Read a specific cell's content
- `notebook_get_cells`: List all cells
- `notebook_update_cell`: Modify an existing cell
- `notebook_delete_cell`: Remove a cell
- `notebook_run_cell`: Execute a specific cell
- `notebook_run_all_cells`: Execute all cells in sequence

### Kernel Tools
- `kernel_execute`: Execute code in the notebook kernel
- `kernel_interrupt`: Interrupt running code
- `kernel_restart`: Restart the kernel
- `kernel_get_info`: Get kernel information

### File System Tools (if enabled)
- `fs_read_file`: Read file contents
- `fs_write_file`: Write to a file
- `fs_list_directory`: List directory contents

## Configuration

### Environment Variables

The agents respect standard pydantic-ai environment variables:

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `AZURE_OPENAI_API_KEY`: Azure OpenAI key
- `AZURE_OPENAI_ENDPOINT`: Azure endpoint
- `GITHUB_TOKEN`: GitHub token for Copilot
- `PYDANTIC_AI_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### jupyter-mcp-server

Make sure jupyter-mcp-server is installed and running:

```bash
pip install jupyter-mcp-server
```

The MCP server is automatically started with JupyterLab when jupyter_ai_agents extension is loaded.

## Programmatic Usage

You can also use the agents programmatically:

```python
import asyncio
from jupyter_ai_agents.agents.cli.prompt_agent import (
    create_prompt_agent,
    run_prompt_agent,
)
from jupyter_ai_agents.tools import create_mcp_server

async def main():
    # Create MCP connection
    mcp_server = create_mcp_server(
        "http://localhost:8888",
        token="YOUR_TOKEN"
    )
    
    # Create agent
    agent = create_prompt_agent(
        model="openai:gpt-4o",
        mcp_server=mcp_server,
    )
    
    # Run agent
    result = await run_prompt_agent(
        agent,
        "Create a simple plot",
    )
    
    print(result)

asyncio.run(main())
```

## Troubleshooting

### Connection Issues

If the agent can't connect to Jupyter:

1. Verify JupyterLab is running: `jupyter lab list`
2. Check the URL and token are correct
3. Ensure jupyter-mcp-server is installed
4. Check if the MCP endpoint is accessible: `curl http://localhost:8888/mcp`

### API Key Issues

If you get authentication errors:

1. Verify your API key is set: `echo $OPENAI_API_KEY`
2. Check key permissions and quotas
3. Try a different model provider

### Tool Execution Issues

If tools aren't working:

1. Enable verbose logging: `--verbose`
2. Check jupyter-mcp-server logs
3. Verify notebook path is correct
4. Ensure notebook is not locked by another process

## Migration from LangChain Agents

If you're migrating from the legacy LangChain agents:

| LangChain | Pydantic AI |
|-----------|-------------|
| `jupyter-ai-agents prompt` | `jupyter-ai-agents-pydantic prompt` |
| `jupyter-ai-agents explain-error` | `jupyter-ai-agents-pydantic explain-error` |
| Uses NbModel Client + Kernel Client | Uses MCP Client |
| RTC WebSocket communication | HTTP/SSE communication |
| LangChain provider setup | Pydantic AI model strings |

**Key Differences**:
1. No need to pass `--agent` parameter (built into command)
2. Model provider format: `--model-provider openai --model-name gpt-4o` instead of LangChain specific configs
3. No need for separate kernel client setup
4. Simpler architecture with MCP

## Contributing

To add new agent capabilities:

1. Define tools in jupyter-mcp-server
2. Agents automatically discover new tools via MCP
3. Update agent instructions to use new tools
4. Test with `--verbose` flag

## References

- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server)
- [Pydantic AI CLI](https://ai.pydantic.dev/cli/)
