# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

import re

from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import NbModelClient


def retrieve_cells_content(notebook: NbModelClient, cell_index_stop: int=-1) -> list:
    """Retrieve the content of the cells."""
    cells_content = []
    ydoc = notebook._doc
    
    for index, cell in enumerate(ydoc._ycells):
        if cell_index_stop != -1 and index == cell_index_stop:
            break
        cells_content.append((index, cell["cell_type"], str(cell["source"])))

    return cells_content


def retrieve_cells_content_error(notebook: NbModelClient, cell_index_stop) -> list:
    """Retrieve the content of the cells until the error."""
    cells_content = []
    error = ()
    ydoc = notebook._doc
    
    for index, cell in enumerate(ydoc._ycells):
        error_flag = ("outputs" in cell.keys() and len(cell["outputs"]) > 0 and cell["outputs"][0]['output_type'] == "error")
        if index == cell_index_stop and error_flag:
            error = (
                index,
                cell["cell_type"],  # Cell type
                str(cell["source"]),  # Cell content
                cell["outputs"][0]['traceback']  # Traceback
            )
            break
        cells_content.append((index, cell["cell_type"], str(cell["source"])))
        
    return cells_content, error


def retrieve_cells_content_until_first_error(notebook: NbModelClient) -> tuple:
    """Retrieve the content of the cells until the first error."""
    cells_content = []
    error = ()
    ydoc = notebook._doc
    
    for index, cell in enumerate(ydoc._ycells):
        if "outputs" in cell.keys() and len(cell["outputs"]) > 0 and cell["outputs"][0]['output_type'] == "error":
            error = (
                index,
                cell["cell_type"],  # Cell type
                str(cell["source"]),  # Cell content
                cell["outputs"][0]['traceback']  # Traceback
            )
            break
        cells_content.append((index, cell["cell_type"], str(cell["source"])))
        
    return cells_content, error


def add_markdown_cell_tool(notebook: NbModelClient, cell_content: str) -> None:
    """Add a Markdown cell with a content to the notebook."""
    notebook.add_markdown_cell(cell_content)


def insert_markdown_cell_tool(notebook: NbModelClient, cell_content: str, cell_index:int) -> None:
    """Insert a Markdown cell with a content at a specific index in the notebook."""
    notebook.insert_markdown_cell(cell_index, cell_content)


def add_execute_code_cell_tool(notebook: NbModelClient, kernel: KernelClient, cell_content: str) -> None:
    """Add a Python code cell with a content to the notebook and execute it."""
    cell_index = notebook.add_code_cell(cell_content)
    results = notebook.execute_cell(cell_index, kernel)
    assert results["status"] == "ok"


def insert_execute_code_cell_tool(notebook: NbModelClient, kernel: KernelClient | None, cell_content: str, cell_index:int) -> None:
    """Insert a Python code cell with a content at a specific index in the notebook and execute it."""
    notebook.insert_code_cell(cell_index, cell_content)
    if kernel is not None:
        results = notebook.execute_cell(cell_index, kernel)
        assert results["status"] == "ok"


def http_to_ws(s: str):
    return re.sub("^http", "ws", s)
