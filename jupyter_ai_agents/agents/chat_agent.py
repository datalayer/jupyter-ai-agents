# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""AI agent for Jupyter AI Agents chat."""

from pydantic_ai import Agent

from jupyter_ai_agents.utils import create_model_with_provider


def create_chat_agent(
    model: str | None = None,
    model_provider: str = "anthropic",
    model_name: str = "claude-sonnet-4-5",
    timeout: float = 60.0,
) -> Agent | None:
    """
    Create the main chat agent for Jupyter AI Agents.

    Args:
        model: Optional full model string (e.g., "openai:gpt-4o", "azure-openai:gpt-4o-mini").
               If not provided, uses model_provider and model_name.
        model_provider: Model provider name (default: "anthropic")
        model_name: Model/deployment name (default: "claude-sonnet-4-5")
        timeout: HTTP timeout in seconds for API requests (default: 60.0)

    Returns:
        Configured Pydantic AI agent, or None if creation fails (e.g., missing API keys)

    Note:
        For Azure OpenAI, requires these environment variables:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT (base URL only, e.g., https://your-resource.openai.azure.com)
        - AZURE_OPENAI_API_VERSION (optional, defaults to latest)
    """
    try:
        # Determine model to use
        if model:
            # User provided full model string
            if model.startswith("azure-openai:"):
                # Special handling for Azure OpenAI format
                deployment_name = model.split(":", 1)[1]
                model_obj = create_model_with_provider(
                    "azure-openai", deployment_name, timeout
                )
            else:
                model_obj = model
        else:
            # Create model object with provider-specific configuration
            model_obj = create_model_with_provider(model_provider, model_name, timeout)
    except Exception:
        # Failed to create model (likely missing API keys)
        return None

    try:
        agent = Agent(
            model_obj,
            instructions="""You are a helpful AI assistant integrated into JupyterLab.

You can help users with:
- Writing and debugging Python code
- Data analysis and visualization
- Understanding Jupyter notebooks
- General programming questions
- Scientific computing tasks

Always be clear, concise, and provide working code examples when appropriate.""",
        )

        return agent
    except Exception:
        return None
