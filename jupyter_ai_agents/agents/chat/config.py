# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Configuration management for AI Chat."""

import json
from pathlib import Path
from typing import List, Optional

from jupyter_ai_agents.agents.models import MCPServer


class ChatConfig:
    """Manage chat configuration."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize chat configuration.
        
        Args:
            config_dir: Directory to store configuration files.
                       If None, uses ~/.jupyter/jupyter_ai_agents
        """
        if config_dir is None:
            from jupyter_core.paths import jupyter_config_dir
            config_dir = Path(jupyter_config_dir()) / 'jupyter_ai_agents'
        
        self.config_dir = config_dir
        self.config_file = config_dir / 'chat_config.json'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize default config if doesn't exist
        if not self.config_file.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file."""
        default_config = {
            'mcp_servers': [],
            'default_model': 'anthropic:claude-sonnet-4-5',
            'enabled_tools': []
        }
        self.save_config(default_config)
    
    def load_config(self) -> dict:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {}
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_config(self, config: dict):
        """Save configuration to file."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def load_mcp_servers(self) -> List[MCPServer]:
        """Load MCP servers from config."""
        config = self.load_config()
        servers_data = config.get('mcp_servers', [])
        return [MCPServer(**server) for server in servers_data]
    
    def save_mcp_servers(self, servers: List[MCPServer]):
        """Save MCP servers to config."""
        config = self.load_config()
        config['mcp_servers'] = [server.model_dump() for server in servers]
        self.save_config(config)
    
    def get_default_model(self) -> str:
        """Get the default model ID."""
        config = self.load_config()
        return config.get('default_model', 'anthropic:claude-sonnet-4-5')
    
    def set_default_model(self, model_id: str):
        """Set the default model ID."""
        config = self.load_config()
        config['default_model'] = model_id
        self.save_config(config)
