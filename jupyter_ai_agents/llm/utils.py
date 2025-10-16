# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from langchain.agents import AgentExecutor

from jupyter_ai_agents.llm.anthropic import create_anthropic_llm
from jupyter_ai_agents.llm.azure_openai import create_azure_openai_llm
from jupyter_ai_agents.llm.github_copilot import create_github_copilot_llm
from jupyter_ai_agents.llm.bedrock import create_bedrock_llm
from jupyter_ai_agents.llm.openai import create_openai_llm


def create_llm(
    model_provider: str, model_name: str, system_prompt_final: str, tools: list
) -> AgentExecutor:
    """Create an AI Agent based on the model provider."""
    if model_provider == "azure-openai":
        agent = create_azure_openai_llm(model_name, system_prompt_final, tools)
    elif model_provider == "github-copilot":
        agent = create_github_copilot_llm(model_name, system_prompt_final, tools)
    elif model_provider == "openai":
        agent = create_openai_llm(model_name, system_prompt_final, tools)
    elif model_provider == "anthropic":
        agent = create_anthropic_llm(model_name, system_prompt_final, tools)
    elif model_provider == "bedrock":
        agent = create_bedrock_llm(model_name, system_prompt_final, tools)
    else:
        raise ValueError(f"Model provider {model_provider} is not supported.")
    return agent
