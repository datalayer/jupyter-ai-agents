# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from langchain.agents import tool
from langchain.agents import AgentExecutor

from jupyter_nbmodel_client import NbModelClient
from jupyter_kernel_client import KernelClient

from jupyter_ai_agent.providers.azure_openai import create_azure_open_ai_agent
from jupyter_ai_agent.tools import add_code_cell_tool, add_markdown_cell_tool
from jupyter_ai_agent.utils import retrieve_cells_content_until_first_error

SYSTEM_PROMPT = """You are a powerful coding assistant.
Create and execute code in a notebook based on user instructions.
Add markdown cells to explain the code and structure the notebook clearly.
Assume that no packages are installed in the notebook, so install them using !pip install."""

def prompt(notebook: NbModelClient, kernel: KernelClient, input: str, azure_deployment_name: str, full_context: bool) -> list:
    """From a given instruction, code and markdown cells are added to a notebook."""

    @tool
    def add_code_cell(cell_content: str) -> None:
        """Add a Python code cell with a content to the notebook and execute it."""
        return add_code_cell_tool(notebook, kernel, cell_content)
            
    @tool
    def add_markdown_cell(cell_content: str) -> None:
        """Add a Markdown cell with a content to the notebook."""
        return add_markdown_cell_tool(notebook, cell_content)
    

    tools = [add_code_cell, add_markdown_cell]
    
    if full_context:
        SYSTEM_PROMP_FINAL = f"""
        {SYSTEM_PROMPT}
        
        Notebook content: {retrieve_cells_content_until_first_error(notebook)[0]}
        """         
    else:
        SYSTEM_PROMP_FINAL = SYSTEM_PROMPT
        
    agent = create_azure_open_ai_agent(azure_deployment_name, SYSTEM_PROMP_FINAL, tools)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return list(agent_executor.stream({"input": input}))
