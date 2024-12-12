# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from dotenv import load_dotenv, find_dotenv

from langchain.agents import tool

from jupyter_nbmodel_client import NbModelClient
from jupyter_kernel_client import KernelClient


def add_code_cell_tool(notebook: NbModelClient, kernel: KernelClient, cell_content: str) -> None:
    """Add a Python code cell with a content to the notebook and execute it."""
    cell_index = notebook.add_code_cell(cell_content)
    results = notebook.execute_cell(cell_index, kernel)
    assert results["status"] == "ok"
        

def add_markdown_cell_tool(notebook: NbModelClient, cell_content: str) -> None:
    """Add a Markdown cell with a content to the notebook."""
    notebook.add_markdown_cell(cell_content)
