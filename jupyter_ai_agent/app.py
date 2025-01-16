# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import warnings
import logging

from traitlets import CBool
from traitlets.config import boolean_flag

from jupyter_ai_agent.base import JupyterAIAgentAskApp, base_flags
from jupyter_ai_agent.agents.prompt import prompt
from jupyter_ai_agent.agents.explain_error import explain_error


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


prompt_flags = dict(base_flags)
prompt_flags.update(
    boolean_flag(
        "full-context",
        "PromptAgentApp.full_context",
    )
)
    
class PromptAgentApp(JupyterAIAgentAskApp):
    """From a given instruction, code and markdown cells are added to a notebook."""

    name = "jupyter-ai-agent-prompt"

    description = """
      An application to ask the agent
    """

    flags = prompt_flags

    full_context = CBool(
        False,
        config=True,
        help="Fag to provide the full notebook context i.e. notebook content to the AI model.",
    )

    def initialize(self, *args, **kwargs):
        """Initialize the app."""
        super(PromptAgentApp, self).initialize(*args, **kwargs)

    def ask(self):
        reply = prompt(self.notebook, self.kernel, super().input, super().azure_ai_deployment_name, self.full_context, self.current_cell_index)
        logger.debug("Reply", reply)

    def start(self):
        """Start the app."""
        if len(self.extra_args) > 1:  # pragma: no cover
            warnings.warn("Too many arguments were provided for workspace export.")
            self.exit(1)
        super(PromptAgentApp, self).start()
        self.exit(0)


class ExplainErrorAgentApp(JupyterAIAgentAskApp):

    name = "jupyter-ai-agent-explain-error"

    description = """
      An application to explain an error
    """

    def initialize(self, *args, **kwargs):
        """Initialize the app."""
        super(ExplainErrorAgentApp, self).initialize(*args, **kwargs)

    def ask(self):
        reply = explain_error(self.notebook, self.kernel, super().azure_ai_deployment_name, self.current_cell_index)
        logger.debug("Reply", reply)

    def start(self):
        """Start the app."""
        if len(self.extra_args) > 1:  # pragma: no cover
            warnings.warn("Too many arguments were provided for workspace export.")
            self.exit(1)
        super(ExplainErrorAgentApp, self).start()
        self.exit(0)


class JupyterAIAgentApp(JupyterAIAgentAskApp):
    name = "jupyter-ai-agent"

    description = """
      The Jupyter AI Agent application.
    """

    subcommands = {
        "prompt": (PromptAgentApp, PromptAgentApp.description.splitlines()[0]),
        "explain-error": (ExplainErrorAgentApp, ExplainErrorAgentApp.description.splitlines()[0]),
    }

    def initialize(self, argv=None):
        """Subclass because the ExtensionApp.initialize() method does not take arguments."""
        super(JupyterAIAgentApp, self).initialize()

    def start(self):
        super(JupyterAIAgentApp, self).start()
        self.log.info("Jupyter AI Agent [%s] ", self.version)


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

main = launch_new_instance = JupyterAIAgentApp.launch_instance

if __name__ == "__main__":
    main()
