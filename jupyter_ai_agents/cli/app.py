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

# Import tools for REPL
from jupyter_ai_agents.tools import get_available_tools_from_mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def enable_verbose_logging():
    """Enable verbose logging for debugging API calls and retries."""
    logging.getLogger().setLevel(logging.DEBUG)
    # Enable detailed HTTP logging to see retry reasons
    logging.getLogger("httpx").setLevel(logging.DEBUG)
    logging.getLogger("anthropic").setLevel(logging.DEBUG)
    logging.getLogger("openai").setLevel(logging.DEBUG)
    logger.debug("Verbose logging enabled - will show detailed HTTP requests, responses, and retry reasons")

app = typer.Typer(help="Jupyter AI Agents - AI-powered notebook manipulation with Pydantic AI and MCP.")


def get_model_string(model_provider: str, model_name: str) -> str:
    """
    Convert model provider and name to pydantic-ai model string format.
    
    Args:
        model_provider: Provider name (azure-openai, openai, anthropic, github-copilot, etc.)
        model_name: Model/deployment name
    
    Returns:
        Model string in format 'provider:model' 
        For Azure OpenAI, returns the model name and sets provider via create_model_with_provider()
    
    Note:
        For Azure OpenAI, the returned string is just the model name.
        The Azure provider configuration is handled separately via OpenAIModel(provider='azure').
        Required env vars for Azure:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT (base URL only, e.g., https://your-resource.openai.azure.com)
        - AZURE_OPENAI_API_VERSION (optional, defaults to latest)
    """
    # For Azure OpenAI, we return just the model name
    # The provider will be set to 'azure' when creating the OpenAIModel
    if model_provider.lower() == 'azure-openai':
        return model_name
    
    # Map provider names to pydantic-ai format for other providers
    provider_map = {
        'openai': 'openai',
        'anthropic': 'anthropic',
        'github-copilot': 'openai',      # GitHub Copilot uses OpenAI models
        'bedrock': 'bedrock',
        'google': 'google',
        'gemini': 'google',
        'groq': 'groq',
        'mistral': 'mistral',
        'cohere': 'cohere',
    }
    
    provider = provider_map.get(model_provider.lower(), model_provider)
    return f"{provider}:{model_name}"


def create_model_with_provider(model_provider: str, model_name: str):
    """
    Create a pydantic-ai model object with the appropriate provider configuration.
    
    This is necessary for providers like Azure OpenAI that need special initialization.
    
    Args:
        model_provider: Provider name (e.g., 'azure-openai', 'openai', 'anthropic')
        model_name: Model/deployment name
        
    Returns:
        Model object or string for pydantic-ai Agent
        
    Note:
        For Azure OpenAI, requires these environment variables:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT (base URL only, e.g., https://your-resource.openai.azure.com)
        - AZURE_OPENAI_API_VERSION (optional, defaults to latest)
    """
    if model_provider.lower() == 'azure-openai':
        from pydantic_ai.models.openai import OpenAIChatModel
        # For Azure OpenAI, create OpenAIChatModel with provider='azure'
        # Environment variables AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT must be set
        return OpenAIChatModel(model_name, provider='azure')
    else:
        # For other providers, use the standard string format
        return get_model_string(model_provider, model_name)


@app.command()
def prompt(
    url: str = typer.Option("http://localhost:8888", help="URL to the Jupyter Server."),
    token: str = typer.Option("", help="Jupyter Server token."),
    path: str = typer.Option("", help="Jupyter Notebook path."),
    input: str = typer.Option("", help="User instruction/prompt."),
    model: str = typer.Option(
        None,
        help="Full model string (e.g., 'openai:gpt-4o', 'anthropic:claude-sonnet-4-0', 'azure-openai:gpt-4o-mini'). If not provided, uses --model-provider and --model-name."
    ),
    model_provider: str = typer.Option(
        "openai",
        help="Model provider: 'openai', 'anthropic', 'azure-openai', 'github-copilot', 'google', 'bedrock', 'groq', 'mistral', 'cohere'."
    ),
    model_name: str = typer.Option("gpt-4o", help="Model name or deployment name."),
    current_cell_index: int = typer.Option(-1, help="Index of the cell where the prompt is asked."),
    full_context: bool = typer.Option(False, help="Flag to provide full notebook context to the AI model."),
    max_tool_calls: int = typer.Option(10, help="Maximum number of tool calls per agent run (prevents excessive API usage)."),
    max_requests: int = typer.Option(4, help="Maximum number of API requests per run (defaults to 4; lower for strict rate limits)."),
    verbose: bool = typer.Option(False, help="Enable verbose logging."),
):
    """
    Execute user instructions in a Jupyter notebook using AI.
    
    The agent will create code and markdown cells based on your instructions,
    execute the code, and verify it works properly.
    
    You can specify the model in two ways:
    1. Using --model with full string: --model "openai:gpt-4o"
    2. Using --model-provider and --model-name: --model-provider openai --model-name gpt-4o
    
    For Azure OpenAI, you can use either:
    - --model "azure-openai:gpt-4o-mini"
    - --model-provider azure-openai --model-name gpt-4o-mini
    
    Required environment variables for Azure OpenAI:
    - AZURE_OPENAI_API_KEY
    - AZURE_OPENAI_ENDPOINT (base URL, e.g., https://your-resource.openai.azure.com)
    - AZURE_OPENAI_API_VERSION (optional)
    
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
        enable_verbose_logging()
    
    async def _run():
        try:
            # Create MCP server connection
            logger.info(f"Connecting to Jupyter server at {url}")
            mcp_server = create_mcp_server(url, token)
            
            # Determine model - handle azure-openai:deployment format or use provider+name
            if model:
                # Check if model string is in azure-openai:deployment format
                if model.startswith('azure-openai:'):
                    from pydantic_ai.models.openai import OpenAIChatModel
                    deployment_name = model.split(':', 1)[1]
                    model_obj = OpenAIChatModel(deployment_name, provider='azure')
                    logger.info(f"Using Azure OpenAI deployment: {deployment_name}")
                else:
                    # User provided full model string
                    model_obj = model
                    logger.info(f"Using explicit model: {model_obj}")
            else:
                # Create model object with provider-specific configuration
                model_obj = create_model_with_provider(model_provider, model_name)
                if isinstance(model_obj, str):
                    logger.info(f"Using model: {model_obj} (from {model_provider} + {model_name})")
                else:
                    logger.info(f"Using {model_provider} model: {model_name}")
            
            # Prepare notebook context
            notebook_context = {
                'notebook_path': path,
                'current_cell_index': current_cell_index,
                'full_context': full_context,
            }
            
            # Create and run agent
            logger.info("Creating prompt agent...")
            agent = create_prompt_agent(model_obj, mcp_server, notebook_context, max_tool_calls=max_tool_calls)
            
            logger.info("Running prompt agent...")
            result = await run_prompt_agent(agent, input, notebook_context, max_tool_calls=max_tool_calls, max_requests=max_requests)
            
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
        help="Full model string (e.g., 'openai:gpt-4o', 'anthropic:claude-sonnet-4-0', 'azure-openai:gpt-4o-mini'). If not provided, uses --model-provider and --model-name."
    ),
    model_provider: str = typer.Option(
        "openai",
        help="Model provider: 'openai', 'anthropic', 'azure-openai', 'github-copilot', 'google', 'bedrock', 'groq', 'mistral', 'cohere'."
    ),
    model_name: str = typer.Option("gpt-4o", help="Model name or deployment name."),
    current_cell_index: int = typer.Option(-1, help="Index of the cell with the error (-1 for first error)."),
    max_tool_calls: int = typer.Option(10, help="Maximum number of tool calls per agent run (prevents excessive API usage)."),
    verbose: bool = typer.Option(False, help="Enable verbose logging."),
):
    """
    Explain and fix errors in a Jupyter notebook using AI.
    
    The agent will analyze the error, explain what went wrong, and insert
    corrected code cells to fix the issue.
    
    You can specify the model in two ways:
    1. Using --model with full string: --model "openai:gpt-4o"
    2. Using --model-provider and --model-name: --model-provider openai --model-name gpt-4o
    
    For Azure OpenAI, you can use either:
    - --model "azure-openai:gpt-4o-mini"
    - --model-provider azure-openai --model-name gpt-4o-mini
    
    Required environment variables for Azure OpenAI:
    - AZURE_OPENAI_API_KEY
    - AZURE_OPENAI_ENDPOINT (base URL, e.g., https://your-resource.openai.azure.com)
    - AZURE_OPENAI_API_VERSION (optional)
    
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
        enable_verbose_logging()
    
    async def _run():
        try:
            # Create MCP server connection
            logger.info(f"Connecting to Jupyter server at {url}")
            mcp_server = create_mcp_server(url, token)
            
            # Determine model - handle azure-openai:deployment format or use provider+name
            if model:
                # Check if model string is in azure-openai:deployment format
                if model.startswith('azure-openai:'):
                    from pydantic_ai.models.openai import OpenAIChatModel
                    deployment_name = model.split(':', 1)[1]
                    model_obj = OpenAIChatModel(deployment_name, provider='azure')
                    logger.info(f"Using Azure OpenAI deployment: {deployment_name}")
                else:
                    model_obj = model
                    logger.info(f"Using explicit model: {model_obj}")
            else:
                model_obj = create_model_with_provider(model_provider, model_name)
                if isinstance(model_obj, str):
                    logger.info(f"Using model: {model_obj} (from {model_provider} + {model_name})")
                else:
                    logger.info(f"Using {model_provider} model: {model_name}")
            
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
                model_obj,
                mcp_server,
                notebook_content=notebook_content,
                error_cell_index=current_cell_index,
                max_tool_calls=max_tool_calls,
            )
            
            logger.info("Running explain error agent...")
            result = await run_explain_error_agent(
                agent,
                error_description,
                notebook_content=notebook_content,
                error_cell_index=current_cell_index,
                max_tool_calls=max_tool_calls,
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
def repl(
    url: str = typer.Option(None, help="URL to the Jupyter Server (for jupyter-mcp-server integration)."),
    token: str = typer.Option("", help="Jupyter Server token."),
    mcp_servers: str = typer.Option(
        None,
        help="Comma-separated list of MCP server URLs (e.g., 'http://localhost:8001,http://localhost:8002'). Use this OR --url, not both."
    ),
    model: str = typer.Option(
        None,
        help="Full model string (e.g., 'openai:gpt-4o', 'anthropic:claude-sonnet-4-0', 'azure-openai:gpt-4o-mini'). If not provided, uses --model-provider and --model-name."
    ),
    model_provider: str = typer.Option(
        "openai",
        help="Model provider: 'openai', 'anthropic', 'azure-openai', 'github-copilot', 'google', 'bedrock', 'groq', 'mistral', 'cohere'."
    ),
    model_name: str = typer.Option("gpt-4o", help="Model name or deployment name."),
    system_prompt: str = typer.Option(
        None,
        help="Custom system prompt. If not provided, uses a default prompt based on the MCP servers being used."
    ),
    verbose: bool = typer.Option(False, help="Enable verbose logging."),
):
    """
    Start an interactive REPL with access to MCP tools.
    
    This command launches pydantic-ai's built-in CLI with MCP server tools.
    You can connect to:
    1. Jupyter MCP server (jupyter-mcp-server) via --url
    2. External MCP servers via --mcp-servers
    
    Use --url for jupyter-mcp-server integration with Jupyter notebooks.
    Use --mcp-servers for connecting to standalone MCP servers (e.g., calculator, weather, etc.).
    
    You can specify the model in two ways:
    1. Using --model with full string: --model "openai:gpt-4o"
    2. Using --model-provider and --model-name: --model-provider openai --model-name gpt-4o
    
    For Azure OpenAI, you can use either:
    - --model "azure-openai:gpt-4o-mini"
    - --model-provider azure-openai --model-name gpt-4o-mini
    
    Required environment variables for Azure OpenAI:
    - AZURE_OPENAI_API_KEY
    - AZURE_OPENAI_ENDPOINT (base URL, e.g., https://your-resource.openai.azure.com)
    - AZURE_OPENAI_API_VERSION (optional)
    
    Special commands in the REPL:
    - /exit: Exit the session
    - /markdown: Show last response in markdown format
    - /multiline: Toggle multiline input mode (use Ctrl+D to submit)
    - /cp: Copy last response to clipboard
    
    Examples:
        # Connect to Jupyter Server (jupyter-mcp-server)
        jupyter-ai-agents repl \\
            --url http://localhost:8888 \\
            --token MY_TOKEN \\
            --model "openai:gpt-4o"
        
        # Connect to external MCP servers
        jupyter-ai-agents repl \\
            --mcp-servers "http://localhost:8001,http://localhost:8002" \\
            --model-provider openai \\
            --model-name gpt-4o
        
        # Then in the REPL with Jupyter, you can ask:
        > List all notebooks in the current directory
        > Create a new notebook called analysis.ipynb
        > In analysis.ipynb, create a cell that imports pandas
        
        # Or with external MCP servers (e.g., calculator + echo):
        > Add 5 and 7
        > Reverse the text "hello world"
    """
    if verbose:
        enable_verbose_logging()
    
    # Validate that user provides either --url or --mcp-servers, not both
    if url and mcp_servers:
        typer.echo("❌ Error: Cannot use both --url and --mcp-servers. Choose one:", err=True)
        typer.echo("   --url: For Jupyter Server (jupyter-mcp-server)", err=True)
        typer.echo("   --mcp-servers: For external MCP servers", err=True)
        raise typer.Exit(code=1)
    
    if not url and not mcp_servers:
        typer.echo("❌ Error: Must provide either --url or --mcp-servers:", err=True)
        typer.echo("   --url: For Jupyter Server (jupyter-mcp-server)", err=True)
        typer.echo("   --mcp-servers: For external MCP servers (comma-separated URLs)", err=True)
        raise typer.Exit(code=1)
    
    # Separate function to initialize and list tools
    async def list_tools_async():
        """List all tools available from the MCP server(s)"""
        try:
            if url:
                # Jupyter MCP server
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
            else:
                # External MCP servers
                from jupyter_ai_agents.tools import MCPServerStreamableHTTP
                
                server_urls = [s.strip() for s in mcp_servers.split(',')]
                typer.echo("\n🔧 Available MCP Tools:")
                
                for server_url in server_urls:
                    typer.echo(f"\n   Connecting to: {server_url}")
                    try:
                        mcp_client = MCPServerStreamableHTTP(server_url)
                        
                        # Initialize connection and list tools
                        async with mcp_client:
                            await mcp_client.initialize()
                            tools = await mcp_client.list_tools()
                            
                            if not tools or len(tools) == 0:
                                typer.echo("     No tools available")
                                continue
                            
                            typer.echo(f"     Found {len(tools)} tools:")
                            for tool in tools:
                                name = tool.name
                                description = tool.description or ""
                                schema = tool.inputSchema
                                
                                params = []
                                if schema and "properties" in schema:
                                    for param_name, param_info in schema["properties"].items():
                                        param_type = param_info.get("type", "any")
                                        params.append(f"{param_name}: {param_type}")
                                
                                param_str = f"({', '.join(params)})" if params else "()"
                                desc_first_line = description.split('\n')[0] if description else ""
                                typer.echo(f"     • {name}{param_str} - {desc_first_line}")
                    except Exception as e:
                        logger.warning(f"Could not connect to {server_url}: {e}")
                        typer.echo(f"     ⚠️  Could not connect: {e}")

        except Exception as e:
            logger.warning(f"Could not list tools: {e}")
            typer.echo(f"\n⚠️  Could not list tools: {e}")
            typer.echo("   The agent will still work with available tools\n")
    
    try:
        from pydantic_ai import Agent
        
        # Determine model - handle azure-openai:deployment format or use provider+name
        if model:
            # Check if model string is in azure-openai:deployment format
            if model.startswith('azure-openai:'):
                from pydantic_ai.models.openai import OpenAIChatModel
                deployment_name = model.split(':', 1)[1]
                model_obj = OpenAIChatModel(deployment_name, provider='azure')
                logger.info(f"Using Azure OpenAI deployment: {deployment_name}")
            else:
                model_obj = model
                logger.info(f"Using explicit model: {model_obj}")
        else:
            model_obj = create_model_with_provider(model_provider, model_name)
            if isinstance(model_obj, str):
                logger.info(f"Using model: {model_obj} (from {model_provider} + {model_name})")
            else:
                logger.info(f"Using {model_provider} model: {model_name}")
        
        # Create MCP server connection(s)
        toolsets = []
        if url:
            # Jupyter MCP server
            logger.info(f"Connecting to Jupyter server at {url}")
            mcp_server = create_mcp_server(url, token)
            toolsets.append(mcp_server)
        else:
            # External MCP servers
            from jupyter_ai_agents.tools import MCPServerStreamableHTTP
            
            server_urls = [s.strip() for s in mcp_servers.split(',')]
            logger.info(f"Connecting to {len(server_urls)} MCP server(s)")
            
            for server_url in server_urls:
                logger.info(f"  - {server_url}")
                mcp_client = MCPServerStreamableHTTP(server_url)
                toolsets.append(mcp_client)
        
        # List tools before starting the agent (separate asyncio.run call)
        asyncio.run(list_tools_async())
        
        # Create default system prompt if not provided
        if system_prompt is None:
            if url:
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
                instructions = """You are a helpful AI assistant with access to various MCP tools.

Use the available tools to help the user accomplish their tasks.
Be proactive in suggesting what you can do with the available tools.
"""
        else:
            instructions = system_prompt
        
        # Create agent with MCP toolset(s)
        logger.info("Creating agent with MCP tools...")
        agent = Agent(
            model_obj,
            toolsets=toolsets,
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
        
        if url:
            typer.echo(f"Jupyter Server: {url}")
        else:
            server_urls = [s.strip() for s in mcp_servers.split(',')]
            typer.echo(f"MCP Servers: {len(server_urls)} connected")
            for server_url in server_urls:
                typer.echo(f"  - {server_url}")
        
        typer.echo("="*70)
        typer.echo("\nSpecial commands:")
        typer.echo("  /exit       - Exit the session")
        typer.echo("  /markdown   - Show last response in markdown")
        typer.echo("  /multiline  - Toggle multiline mode (Ctrl+D to submit)")
        typer.echo("  /cp         - Copy last response to clipboard")
        
        if url:
            typer.echo("\nYou can directly ask the AI to interact with Jupyter notebooks!")
            typer.echo("Example: 'List all notebooks' or 'Create a matplotlib plot in notebook.ipynb'")
        else:
            typer.echo("\nYou can directly ask the AI to use the available MCP tools!")
            typer.echo("Example: 'Add 5 and 7' or 'Reverse the text hello world'")
        
        typer.echo("="*70 + "\n")
        
        # Launch the CLI interface (separate asyncio.run call with context manager)
        async def _run_cli() -> None:
            assert agent is not None
            async with agent:
                await agent.to_cli()
        
        asyncio.run(_run_cli())
    
    except KeyboardInterrupt:
        typer.echo("\n\n🛑 Agent stopped by user")
    except asyncio.CancelledError:
        # Handle cancellation from Ctrl+C during SDK retries
        logger.info("REPL session cancelled")
        typer.echo("\n\n🛑 Session cancelled")
    except BaseExceptionGroup as exc:
        typer.echo("\n❌ Encountered errors while running the CLI:")
        for idx, sub_exc in enumerate(exc.exceptions, start=1):
            typer.echo(f"  [{idx}] {type(sub_exc).__name__}: {sub_exc}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Error in REPL: {e}", exc_info=True)
        typer.echo(f"\n❌ Error: {str(e)}", err=True)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
