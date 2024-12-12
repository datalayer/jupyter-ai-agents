# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

import logging

from langchain.agents import tool
from langchain.agents import AgentExecutor

from jupyter_ydoc import YNotebook
from jupyter_nbmodel_client import NbModelClient
from jupyter_kernel_client import KernelClient

from jupyter_ai_agent.providers.azure_openai import create_azure_open_ai_agent
from jupyter_ai_agent.tools import add_code_cell_tool, add_markdown_cell_tool
from jupyter_ai_agent.utils import retrieve_cells_content_until_first_error

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a powerful coding assistant.
Your goal is to help the user understand the coding error in a notebook and provide a correction.
You will receive the notebook content and error and you will need to add code cells with the correction and comments to explain the error in a concise way.
"""


def explain_error(notebook: NbModelClient, kernel: KernelClient, azure_deployment_name: str) -> list:
    """Explain and correct an error in a notebook based on the prior cells."""

    @tool
    def add_code_cell(cell_content: str) -> None:
        """Add a Python code cell with a content to the notebook and execute it."""
        return add_code_cell_tool(notebook, kernel, cell_content)

    tools = [add_code_cell]
    
    cells_content_until_first_error, first_error = retrieve_cells_content_until_first_error(notebook)
    
    SYSTEM_PROMPT_WITH_CONTENT = f"""
    {SYSTEM_PROMPT}
    
    Notebook content: {cells_content_until_first_error}
    """ 
    input = f"Error: {first_error}"
    
    logger.debug("Prompt with content", SYSTEM_PROMPT_WITH_CONTENT)
    logger.debug("Input", input)

    agent = create_azure_open_ai_agent(azure_deployment_name, SYSTEM_PROMPT_WITH_CONTENT, tools)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return list(agent_executor.stream({"input": input}))
