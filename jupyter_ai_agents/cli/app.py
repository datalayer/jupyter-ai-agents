# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Jupyter AI Agents CLI - Pydantic AI agents with MCP integration."""

from __future__ import annotations

import typer
import asyncio
import logging

# Pydantic AI agents
from jupyter_ai_agents.agents.pydantic.cli.prompt_agent import (
    create_prompt_agent,
    run_prompt_agent,
)
from jupyter_ai_agents.agents.pydantic.cli.explain_error_agent import (
    create_explain_error_agent,
    run_explain_error_agent,
)
from jupyter_ai_agents.tools import create_mcp_server

# Import repl command directly
from jupyter_ai_agents.cli.repl import repl as repl_command

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = typer.Typer(help="Jupyter AI Agents - AI-powered notebook manipulation with Pydantic AI and MCP.")

# Register repl command
app.command(name="repl")(repl_command)


def get_model_string(model_provider: str, model_name: str) -> str:
    """
    Convert model provider and name to pydantic-ai model string format.
    
    Args:
        model_provider: Provider name (azure-openai, openai, anthropic, github-copilot, etc.)
        model_name: Model/deployment name
    
    Returns:
        Model string in format 'provider:model'
    """
    # Map provider names to pydantic-ai format
    provider_map = {
        'azure-openai': 'openai',  # Azure OpenAI uses openai provider
        'openai': 'openai',
        'anthropic': 'anthropic',
        'github-copilot': 'openai',  # GitHub Copilot uses OpenAI models
        'bedrock': 'bedrock',
        'google': 'google',
        'gemini': 'google',
        'groq': 'groq',
        'mistral': 'mistral',
        'cohere': 'cohere',
    }
    
    provider = provider_map.get(model_provider, model_provider)
    return f"{provider}:{model_name}"


@app.command()
def prompt(
    url: str = typer.Option("http://localhost:8888", help="URL to the Jupyter Server."),
    token: str = typer.Option("", help="Jupyter Server token."),
    path: str = typer.Option("", help="Jupyter Notebook path."),
    input: str = typer.Option("", help="User instruction/prompt."),
    model: str = typer.Option(
        None,
        help="Full model string (e.g., 'openai:gpt-4o', 'anthropic:claude-sonnet-4-0'). If not provided, uses --model-provider and --model-name."
    ),
    model_provider: str = typer.Option(
        "openai",
        help="Model provider: 'openai', 'anthropic', 'azure-openai', 'github-copilot', 'google', 'bedrock', 'groq', 'mistral', 'cohere'."
    ),
    model_name: str = typer.Option("gpt-4o", help="Model name or deployment name."),
    current_cell_index: int = typer.Option(-1, help="Index of the cell where the prompt is asked."),
    full_context: bool = typer.Option(False, help="Flag to provide full notebook context to the AI model."),
    verbose: bool = typer.Option(False, help="Enable verbose logging."),
):
    """
    Execute user instructions in a Jupyter notebook using AI.
    
    The agent will create code and markdown cells based on your instructions,
    execute the code, and verify it works properly.
    
    You can specify the model in two ways:
    1. Using --model with full string: --model "openai:gpt-4o"
    2. Using --model-provider and --model-name: --model-provider openai --model-name gpt-4o
    
    Examples:
        # Using full model string
        jupyter-ai-agents prompt \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --path notebook.ipynb \\
            --model "openai:gpt-4o" \\
            --input "Create a matplotlib example"
        
        # Using provider and name
        jupyter-ai-agents prompt \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --path notebook.ipynb \\
            --model-provider anthropic \\
            --model-name claude-sonnet-4-0 \\
            --input "Create a matplotlib example"
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async def _run():
        try:
            # Create MCP server connection
            logger.info(f"Connecting to Jupyter server at {url}")
            mcp_server = create_mcp_server(url, token)
            
            # Determine model string
            if model:
                model_str = model
                logger.info(f"Using explicit model: {model_str}")
            else:
                model_str = get_model_string(model_provider, model_name)
                logger.info(f"Using model: {model_str} (from {model_provider} + {model_name})")
            
            # Prepare notebook context
            notebook_context = {
                'notebook_path': path,
                'current_cell_index': current_cell_index,
                'full_context': full_context,
            }
            
            # Create and run agent
            logger.info("Creating prompt agent...")
            agent = create_prompt_agent(model_str, mcp_server, notebook_context)
            
            logger.info("Running prompt agent...")
            result = await run_prompt_agent(agent, input, notebook_context)
            
            # Print result
            typer.echo("\n" + "="*60)
            typer.echo("AI Agent Response:")
            typer.echo("="*60)
            typer.echo(result)
            typer.echo("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"Error running prompt agent: {e}", exc_info=True)
            typer.echo(f"Error: {str(e)}", err=True)
            raise typer.Exit(code=1)
    
    asyncio.run(_run())

@app.command()
def explain_error(
    url: str = typer.Option("http://localhost:8888", help="URL to the Jupyter Server."),
    token: str = typer.Option("", help="Jupyter Server token."),
    path: str = typer.Option("", help="Jupyter Notebook path."),
    model: str = typer.Option(
        None,
        help="Full model string (e.g., 'openai:gpt-4o', 'anthropic:claude-sonnet-4-0'). If not provided, uses --model-provider and --model-name."
    ),
    model_provider: str = typer.Option(
        "openai",
        help="Model provider: 'openai', 'anthropic', 'azure-openai', 'github-copilot', 'google', 'bedrock', 'groq', 'mistral', 'cohere'."
    ),
    model_name: str = typer.Option("gpt-4o", help="Model name or deployment name."),
    current_cell_index: int = typer.Option(-1, help="Index of the cell with the error (-1 for first error)."),
    verbose: bool = typer.Option(False, help="Enable verbose logging."),
):
    """
    Explain and fix errors in a Jupyter notebook using AI.
    
    The agent will analyze the error, explain what went wrong, and insert
    corrected code cells to fix the issue.
    
    You can specify the model in two ways:
    1. Using --model with full string: --model "openai:gpt-4o"
    2. Using --model-provider and --model-name: --model-provider openai --model-name gpt-4o
    
    Examples:
        # Using full model string
        jupyter-ai-agents explain-error \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --path notebook.ipynb \\
            --model "anthropic:claude-sonnet-4-0" \\
            --current-cell-index 5
        
        # Using provider and name
        jupyter-ai-agents explain-error \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --path notebook.ipynb \\
            --model-provider openai \\
            --model-name gpt-4o
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async def _run():
        try:
            # Create MCP server connection
            logger.info(f"Connecting to Jupyter server at {url}")
            mcp_server = create_mcp_server(url, token)
            
            # Determine model string
            if model:
                model_str = model
                logger.info(f"Using explicit model: {model_str}")
            else:
                model_str = get_model_string(model_provider, model_name)
                logger.info(f"Using model: {model_str} (from {model_provider} + {model_name})")
            
            # In a real implementation, we would:
            # 1. Fetch notebook content from server
            # 2. Extract error information
            # 3. Pass to agent
            
            # For now, create a placeholder
            # TODO: Implement notebook content fetching via MCP or direct API
            notebook_content = "# Notebook content would be fetched here"
            error_description = "Error: Please implement notebook error fetching"
            
            logger.info("Creating explain error agent...")
            agent = create_explain_error_agent(
                model_str,
                mcp_server,
                notebook_content=notebook_content,
                error_cell_index=current_cell_index,
            )
            
            logger.info("Running explain error agent...")
            result = await run_explain_error_agent(
                agent,
                error_description,
                notebook_content=notebook_content,
                error_cell_index=current_cell_index,
            )
            
            # Print result
            typer.echo("\n" + "="*60)
            typer.echo("AI Agent Error Analysis:")
            typer.echo("="*60)
            typer.echo(result)
            typer.echo("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"Error running explain error agent: {e}", exc_info=True)
            typer.echo(f"Error: {str(e)}", err=True)
            raise typer.Exit(code=1)
    
    asyncio.run(_run())


@app.command()
def interactive(
    url: str = typer.Option("http://localhost:8888", help="URL to the Jupyter Server."),
    token: str = typer.Option("", help="Jupyter Server token."),
    path: str = typer.Option("", help="Jupyter Notebook path."),
    model: str = typer.Option(
        None,
        help="Full model string (e.g., 'openai:gpt-4o', 'anthropic:claude-sonnet-4-0'). If not provided, uses --model-provider and --model-name."
    ),
    model_provider: str = typer.Option(
        "openai",
        help="Model provider: 'openai', 'anthropic', 'azure-openai', 'github-copilot', 'google', 'bedrock', 'groq', 'mistral', 'cohere'."
    ),
    model_name: str = typer.Option("gpt-4o", help="Model name or deployment name."),
):
    """
    Start an interactive session with the AI agent (Pydantic AI only).
    
    Uses pydantic-ai's built-in CLI interface for a conversational experience
    with the notebook. This mode is only available with the Pydantic AI backend.
    
    You can specify the model in two ways:
    1. Using --model with full string: --model "openai:gpt-4o"
    2. Using --model-provider and --model-name: --model-provider openai --model-name gpt-4o
    
    Special commands:
    - /exit: Exit the session
    - /markdown: Show last response in markdown format
    - /multiline: Toggle multiline input mode (use Ctrl+D to submit)
    - /cp: Copy last response to clipboard
    
    Examples:
        # Using full model string
        jupyter-ai-agents interactive \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --path notebook.ipynb \\
            --model "anthropic:claude-sonnet-4-0"
        
        # Using provider and name
        jupyter-ai-agents interactive \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --path notebook.ipynb \\
            --model-provider openai \\
            --model-name gpt-4o
    """
    async def _run():
        try:
            # Create MCP server connection
            logger.info(f"Connecting to Jupyter server at {url}")
            mcp_server = create_mcp_server(url, token)
            
            # Determine model string
            if model:
                model_str = model
                logger.info(f"Using explicit model: {model_str}")
            else:
                model_str = get_model_string(model_provider, model_name)
                logger.info(f"Using model: {model_str} (from {model_provider} + {model_name})")
            
            # Create agent
            notebook_context = {'notebook_path': path}
            agent = create_prompt_agent(model_str, mcp_server, notebook_context)
            
            typer.echo("="*60)
            typer.echo("Jupyter AI Agents - Interactive Mode")
            typer.echo("="*60)
            typer.echo(f"Connected to: {url}")
            typer.echo(f"Notebook: {path}")
            typer.echo(f"Model: {model_str}")
            typer.echo("="*60)
            typer.echo("Type your instructions. Use /exit to quit.\n")
            
            # Use pydantic-ai's CLI
            await agent.to_cli()
            
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}", exc_info=True)
            typer.echo(f"Error: {str(e)}", err=True)
            raise typer.Exit(code=1)
    
    asyncio.run(_run())


def main():
    app()


if __name__ == "__main__":
    main()
