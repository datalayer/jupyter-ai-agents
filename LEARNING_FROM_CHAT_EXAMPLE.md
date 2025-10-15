# Learning from the Chat Project Example

## Overview

The chat project is a full-stack AI chatbot application that combines:
- **Frontend**: React + TypeScript with Vite, using Vercel AI SDK and AI Elements
- **Backend**: Python with Pydantic AI, FastAPI, and Model Context Protocol (MCP) support
- **Key Libraries**: @ai-sdk/react, ai (Vercel AI SDK), pydantic-ai, streamdown

## Architecture

### Frontend Architecture (TypeScript/React)

#### 1. Core Structure
```
src/
├── App.tsx                 # Root component with providers
├── Chat.tsx                # Main chat interface
├── Part.tsx                # Individual message part renderer
├── types.ts                # TypeScript types
├── components/
│   ├── ai-elements/        # AI-specific UI components
│   │   ├── conversation.tsx
│   │   ├── message.tsx
│   │   ├── prompt-input.tsx
│   │   ├── response.tsx
│   │   ├── tool.tsx
│   │   ├── reasoning.tsx
│   │   ├── sources.tsx
│   │   └── ...
│   └── ui/                 # shadcn/ui base components
└── hooks/
    └── useConversationIdFromUrl.tsx
```

#### 2. Key Frontend Patterns

**a) Vercel AI SDK Integration**
```tsx
import { useChat } from '@ai-sdk/react'

const { messages, sendMessage, status, setMessages, regenerate } = useChat()
```

The `useChat` hook provides:
- `messages`: Array of conversation messages with parts
- `sendMessage`: Function to send user input
- `status`: Chat state ('ready', 'submitted', 'streaming', 'error')
- `setMessages`: Manually update messages
- `regenerate`: Regenerate a specific message

**b) AI Elements Component Pattern**
Components follow a composable pattern with context providers:

```tsx
<Conversation>
  <ConversationContent>
    <Message from="user">
      <MessageContent>
        <Response>Text content here</Response>
      </MessageContent>
    </Message>
  </ConversationContent>
  <ConversationScrollButton />
</Conversation>
```

**c) Message Parts Architecture**
Messages contain "parts" with different types:
- `text`: Regular text response
- `reasoning`: AI thought process (collapsible)
- `tool-*`: Tool call with input/output
- `source-url`: Source citations
- `dynamic-tool`: Dynamic tool execution

**d) Prompt Input Component**
Advanced input with model selection and tools:
```tsx
<PromptInput onSubmit={handleSubmit}>
  <PromptInputTextarea />
  <PromptInputToolbar>
    <PromptInputTools>
      {/* Model selector */}
      <PromptInputModelSelect />
      {/* Tools dropdown */}
      <DropdownMenu>...</DropdownMenu>
    </PromptInputTools>
    <PromptInputSubmit status={status} />
  </PromptInputToolbar>
</PromptInput>
```

**e) State Management**
- Uses React Query for server state (model config)
- Local storage for conversation persistence
- URL-based routing for conversations
- Custom events for cross-component updates

#### 3. Tool System

Tools are displayed with collapsible UI showing:
- Tool name and icon
- Status badge (Pending/Running/Completed/Error)
- Input parameters (JSON)
- Output/result (JSON or custom rendering)

```tsx
<Tool>
  <ToolHeader type={part.type} state={part.state} />
  <ToolContent>
    <ToolInput input={part.input} />
    <ToolOutput output={part.output} />
  </ToolContent>
</Tool>
```

#### 4. Styling & UI

- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Base component library (Button, Select, etc.)
- **CSS Variables**: Theme support (light/dark mode)
- **Responsive**: Mobile-first design with sidebar

### Backend Architecture (Python/Pydantic AI)

#### 1. Core Structure
```
agent/chatbot/
├── __init__.py
├── server.py          # FastAPI server with Vercel AI adapter
├── agent.py           # Pydantic AI agent definition
├── db.py              # Vector database for RAG
└── data.py            # Data loading utilities
```

#### 2. Key Backend Patterns

**a) Pydantic AI Agent**
```python
from pydantic_ai import Agent

agent = Agent(
    'anthropic:claude-sonnet-4-0',
    instructions="System prompt here...",
)

# Add tools
@agent.tool_plain
def search_docs(repo: str, query: str):
    # Tool implementation
    pass
```

**b) FastAPI + Vercel AI Adapter**
```python
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

@app.post('/api/chat')
async def post_chat(request: Request) -> Response:
    request_data = await VercelAIAdapter.validate_request(request)
    return await VercelAIAdapter.dispatch_request(
        agent,
        request,
        model=extra_data.model,
        builtin_tools=[...],
    )
```

The Vercel AI Adapter:
- Validates incoming streaming requests
- Dispatches to Pydantic AI agent
- Streams responses in Vercel AI format
- Handles tool calls and reasoning

**c) Configuration Endpoint**
```python
@app.get('/api/configure')
async def configure_frontend() -> ConfigureFrontend:
    return ConfigureFrontend(
        models=[...],          # Available models
        builtin_tools=[...],   # Available tools
    )
```

Frontend fetches this to populate model/tool selectors.

**d) Builtin Tools**
Pydantic AI provides builtin tools:
- `WebSearchTool()`: Web search capability
- `CodeExecutionTool()`: Execute code safely
- `ImageGenerationTool()`: Generate images

Custom tools can be added with `@agent.tool_plain` decorator.

#### 3. Model Support

Multiple models with different tool support:
```python
AI_MODELS = [
    AIModel(
        id='anthropic:claude-sonnet-4-5',
        name='Claude Sonnet 4.5',
        builtin_tools=['web_search', 'code_execution'],
    ),
    AIModel(
        id='openai-responses:gpt-5',
        name='GPT 5',
        builtin_tools=['web_search', 'code_execution', 'image_generation'],
    ),
]
```

### Data Flow

1. **User Input** → Frontend collects text + selected model + enabled tools
2. **POST /api/chat** → Send to backend with streaming enabled
3. **Pydantic AI Agent** → Processes request, may call tools
4. **Stream Response** → Backend streams tokens/parts to frontend
5. **Render Parts** → Frontend renders each part (text, tool, reasoning)
6. **Local Storage** → Persist conversation for history

### Key Technologies

#### Frontend
- **React 19** with TypeScript
- **Vite** for build tooling
- **@ai-sdk/react** (useChat hook)
- **ai** package v5 (Vercel AI SDK core)
- **Tailwind CSS v4** with @tailwindcss/vite
- **shadcn/ui** component library
- **Radix UI** primitives
- **streamdown** for markdown rendering
- **react-syntax-highlighter** for code blocks
- **nanoid** for ID generation
- **@tanstack/react-query** for server state

#### Backend
- **Python 3.12+**
- **pydantic-ai** with Anthropic/OpenAI support
- **FastAPI** for HTTP server
- **uvicorn** ASGI server
- **sse-starlette** for server-sent events
- **logfire** for observability
- **lancedb** for vector storage (RAG)
- **sentence-transformers** for embeddings

## Vercel AI Elements

### What are AI Elements?

AI Elements is an open-source library of **customizable React components** built on shadcn/ui specifically for building AI interfaces. It's framework-agnostic but optimized for Next.js.

### Key Features

1. **Composable**: Mix and match components
2. **Customizable**: Full source code in your project
3. **Typed**: Full TypeScript support
4. **Accessible**: Built on Radix UI
5. **Themed**: Supports CSS variables for theming

### Installation

```bash
# Install AI Elements CLI
npx ai-elements@latest

# Or specific components
npx ai-elements@latest add message conversation prompt-input

# Or via shadcn CLI
npx shadcn@latest add https://registry.ai-sdk.dev/all.json
```

### Available Components

| Component | Purpose |
|-----------|---------|
| `actions` | Action buttons (copy, regenerate, etc.) |
| `branch` | Conversation branching |
| `chain-of-thought` | Extended reasoning display |
| `code-block` | Syntax-highlighted code |
| `context` | Token usage display |
| `conversation` | Chat container with scrolling |
| `image` | AI-generated images |
| `inline-citation` | Source citations |
| `loader` | Loading states |
| `message` | Individual messages |
| `open-in-chat` | Open in external chat |
| `prompt-input` | Advanced input with attachments |
| `reasoning` | Collapsible reasoning |
| `response` | Markdown response |
| `sources` | Source attribution |
| `suggestion` | Quick suggestions |
| `task` | Task tracking |
| `tool` | Tool call visualization |
| `web-preview` | Embedded web previews |

### Component Philosophy

**Compound Components Pattern:**
```tsx
<Parent>
  <ParentTrigger />
  <ParentContent>
    <ParentItem />
  </ParentContent>
</Parent>
```

**Props Over Slots:**
- Components accept children and props
- Flexible composition
- Type-safe with TypeScript

**Unstyled → Styled:**
- Built on Radix UI (unstyled)
- Styled with Tailwind classes
- Fully customizable

### Integration with AI SDK

```tsx
import { useChat } from '@ai-sdk/react'

// AI SDK provides state management
const { messages, status, sendMessage } = useChat()

// AI Elements provides UI components
<Conversation>
  {messages.map(message => (
    <Message from={message.role}>
      <MessageContent>
        <Response>{message.content}</Response>
      </MessageContent>
    </Message>
  ))}
</Conversation>
```

## MCP (Model Context Protocol) Support

While the chat example uses Pydantic AI's builtin tools, MCP is a protocol for connecting AI agents to external tools and data sources.

### How to Add MCP

1. **MCP Server**: Tools exposed via MCP protocol
2. **Agent Integration**: Connect agent to MCP servers
3. **Tool Registration**: Register MCP tools with agent
4. **Frontend Display**: Show MCP tool calls in UI

Pydantic AI supports MCP through custom tool implementations.

## Lessons for jupyter-ai-agents

### 1. Architecture Recommendations

**Frontend (JupyterLab Extension):**
```
jupyter-ai-agents/frontend/
├── components/
│   ├── ai-elements/      # Copy from chat example
│   ├── ChatSidebar.tsx   # JupyterLab sidebar widget
│   └── ...
├── hooks/
│   └── useJupyterChat.ts # Adapt useChat for Jupyter
└── index.ts              # Extension entry
```

**Backend (Python Package):**
```
jupyter_ai_agents/
├── server/
│   ├── chat_handler.py   # Similar to server.py
│   └── api/
│       └── chat.py       # Vercel AI endpoints
├── agents/
│   └── jupyter_agent.py  # Agent with Jupyter tools
└── tools/
    └── jupyter_tools.py  # Notebook execution, etc.
```

### 2. Key Adaptations

**a) JupyterLab Integration**
- Use `@jupyterlab/apputils` for sidebar
- Use Jupyter server extensions for backend
- Communicate via Jupyter REST API

**b) Jupyter-Specific Tools**
- Execute notebook cells
- Read/write notebooks
- Access kernel state
- File system operations
- Git operations

**c) State Management**
- Use JupyterLab state database
- Integrate with existing Jupyter contexts
- Share state with other extensions

### 3. Component Reuse

**Directly Reusable:**
- All AI Elements components
- Message rendering logic
- Tool visualization
- Reasoning display

**Needs Adaptation:**
- Sidebar (use JupyterLab's)
- Routing (use JupyterLab's)
- Storage (use JupyterLab's state)

### 4. Backend Strategy

**Option A: Extend Existing Server**
- Add Vercel AI endpoints to existing server
- Reuse agent infrastructure

**Option B: Separate Chat Server**
- Run chat server alongside Jupyter
- Use websockets for communication

**Recommended: Option A** for better integration

### 5. MCP Integration

1. **Define Jupyter MCP Server**
   - Expose notebook operations as MCP tools
   - Connect to kernel
   - File system access

2. **Connect to External MCP Servers**
   - Web search
   - Code execution sandbox
   - Data sources

3. **UI for MCP Tools**
   - Reuse tool component
   - Show MCP server status
   - Configure MCP connections

## Next Steps

1. **Set up base structure**
   - Create frontend extension scaffold
   - Set up Vercel AI endpoint in backend

2. **Copy AI Elements components**
   - Install in frontend project
   - Customize for JupyterLab theme

3. **Create chat handler**
   - Adapt server.py pattern
   - Use existing agent infrastructure

4. **Add Jupyter tools**
   - Notebook operations
   - Kernel communication
   - File system

5. **Integrate MCP**
   - Define Jupyter MCP server
   - Connect external MCP servers
   - UI for tool configuration

## Code Examples to Reference

**Frontend:**
- `Chat.tsx` - Main chat interface pattern
- `Part.tsx` - Message part rendering
- `app-sidebar.tsx` - Conversation history
- `components/ai-elements/*` - All UI components

**Backend:**
- `server.py` - FastAPI + Vercel AI adapter
- `agent.py` - Agent definition with tools
- Tool registration patterns

## Resources

- **Vercel AI SDK**: https://ai-sdk.dev/
- **AI Elements**: https://ai-sdk.dev/elements/overview
- **Pydantic AI**: https://ai.pydantic.dev/
- **MCP Specification**: https://modelcontextprotocol.io/
- **Chat Example**: The project we just analyzed

## Summary

The chat project demonstrates a clean separation between:
1. **State management** (Vercel AI SDK)
2. **UI components** (AI Elements)
3. **Agent logic** (Pydantic AI)
4. **Tool execution** (MCP-compatible)

This architecture is highly adaptable to JupyterLab, where we'll need to:
- Replace web routing with JupyterLab navigation
- Add Jupyter-specific tools (notebooks, kernels)
- Integrate with JupyterLab's extension system
- Maintain the same clean component architecture
