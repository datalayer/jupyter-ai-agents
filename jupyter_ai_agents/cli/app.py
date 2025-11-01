# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Jupyter AI Agents CLI - Pydantic AI agents with MCP integration."""

from __future__ import annotations

import typer
import asyncio
import logging
import httpx

# Pydantic AI agents
from jupyter_ai_agents.agents.prompt.prompt_agent import (
    create_prompt_agent,
    run_prompt_agent,
)
from jupyter_ai_agents.agents.explain_error.explain_error_agent import (
    create_explain_error_agent,
    run_explain_error_agent,
)
from jupyter_ai_agents.agents.prompt.prompt_agent import (
    create_prompt_agent,
    run_prompt_agent,
)
from jupyter_ai_agents.tools import create_mcp_server

# Import tools for REPL
# Import model utilities
from jupyter_ai_agents.utils.model import create_model_with_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("anthropic").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)

def enable_verbose_logging():
    """Enable verbose logging for debugging API calls and retries."""
    # logging.getLogger().setLevel(logging.DEBUG)
    # Enable detailed HTTP logging to see retry reasons
    logging.getLogger("httpx").setLevel(logging.DEBUG)
    logging.getLogger("anthropic").setLevel(logging.DEBUG)
    logging.getLogger("openai").setLevel(logging.DEBUG)
    logger.debug("Verbose logging enabled - will show detailed HTTP requests, responses, and retry reasons")

app = typer.Typer(help="Jupyter AI Agents - AI-powered notebook manipulation with Pydantic AI and MCP.")


@app.command()
def prompt(
    mcp_servers: str = typer.Option(
        "http://localhost:8888/mcp",
        help="Comma-separated list of MCP server URLs (e.g., 'http://localhost:8888/mcp' for jupyter-mcp-server)."
    ),
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
    timeout: float = typer.Option(60.0, help="HTTP timeout in seconds for API requests (default: 60.0)."),
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
            --mcp-servers http://localhost:8888/mcp \\
            --path notebook.ipynb \\
            --model "openai:gpt-4o" \\
            --input "Create a matplotlib example"
        
        # Using provider and name
        jupyter-ai-agents prompt \\
            --mcp-servers http://localhost:8888/mcp \\
            --path notebook.ipynb \\
            --model-provider anthropic \\
            --model-name claude-sonnet-4-0 \\
            --input "Create a matplotlib example"
    """
    if verbose:
        enable_verbose_logging()
    
    async def _run():
        try:
            # Create MCP server connection(s)
            from jupyter_ai_agents.tools import MCPServerStreamableHTTP
            
            server_urls = [s.strip() for s in mcp_servers.split(',')]
            logger.info(f"Connecting to {len(server_urls)} MCP server(s)")
            
            toolsets = []
            for server_url in server_urls:
                logger.info(f"  - {server_url}")
                mcp_client = MCPServerStreamableHTTP(server_url)
                toolsets.append(mcp_client)
            
            # Use first MCP server for backward compatibility with create_prompt_agent
            mcp_server = toolsets[0] if toolsets else None
            
            # Determine model - handle azure-openai:deployment format or use provider+name
            if model:
                # Check if model string is in azure-openai:deployment format
                if model.startswith('azure-openai:'):
                    from pydantic_ai.models.openai import OpenAIChatModel
                    deployment_name = model.split(':', 1)[1]
                    model_obj = OpenAIChatModel(deployment_name, provider='azure')
                    logger.info(f"Using Azure OpenAI deployment: {deployment_name}")
                elif model.startswith('anthropic:'):
                    # Parse anthropic:model-name format and use create_model_with_provider
                    model_name_part = model.split(':', 1)[1]
                    model_obj = create_model_with_provider('anthropic', model_name_part, timeout)
                    logger.info(f"Using Anthropic model: {model_name_part} (timeout: {timeout}s)")
                else:
                    # User provided full model string
                    model_obj = model
                    logger.info(f"Using explicit model: {model_obj}")
            else:
                # Create model object with provider-specific configuration
                model_obj = create_model_with_provider(model_provider, model_name, timeout)
                if isinstance(model_obj, str):
                    logger.info(f"Using model: {model_obj} (from {model_provider} + {model_name})")
                else:
                    logger.info(f"Using {model_provider} model: {model_name} (timeout: {timeout}s)")
            
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
    mcp_servers: str = typer.Option(
        "http://localhost:8888/mcp",
        help="Comma-separated list of MCP server URLs (e.g., 'http://localhost:8888/mcp' for jupyter-mcp-server)."
    ),
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
    timeout: float = typer.Option(60.0, help="HTTP timeout in seconds for API requests (default: 60.0)."),
    current_cell_index: int = typer.Option(-1, help="Index of the cell with the error (-1 for first error)."),
    max_tool_calls: int = typer.Option(10, help="Maximum number of tool calls per agent run (prevents excessive API usage)."),
    max_requests: int = typer.Option(3, help="Maximum number of API requests per run (defaults to 3 for error fixing)."),
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
            --mcp-servers http://localhost:8888/mcp \\
            --path notebook.ipynb \\
            --model "anthropic:claude-sonnet-4-0" \\
            --current-cell-index 5
        
        # Using provider and name
        jupyter-ai-agents explain-error \\
            --mcp-servers http://localhost:8888/mcp \\
            --path notebook.ipynb \\
            --model-provider openai \\
            --model-name gpt-4o
    """
    if verbose:
        enable_verbose_logging()
    
    async def _run():
        try:
            # Create MCP server connection(s)
            from jupyter_ai_agents.tools import MCPServerStreamableHTTP
            
            server_urls = [s.strip() for s in mcp_servers.split(',')]
            logger.info(f"Connecting to {len(server_urls)} MCP server(s)")
            
            toolsets = []
            for server_url in server_urls:
                logger.info(f"  - {server_url}")
                mcp_client = MCPServerStreamableHTTP(server_url)
                toolsets.append(mcp_client)
            
            # Use first MCP server for backward compatibility with create_explain_error_agent
            mcp_server = toolsets[0] if toolsets else None
            
            # Determine model - handle azure-openai:deployment format or use provider+name
            if model:
                # Check if model string is in azure-openai:deployment format
                if model.startswith('azure-openai:'):
                    from pydantic_ai.models.openai import OpenAIChatModel
                    deployment_name = model.split(':', 1)[1]
                    model_obj = OpenAIChatModel(deployment_name, provider='azure')
                    logger.info(f"Using Azure OpenAI deployment: {deployment_name}")
                elif model.startswith('anthropic:'):
                    # Parse anthropic:model-name format and use create_model_with_provider
                    model_name_part = model.split(':', 1)[1]
                    model_obj = create_model_with_provider('anthropic', model_name_part, timeout)
                    logger.info(f"Using Anthropic model: {model_name_part} (timeout: {timeout}s)")
                else:
                    model_obj = model
                    logger.info(f"Using explicit model: {model_obj}")
            else:
                model_obj = create_model_with_provider(model_provider, model_name, timeout)
                if isinstance(model_obj, str):
                    logger.info(f"Using model: {model_obj} (from {model_provider} + {model_name})")
                else:
                    logger.info(f"Using {model_provider} model: {model_name} (timeout: {timeout}s)")
            
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
                notebook_path=path,
                max_tool_calls=max_tool_calls,
                max_requests=max_requests,
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
    mcp_servers: str = typer.Option(
        ...,
        help="Comma-separated list of MCP server URLs (e.g., 'http://localhost:8001/mcp,http://localhost:8002/mcp' for standalone servers, or 'http://localhost:8888/mcp' for jupyter-mcp-server)."
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
    timeout: float = typer.Option(60.0, help="HTTP timeout in seconds for API requests (default: 60.0)."),
    system_prompt: str = typer.Option(
        None,
        help="Custom system prompt. If not provided, uses a default prompt based on the MCP servers being used."
    ),
    verbose: bool = typer.Option(False, help="Enable verbose logging."),
):
    """
    Start an interactive REPL with access to MCP tools.
    
    This command launches pydantic-ai's built-in CLI with MCP server tools.
    You can connect to any MCP servers implementing the Streamable HTTP transport:
    - Jupyter MCP server (jupyter-mcp-server): http://localhost:8888/mcp
    - Standalone MCP servers: http://localhost:8001/mcp, http://localhost:8002/mcp, etc.
    
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
        # Connect to Jupyter MCP Server with OpenAI
        jupyter-ai-agents repl \\
            --mcp-servers "http://localhost:8888/mcp" \\
            --model "openai:gpt-4o"
        
        # Connect to standalone MCP servers with Anthropic
        # Note: Use correct Anthropic model names like claude-sonnet-4-20250514
        jupyter-ai-agents repl \\
            --mcp-servers "http://localhost:8001/mcp,http://localhost:8002/mcp" \\
            --model-provider anthropic \\
            --model-name claude-sonnet-4-20250514
        
        # Set custom timeout (useful for slow connections)
        jupyter-ai-agents repl \\
            --mcp-servers "http://localhost:8888/mcp" \\
            --timeout 120.0
        
        # Then in the REPL, you can ask:
        > List all notebooks in the current directory  (with jupyter-mcp-server)
        > Add 5 and 7  (with calculator server)
        > Reverse the text "hello world"  (with echo server)
    """
    if verbose:
        enable_verbose_logging()
    
    # Separate function to initialize and list tools
    async def list_tools_async():
        """List all tools available from the MCP server(s)"""
        try:
            from jupyter_ai_agents.tools import MCPServerStreamableHTTP
            
            server_urls = [s.strip() for s in mcp_servers.split(',')]
            
            for server_url in server_urls:
                try:
                    mcp_client = MCPServerStreamableHTTP(server_url)
                    
                    # Use context manager to connect and list tools
                    async with mcp_client:
                        tools = await mcp_client.list_tools()
                        
                        if not tools or len(tools) == 0:
                            typer.echo("\n  No tools available")
                            continue
                        
                        typer.echo(f"\n  Available Tools ({len(tools)}):")
                        for tool in tools:
                            name = tool.name
                            description = tool.description or ""
                            schema = tool.inputSchema
                            
                            # Build parameter list
                            params = []
                            if schema and "properties" in schema:
                                for param_name, param_info in schema["properties"].items():
                                    param_type = param_info.get("type", "any")
                                    params.append(f"{param_name}: {param_type}")
                            
                            param_str = f"({', '.join(params)})" if params else "()"
                            desc_first_line = description.split('\n')[0] if description else "No description"
                            typer.echo(f"    • {name}{param_str} - {desc_first_line}")
                except Exception as e:
                    logger.warning(f"Could not connect to {server_url}: {e}")
                    typer.echo(f"\n  ⚠️  Could not list tools from {server_url}")

        except Exception as e:
            logger.warning(f"Could not list tools: {e}")
            typer.echo(f"\n  ⚠️  Could not list tools: {e}")

    
    try:
        from pydantic_ai import Agent
        
        # Determine model - handle azure-openai:deployment format or use provider+name
        model_display_name = None  # Track the display name for welcome message
        
        if model:
            # Check if model string is in azure-openai:deployment format
            if model.startswith('azure-openai:'):
                from pydantic_ai.models.openai import OpenAIChatModel
                from pydantic_ai.providers import infer_provider
                from pydantic_ai.providers.openai import OpenAIProvider
                from openai.lib.azure import AsyncAzureOpenAI
                
                deployment_name = model.split(':', 1)[1]
                http_timeout = httpx.Timeout(timeout, connect=30.0)
                
                # Infer Azure provider first to get proper configuration (API key, API version, etc.)
                azure_provider_base = infer_provider('azure')
                
                # Extract base URL - remove /openai suffix since AsyncAzureOpenAI adds it
                base_url = str(azure_provider_base.client.base_url)
                # base_url is like: https://xxx.openai.azure.com/openai/
                # AsyncAzureOpenAI expects: https://xxx.openai.azure.com (it adds /openai automatically)
                azure_endpoint = base_url.rstrip('/').rsplit('/openai', 1)[0]
                
                logger.info(f"Azure OpenAI endpoint: {azure_endpoint}")
                logger.info(f"Azure OpenAI API version: {azure_provider_base.client.default_query}")
                logger.info(f"Azure OpenAI timeout: {http_timeout}")
                
                # Create Azure OpenAI client with custom timeout
                azure_client = AsyncAzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    azure_deployment=deployment_name,
                    api_version=azure_provider_base.client.default_query.get('api-version'),
                    api_key=azure_provider_base.client.api_key,
                    timeout=http_timeout,
                )
                
                # Create provider with the configured client
                from pydantic_ai.providers.openai import OpenAIProvider
                azure_provider = OpenAIProvider(openai_client=azure_client)
                
                model_obj = OpenAIChatModel(
                    deployment_name, 
                    provider=azure_provider
                )
                model_display_name = model  # azure-openai:deployment-name
                logger.info(f"Using Azure OpenAI deployment: {deployment_name}")
            elif model.startswith('anthropic:'):
                # Parse anthropic:model-name format and use create_model_with_provider
                model_name_part = model.split(':', 1)[1]
                model_obj = create_model_with_provider('anthropic', model_name_part, timeout)
                model_display_name = model
                logger.info(f"Using Anthropic model: {model_name_part} (timeout: {timeout}s)")
            else:
                model_obj = model
                model_display_name = model
                logger.info(f"Using explicit model: {model_obj}")
        else:
            model_obj = create_model_with_provider(model_provider, model_name, timeout)
            if isinstance(model_obj, str):
                model_display_name = model_obj
                logger.info(f"Using model: {model_obj} (from {model_provider} + {model_name})")
            else:
                model_display_name = f"{model_provider}:{model_name}"
                logger.info(f"Using {model_provider} model: {model_name} (timeout: {timeout}s)")
        
        # Create MCP server connection(s)
        from jupyter_ai_agents.tools import MCPServerStreamableHTTP
        
        server_urls = [s.strip() for s in mcp_servers.split(',')]
        logger.info(f"Connecting to {len(server_urls)} MCP server(s)")
        
        toolsets = []
        for server_url in server_urls:
            logger.info(f"  - {server_url}")
            mcp_client = MCPServerStreamableHTTP(server_url)
            toolsets.append(mcp_client)
        
        # Display welcome message
        typer.echo("="*70)
        typer.echo("🪐 ✨ Jupyter AI Agents - Interactive REPL")
        typer.echo("="*70)
        typer.echo(f"Model: {model_display_name}")
        
        typer.echo(f"MCP Servers: {len(server_urls)} connected")
        for server_url in server_urls:
            typer.echo(f"  - {server_url}")
        
        # List tools inline in welcome message
        asyncio.run(list_tools_async())
        
        # Create default system prompt if not provided
        if system_prompt is None:
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
        
        typer.echo("="*70)
        typer.echo("\nSpecial commands:")
        typer.echo("  /exit       - Exit the session")
        typer.echo("  /markdown   - Show last response in markdown")
        typer.echo("  /multiline  - Toggle multiline mode (Ctrl+D to submit)")
        typer.echo("  /cp         - Copy last response to clipboard")
        typer.echo("="*70 + "\n")
        
        # Launch the CLI interface (separate asyncio.run call with context manager)
        async def _run_cli() -> None:
            assert agent is not None
            async with agent:
                await agent.to_cli(prog_name='jupyter-ai-agents')
        
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
