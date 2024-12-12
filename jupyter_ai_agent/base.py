# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations


import os
import logging

from dotenv import load_dotenv, find_dotenv

from traitlets import Unicode
from jupyter_core.application import JupyterApp, base_aliases, base_flags

from jupyter_nbmodel_client import NbModelClient
from jupyter_kernel_client import KernelClient

from jupyter_ai_agent.__version__ import __version__


logger = logging.getLogger(__name__)



load_dotenv(find_dotenv())


# -----------------------------------------------------------------------------
# Flags and Aliases
# -----------------------------------------------------------------------------

jupyter_ai_agent_flags = dict(base_flags)

jupyter_ai_agent_aliases = dict(base_aliases)
jupyter_ai_agent_aliases.update(
    {
        "url": "JupyterAIAgentBaseApp.server_url",
        "token": "JupyterAIAgentBaseApp.token",
        "path": "JupyterAIAgentBaseApp.path",
        "agent": "JupyterAIAgentBaseApp.agent_name",
        "input": "JupyterAIAgentBaseApp.input",
        "openai-api-version": "JupyterAIAgentBaseApp.openai_api_version",
        "azure-openai-version": "JupyterAIAgentBaseApp.azure_openai_version",
        "azure-openai-api-key": "JupyterAIAgentBaseApp.azure_openai_api_key",
        "azure-ai-deployment-name": "JupyterAIAgentBaseApp.azure_ai_deployment_name",
    }
)


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class JupyterAIAgentBaseApp(JupyterApp):
    aliases = jupyter_ai_agent_aliases
    flags = jupyter_ai_agent_flags

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
        help="Jupyter Notebok path."
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

    openai_api_version = Unicode(
        os.environ.get("OPENAI_API_VERSION"),
        help="""OpenAI version.""",
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
    azure_ai_deployment_name = Unicode(
        "",
        help="""Azure AI deployment name.""",
        config=True,
    )


class JupyterAIAgentAskApp(JupyterAIAgentBaseApp):

    kernel = None
    notebook = None

    def ask(self):
        pass

    def start(self):
        """Start the app."""
        super(JupyterAIAgentAskApp, self).start()
        try:
            self.kernel = KernelClient(server_url=self.server_url, token=self.token)
            self.kernel.start()
            self.notebook = NbModelClient(server_url=self.server_url, token=self.token, path=self.path)
            self.notebook.start()
            self.ask()
        except Exception as e:
            logger.error("Exception", e)
        finally:
            self.notebook.stop()
            self.kernel.stop()
    

class JupyterAIAgentListenApp(JupyterAIAgentBaseApp):
    pass    

