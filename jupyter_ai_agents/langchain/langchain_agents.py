# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from langchain.agents import AgentExecutor

from jupyter_ai_agents.langchain.anthropic import create_anthropic_langchain_agent
from jupyter_ai_agents.langchain.azure_openai import create_azure_openai_langchain_agent
from jupyter_ai_agents.langchain.github_copilot import create_github_copilot_langchain_agent
from jupyter_ai_agents.langchain.bedrock import create_bedrock_langchain_agent
from jupyter_ai_agents.langchain.openai import create_openai_langchain_agent


def create_langchain_agent(
    model_provider: str, model_name: str, system_prompt_final: str, tools: list
) -> AgentExecutor:
    """Create an AI Agent based on the model provider."""
    if model_provider == "azure-openai":
        langchain_agent = create_azure_openai_langchain_agent(model_name, system_prompt_final, tools)
    elif model_provider == "github-copilot":
        langchain_agent = create_github_copilot_langchain_agent(model_name, system_prompt_final, tools)
    elif model_provider == "openai":
        langchain_agent = create_openai_langchain_agent(model_name, system_prompt_final, tools)
    elif model_provider == "anthropic":
        langchain_agent = create_anthropic_langchain_agent(model_name, system_prompt_final, tools)
    elif model_provider == "bedrock":
        langchain_agent = create_bedrock_langchain_agent(model_name, system_prompt_final, tools)
    else:
        raise ValueError(f"Model provider {model_provider} is not supported.")
    return langchain_agent
