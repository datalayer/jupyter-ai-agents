# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Pydantic AI agent for JupyterLab chat."""

from typing import Any

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

from jupyter_ai_agents.utils.model import create_model_with_provider


def create_chat_agent(
    model: str | None = None,
    model_provider: str = "anthropic",
    model_name: str = "claude-sonnet-4-5",
    timeout: float = 60.0,
    mcp_server: MCPServerStreamableHTTP | None = None,
) -> Agent:
    """
    Create the main chat agent for JupyterLab.
    
    Args:
        model: Optional full model string (e.g., "openai:gpt-4o", "azure-openai:gpt-4o-mini").
               If not provided, uses model_provider and model_name.
        model_provider: Model provider name (default: "anthropic")
        model_name: Model/deployment name (default: "claude-sonnet-4-5")
        timeout: HTTP timeout in seconds for API requests (default: 60.0)
        mcp_server: Optional MCP server connection for Jupyter tools
    
    Returns:
        Configured Pydantic AI agent
        
    Note:
        For Azure OpenAI, requires these environment variables:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT (base URL only, e.g., https://your-resource.openai.azure.com)
        - AZURE_OPENAI_API_VERSION (optional, defaults to latest)
    """
    # Determine model to use
    if model:
        # User provided full model string
        if model.startswith('azure-openai:'):
            # Special handling for Azure OpenAI format
            deployment_name = model.split(':', 1)[1]
            model_obj = create_model_with_provider('azure-openai', deployment_name, timeout)
        else:
            model_obj = model
    else:
        # Create model object with provider-specific configuration
        model_obj = create_model_with_provider(model_provider, model_name, timeout)
    
    # Create toolsets list
    toolsets = []
    if mcp_server:
        toolsets.append(mcp_server)
    
    agent = Agent(
        model_obj,
        toolsets=toolsets,
        instructions="""You are a helpful AI assistant integrated into JupyterLab.
        
You can help users with:
- Writing and debugging Python code
- Data analysis and visualization
- Understanding Jupyter notebooks
- General programming questions
- Scientific computing tasks

You have access to various tools to interact with the Jupyter environment.
When users ask you to execute code or work with notebooks, use the available tools.

Always be clear, concise, and provide working code examples when appropriate.""",
    )
    
    # Note: Built-in Jupyter tools are now provided via MCP server
    # No need to register them manually
    
    return agent


def register_jupyter_tools(agent: Agent):
    """
    Register Jupyter-specific tools with the agent.
    
    Args:
        agent: The Pydantic AI agent to register tools with
    """
    
    @agent.tool_plain
    def execute_python_code(code: str) -> str:
        """
        Execute Python code in the active notebook kernel.
        
        This tool allows executing Python code and getting back the result.
        Use this when the user asks you to run code or needs to see output.
        
        Args:
            code: Python code to execute
        
        Returns:
            Execution result as string
        """
        # TODO: Implement kernel execution via Jupyter services
        # For now, return placeholder
        return f"Code execution not yet implemented. Would execute:\n{code}"
    
    @agent.tool_plain
    def read_notebook_file(path: str) -> str:
        """
        Read a Jupyter notebook file and return its contents.
        
        Args:
            path: Path to the notebook file
        
        Returns:
            Notebook contents as formatted text
        """
        # TODO: Implement notebook reading
        return f"Notebook reading not yet implemented. Would read: {path}"
    
    @agent.tool_plain
    def list_workspace_files(directory: str = ".") -> list[str]:
        """
        List files in the workspace directory.
        
        Args:
            directory: Directory to list (default: current directory)
        
        Returns:
            List of file names
        """
        # TODO: Implement file listing via Jupyter services
        return [f"File listing not yet implemented for: {directory}"]
    
    @agent.tool_plain
    def get_notebook_metadata() -> dict[str, Any]:
        """
        Get metadata about the currently active notebook.
        
        Returns:
            Dictionary with notebook metadata (name, path, kernel, etc.)
        """
        # TODO: Implement metadata retrieval
        return {
            "status": "not_implemented",
            "message": "Notebook metadata retrieval not yet implemented"
        }


def add_mcp_tools(agent: Agent, mcp_tools: list):
    """
    Add MCP tools to the agent dynamically.
    
    Args:
        agent: The Pydantic AI agent
        mcp_tools: List of MCP tool definitions
    """
    # TODO: Implement dynamic MCP tool registration
    pass
