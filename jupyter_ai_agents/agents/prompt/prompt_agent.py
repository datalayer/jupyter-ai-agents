# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Pydantic AI Prompt Agent - creates and executes code based on user instructions."""

import logging
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a powerful coding assistant for Jupyter notebooks.
Create and execute code in a notebook based on user instructions.
Add markdown cells to explain the code and structure the notebook clearly.

Important guidelines:
- Assume that no packages are installed in the notebook, so install them using code cells with !pip install
- Ensure updates to cell indexing when new cells are inserted
- Maintain the logical flow of execution by adjusting cell index as needed
- Use the available Jupyter MCP tools to interact with the notebook
- Always execute code cells after inserting them to verify they work

Available tools through MCP:
- notebook tools for inserting/modifying cells
- kernel tools for executing code
- file system tools for reading/writing files

When the user asks you to create something, break it down into steps:
1. Install any required packages
2. Import necessary libraries
3. Write the main code
4. Add markdown explanations

Execute each code cell as you create it to ensure it works properly.

IMPORTANT: When you have completed the task successfully, provide a final text response summarizing what you did WITHOUT making any more tool calls. This signals completion and allows the program to exit properly."""


class PromptAgentDeps:
    """Dependencies for the prompt agent."""
    
    def __init__(self, notebook_context: dict[str, Any] | None = None):
        """Initialize dependencies.
        
        Args:
            notebook_context: Optional context about the notebook (path, cells, etc.)
        """
        self.notebook_context = notebook_context or {}
        self.current_cell_index = notebook_context.get('current_cell_index', -1) if notebook_context else -1
        self.full_context = notebook_context.get('full_context', False) if notebook_context else False
        self.notebook_content = notebook_context.get('notebook_content', '') if notebook_context else ''


def create_prompt_agent(
    model: str,
    mcp_server: MCPServerStreamableHTTP,
    notebook_context: dict[str, Any] | None = None,
    max_tool_calls: int = 10,
) -> Agent[PromptAgentDeps, str]:
    """
    Create the Prompt Agent for handling user instructions.
    
    Args:
        model: Model identifier (e.g., 'anthropic:claude-sonnet-4-0', 'openai:gpt-4o')
        mcp_server: MCP server connection to jupyter-mcp-server
        notebook_context: Optional context about the notebook
        max_tool_calls: Maximum number of tool calls to make (default: 10)
    
    Returns:
        Configured Pydantic AI agent
    """
    # Enhance system prompt with notebook context if available
    system_prompt = SYSTEM_PROMPT
    
    if notebook_context:
        if notebook_context.get('full_context') and notebook_context.get('notebook_content'):
            system_prompt += f"\n\nCurrent notebook content:\n{notebook_context['notebook_content']}"
        
        if notebook_context.get('current_cell_index', -1) != -1:
            system_prompt += f"\n\nUser instruction was given at cell index: {notebook_context['current_cell_index']}"
    
    # Add reminder to be efficient and complete properly
    system_prompt += (
        "\n\nBe efficient: Complete the task in as few steps as possible. "
        "Don't over-verify or re-check unnecessarily. "
        "When the task is done, provide a final summary WITHOUT tool calls to signal completion."
    )
    
    # Create agent with MCP toolset
    agent = Agent(
        model,
        toolsets=[mcp_server],
        deps_type=PromptAgentDeps,
        system_prompt=system_prompt,
    )
    
    logger.info(f"Created prompt agent with model {model} (max_tool_calls={max_tool_calls})")
    
    return agent


async def run_prompt_agent(
    agent: Agent[PromptAgentDeps, str],
    user_input: str,
    notebook_context: dict[str, Any] | None = None,
    max_tool_calls: int = 10,
    max_requests: int = 2,
) -> str:
    """
    Run the prompt agent with user input.
    
    Args:
        agent: The configured prompt agent
        user_input: User's instruction/prompt
        notebook_context: Optional notebook context (should include 'notebook_path')
        max_tool_calls: Maximum number of tool calls to prevent excessive API usage
    max_requests: Maximum number of API requests (default: 4, lower if needed for strict rate limits)
    
    Returns:
        Agent's response
    """
    import asyncio
    import os
    from pydantic_ai import UsageLimitExceeded, UsageLimits
    
    deps = PromptAgentDeps(notebook_context)
    
    logger.info(f"Running prompt agent with input: {user_input[:50]}... (max_tool_calls={max_tool_calls}, max_requests={max_requests})")
    
    # Prepend notebook connection instruction if path is provided
    if notebook_context and notebook_context.get('notebook_path'):
        notebook_path = notebook_context['notebook_path']
        notebook_name = os.path.splitext(os.path.basename(notebook_path))[0]
        
        # Prepend instruction to connect to the notebook first
        enhanced_input = (
            f"First, use the use_notebook tool to connect to the notebook at path '{notebook_path}' "
            f"with notebook_name '{notebook_name}' and mode 'connect'. "
            f"Then, {user_input}"
        )
        logger.info(f"Enhanced input to connect to notebook: {notebook_path}")
    else:
        enhanced_input = user_input
    
    # Warn about low limits
    if max_requests <= 2:
        logger.warning(
            f"Using very conservative request limit ({max_requests}). "
            "This may result in incomplete responses. "
            "Increase --max-requests if your Azure tier allows."
        )
    
    try:
        # Create usage limits to prevent excessive API calls
        # Use strict limits to avoid rate limiting
        usage_limits = UsageLimits(
            tool_calls_limit=max_tool_calls,
            request_limit=max_requests,  # Strict limit to avoid rate limiting
        )
        
        # Add timeout to prevent hanging on retries
        result = await asyncio.wait_for(
            agent.run(enhanced_input, deps=deps, usage_limits=usage_limits),
            timeout=120.0  # 2 minute timeout
        )
        logger.info("Prompt agent completed successfully")
        return result.response
    except asyncio.TimeoutError:
        logger.error("Prompt agent timed out after 120 seconds")
        return "Error: Operation timed out. The agent may have hit rate limits or is taking too long."
    except UsageLimitExceeded as e:
        logger.error(f"Prompt agent hit usage limits: {e}")
        return (
            "Error: Reached the configured usage limits.\n"
            f"Increase --max-requests (currently {max_requests}) or --max-tool-calls (currently {max_tool_calls}) "
            "if your model provider allows more usage."
        )
    except Exception as e:
        logger.error(f"Error running prompt agent: {e}", exc_info=True)
        return f"Error: {str(e)}"


def create_prompt_agent_sync(
    base_url: str,
    token: str,
    model: str,
    notebook_context: dict[str, Any] | None = None,
) -> Agent[PromptAgentDeps, str]:
    """
    Create prompt agent with MCP server connection (synchronous wrapper).
    
    Args:
        base_url: Jupyter server base URL
        token: Authentication token
        model: Model identifier
        notebook_context: Optional notebook context
    
    Returns:
        Configured agent
    """
    mcp_server = create_mcp_server(base_url, token)
    return create_prompt_agent(model, mcp_server, notebook_context)
