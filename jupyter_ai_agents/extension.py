# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

# Copyright (c) 2023-2024 Datalayer, Inc.
#
# Datalayer License

"""The Jupyter AI Agents Server application."""

import os

from traitlets import default, CInt, Instance, Unicode
from traitlets.config import Configurable

from jupyter_server.utils import url_path_join
from jupyter_server.extension.application import ExtensionApp, ExtensionAppJinjaMixin

from jupyter_ai_agents.handlers.index import IndexHandler
from jupyter_ai_agents.handlers.config import ConfigHandler
from jupyter_ai_agents.handlers.nbmodel import AINbModelAgentsHandler, AINbModelAgentsInstanceHandler
from jupyter_ai_agents.handlers.chat import ChatHandler
from jupyter_ai_agents.handlers.configure import ConfigureHandler
from jupyter_ai_agents.handlers.mcp import (
    MCPServersHandler,
    MCPServerHandler,
)
from jupyter_ai_agents.agents.pydantic.mcp import MCPToolManager
from jupyter_ai_agents.agents.pydantic.chat.config import ChatConfig
from jupyter_ai_agents.agents.pydantic.chat.agent import create_chat_agent
from jupyter_ai_agents.tools import create_mcp_server
from jupyter_ai_agents.__version__ import __version__


DEFAULT_STATIC_FILES_PATH = os.path.join(os.path.dirname(__file__), "./static")

DEFAULT_TEMPLATE_FILES_PATH = os.path.join(os.path.dirname(__file__), "./templates")


class JupyterAIAgentsExtensionApp(ExtensionAppJinjaMixin, ExtensionApp):
    """The Jupyter AI Agents Server extension."""

    name = "jupyter_ai_agents"

    description = "AI Agents for JupyterLab with MCP support"

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
        """Initialize extension settings."""

        self.log.info("Initializing Jupyter AI Agents extension...")
        
        # Initialize cleanup tracking
        self._http_client = None
        self._mcp_server = None
        self._agent = None
        
        try:
            # Create configuration manager
            config = ChatConfig()
            
            # Get Jupyter server connection details
            base_url = self.serverapp.connection_url
            token = self.serverapp.token
            self.log.info(f"Jupyter server URL: {base_url}")
            
            # Create MCP server connection to jupyter-mcp-server
            self.log.info("Creating MCP server connection to jupyter-mcp-server...")
            mcp_server, http_client = create_mcp_server(base_url, token)
            self._mcp_server = mcp_server
            self._http_client = http_client  # Keep reference for cleanup
            self.log.info("MCP server connection created")
            
            # Create chat agent with MCP server toolset
            default_model = config.get_default_model()
            self.log.info(f"Creating chat agent with model: {default_model}")
            agent = create_chat_agent(model=default_model, mcp_server=mcp_server)
            self._agent = agent  # Keep reference for cleanup
            self.log.info("Chat agent created with MCP tools")
            
            # Create MCP tool manager for additional MCP servers
            mcp_manager = MCPToolManager()
            
            # Load additional MCP servers from configuration
            saved_servers = config.load_mcp_servers()
            for server in saved_servers:
                self.log.info(f"Loading additional MCP server: {server.name} ({server.url})")
                mcp_manager.add_server(server)
            
            # Register additional MCP tools with agent
            mcp_manager.register_with_agent(agent)
            
            # Store in settings for handlers to access
            self.settings['chat_agent'] = agent
            self.settings['mcp_manager'] = mcp_manager
            self.settings['chat_config'] = config
            self.settings['jupyter_mcp_server'] = mcp_server
            
            self.log.info("Jupyter AI Agents extension initialized successfully")
            
        except Exception as e:
            self.log.error(f"Error initializing Jupyter AI Agents: {e}", exc_info=True)
            raise

        self.settings.update({"disable_check_xsrf": True})

        self.log.debug("Jupyter AI Agents Config {}".format(self.config))


    def initialize_templates(self):
        self.serverapp.jinja_template_vars.update({"jupyter_ai_agents_version" : __version__})


    def initialize_handlers(self):
        """Register HTTP handlers."""

        self.log.info("Registering Jupyter AI Agents handlers...")
        self.log.info("Jupyter AI Agents Config {}".format(self.settings['jupyter_ai_agents_jinja2_env']))
        
        # Use relative paths - they will be joined with base_url in _load_jupyter_server_extension
        handlers = [
            (url_path_join(self.name), IndexHandler),
            (url_path_join(self.name, "config"), ConfigHandler),
            (url_path_join(self.name, "configure"), ConfigureHandler),
            (url_path_join(self.name, "agents"), AINbModelAgentsHandler),
            (url_path_join(self.name, r"agents/(.+)$"), AINbModelAgentsInstanceHandler),
            (url_path_join("api", "chat"), ChatHandler),
            (url_path_join("api", "mcp/servers"), MCPServersHandler),
            (url_path_join("api", r"mcp/servers/([^/]+)"), MCPServerHandler),
        ]
        self.handlers.extend(handlers)

        self.log.info(f"Registered {len(handlers)} HTTP handlers")

    
    def stop_extension(self):
        """Clean up resources when extension is stopped."""
        import asyncio
        
        self.log.info("Stopping Jupyter AI Agents extension...")
        
        # Close MCP manager clients first
        mcp_manager = self.settings.get('mcp_manager')
        if mcp_manager:
            self.log.info("Closing MCP manager clients...")
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(mcp_manager.close_all())
                else:
                    asyncio.run(mcp_manager.close_all())
                self.log.info("MCP manager clients closed successfully")
            except RuntimeError as e:
                self.log.warning(f"Could not close MCP manager clients: {e}")
            except Exception as e:
                self.log.error(f"Error closing MCP manager clients: {e}", exc_info=True)
        
        # Close the HTTP client to free connections
        if self._http_client:
            self.log.info("Closing HTTP client connections...")
            try:
                # Try to close using existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule cleanup as a task
                    loop.create_task(self._http_client.aclose())
                else:
                    # Run in new event loop
                    asyncio.run(self._http_client.aclose())
                self.log.info("HTTP client closed successfully")
            except RuntimeError as e:
                # Event loop may be closed already
                self.log.warning(f"Could not close HTTP client: {e}")
            except Exception as e:
                self.log.error(f"Error closing HTTP client: {e}", exc_info=True)
        
        self.log.info("Jupyter AI Agents extension stopped")


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

main = launch_new_instance = JupyterAIAgentsExtensionApp.launch_instance
