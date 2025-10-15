"""JupyterLab extension for AI Chat."""

from jupyter_server.extension.application import ExtensionApp
from jupyter_server.utils import url_path_join

from .chat.handler import (
    ChatHandler,
    ConfigureHandler,
    MCPServersHandler,
    MCPServerHandler
)
from .chat.agent import create_chat_agent
from .chat.mcp_tools import MCPToolManager
from .chat.config import ChatConfig


class AIChatExtension(ExtensionApp):
    """JupyterLab AI Chat Extension."""
    
    name = "jupyter_ai_agents"
    app_name = "Jupyter AI Agents"
    description = "AI Chat sidebar for JupyterLab with MCP support"
    
    app_version = "0.1.0"
    extension_url = "/jupyter-ai-agents"
    load_other_extensions = True
    
    def initialize_settings(self):
        """Initialize extension settings."""
        self.log.info("Initializing Jupyter AI Agents extension...")
        
        try:
            # Create configuration manager
            config = ChatConfig()
            
            # Create chat agent with default model
            default_model = config.get_default_model()
            self.log.info(f"Creating chat agent with model: {default_model}")
            agent = create_chat_agent(model=default_model)
            
            # Create MCP tool manager
            mcp_manager = MCPToolManager()
            
            # Load MCP servers from configuration
            saved_servers = config.load_mcp_servers()
            for server in saved_servers:
                self.log.info(f"Loading MCP server: {server.name} ({server.url})")
                mcp_manager.add_server(server)
            
            # Register MCP tools with agent
            mcp_manager.register_with_agent(agent)
            
            # Store in settings for handlers to access
            self.settings['chat_agent'] = agent
            self.settings['mcp_manager'] = mcp_manager
            self.settings['chat_config'] = config
            
            self.log.info("Jupyter AI Agents extension initialized successfully")
            
        except Exception as e:
            self.log.error(f"Error initializing Jupyter AI Agents: {e}", exc_info=True)
            raise
    
    def initialize_handlers(self):
        """Register HTTP handlers."""
        self.log.info("Registering Jupyter AI Agents handlers...")
        
        handlers = [
            (r"/api/chat", ChatHandler),
            (r"/api/configure", ConfigureHandler),
            (r"/api/mcp/servers", MCPServersHandler),
            (r"/api/mcp/servers/([^/]+)", MCPServerHandler),
        ]
        
        self.handlers.extend(handlers)
        self.log.info(f"Registered {len(handlers)} HTTP handlers")


# Entry point for jupyter server
def _jupyter_server_extension_points():
    """
    Returns a list of dictionaries with metadata describing
    where to find the `_load_jupyter_server_extension` function.
    """
    return [{"module": "jupyter_ai_agents.extension"}]


def _load_jupyter_server_extension(server_app):
    """Load the JupyterLab extension."""
    extension = AIChatExtension()
    extension.load_config_file()
    extension.update_config(server_app.config)
    extension.initialize_settings()
    extension.initialize_handlers()
    server_app.web_app.settings.update(extension.settings)
    
    # Add handlers to the server app
    for handler in extension.handlers:
        pattern = url_path_join(server_app.web_app.settings['base_url'], handler[0])
        server_app.web_app.add_handlers(".*$", [(pattern, handler[1], dict(
            config=server_app.config
        ))])
    
    extension.log.info("Jupyter AI Agents extension loaded!")


# For backward compatibility
load_jupyter_server_extension = _load_jupyter_server_extension
