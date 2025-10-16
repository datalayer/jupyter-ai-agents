"""Pydantic AI agent for JupyterLab chat."""

from typing import Any
from pydantic_ai import Agent


def create_chat_agent(model: str = "anthropic:claude-sonnet-4.0") -> Agent:
    """
    Create the main chat agent for JupyterLab.
    
    Args:
        model: The model identifier to use (default: Claude Sonnet 4.0)
    
    Returns:
        Configured Pydantic AI agent
    """
    agent = Agent(
        model,
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
    
    # Register built-in Jupyter tools
    register_jupyter_tools(agent)
    
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
