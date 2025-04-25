# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Jupyter AI Agents."""

from typing import Any, Dict, List

from jupyter_ai_agents.__version__ import __version__
from jupyter_ai_agents.serverapplication import JupyterAIAgentsExtensionApp


__all__ = []


def _jupyter_server_extension_points() -> List[Dict[str, Any]]:
    return [{
        "module": "jupyter_ai_agents",
        "app": JupyterAIAgentsExtensionApp,
    }]
