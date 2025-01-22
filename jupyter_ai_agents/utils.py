# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

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