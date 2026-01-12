# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""The Jupyter AI Agents Server application."""

import os
import logging

from traitlets import default, CInt, Instance, Unicode
from traitlets.config import Configurable

from jupyter_server.utils import url_path_join
from jupyter_server.extension.application import ExtensionApp, ExtensionAppJinjaMixin

from jupyter_ai_agents.handlers.index import IndexHandler
from jupyter_ai_agents.handlers.config import ConfigHandler
from jupyter_ai_agents.handlers.chat_handler import VercelAIChatHandler
from jupyter_ai_agents.agents.chat_agent import create_chat_agent
from jupyter_ai_agents.__version__ import __version__

logger = logging.getLogger(__name__)


DEFAULT_STATIC_FILES_PATH = os.path.join(os.path.dirname(__file__), "./static")

DEFAULT_TEMPLATE_FILES_PATH = os.path.join(os.path.dirname(__file__), "./templates")


class JupyterAIAgentsExtensionApp(ExtensionAppJinjaMixin, ExtensionApp):
    """The Jupyter AI Agents Server extension."""

    name = "agent_runtimes"

    description = "AI Agents for JupyterLab with MCP support"

    extension_url = "/agent_runtimes"

    load_other_extensions = True

    static_paths = [DEFAULT_STATIC_FILES_PATH]

    template_paths = [DEFAULT_TEMPLATE_FILES_PATH]

    class Launcher(Configurable):
        """Jupyter AI Agents launcher configuration"""

        def to_dict(self):
            return {
                "category": self.category,
                "name": self.name,
                "icon_svg_url": self.icon_svg_url,
                "rank": self.rank,
            }

        category = Unicode(
            "",
            config=True,
            help=("Application launcher card category."),
        )

        name = Unicode(
            "Jupyter AI Agents",
            config=True,
            help=("Application launcher card name."),
        )

        icon_svg_url = Unicode(
            None,
            allow_none=True,
            config=True,
            help=("Application launcher card icon."),
        )

        rank = CInt(
            0,
            config=True,
            help=("Application launcher card rank."),
        )

    launcher = Instance(Launcher)

    @default("launcher")
    def _default_launcher(self):
        return JupyterAIAgentsExtensionApp.Launcher(parent=self, config=self.config)


    def initialize_settings(self):
        """Initialize extension settings."""

        self.log.info("Initializing Jupyter AI Agents extension...")
        
        self.settings.update({"disable_check_xsrf": True})

        # Store server connection info for MCP server creation
        # These will be used lazily when handling chat requests
        self.settings["chat_base_url"] = self.serverapp.connection_url
        self.settings["chat_token"] = self.serverapp.token

        # Create chat agent
        try:
            self.log.info("Creating chat agent...")
            agent = create_chat_agent()
            if agent:
                self.settings["chat_agent"] = agent
                self.settings["chat_toolsets"] = []  # Can be extended with MCP servers via request parameter
                self.log.info("Chat agent created successfully")
            else:
                self.log.warning(
                    "Could not create chat agent. Please configure AI provider API keys "
                    "(e.g., ANTHROPIC_API_KEY, OPENAI_API_KEY)"
                )
        except Exception as e:
            self.log.error(f"Failed to create chat agent: {e}", exc_info=True)

        self.log.debug("Jupyter AI Agents Config {}".format(self.config))


    def initialize_templates(self):
        self.serverapp.jinja_template_vars.update({"jupyter_ai_agents_version" : __version__})


    def initialize_handlers(self):
        """Register HTTP handlers."""

        self.log.info("Registering Jupyter AI Agents handlers...")
        self.log.info("Jupyter AI Agents Config {}".format(self.settings['agent_runtimes_jinja2_env']))
        
        # Use relative paths - they will be joined with base_url in _load_jupyter_server_extension
        # These paths match the agent-runtimes requestAPI expectations:
        # - /agent_runtimes/configure - for config query (models, tools)
        # - /agent_runtimes/chat - for chat messages (Vercel AI protocol)
        handlers = [
            (url_path_join(self.name), IndexHandler),
            (url_path_join(self.name, "configure"), ConfigHandler),
            (url_path_join(self.name, "chat"), VercelAIChatHandler),
        ]
        self.handlers.extend(handlers)

        self.log.info(f"Registered {len(handlers)} HTTP handlers")


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

main = launch_new_instance = JupyterAIAgentsExtensionApp.launch_instance
