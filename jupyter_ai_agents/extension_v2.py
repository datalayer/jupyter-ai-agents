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


class JupyterAIAgentsV2ExtensionApp(ExtensionApp):
    """JupyterLab AI Chat Extension."""
    
    name = "jupyter_ai_agents"

    extension_url = "/jupyter_ai_agents"

    load_other_extensions = True

    description = "AI Chat sidebar for JupyterLab with MCP support"
    
    app_name = "Jupyter AI Agents"
    app_version = "0.1.0"
    
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
        
        # Use relative paths - they will be joined with base_url in _load_jupyter_server_extension
        handlers = [
            (url_path_join(self.name, "v2", "chat"), ChatHandler),
            (url_path_join(self.name, "v2", "configure"), ConfigureHandler),
            (url_path_join(self.name, "v2", "mcp/servers"), MCPServersHandler),
            (r"jupyter_ai_agents/v2/mcp/servers/([^/]+)", MCPServerHandler),
        ]
        
        self.handlers.extend(handlers)
        self.log.info(f"Registered {len(handlers)} HTTP handlers")


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

main = launch_new_instance = JupyterAIAgentsV2ExtensionApp.launch_instance
