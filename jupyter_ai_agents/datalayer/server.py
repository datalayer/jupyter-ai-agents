# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import asyncio
import contextlib
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jupyter_ai_agents.datalayer.agents import AIAgentManager
from jupyter_ai_agents.datalayer.api import router


logger = logging.getLogger(__name__)


# Callback to shutdown instrumentation resources.
shutdown = None


logger.info('Starting AI Agent Server')


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    manager = AIAgentManager()
    try:
        yield {"agent_manager": manager}
    finally:
        if shutdown is not None:
            shutdown()
        await asyncio.shield(manager.stop_all())


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://datalayer.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router,
    prefix="/api/ai-agents",
    tags=[
        "ai",
        "ai-agents",
        "jupyter",
    ]
)
