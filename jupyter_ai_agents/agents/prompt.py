# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from langchain.agents import tool

from jupyter_nbmodel_client import NbModelClient
from jupyter_kernel_client import KernelClient

from jupyter_ai_agents.agents.utils import create_ai_agent
from jupyter_ai_agents.tools import insert_execute_code_cell_tool, insert_markdown_cell_tool
from jupyter_ai_agents.utils import retrieve_cells_content

SYSTEM_PROMPT = """You are a powerful coding assistant.
Create and execute code in a notebook based on user instructions.
Add markdown cells to explain the code and structure the notebook clearly.
Assume that no packages are installed in the notebook, so install them using !pip install.
Ensure updates to cell indexing when new cells are inserted. Maintain the logical flow of execution by adjusting cell index as needed.
"""

def prompt(notebook: NbModelClient, kernel: KernelClient, input: str, model_provider: str, model_name: str, full_context: bool, current_cell_index: int) -> list:
    """From a given instruction, code and markdown cells are added to a notebook."""

    @tool
    def insert_execute_code_cell(cell_index: int, cell_content: str) -> str:
        """Add a Python code cell to the notebook at the given index with a content and execute it."""
        insert_execute_code_cell_tool(notebook, kernel, cell_content, cell_index)
        return "Code cell added and executed."
            
    @tool
    def insert_markdown_cell(cell_index: int, cell_content: str) -> str:
        """Add a Markdown cell to the notebook at the given index with a content."""
        insert_markdown_cell_tool(notebook, cell_content, cell_index)
        return "Markdown cell added."
    
    tools = [insert_execute_code_cell, insert_markdown_cell]
    
    if full_context:
        system_prompt_enriched = f"""
        {SYSTEM_PROMPT}
        
        Notebook content: {retrieve_cells_content(notebook)}
        """   
    else:
        system_prompt_enriched = SYSTEM_PROMPT
        
    if current_cell_index != -1:
        system_prompt_final = f"""
        {system_prompt_enriched}
        
        Cell index on which the user instruction was given: {current_cell_index}
        """
    else:
        system_prompt_final = system_prompt_enriched
        
    agent = create_ai_agent(model_provider, model_name, system_prompt_final, tools)

    return list(agent.stream({"input": input}))
