# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

# Copyright (c) 2023-2024 Datalayer, Inc.
#
# Datalayer License

"""Base handler."""

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin, ExtensionHandlerJinjaMixin


class BaseTemplateHandler(ExtensionHandlerJinjaMixin, ExtensionHandlerMixin, JupyterHandler):
    """The Base handler for the templates."""
