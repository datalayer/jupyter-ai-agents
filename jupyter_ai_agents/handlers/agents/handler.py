# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

# Copyright (c) 2021-2024 Datalayer, Inc.
#
# Datalayer License

from __future__ import annotations

import json
import logging

from pydantic import BaseModel
from typing import Optional

from concurrent import futures
from concurrent.futures import as_completed

from anyio import create_task_group, sleep
from anyio.from_thread import start_blocking_portal

from jupyter_kernel_client import KernelClient

from jupyter_server.utils import url_path_join
from jupyter_server.base.handlers import APIHandler

from jupyter_ai_agents import __version__
from jupyter_ai_agents.agents.prompt import PromptAgent
from jupyter_ai_agents.handlers.agents.agents import AIAgentsManager
from jupyter_ai_agents.utils import http_to_ws


logger = logging.getLogger(__name__)

EXECUTOR = futures.ThreadPoolExecutor(8)

MANAGER = None

ROOMS = {}


def prompt_ai_agent(room_id, jupyter_ingress, jupyter_token, kernel_id):
    async def long_running_prompt():
        global MANAGER
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
        async def sometask() -> None:
            print('Task running')
            await prompt_agent.start()
            if prompt_agent.runtime_client is not None:
                prompt_agent.runtime_client.start()
            print('Task finished')
        async with create_task_group() as tg:
            tg.start_soon(sometask)
        await sleep(20)
#        await MANAGER.track_agent(room_id, prompt_agent)
        print('Task running...')
        return 'Task return value'
    with start_blocking_portal() as portal:
        futures = [portal.start_task_soon(long_running_prompt)]
        for future in as_completed(futures):
            print(future.result())


class RuntimeModel(BaseModel):
    ingress: Optional[str] = None
    token: Optional[str] = None
    kernel_id: Optional[str] = None
    jupyter_pod_name: Optional[str] = None


class AgentRequestModel(BaseModel):
    room_id: Optional[str] = None
    runtime: Optional[RuntimeModel] = None


class AIAgentHandler(APIHandler):

#    @web.authenticated
    async def get(self, matched_part=None, *args, **kwargs):
        global MANAGER
        if MANAGER is None:
            MANAGER = AIAgentsManager()
        self.write({
            "success": True,
            "matched_part": matched_part,
        })

#    @web.authenticated
    async def post(self, matched_part=None, *args, **kwargs):
        global MANAGER
        if MANAGER is None:
            MANAGER = AIAgentsManager()
        body_data = json.loads(self.request.body)
        print(body_data)
        self.write({
            "success": True,
            "matched_part": matched_part,
        })


class AIAgentsHandler(APIHandler):

#    @web.authenticated
    async def get(self, *args, **kwargs):
        global MANAGER
        if MANAGER is None:
            MANAGER = AIAgentsManager()
        self.write({
            "success": True,
        })

#    @web.authenticated
    async def post(self, *args, **kwargs):
        """Endpoint creating an AI Agent for a given room."""
        global MANAGER
        if MANAGER is None:
            MANAGER = AIAgentsManager()
        request_body = json.loads(self.request.body)
        agent_request = AgentRequestModel(**request_body)
        self.log.info("Create AI Agents is requested [%s]", agent_request.model_dump())
        room_id = agent_request.room_id
        if room_id in MANAGER:
            self.log.info("AI Agent for room [%s] already exists.", room_id)
            # TODO check agent
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
            # Start AI Agent
            EXECUTOR.submit(prompt_ai_agent, room_id, jupyter_ingress, jupyter_token, kernel_id)
        res = json.dumps({
            "success": True,
            "message": f"AI Agent started for room '{room_id}'.",
        })
        print(res)
        self.finish(res)
