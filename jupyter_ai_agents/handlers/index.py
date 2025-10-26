# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

# Copyright (c) 2023-2024 Datalayer, Inc.
#
# Datalayer License

"""Index handler."""

import tornado

from jupyter_ai_agents.handlers.base import BaseTemplateHandler


class IndexHandler(BaseTemplateHandler):
    """The handler for the index."""

    @tornado.web.authenticated
    def get(self):
        """The index page."""
        self.write(self.render_template("index.html"))
