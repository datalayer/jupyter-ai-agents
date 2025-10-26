# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tornado handlers for chat API compatible with Vercel AI SDK."""

import json
import tornado.web

from jupyter_server.base.handlers import APIHandler
from pydantic import BaseModel
from pydantic_ai.ui.vercel_ai import VercelAIAdapter


class ChatRequestExtra(BaseModel, extra='ignore'):
    """Extra data from chat request."""
    model: str | None = None
    builtin_tools: list[str] = []


class TornadoRequestAdapter:
    """Adapter to make Tornado request compatible with Vercel AI adapter."""
    
    def __init__(self, handler):
        self.handler = handler
        self._body = None
    
    @property
    def url(self):
        """Get request URL."""
        return self.handler.request.uri
    
    @property
    def method(self):
        """Get request method."""
        return self.handler.request.method
    
    async def body(self):
        """Get request body as bytes."""
        if self._body is None:
            self._body = self.handler.request.body
        return self._body
    
    async def json(self):
        """Get request body as JSON."""
        body = await self.body()
        return json.loads(body.decode('utf-8'))
    
    @property
    def headers(self):
        """Get request headers."""
        return dict(self.handler.request.headers)


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
            
            # Create request adapter
            tornado_request = TornadoRequestAdapter(self)
            
            # Validate request using Vercel AI adapter
            request_data = await VercelAIAdapter.validate_request(tornado_request)
            extra_data = ChatRequestExtra.model_validate(request_data.__pydantic_extra__)
            
            # Get builtin tools (TODO: map from IDs)
            builtin_tools = []
            
            # Use VercelAIAdapter to dispatch the request
            # This returns a FastAPI StreamingResponse
            response = await VercelAIAdapter.dispatch_request(
                agent,
                tornado_request,
                model=extra_data.model,
                builtin_tools=builtin_tools,
            )
            
            # Set headers from FastAPI response
            for key, value in response.headers.items():
                self.set_header(key, value)
            
            # Stream the response body
            # FastAPI StreamingResponse has body_iterator
            if hasattr(response, 'body_iterator'):
                async for chunk in response.body_iterator:
                    if isinstance(chunk, bytes):
                        self.write(chunk)
                    else:
                        self.write(chunk.encode('utf-8') if isinstance(chunk, str) else chunk)
                    await self.flush()
            else:
                # Fallback for non-streaming response
                body = response.body
                if isinstance(body, bytes):
                    self.write(body)
                else:
                    self.write(body.encode('utf-8') if isinstance(body, str) else body)
            
            # Finish the response
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
