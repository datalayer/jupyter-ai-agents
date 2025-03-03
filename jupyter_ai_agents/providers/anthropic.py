# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from typing import List, Any, Dict
from langchain.agents.agent import AgentExecutor
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.tool_calling_agent.base import create_tool_calling_agent
from langchain_core.tools import BaseTool

def create_anthropic_agent(model_name: str, system_prompt: str, tools: List[BaseTool]) -> AgentExecutor:
    """Create an agent from a set of tools using Anthropic's Claude API.
    
    Args:
        model_name: The name of the Claude model to use (e.g., "claude-3-haiku-20240307")
        system_prompt: The system prompt to use for the agent
        tools: A list of tools for the agent to use
        
    Returns:
        An agent executor that can use tools via Claude
    """

    # Create the Anthropic LLM
    llm = ChatAnthropic(model=model_name)

    # Create a prompt template for the agent with enhanced instructions
    enhanced_system_prompt = f"""
{system_prompt}

When you use tools, please include the results in your response to the user.
Be sure to always provide a text response, even if it's just to acknowledge the tool's output.
After using a tool, explain what the result means in a clear and helpful way.
"""

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(
    [
        ("system", enhanced_system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create a tool-calling agent
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Create an agent executor with output parsing
    agent_executor = AgentExecutor(
        name="AnthropicToolAgent", 
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True,
        return_intermediate_steps=True  # Include intermediate steps in the output
    )
    
    return agent_executor 