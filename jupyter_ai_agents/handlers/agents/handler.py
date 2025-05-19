# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import json
import logging

from concurrent import futures
from concurrent.futures import as_completed

from anyio import create_task_group, sleep
from anyio.from_thread import start_blocking_portal

from jupyter_server.utils import url_path_join
from jupyter_server.base.handlers import APIHandler

from jupyter_kernel_client import KernelClient

from jupyter_ai_agents.handlers.agents.manager import AIAgentsManager
from jupyter_ai_agents.agents.prompt import PromptAgent
from jupyter_ai_agents.models import AgentRequestModel
from jupyter_ai_agents.utils import http_to_ws
from jupyter_ai_agents import __version__


logger = logging.getLogger(__name__)


EXECUTOR = futures.ThreadPoolExecutor(8)

AI_AGENTS_MANAGER: AIAgentsManager | None = None

# COLLABORATION_ROOMS = {}


def prompt_ai_agent(room_id, jupyter_ingress, jupyter_token, kernel_id):
    async def long_running_prompt():
        global AI_AGENTS_MANAGER
        room_ws_url = http_to_ws(url_path_join(jupyter_ingress, "/api/collaboration/room", room_id))
        logger.info("AI Agent will connect to room [%s]…", room_ws_url)
        has_runtime = jupyter_ingress and jupyter_token and kernel_id
        prompt_agent = PromptAgent(
            websocket_url=room_ws_url,
            runtime_client=KernelClient(
                server_url=jupyter_ingress,
                token=jupyter_token,
                kernel_id=kernel_id,
            ) if has_runtime else None,
            log=logger,
        )
        logger.info("Starting AI Agent for room [%s]…", room_id)
        async def prompt_task() -> None:
            logger.info('Starting Prompt Agent.')
            await prompt_agent.start()
            if prompt_agent.runtime_client is not None:
                prompt_agent.runtime_client.start()
            logger.info('Prompt Agent is started.')
        async with create_task_group() as tg:
            tg.start_soon(prompt_task)
        AI_AGENTS_MANAGER.register_ai_agent(room_id, prompt_agent)
        # Sleep forever to keep the ai agent alive.
        # TODO Replace with AI_AGENTS_MANAGER
        while True:
           await sleep(10)
#        await AI_AGENTS_MANAGER.track_agent(room_id, prompt_agent)
        return 'Prompt task is finished.'
    with start_blocking_portal() as portal:
        futures = [portal.start_task_soon(long_running_prompt)]
        for future in as_completed(futures):
            logger.info("Future is completed with result [%s]", future.result())


class AIAgentsInstanceHandler(APIHandler):

#    @web.authenticated
    async def get(self, matched_part=None, *args, **kwargs):
        global AI_AGENTS_MANAGER
        if AI_AGENTS_MANAGER is None:
            AI_AGENTS_MANAGER = AIAgentsManager()
        self.write({
            "success": True,
            "matched_part": matched_part,
        })

#    @web.authenticated
    async def post(self, matched_part=None, *args, **kwargs):
        global AI_AGENTS_MANAGER
        if AI_AGENTS_MANAGER is None:
            AI_AGENTS_MANAGER = AIAgentsManager()
        body_data = json.loads(self.request.body)
        logger.info("Body data", body_data)
        self.write({
            "success": True,
            "matched_part": matched_part,
        })


class AIAgentsHandler(APIHandler):

#    @web.authenticated
    async def get(self, *args, **kwargs):
        global AI_AGENTS_MANAGER
        if AI_AGENTS_MANAGER is None:
            AI_AGENTS_MANAGER = AIAgentsManager()
        self.write({
            "success": True,
        })

#    @web.authenticated
    async def post(self, *args, **kwargs):
        """Endpoint creating an AI Agent for a given room."""
        global AI_AGENTS_MANAGER
        if AI_AGENTS_MANAGER is None:
            AI_AGENTS_MANAGER = AIAgentsManager()
        request_body = json.loads(self.request.body)
        agent_request = AgentRequestModel(**request_body)
        self.log.info("AI Agents create handler requested with [%s]", agent_request.model_dump())
        room_id = agent_request.room_id
        if room_id in AI_AGENTS_MANAGER:
            self.log.info("AI Agent for room [%s] already exists.", room_id)
            # TODO check the ai agent.
            return {
                "success": True,
                "message": "AI Agent already exists",
            }
        else:
            self.log.info("Creating AI Agent for room [%s]…", room_id)
            runtime = agent_request.runtime
            jupyter_ingress = runtime.ingress
            jupyter_token = runtime.token
            kernel_id = runtime.kernel_id
            # Start AI Agent in a ThreadPoolExecutor.
            EXECUTOR.submit(prompt_ai_agent, room_id, jupyter_ingress, jupyter_token, kernel_id)
        res = json.dumps({
            "success": True,
            "message": f"AI Agent is started for room '{room_id}'.",
        })
        logger.info("AI Agent create request exiting with reponse [%s]", res)
        self.finish(res)
