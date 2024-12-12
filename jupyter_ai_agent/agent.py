# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from dotenv import load_dotenv, find_dotenv

from jupyter_nbmodel_client import NbModelClient
from jupyter_kernel_client import KernelClient

from jupyter_ai_agent.agents.prompt import prompt
from jupyter_ai_agent.agents.explain_error import explain_error


load_dotenv(find_dotenv())


def ask_agent(server_url: str, token: str, azure_deployment_name: str, notebook_path: str, agent_type: str, input: str='') -> list:
    """From a given instruction, code and markdown cells are added to a notebook."""

    kernel = KernelClient(server_url=server_url, token=token)
    kernel.start()

    notebook = NbModelClient(server_url=server_url, token=token, path=notebook_path)
    notebook.start()

    if agent_type == "prompt":
        prompt(notebook, kernel, input, azure_deployment_name)

    if agent_type == "explain_error":
        explain_error(notebook, kernel, azure_deployment_name)
