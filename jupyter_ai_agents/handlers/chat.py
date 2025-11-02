# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tornado handlers for chat API compatible with Vercel AI SDK."""

import json
import logging
from pydantic_ai import UsageLimits
import tornado.web

from jupyter_server.base.handlers import APIHandler
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from starlette.requests import Request
from starlette.datastructures import Headers

from ..tools import create_mcp_server

logger = logging.getLogger(__name__)


class TornadoRequestAdapter(Request):
    """Adapter to make Tornado request compatible with Starlette Request interface."""
    
    def __init__(self, handler):
        """
        Initialize the adapter with a Tornado handler.
        
        Args:
            handler: The Tornado RequestHandler instance
        """
        self.handler = handler
        self._body_cache = None
        
        # Create a minimal scope for Starlette Request
        scope = {
            'type': 'http',
            'method': handler.request.method,
            'path': handler.request.path,
            'query_string': handler.request.query.encode('utf-8'),
            'headers': [(k.lower().encode(), v.encode()) for k, v in handler.request.headers.items()],
            'server': (handler.request.host.split(':')[0], int(handler.request.host.split(':')[1]) if ':' in handler.request.host else 80),
        }
        
        # Initialize the parent Starlette Request
        # We need to provide a receive callable
        async def receive():
            return {
                'type': 'http.request',
                'body': handler.request.body,
                'more_body': False,
            }
        
        super().__init__(scope, receive)
    
    async def body(self) -> bytes:
        """Get request body as bytes."""
        if self._body_cache is None:
            self._body_cache = self.handler.request.body
        return self._body_cache


class ChatHandler(APIHandler):
    """
    Handler for /api/chat endpoint.
    
    This handler implements the Vercel AI protocol for streaming chat responses.
    It receives chat messages and streams back AI responses with support for:
    - Text responses
    - Tool calls
    - Reasoning steps
    - Source citations
    """
    
    async def post(self):
        """Handle chat POST request with streaming."""
        try:
            # Get agent from application settings
            agent = self.settings.get('chat_agent')
            if not agent:
                self.set_status(500)
                self.finish(json.dumps({"error": "Chat agent not initialized"}))
                return
            
            # Lazily create the MCP server connection for this request
            base_url = self.settings.get('chat_base_url')
            token = self.settings.get('chat_token')
            mcp_server = create_mcp_server(base_url, token)

            async with mcp_server:
                # Create request adapter (Starlette-compatible)
                tornado_request = TornadoRequestAdapter(self)
                
                # Parse request body to extract model if specified
                try:
                    body = await tornado_request.json()
                    model = body.get('model') if isinstance(body, dict) else None
                except Exception:
                    model = None
                
                # Get builtin tools (empty list - tools metadata is only for UI display)
                # The actual pydantic-ai tools are registered in the agent itself
                builtin_tools = []
                
                # Create usage limits for the agent
                usage_limits = UsageLimits(
                    tool_calls_limit=5,                    
                    output_tokens_limit=5000,
                    total_tokens_limit=100000,
                )
                
                # Use VercelAIAdapter.dispatch_request (new API)
                response = await VercelAIAdapter.dispatch_request(
                    tornado_request,
                    agent=agent,
                    model=model,
                    usage_limits=usage_limits,
                    toolsets=[mcp_server],
                    builtin_tools=builtin_tools,
                )
            
                # Set headers from FastAPI response
                for key, value in response.headers.items():
                    self.set_header(key, value)
                
                # Stream the response body
                if hasattr(response, 'body_iterator'):
                    try:
                        async for chunk in response.body_iterator:
                            if isinstance(chunk, bytes):
                                self.write(chunk)
                            else:
                                self.write(chunk.encode('utf-8') if isinstance(chunk, str) else chunk)
                            await self.flush()
                    except Exception as stream_error:
                        self.log.debug(f"Stream iteration completed with: {stream_error}")
                else:
                    body = response.body
                    if isinstance(body, bytes):
                        self.write(body)
                    else:
                        self.write(body.encode('utf-8') if isinstance(body, str) else body)
                
                # Finish the response while MCP context is active
                self.finish()
            
        except Exception as e:
            self.log.error(f"Error in chat handler: {e}", exc_info=True)
            if not self._finished:
                self.set_status(500)
                self.finish(json.dumps({"error": str(e)}))
    

    @tornado.web.authenticated
    async def options(self):
        """Handle OPTIONS request for CORS."""
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')
        self.set_status(204)
        self.finish()
