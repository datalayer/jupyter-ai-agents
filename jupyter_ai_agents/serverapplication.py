# Copyright (c) 2023-2024 Datalayer, Inc.
#
# Datalayer License

"""The Jupyter AI Agents Server application."""

import os

from traitlets import default, CInt, Instance, Unicode
from traitlets.config import Configurable

from jupyter_server.utils import url_path_join
from jupyter_server.extension.application import ExtensionApp, ExtensionAppJinjaMixin

from jupyter_ai_agents.__version__ import __version__

from jupyter_ai_agents.handlers.index.handler import IndexHandler
from jupyter_ai_agents.handlers.config.handler import ConfigHandler
from jupyter_ai_agents.handlers.agents.handler import AIAgentsHandler, AIAgentsInstanceHandler


DEFAULT_STATIC_FILES_PATH = os.path.join(os.path.dirname(__file__), "./static")

DEFAULT_TEMPLATE_FILES_PATH = os.path.join(os.path.dirname(__file__), "./templates")


class JupyterAIAgentsExtensionApp(ExtensionAppJinjaMixin, ExtensionApp):
    """The Jupyter AI Agents Server extension."""

    name = "jupyter_ai_agents"

    extension_url = "/jupyter_ai_agents"

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
        self.settings.update({"disable_check_xsrf": True})
        self.log.debug("Jupyter AI Agents Config {}".format(self.config))


    def initialize_templates(self):
        self.serverapp.jinja_template_vars.update({"jupyter_ai_agents_version" : __version__})


    def initialize_handlers(self):
        self.log.debug("Jupyter AI Agents Config {}".format(self.settings['jupyter_ai_agents_jinja2_env']))
        handlers = [
            ("jupyter_ai_agents", IndexHandler),
            (url_path_join(self.name, "config"), ConfigHandler),
            (url_path_join(self.name, "agents"), AIAgentsHandler),
            (url_path_join(self.name, r"agents/(.+)$"), AIAgentsInstanceHandler),
        ]
        self.handlers.extend(handlers)


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

main = launch_new_instance = JupyterAIAgentsExtensionApp.launch_instance
