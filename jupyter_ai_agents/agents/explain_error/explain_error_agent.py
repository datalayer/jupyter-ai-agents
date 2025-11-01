# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Pydantic AI Explain Error Agent - analyzes and fixes notebook errors."""

import logging
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStreamableHTTP

from jupyter_ai_agents.tools import create_mcp_server

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a powerful coding assistant specialized in debugging Jupyter notebooks.
Your goal is to help users understand coding errors and provide corrections.

When you receive notebook content and an error:
1. Analyze the error traceback carefully
2. Identify the root cause of the problem
3. Explain the error in clear, concise terms
4. Provide a corrected code cell
5. Add comments to explain what was wrong and how you fixed it

Important guidelines:
- Use the available Jupyter MCP tools to insert corrected code cells
- Execute the corrected code to verify it works
- Ensure updates to cell indexing when new cells are inserted
- Maintain the logical flow of execution by adjusting cell index as needed
- Be concise but thorough in your explanations

Available tools through MCP:
- notebook tools for inserting/modifying cells
- kernel tools for executing code
- file system tools if needed

Your response should:
1. Briefly explain what caused the error
2. Insert a corrected code cell at the appropriate location
3. Execute it to verify the fix works

IMPORTANT: When you have completed the fix successfully, provide a final text response summarizing what you did WITHOUT making any more tool calls. This signals completion and allows the program to exit properly."""


class ExplainErrorAgentDeps:
    """Dependencies for the explain error agent."""
    
    def __init__(
        self,
        notebook_content: str = "",
        error_info: dict[str, Any] | None = None,
        error_cell_index: int = -1,
    ):
        """Initialize dependencies.
        
        Args:
            notebook_content: Content of notebook cells leading up to error
            error_info: Information about the error (traceback, cell content, etc.)
            error_cell_index: Index of the cell where error occurred
        """
        self.notebook_content = notebook_content
        self.error_info = error_info or {}
        self.error_cell_index = error_cell_index


def create_explain_error_agent(
    model: str,
    mcp_server: MCPServerStreamableHTTP,
    notebook_content: str = "",
    error_info: dict[str, Any] | None = None,
    error_cell_index: int = -1,
    max_tool_calls: int = 10,
) -> Agent[ExplainErrorAgentDeps, str]:
    """
    Create the Explain Error Agent for analyzing and fixing errors.
    
    Args:
        model: Model identifier (e.g., 'anthropic:claude-sonnet-4-0', 'openai:gpt-4o')
        mcp_server: MCP server connection to jupyter-mcp-server
        notebook_content: Content of notebook cells leading up to the error
        error_info: Information about the error
        error_cell_index: Index of the cell where error occurred
        max_tool_calls: Maximum number of tool calls to make (default: 10)
    
    Returns:
        Configured Pydantic AI agent
    """
    # Enhance system prompt with notebook and error context
    system_prompt = SYSTEM_PROMPT
    
    if notebook_content:
        system_prompt += f"\n\nNotebook content (cells leading to error):\n{notebook_content}"
    
    if error_cell_index != -1:
        system_prompt += f"\n\nError occurred at cell index: {error_cell_index}"
    
    # Add reminder to be efficient and complete properly
    system_prompt += (
        "\n\nBe efficient: Fix the error in as few steps as possible. "
        "When the fix is complete, provide a final summary WITHOUT tool calls to signal completion."
    )
    
    # Create agent with MCP toolset
    agent = Agent(
        model,
        toolsets=[mcp_server],
        deps_type=ExplainErrorAgentDeps,
        system_prompt=system_prompt,
    )
    
    logger.info(f"Created explain error agent with model {model} (max_tool_calls={max_tool_calls})")
    
    return agent


async def run_explain_error_agent(
    agent: Agent[ExplainErrorAgentDeps, str],
    error_description: str,
    notebook_content: str = "",
    error_info: dict[str, Any] | None = None,
    error_cell_index: int = -1,
    notebook_path: str = "",
    max_tool_calls: int = 10,
    max_requests: int = 3,
) -> str:
    """
    Run the explain error agent to analyze and fix an error.
    
    Args:
        agent: The configured explain error agent
        error_description: Description of the error (traceback, message, etc.)
        notebook_content: Content of notebook cells
        error_info: Additional error information
        error_cell_index: Index where error occurred
        notebook_path: Path to the notebook file
        max_tool_calls: Maximum number of tool calls to prevent excessive API usage
        max_requests: Maximum number of API requests (default: 3)
    
    Returns:
        Agent's response with explanation and fix
    """
    import asyncio
    import os
    from pydantic_ai import UsageLimitExceeded, UsageLimits
    
    deps = ExplainErrorAgentDeps(
        notebook_content=notebook_content,
        error_info=error_info,
        error_cell_index=error_cell_index,
    )
    
    logger.info(f"Running explain error agent for error: {error_description[:50]}... (max_tool_calls={max_tool_calls}, max_requests={max_requests})")
    
    # Prepend notebook connection instruction if path is provided
    if notebook_path:
        notebook_name = os.path.splitext(os.path.basename(notebook_path))[0]
        
        # Prepend instruction to connect to the notebook first
        enhanced_description = (
            f"First, use the use_notebook tool to connect to the notebook at path '{notebook_path}' "
            f"with notebook_name '{notebook_name}' and mode 'connect'. "
            f"Then, analyze and fix this error: {error_description}"
        )
        logger.info(f"Enhanced input to connect to notebook: {notebook_path}")
    else:
        enhanced_description = error_description
    
    try:
        # Create usage limits to prevent excessive API calls
        # Use strict limits: fewer requests to avoid rate limiting
        usage_limits = UsageLimits(
            tool_calls_limit=max_tool_calls,
            request_limit=max_requests,  # Strict limit to avoid rate limiting
        )
        
        # Add timeout to prevent hanging on retries
        result = await asyncio.wait_for(
            agent.run(enhanced_description, deps=deps, usage_limits=usage_limits),
            timeout=120.0  # 2 minute timeout
        )
        logger.info("Explain error agent completed successfully")
        return result.response
    except asyncio.TimeoutError:
        logger.error("Explain error agent timed out after 120 seconds")
        return "Error: Operation timed out. The agent may have hit rate limits or is taking too long."
    except UsageLimitExceeded as e:
        logger.error(f"Explain error agent hit usage limits: {e}")
        return (
            "Error: Reached the configured usage limits.\n"
            f"Increase --max-requests (currently {max_requests}) or --max-tool-calls (currently {max_tool_calls}) "
            "if your model provider allows more usage."
        )
    except UsageLimitExceeded as e:
        logger.error(f"Explain error agent hit usage limits: {e}")
        return (
            "Error: Reached the configured usage limits.\n"
            f"Increase --max-requests (currently {max_requests}) or --max-tool-calls (currently {max_tool_calls}) "
            "if your model provider allows more usage."
        )
    except Exception as e:
        logger.error(f"Error running explain error agent: {e}", exc_info=True)
        return f"Error: {str(e)}"


def create_explain_error_agent_sync(
    base_url: str,
    token: str,
    model: str,
    notebook_content: str = "",
    error_info: dict[str, Any] | None = None,
    error_cell_index: int = -1,
) -> Agent[ExplainErrorAgentDeps, str]:
    """
    Create explain error agent with MCP server connection (synchronous wrapper).
    
    Args:
        base_url: Jupyter server base URL
        token: Authentication token
        model: Model identifier
        notebook_content: Notebook content
        error_info: Error information
        error_cell_index: Error cell index
    
    Returns:
        Configured agent
    """
    mcp_server = create_mcp_server(base_url, token)
    return create_explain_error_agent(
        model, mcp_server, notebook_content, error_info, error_cell_index
    )
