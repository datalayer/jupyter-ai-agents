#!/usr/bin/env python3
"""
REPL CLI for Jupyter AI Agents using pydantic-ai's built-in CLI with MCP tools.

This provides an interactive REPL where jupyter-mcp-server tools are directly available
to the AI model for interacting with Jupyter notebooks.
"""

import asyncio
import logging
from typing import Optional

import typer

from jupyter_ai_agents.tools import create_mcp_server, get_available_tools_from_mcp

logger = logging.getLogger(__name__)

app = typer.Typer(help="Interactive REPL with Jupyter MCP tools")


def enable_verbose_logging():
    """Enable verbose logging for debugging API calls and retries."""
    logging.getLogger().setLevel(logging.DEBUG)
    # Enable detailed HTTP logging to see retry reasons
    logging.getLogger("httpx").setLevel(logging.DEBUG)
    logging.getLogger("anthropic").setLevel(logging.DEBUG)
    logging.getLogger("openai").setLevel(logging.DEBUG)
    logger.debug("Verbose logging enabled - will show detailed HTTP requests, responses, and retry reasons")


def get_model_string(provider: str, model_name: str) -> str:
    """
    Convert provider and model name to pydantic-ai model string format.
    
    Note:
        For Azure OpenAI, returns just the model name.
        Required env vars for Azure:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT (base URL only, e.g., https://your-resource.openai.azure.com)
        - AZURE_OPENAI_API_VERSION (optional, defaults to latest)
    """
    # For Azure OpenAI, return just the model name
    if provider.lower() == 'azure-openai':
        return model_name
    
    # Map common providers to pydantic-ai format
    provider_map = {
        "openai": "openai",              # Regular OpenAI - requires OPENAI_API_KEY
        "anthropic": "anthropic",
        "github-copilot": "openai",      # GitHub Copilot uses OpenAI-compatible API
        "google": "google",
        "gemini": "google",
        "bedrock": "bedrock",
        "groq": "groq",
        "mistral": "mistral",
        "cohere": "cohere",
    }
    
    mapped_provider = provider_map.get(provider.lower(), provider)
    return f"{mapped_provider}:{model_name}"


def create_model_with_provider(provider: str, model_name: str):
    """
    Create a pydantic-ai model object with the appropriate provider configuration.
    
    Args:
        provider: Provider name
        model_name: Model/deployment name
        
    Returns:
        Model object or string for pydantic-ai Agent
    """
    if provider.lower() == 'azure-openai':
        from pydantic_ai.models.openai import OpenAIModel
        return OpenAIModel(model_name, provider='azure')
    else:
        return get_model_string(provider, model_name)


@app.command()
def repl(
    url: str = typer.Option("http://localhost:8888", help="URL to the Jupyter Server."),
    token: str = typer.Option("", help="Jupyter Server token."),
    model: str = typer.Option(
        None,
        help="Full model string (e.g., 'openai:gpt-4o', 'anthropic:claude-sonnet-4-0'). If not provided, uses --model-provider and --model-name."
    ),
    model_provider: str = typer.Option(
        "openai",
        help="Model provider: 'openai', 'anthropic', 'azure-openai', 'github-copilot', 'google', 'bedrock', 'groq', 'mistral', 'cohere'."
    ),
    model_name: str = typer.Option("gpt-4o", help="Model name or deployment name."),
    system_prompt: Optional[str] = typer.Option(
        None,
        help="Custom system prompt. If not provided, uses a default prompt optimized for Jupyter interaction."
    ),
    verbose: bool = typer.Option(False, help="Enable verbose logging."),
):
    """
    Start an interactive REPL with direct access to Jupyter MCP tools.
    
    This command launches pydantic-ai's built-in CLI (clai) with jupyter-mcp-server
    tools pre-configured. You can directly ask the AI to interact with Jupyter notebooks,
    execute code, read files, and more.
    
    The AI has access to jupyter-mcp-server tools:
    - list_notebooks: List available notebooks
    - read_notebook: Read notebook content
    - execute_cell: Execute code in a notebook cell
    - insert_cell: Insert new cells
    - And more...
    
    You can specify the model in two ways:
    1. Using --model with full string: --model "openai:gpt-4o"
    2. Using --model-provider and --model-name: --model-provider openai --model-name gpt-4o
    
    Special commands in the REPL:
    - /exit: Exit the session
    - /markdown: Show last response in markdown format
    - /multiline: Toggle multiline input mode (use Ctrl+D to submit)
    - /cp: Copy last response to clipboard
    
    Examples:
        # Using full model string
        jupyter-ai-agents repl \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --model "openai:gpt-4o"
        
        # Using provider and name with custom prompt
        jupyter-ai-agents repl \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --model-provider anthropic \\
            --model-name claude-sonnet-4-0 \\
            --system-prompt "You are a data science expert."
        
        # Then in the REPL, you can ask:
        > List all notebooks in the current directory
        > Create a new notebook called analysis.ipynb
        > In analysis.ipynb, create a cell that imports pandas and loads data.csv
        > Execute the cell and show me the first 5 rows
    """
    if verbose:
        enable_verbose_logging()
    
    async def _run():
        try:
            from pydantic_ai import Agent
            
            # Determine model - use model object for special providers like Azure
            if model:
                model_obj = model
                logger.info(f"Using explicit model: {model_obj}")
            else:
                model_obj = create_model_with_provider(model_provider, model_name)
                if isinstance(model_obj, str):
                    logger.info(f"Using model: {model_obj} (from {model_provider} + {model_name})")
                else:
                    logger.info(f"Using {model_provider} model: {model_name}")
            
            # Create MCP server connection
            logger.info(f"Connecting to Jupyter server at {url}")
            mcp_server = create_mcp_server(url, token)
            
            # List available tools from the MCP server
            async def list_tools():
                """List all tools available from the jupyter-mcp-server"""
                try:
                    typer.echo("\n🔧 Available Jupyter MCP Tools:")
                    typer.echo(f"   Connecting to: {url.rstrip('/')}/mcp")

                    tools = await get_available_tools_from_mcp(url, token)

                    if not tools:
                        typer.echo("\n   No tools reported by the MCP server.\n")
                        return

                    typer.echo(f"\n   Found {len(tools)} tools:\n")

                    for tool in tools:
                        name = tool.get("name", "<unknown>")
                        description = tool.get("description", "")
                        schema = tool.get("inputSchema", {}) or {}

                        params = []
                        if isinstance(schema, dict) and "properties" in schema:
                            for param_name, param_info in schema["properties"].items():
                                param_type = param_info.get("type", "any")
                                params.append(f"{param_name}: {param_type}")

                        param_str = f"({', '.join(params)})" if params else "()"
                        
                        # One-line format: name(params) - first line of description
                        desc_first_line = description.split('\n')[0] if description else ""
                        typer.echo(f"   • {name}{param_str} - {desc_first_line}")

                except Exception as e:
                    logger.warning(f"Could not list tools: {e}")
                    typer.echo(f"\n⚠️  Could not list tools: {e}")
                    typer.echo("   The agent will still work with available tools\n")
            
            # List tools before starting the agent
            await list_tools()
            
            # Create default system prompt if not provided
            if system_prompt is None:
                instructions = """You are a helpful AI assistant with direct access to Jupyter notebooks via MCP tools.

You can:
- List notebooks in directories
- Read notebook contents
- Execute code in notebook cells
- Insert new cells (code or markdown)
- Modify existing cells
- Install Python packages if needed

When the user asks you to work with notebooks:
1. Use list_notebooks to find available notebooks
2. Use read_notebook to examine notebook content
3. Use execute_cell to run code
4. Use insert_cell to add new content

Be proactive in suggesting what you can do with the available tools.
Always confirm before making destructive changes.
"""
            else:
                instructions = system_prompt
            
            # Create agent with MCP toolset
            logger.info("Creating agent with Jupyter MCP tools...")
            agent = Agent(
                model_obj,
                toolsets=[mcp_server],
                system_prompt=instructions,
            )
            
            # Display welcome message
            typer.echo("="*70)
            typer.echo("🪐 ✨ Jupyter AI Agents - Interactive REPL")
            typer.echo("="*70)
            if isinstance(model_obj, str):
                typer.echo(f"Model: {model_obj}")
            else:
                typer.echo(f"Model: {model_provider}:{model_name}")
            typer.echo(f"Jupyter Server: {url}")
            typer.echo("="*70)
            typer.echo("\nSpecial commands:")
            typer.echo("  /exit       - Exit the session")
            typer.echo("  /markdown   - Show last response in markdown")
            typer.echo("  /multiline  - Toggle multiline mode (Ctrl+D to submit)")
            typer.echo("  /cp         - Copy last response to clipboard")
            typer.echo("\nYou can directly ask the AI to interact with Jupyter notebooks!")
            typer.echo("Example: 'List all notebooks' or 'Create a matplotlib plot in notebook.ipynb'")
            typer.echo("="*70 + "\n")
            
            # Start the pydantic-ai CLI
            logger.info("Starting interactive REPL...")
            await agent.to_cli()
            
        except KeyboardInterrupt:
            typer.echo("\n\nSession interrupted by user.")
        except asyncio.CancelledError:
            # Handle cancellation from Ctrl+C during SDK retries
            logger.info("REPL session cancelled")
            typer.echo("\n\nSession cancelled.")
        except Exception as e:
            logger.error(f"Error in REPL: {e}", exc_info=True)
            typer.echo(f"\nError: {str(e)}", err=True)
            raise typer.Exit(code=1)
    
    asyncio.run(_run())


def main():
    app()


if __name__ == "__main__":
    main()
