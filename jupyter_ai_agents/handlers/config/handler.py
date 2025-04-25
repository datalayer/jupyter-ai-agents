# Copyright (c) 2023-2024 Datalayer, Inc.
#
# Datalayer License

"""Config handler."""

import json

import tornado

from jupyter_server.base.handlers import APIHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin

from jupyter_ai_agents.__version__ import __version__


class ConfigHandler(ExtensionHandlerMixin, APIHandler):
    """The handler for configurations."""

    @tornado.web.authenticated
    def get(self):
        """Returns the configuration of the server extensions."""
        res = json.dumps({
            "extension": self.name,
            "version": __version__,
            "configuration": {
                "launcher": self.config["launcher"].to_dict()
            }
        })
        self.finish(res)
