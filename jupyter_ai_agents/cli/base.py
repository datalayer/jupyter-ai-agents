# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import asyncio
import os
import logging

from dotenv import load_dotenv, find_dotenv

from traitlets import Unicode, Integer
from jupyter_core.application import JupyterApp, base_aliases, base_flags

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient 

from jupyter_ai_agents.__version__ import __version__


logger = logging.getLogger(__name__)


load_dotenv(find_dotenv())


# -----------------------------------------------------------------------------
# Flags and Aliases
# -----------------------------------------------------------------------------

jupyter_ai_agents_flags = dict(base_flags)

jupyter_ai_agents_aliases = dict(base_aliases)
jupyter_ai_agents_aliases.update(
    {
        "url": "JupyterAIAgentBaseApp.server_url",
        "token": "JupyterAIAgentBaseApp.token",
        "path": "JupyterAIAgentBaseApp.path",
        "agent": "JupyterAIAgentBaseApp.agent_name",
        "input": "JupyterAIAgentBaseApp.input",
        "model-provider": "JupyterAIAgentBaseApp.model_provider",
        "openai-api-version": "JupyterAIAgentBaseApp.openai_api_version",
        "azure-openai-version": "JupyterAIAgentBaseApp.azure_openai_version",
        "azure-openai-api-key": "JupyterAIAgentBaseApp.azure_openai_api_key",
        "openai-api-key": "JupyterAIAgentBaseApp.openai_api_key",
        "anthropic-api-key": "JupyterAIAgentBaseApp.anthropic_api_key",
        "model-name": "JupyterAIAgentBaseApp.model_name",
        "current-cell-index": "JupyterAIAgentBaseApp.current_cell_index",
    }
)


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class JupyterAIAgentBaseApp(JupyterApp):
    aliases = jupyter_ai_agents_aliases
    flags = jupyter_ai_agents_flags

    version = __version__

    server_url = Unicode(
        "http://localhost:8888",
        config=True,
        help="URL to the Jupyter Server."
    )
    token = Unicode(
        "",
        config=True,
        help="Jupyter Server token."
    )
    path = Unicode(
        "",
        config=True,
        help="Jupyter Notebook path."
    )
    agent_name = Unicode(
        "prompt",
        config=True,
        help="Agent name."
    )
    input = Unicode(
        "",
        config=True,
        help="Input."
    )
    model_provider = Unicode(
        "github-copilot",
        config=True,
        help="Model provider can be 'azure-openai', 'github-copilot', or 'openai'."
    )
    openai_api_version = Unicode(
        os.environ.get("OPENAI_API_VERSION"),
        help="""OpenAI API version.""",
        config=True,
    )
    azure_openai_version = Unicode(
        os.environ.get("AZURE_OPENAI_ENDPOINT"),
        help="""Azure OpenAI endpoint.""",
        config=True,
    )
    azure_openai_api_key = Unicode(
        os.environ.get("AZURE_OPENAI_API_KEY"),
        help="""Azure OpenAI key.""",
        config=True,
    )
    github_token = Unicode(
        os.environ.get("GITHUB_TOKEN"),
        help="""Github token.""",
        config=True,
    )
    openai_api_key = Unicode(
        os.environ.get("OPENAI_API_KEY"),
        help="""OpenAI API key.""",
        config=True,
    )
    anthropic_api_key = Unicode(
        os.environ.get("ANTHROPIC_API_KEY"),
        help="""Anthropic API key.""",
        config=True,
    )
    model_name = Unicode(
        "gpt-4o",
        help=(
            "The 'Azure AI deployment' name for 'azure-openai' model provider."
            "For 'github-copilot' model provider, gpt-4o, o1, or o3-mini (as of 2024-02-07) "
            "- check your GithubCopilot settings to make sure the model you want to use is enabled."
            "For 'openai' model provider, gpt-4o, o1, or o3-mini (as of 2024-02-07) "
            "- check the limits in your OpenAI API Dashboard to make sure the model you want to use is enabled."
            ),
        config=True,
    )
    current_cell_index = Integer(
        -1,
        config=True,
        help="Index of the cell where the prompt is asked."
    )


class JupyterAIAgentAskApp(JupyterAIAgentBaseApp):

    kernel = None
    notebook = None


    async def ask(self):
        pass


    def _start_clients(self):
        try:
            self.kernel = KernelClient(server_url=self.server_url, token=self.token)
            self.kernel.start()
            self.notebook = NbModelClient(get_jupyter_notebook_websocket_url(server_url=self.server_url, token=self.token, path=self.path))
            asyncio.get_event_loop().run_until_complete(self.notebook.start())
            asyncio.get_event_loop().run_until_complete(self.ask())
        except Exception as e:
            logger.error("Exception", e)
        finally:
            asyncio.get_event_loop().run_until_complete(self.notebook.stop())
            self.kernel.stop()


    def start(self):
        """Start the app."""
        super(JupyterAIAgentAskApp, self).start()
        self._start_clients()


class JupyterAIAgentListenApp(JupyterAIAgentBaseApp):
    pass
