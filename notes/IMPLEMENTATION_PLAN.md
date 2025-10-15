# Implementation Plan: JupyterLab AI Chat Extension with MCP Support

## Project Overview

Transform jupyter-ai-agents into a JupyterLab extension with an AI chat sidebar powered by Vercel AI Elements, Pydantic AI, and MCP (Model Context Protocol) tools.

## Requirements Summary

1. **Transform to JupyterLab Extension**: Convert jupyter-ai-agents to a proper JupyterLab extension
2. **Maintain Independence**: Keep existing functionality but don't rely on it (may be removed)
3. **AI Chat Sidebar**: Add left sidebar with Vercel AI Elements-based chat UI
4. **Pydantic AI Backend**: Use Pydantic AI as agent framework with Tornado handler
5. **Claude Sonnet 4.0**: Default LLM model (anthropic:claude-sonnet-4.0)
6. **MCP Tools Support**: User-configurable MCP tools in UI, integrated with Python agent

## Architecture Overview

```
jupyter-ai-agents/
├── jupyter_ai_agents/          # Python package
│   ├── __init__.py
│   ├── extension.py            # JupyterLab extension entry
│   ├── chat/                   # NEW: Chat functionality
│   │   ├── __init__.py
│   │   ├── agent.py            # Pydantic AI agent
│   │   ├── handler.py          # Tornado handler for chat
│   │   └── mcp_tools.py        # MCP tool integration
│   └── [existing code...]      # Keep but isolate
│
├── packages/                   # NEW: Frontend packages
│   └── jupyterlab-ai-chat/     # JupyterLab extension
│       ├── package.json
│       ├── tsconfig.json
│       ├── src/
│       │   ├── index.ts        # Extension entry
│       │   ├── widget.tsx      # Chat sidebar widget
│       │   ├── components/     # AI Elements components
│       │   │   ├── ai-elements/
│       │   │   └── ui/
│       │   ├── hooks/
│       │   │   └── useJupyterChat.ts
│       │   └── mcp/
│       │       └── MCPConfigPanel.tsx
│       └── style/
│
└── pyproject.toml              # Updated dependencies
```

## Implementation Phases

### Phase 1: Project Structure Setup ✅

**Goal**: Set up the basic JupyterLab extension structure

#### 1.1 Create Frontend Package Structure
- [ ] Create `packages/jupyterlab-ai-chat/` directory
- [ ] Initialize package.json with JupyterLab dependencies
- [ ] Set up TypeScript configuration
- [ ] Configure build system (webpack/vite)
- [ ] Add JupyterLab extension metadata

**Files to Create:**
```
packages/jupyterlab-ai-chat/
├── package.json
├── tsconfig.json
├── webpack.config.js (or vite.config.ts)
├── README.md
└── src/
    └── index.ts (empty for now)
```

**Key Dependencies:**
```json
{
  "dependencies": {
    "@jupyterlab/application": "^4.0.0",
    "@jupyterlab/apputils": "^4.0.0",
    "@jupyterlab/ui-components": "^4.0.0",
    "@ai-sdk/react": "^2.0.34",
    "ai": "^5.0.34",
    "react": "^19.1.1",
    "react-dom": "^19.1.1",
    "@radix-ui/react-*": "...",
    "streamdown": "^1.2.0",
    "nanoid": "^5.1.6"
  }
}
```

#### 1.2 Update Python Package
- [ ] Add JupyterLab extension metadata to `pyproject.toml`
- [ ] Create `jupyter_ai_agents/extension.py` for JupyterLab hooks
- [ ] Update dependencies for Pydantic AI and MCP

**Update pyproject.toml:**
```toml
[project.entry-points."jupyterlab.extensions"]
jupyter-ai-agents = "jupyter_ai_agents.extension"

[project]
dependencies = [
    "jupyterlab>=4.0.0,<5",
    "pydantic-ai-slim[anthropic,openai,cli]>=1.0.10",
    "fastapi>=0.117.1",
    "sse-starlette>=3.0.2",
    # ... existing dependencies
]
```

#### 1.3 Isolate Existing Functionality
- [ ] Document current functionality
- [ ] Ensure it can run independently
- [ ] Add deprecation notices if needed

---

### Phase 2: Backend Chat Infrastructure 🔧

**Goal**: Implement Pydantic AI agent with Tornado handler

#### 2.1 Create Chat Package Structure
```
jupyter_ai_agents/chat/
├── __init__.py
├── agent.py          # Pydantic AI agent definition
├── handler.py        # Tornado handler for Vercel AI protocol
├── mcp_tools.py      # MCP tool integration
├── config.py         # Chat configuration
└── models.py         # Pydantic models
```

#### 2.2 Implement Pydantic AI Agent

**File: `jupyter_ai_agents/chat/agent.py`**

```python
"""Pydantic AI agent for JupyterLab chat."""
from pydantic_ai import Agent
from typing import Any

def create_chat_agent(model: str = "anthropic:claude-sonnet-4.0") -> Agent:
    """Create the main chat agent."""
    agent = Agent(
        model,
        instructions="""You are a helpful AI assistant integrated into JupyterLab.
        You can help users with their notebooks, code, data analysis, and general questions.
        You have access to various tools through MCP (Model Context Protocol).""",
    )
    
    # Register built-in Jupyter tools
    register_jupyter_tools(agent)
    
    return agent

def register_jupyter_tools(agent: Agent):
    """Register Jupyter-specific tools."""
    
    @agent.tool_plain
    def execute_cell(code: str) -> str:
        """Execute Python code in the active notebook kernel."""
        # Implementation will connect to Jupyter kernel
        pass
    
    @agent.tool_plain
    def read_notebook(path: str) -> str:
        """Read a Jupyter notebook file."""
        pass
    
    @agent.tool_plain
    def list_files(directory: str = ".") -> list[str]:
        """List files in a directory."""
        pass
```

**Tasks:**
- [ ] Create `agent.py` with basic agent setup
- [ ] Implement Jupyter-specific tools (execute, read, write)
- [ ] Add system instructions
- [ ] Support dynamic model selection

#### 2.3 Implement Tornado Handler

**File: `jupyter_ai_agents/chat/handler.py`**

```python
"""Tornado handler for chat API compatible with Vercel AI SDK."""
from jupyter_server.base.handlers import APIHandler
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
import tornado.web
import json

class ChatHandler(APIHandler):
    """Handler for /api/chat endpoint."""
    
    @tornado.web.authenticated
    async def post(self):
        """Handle chat POST request with streaming."""
        try:
            # Get agent from application
            agent = self.settings['chat_agent']
            
            # Parse request using Vercel AI adapter
            body = self.request.body.decode('utf-8')
            request_data = json.loads(body)
            
            # Set up streaming response
            self.set_header('Content-Type', 'text/event-stream')
            self.set_header('Cache-Control', 'no-cache')
            self.set_header('Connection', 'keep-alive')
            
            # Stream response
            async for chunk in VercelAIAdapter.stream_response(
                agent,
                request_data,
                model=request_data.get('model'),
            ):
                self.write(chunk)
                await self.flush()
                
        except Exception as e:
            self.log.error(f"Error in chat handler: {e}")
            self.set_status(500)
            self.finish(json.dumps({"error": str(e)}))

class ConfigureHandler(APIHandler):
    """Handler for /api/configure endpoint."""
    
    @tornado.web.authenticated
    async def get(self):
        """Return configuration for frontend."""
        config = {
            "models": [
                {
                    "id": "anthropic:claude-sonnet-4.0",
                    "name": "Claude Sonnet 4.0",
                    "builtinTools": ["jupyter_execute", "jupyter_read"]
                }
            ],
            "builtinTools": [
                {"id": "jupyter_execute", "name": "Execute Code"},
                {"id": "jupyter_read", "name": "Read Notebook"}
            ],
            "mcpServers": self.settings.get('mcp_servers', [])
        }
        self.finish(json.dumps(config))
```

**Tasks:**
- [ ] Create `handler.py` with Tornado handlers
- [ ] Implement streaming response
- [ ] Add Vercel AI protocol support
- [ ] Add error handling and logging
- [ ] Create configuration endpoint

#### 2.4 MCP Tools Integration

**File: `jupyter_ai_agents/chat/mcp_tools.py`**

```python
"""MCP tool integration for Pydantic AI."""
from typing import Any, Dict, List
from pydantic import BaseModel

class MCPServer(BaseModel):
    """Configuration for an MCP server."""
    id: str
    name: str
    url: str
    enabled: bool = True
    tools: List[str] = []

class MCPToolManager:
    """Manage MCP tools and servers."""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
    
    def add_server(self, server: MCPServer):
        """Add an MCP server."""
        self.servers[server.id] = server
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from enabled servers."""
        tools = []
        for server in self.servers.values():
            if server.enabled:
                # Fetch tools from MCP server
                tools.extend(self._fetch_server_tools(server))
        return tools
    
    def _fetch_server_tools(self, server: MCPServer) -> List[Dict[str, Any]]:
        """Fetch tools from an MCP server."""
        # Implementation will use MCP client
        pass
    
    def register_with_agent(self, agent: Any):
        """Register MCP tools with Pydantic AI agent."""
        tools = self.get_available_tools()
        for tool in tools:
            # Dynamically register tool with agent
            self._register_tool(agent, tool)
```

**Tasks:**
- [ ] Create `mcp_tools.py` with MCP integration
- [ ] Implement MCP server discovery
- [ ] Create tool registration system
- [ ] Add tool configuration persistence
- [ ] Implement MCP client wrapper

#### 2.5 Extension Entry Point

**File: `jupyter_ai_agents/extension.py`**

```python
"""JupyterLab extension for AI Chat."""
from jupyter_server.extension.application import ExtensionApp
from .chat.handler import ChatHandler, ConfigureHandler
from .chat.agent import create_chat_agent
from .chat.mcp_tools import MCPToolManager

class AIChatExtension(ExtensionApp):
    """JupyterLab AI Chat Extension."""
    
    name = "jupyter-ai-agents"
    
    def initialize_settings(self):
        """Initialize extension settings."""
        # Create agent
        agent = create_chat_agent()
        
        # Create MCP manager
        mcp_manager = MCPToolManager()
        
        # Load MCP configuration
        # TODO: Load from user settings
        
        # Register MCP tools with agent
        mcp_manager.register_with_agent(agent)
        
        # Store in settings
        self.settings['chat_agent'] = agent
        self.settings['mcp_manager'] = mcp_manager
    
    def initialize_handlers(self):
        """Register handlers."""
        self.handlers.extend([
            (r"/api/chat", ChatHandler),
            (r"/api/configure", ConfigureHandler),
        ])

# Entry point for jupyter server
load_jupyter_server_extension = AIChatExtension.load_classic_server_extension
```

**Tasks:**
- [ ] Create `extension.py` with JupyterLab hooks
- [ ] Initialize agent and MCP manager
- [ ] Register handlers
- [ ] Add settings management

---

### Phase 3: Frontend Chat UI 🎨

**Goal**: Create JupyterLab sidebar with Vercel AI Elements

#### 3.1 Copy AI Elements Components

**Copy from chat example:**
```
src/components/ai-elements/
├── actions.tsx
├── conversation.tsx
├── message.tsx
├── prompt-input.tsx
├── response.tsx
├── tool.tsx
├── reasoning.tsx
├── sources.tsx
├── loader.tsx
├── code-block.tsx
└── ...
```

**Also copy shadcn/ui components:**
```
src/components/ui/
├── button.tsx
├── avatar.tsx
├── badge.tsx
├── collapsible.tsx
├── select.tsx
└── ...
```

**Tasks:**
- [ ] Copy all AI Elements components
- [ ] Copy shadcn/ui components
- [ ] Adapt styling for JupyterLab theme
- [ ] Update imports and paths

#### 3.2 Create Custom Hook for Jupyter

**File: `src/hooks/useJupyterChat.ts`**

```typescript
/**
 * Custom hook for chat in JupyterLab context.
 * Adapts Vercel AI SDK useChat for Jupyter.
 */
import { useChat as useVercelChat } from '@ai-sdk/react';
import { useEffect } from 'react';

export function useJupyterChat() {
  const chat = useVercelChat({
    api: '/api/chat',
    onError: (error) => {
      console.error('Chat error:', error);
      // Show notification in JupyterLab
    },
  });

  // Save messages to JupyterLab state
  useEffect(() => {
    if (chat.messages.length > 0) {
      // Save to JupyterLab state database
      saveToJupyterState(chat.messages);
    }
  }, [chat.messages]);

  return chat;
}

async function saveToJupyterState(messages: any[]) {
  // Use JupyterLab's state database
  // const stateDB = app.serviceManager.contents;
  // await stateDB.save(...)
}
```

**Tasks:**
- [ ] Create `useJupyterChat.ts` hook
- [ ] Integrate with JupyterLab state
- [ ] Add error handling
- [ ] Add notification support

#### 3.3 Create Chat Sidebar Widget

**File: `src/widget.tsx`**

```typescript
/**
 * JupyterLab chat sidebar widget.
 */
import { ReactWidget } from '@jupyterlab/apputils';
import React, { useState } from 'react';
import { Conversation, ConversationContent, ConversationScrollButton } from './components/ai-elements/conversation';
import { Message, MessageContent } from './components/ai-elements/message';
import { PromptInput, PromptInputTextarea, PromptInputSubmit } from './components/ai-elements/prompt-input';
import { Response } from './components/ai-elements/response';
import { useJupyterChat } from './hooks/useJupyterChat';
import { Part } from './components/Part';

function ChatComponent() {
  const { messages, status, sendMessage } = useJupyterChat();
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage({ text: input });
      setInput('');
    }
  };

  return (
    <div className="jupyter-ai-chat">
      <Conversation className="h-full">
        <ConversationContent>
          {messages.map((message) => (
            <div key={message.id}>
              {message.parts.map((part, i) => (
                <Part
                  key={`${message.id}-${i}`}
                  part={part}
                  message={message}
                  status={status}
                  index={i}
                  lastMessage={message.id === messages.at(-1)?.id}
                />
              ))}
            </div>
          ))}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <div className="sticky bottom-0 p-3">
        <PromptInput onSubmit={handleSubmit}>
          <PromptInputTextarea
            onChange={(e) => setInput(e.target.value)}
            value={input}
            autoFocus
          />
          <PromptInputSubmit disabled={!input} status={status} />
        </PromptInput>
      </div>
    </div>
  );
}

export class ChatWidget extends ReactWidget {
  constructor() {
    super();
    this.addClass('jp-AiChatWidget');
  }

  render(): JSX.Element {
    return <ChatComponent />;
  }
}
```

**Tasks:**
- [ ] Create `widget.tsx` with ReactWidget
- [ ] Implement chat UI with AI Elements
- [ ] Add message rendering
- [ ] Add input handling
- [ ] Style for JupyterLab

#### 3.4 Create MCP Configuration Panel

**File: `src/mcp/MCPConfigPanel.tsx`**

```typescript
/**
 * MCP server configuration panel.
 */
import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Switch } from '../components/ui/switch';

interface MCPServer {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
  tools: string[];
}

export function MCPConfigPanel() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [newServer, setNewServer] = useState({ name: '', url: '' });

  useEffect(() => {
    // Load MCP servers from backend
    fetchMCPServers();
  }, []);

  const fetchMCPServers = async () => {
    const response = await fetch('/api/configure');
    const config = await response.json();
    setServers(config.mcpServers || []);
  };

  const addServer = async () => {
    if (newServer.name && newServer.url) {
      const server: MCPServer = {
        id: `mcp-${Date.now()}`,
        name: newServer.name,
        url: newServer.url,
        enabled: true,
        tools: [],
      };
      
      // Save to backend
      await fetch('/api/mcp/servers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(server),
      });
      
      setServers([...servers, server]);
      setNewServer({ name: '', url: '' });
    }
  };

  const toggleServer = async (id: string) => {
    const updated = servers.map(s => 
      s.id === id ? { ...s, enabled: !s.enabled } : s
    );
    setServers(updated);
    
    // Update backend
    const server = updated.find(s => s.id === id);
    await fetch(`/api/mcp/servers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(server),
    });
  };

  return (
    <div className="mcp-config-panel p-4">
      <h2 className="text-lg font-bold mb-4">MCP Servers</h2>
      
      <div className="space-y-4">
        {servers.map(server => (
          <div key={server.id} className="border rounded p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">{server.name}</span>
              <Switch
                checked={server.enabled}
                onCheckedChange={() => toggleServer(server.id)}
              />
            </div>
            <div className="text-sm text-muted-foreground">
              {server.url}
            </div>
            <div className="text-xs mt-2">
              Tools: {server.tools.length}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 border-t pt-4">
        <h3 className="font-medium mb-2">Add Server</h3>
        <div className="space-y-2">
          <Input
            placeholder="Server name"
            value={newServer.name}
            onChange={(e) => setNewServer({ ...newServer, name: e.target.value })}
          />
          <Input
            placeholder="Server URL"
            value={newServer.url}
            onChange={(e) => setNewServer({ ...newServer, url: e.target.value })}
          />
          <Button onClick={addServer}>Add Server</Button>
        </div>
      </div>
    </div>
  );
}
```

**Tasks:**
- [ ] Create `MCPConfigPanel.tsx`
- [ ] Implement server list display
- [ ] Add server add/remove/toggle
- [ ] Connect to backend API
- [ ] Show tool counts

#### 3.5 Extension Entry Point

**File: `src/index.ts`**

```typescript
/**
 * JupyterLab AI Chat extension entry point.
 */
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { ChatWidget } from './widget';
import { MCPConfigPanel } from './mcp/MCPConfigPanel';

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyter-ai-agents:plugin',
  autoStart: true,
  requires: [ICommandPalette],
  activate: (app: JupyterFrontEnd, palette: ICommandPalette) => {
    console.log('JupyterLab AI Chat extension activated!');

    // Create chat widget
    const chatWidget = new ChatWidget();
    chatWidget.id = 'jupyter-ai-chat';
    chatWidget.title.label = 'AI Chat';
    chatWidget.title.closable = true;

    // Add to left sidebar
    app.shell.add(chatWidget, 'left', { rank: 1000 });

    // Add command to open chat
    const command = 'jupyter-ai-chat:open';
    app.commands.addCommand(command, {
      label: 'Open AI Chat',
      execute: () => {
        if (!chatWidget.isAttached) {
          app.shell.add(chatWidget, 'left');
        }
        app.shell.activateById(chatWidget.id);
      }
    });

    // Add to command palette
    palette.addItem({ command, category: 'AI Chat' });

    // Add MCP config command
    const mcpCommand = 'jupyter-ai-chat:configure-mcp';
    app.commands.addCommand(mcpCommand, {
      label: 'Configure MCP Servers',
      execute: () => {
        // Show MCP config dialog
        // TODO: Implement dialog
      }
    });

    palette.addItem({ command: mcpCommand, category: 'AI Chat' });
  }
};

export default plugin;
```

**Tasks:**
- [ ] Create `index.ts` with plugin activation
- [ ] Register chat widget in left sidebar
- [ ] Add commands to palette
- [ ] Add keyboard shortcuts
- [ ] Add menu items

---

### Phase 4: MCP Integration 🔌

**Goal**: Full MCP server support with UI configuration

#### 4.1 MCP Server Management API

**Add handlers to `chat/handler.py`:**

```python
class MCPServersHandler(APIHandler):
    """Handler for MCP server CRUD operations."""
    
    @tornado.web.authenticated
    async def get(self):
        """Get all MCP servers."""
        mcp_manager = self.settings['mcp_manager']
        servers = mcp_manager.get_servers()
        self.finish(json.dumps([s.dict() for s in servers]))
    
    @tornado.web.authenticated
    async def post(self):
        """Add a new MCP server."""
        data = json.loads(self.request.body)
        mcp_manager = self.settings['mcp_manager']
        server = MCPServer(**data)
        mcp_manager.add_server(server)
        await mcp_manager.save_config()
        self.finish(json.dumps(server.dict()))

class MCPServerHandler(APIHandler):
    """Handler for individual MCP server operations."""
    
    @tornado.web.authenticated
    async def put(self, server_id):
        """Update MCP server."""
        data = json.loads(self.request.body)
        mcp_manager = self.settings['mcp_manager']
        server = MCPServer(**data)
        mcp_manager.update_server(server_id, server)
        await mcp_manager.save_config()
        self.finish(json.dumps(server.dict()))
    
    @tornado.web.authenticated
    async def delete(self, server_id):
        """Delete MCP server."""
        mcp_manager = self.settings['mcp_manager']
        mcp_manager.remove_server(server_id)
        await mcp_manager.save_config()
        self.set_status(204)
```

**Tasks:**
- [ ] Add MCP CRUD handlers
- [ ] Implement server persistence
- [ ] Add validation
- [ ] Add error handling

#### 4.2 MCP Client Implementation

**File: `jupyter_ai_agents/chat/mcp_client.py`**

```python
"""MCP client for connecting to MCP servers."""
import httpx
from typing import List, Dict, Any

class MCPClient:
    """Client for communicating with MCP servers."""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = httpx.AsyncClient()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        response = await self.client.get(f"{self.server_url}/tools")
        return response.json()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        response = await self.client.post(
            f"{self.server_url}/tools/{tool_name}",
            json={"arguments": arguments}
        )
        return response.json()
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()
```

**Tasks:**
- [ ] Create MCP client
- [ ] Implement tool discovery
- [ ] Implement tool calling
- [ ] Add authentication support
- [ ] Add error handling

#### 4.3 Dynamic Tool Registration

**Update `mcp_tools.py`:**

```python
def register_mcp_tool_with_agent(agent: Agent, tool_def: Dict[str, Any], client: MCPClient):
    """Dynamically register an MCP tool with the agent."""
    
    tool_name = tool_def['name']
    tool_description = tool_def['description']
    tool_parameters = tool_def['parameters']
    
    # Create a dynamic tool function
    async def mcp_tool(**kwargs):
        """Dynamically created MCP tool."""
        result = await client.call_tool(tool_name, kwargs)
        return result
    
    # Set metadata
    mcp_tool.__name__ = tool_name
    mcp_tool.__doc__ = tool_description
    
    # Register with agent
    agent.tool(mcp_tool)
```

**Tasks:**
- [ ] Implement dynamic tool creation
- [ ] Add parameter validation
- [ ] Add result formatting
- [ ] Handle async tools
- [ ] Add error recovery

#### 4.4 Configuration Persistence

**File: `jupyter_ai_agents/chat/config.py`**

```python
"""Configuration management for AI Chat."""
from pathlib import Path
import json
from typing import List
from .mcp_tools import MCPServer

class ChatConfig:
    """Manage chat configuration."""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "chat_config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_mcp_servers(self) -> List[MCPServer]:
        """Load MCP servers from config."""
        if not self.config_file.exists():
            return []
        
        with open(self.config_file) as f:
            data = json.load(f)
            return [MCPServer(**s) for s in data.get('mcp_servers', [])]
    
    def save_mcp_servers(self, servers: List[MCPServer]):
        """Save MCP servers to config."""
        data = {'mcp_servers': [s.dict() for s in servers]}
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
```

**Tasks:**
- [ ] Create config management
- [ ] Implement load/save
- [ ] Add migration support
- [ ] Add validation

---

### Phase 5: Testing & Polish ✨

#### 5.1 Testing

**Backend Tests:**
- [ ] Unit tests for agent
- [ ] Unit tests for handlers
- [ ] Unit tests for MCP integration
- [ ] Integration tests for streaming
- [ ] MCP mock server for testing

**Frontend Tests:**
- [ ] Component tests for AI Elements
- [ ] Widget tests
- [ ] Hook tests
- [ ] E2E tests with JupyterLab

#### 5.2 Documentation

- [ ] User guide for chat sidebar
- [ ] MCP configuration guide
- [ ] Developer guide for extending
- [ ] API documentation
- [ ] Example notebooks

#### 5.3 Polish

- [ ] Keyboard shortcuts
- [ ] Context menu integration
- [ ] Theming support (light/dark)
- [ ] Loading states
- [ ] Error messages
- [ ] Notifications
- [ ] Settings panel in JupyterLab

---

## Technology Stack

### Frontend
- **React 19** with TypeScript
- **JupyterLab 4** extension framework
- **Vercel AI SDK** (@ai-sdk/react)
- **AI Elements** (copied components)
- **shadcn/ui** components
- **Tailwind CSS** for styling
- **Webpack** or **Vite** for bundling

### Backend
- **Python 3.12+**
- **JupyterLab Server Extension**
- **Tornado** handlers
- **Pydantic AI** with Anthropic support
- **MCP** (Model Context Protocol)
- **httpx** for HTTP clients

---

## Dependencies to Add

### Python (pyproject.toml)
```toml
dependencies = [
    "jupyterlab>=4.0.0,<5",
    "pydantic-ai-slim[anthropic,openai,cli]>=1.0.10",
    "fastapi>=0.117.1",
    "sse-starlette>=3.0.2",
    "httpx>=0.25.0",
    "tornado>=6.0",
]
```

### TypeScript (package.json)
```json
{
  "dependencies": {
    "@jupyterlab/application": "^4.0.0",
    "@jupyterlab/apputils": "^4.0.0",
    "@jupyterlab/ui-components": "^4.0.0",
    "@ai-sdk/react": "^2.0.34",
    "ai": "^5.0.34",
    "react": "^19.1.1",
    "react-dom": "^19.1.1",
    "@radix-ui/react-avatar": "^1.1.10",
    "@radix-ui/react-collapsible": "^1.1.12",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-scroll-area": "^1.2.10",
    "@radix-ui/react-select": "^2.2.6",
    "@radix-ui/react-separator": "^1.1.7",
    "@radix-ui/react-slot": "^1.2.3",
    "@radix-ui/react-switch": "^1.2.6",
    "@radix-ui/react-tooltip": "^1.2.8",
    "streamdown": "^1.2.0",
    "nanoid": "^5.1.6",
    "lucide-react": "^0.542.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.3.1"
  }
}
```

---

## File Checklist

### Backend Files to Create
- [ ] `jupyter_ai_agents/extension.py` - JupyterLab extension entry
- [ ] `jupyter_ai_agents/chat/__init__.py`
- [ ] `jupyter_ai_agents/chat/agent.py` - Pydantic AI agent
- [ ] `jupyter_ai_agents/chat/handler.py` - Tornado handlers
- [ ] `jupyter_ai_agents/chat/mcp_tools.py` - MCP integration
- [ ] `jupyter_ai_agents/chat/mcp_client.py` - MCP client
- [ ] `jupyter_ai_agents/chat/config.py` - Configuration
- [ ] `jupyter_ai_agents/chat/models.py` - Pydantic models

### Frontend Files to Create
- [ ] `packages/jupyterlab-ai-chat/package.json`
- [ ] `packages/jupyterlab-ai-chat/tsconfig.json`
- [ ] `packages/jupyterlab-ai-chat/webpack.config.js`
- [ ] `packages/jupyterlab-ai-chat/src/index.ts` - Extension entry
- [ ] `packages/jupyterlab-ai-chat/src/widget.tsx` - Chat widget
- [ ] `packages/jupyterlab-ai-chat/src/components/Part.tsx` - Part renderer
- [ ] `packages/jupyterlab-ai-chat/src/hooks/useJupyterChat.ts`
- [ ] `packages/jupyterlab-ai-chat/src/mcp/MCPConfigPanel.tsx`
- [ ] Copy all `ai-elements/` components
- [ ] Copy all `ui/` components
- [ ] `packages/jupyterlab-ai-chat/style/index.css` - Styles

### Configuration Files to Update
- [ ] `pyproject.toml` - Add dependencies and entry points
- [ ] Update existing handlers to not conflict

---

## Timeline Estimate

- **Phase 1 (Structure)**: 1-2 days
- **Phase 2 (Backend)**: 3-4 days
- **Phase 3 (Frontend)**: 4-5 days
- **Phase 4 (MCP)**: 3-4 days
- **Phase 5 (Testing)**: 2-3 days

**Total**: ~15-20 days of development

---

## Success Criteria

- ✅ JupyterLab extension installs successfully
- ✅ Chat sidebar appears in left panel
- ✅ Can send messages and receive streaming responses
- ✅ Claude Sonnet 4.0 model works as default
- ✅ Built-in Jupyter tools (execute, read) work
- ✅ Can configure MCP servers in UI
- ✅ MCP tools are discovered and callable
- ✅ Tool calls display properly with input/output
- ✅ Reasoning displays in collapsible sections
- ✅ Conversation history persists
- ✅ Works in light and dark themes
- ✅ No conflicts with existing functionality

---

## Next Steps

1. **Review this plan** - Confirm approach is correct
2. **Set up development environment** - Install dependencies
3. **Start with Phase 1** - Create basic structure
4. **Iterate on each phase** - Test as we go
5. **Get feedback** - Adjust based on usage

---

## Notes

- Keep existing functionality isolated but functional
- Use the chat example as reference throughout
- Test with real MCP servers early
- Document as we build
- Consider performance for large conversations
- Handle errors gracefully
- Support keyboard navigation
- Make UI responsive

---

**Ready to start implementation?** Let me know if you'd like to adjust anything in this plan!
