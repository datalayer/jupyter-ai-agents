# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

from jupyter_kernel_client import KonsoleApp

from .__version__ import __version__


# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

_examples = """
# Start a console connected to a local Jupyter Server running at http://localhost:8888 with a new python kernel.
jupyter-ai-agent --token <server_token>

# Start a console connected to a distant Jupyter Server with a new python kernel.
jupyter-ai-agent --url https://my.jupyter-server.xzy --token <server_token>
"""

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class AIAgentConsoleApp(KonsoleApp):
    """Start a terminal frontend to a kernel."""

    name = "jupyter-ai-agent"
    version = __version__

    description = """
        The Jupyter AI Agent terminal-based Console.

        This launches a Console application inside a terminal.

        By default it will connect to a local Jupyter Server running at http://localhost:8888
        and will create a new python kernel.

        The Console supports various extra features beyond the traditional
        single-process Terminal IPython shell, such as connecting to an
        existing jupyter kernel, via:

            jupyter-ai-agent --token <server token> --existing <kernel_id>

        where the previous session could have been created by another jupyter
        console, or by opening a notebook.
    """
    examples = _examples


main = launch_new_instance = AIAgentConsoleApp.launch_instance


if __name__ == "__main__":
    main()
