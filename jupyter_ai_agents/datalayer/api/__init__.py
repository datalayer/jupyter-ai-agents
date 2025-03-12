# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import logging
import contextlib
import typing
import httpx
import os
import re

from pydantic import BaseModel
from typing import Optional

from http import HTTPStatus
from urllib.parse import urlencode

from fastapi import APIRouter, Request

from jupyter_kernel_client import KernelClient

from jupyter_ai_agents.agents.prompt import PromptAgent
from jupyter_ai_agents.utils import http_to_ws
from jupyter_ai_agents import __version__

from datalayer_core.authn.apps.whoamiapp import WhoamiApp


logger = logging.getLogger(__name__)


router = APIRouter()


DATALAYER_RUN_URL = os.environ.get("DATALAYER_RUN_URL", "https://prod1.datalayer.run")
DATALAYER_RUN_WS_URL = http_to_ws(DATALAYER_RUN_URL)
DATALAYER_RTC_ROOM_WS_URL = os.environ.get(
    "DATALAYER_RTC_ROOM_WS_URL",
    f"{DATALAYER_RUN_WS_URL}/api/spacer/v1/rooms"
)


ROOMS = {}


class RuntimeModel(BaseModel):
    ingress: Optional[str] = None
    token: Optional[str] = None
    kernel_id: Optional[str] = None
    jupyter_pod_name: Optional[str] = None


class AgentRequestModel(BaseModel):
    room_id: Optional[str] = None
    runtime: Optional[RuntimeModel] = None


@contextlib.asynccontextmanager
async def _get_client(
    token: str | None = None,
) -> typing.AsyncIterator[httpx.AsyncClient]:
    headers = {
        "User-Agent": f"datalayer-ai-agents/{__version__}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(headers=headers) as client:
        yield client


async def _fetch_session_id(url: str, token: str | None = None) -> str:
    """Fetch the room session ID.

    Args:
        url: URL to fetch the session ID from.
    """
    async with _get_client(token) as client:
        response = await client.get(url)
        response.raise_for_status()
    data = response.json()
    session_id = data.get("sessionId") if data.get("success", False) else ""

    if not session_id:
        emsg = f"Failed to fetch session_id: {data.get('message', '')}"
        raise ValueError(emsg)

    return session_id


@router.get("/v1/agents", summary="Get a AI Agent")
async def get_ai_agents_endpoint(request: Request = None):

    authorization = request.headers.get("Authorization", "")
    token = re.sub(r"^(B|b)earer\s+", "", authorization).strip()
    whoami = WhoamiApp(token=token)
    user = whoami.get_profile()

    agents = request.state.agent_manager
    user_agents = agents.get_user_agents(user["uid"])

    return {
        "success": True,
        "message": "AI agents spawned by the user.",
        "agents": [
            {"room_id": a.path, "runtime": {"ingress": a.runtime_client.server_url}}
            for a in user_agents
        ],
    }, HTTPStatus.OK


@router.post("/v1/agents", summary="Create a AI Agent")
async def create_ai_agents_endpoint(
    agent_request: AgentRequestModel,
    request: Request = None,
) -> dict:
    """Endpoint creating an AI agent for a given room."""
    
    logger.info("Create AI Agents is requested", agent_request.model_dump())

    agents = request.state.agent_manager

    room_id = agent_request.room_id

    if room_id in agents:
        logger.info("AI agent for room [%s] already exists.", room_id)
        # TODO check agent

        return {
            "success": True,
            "message": "AI agent already exists",
        }
    else:
        logger.info("Creating AI agent for room [%s]…", room_id)
        authorization = request.headers.get("Authorization", "")
        token = re.sub(r"^(B|b)earer\s+", "", authorization).strip()

        whoami = WhoamiApp(token=token)
        user = whoami.get_profile()["profile"]

        runtime = agent_request.runtime
        jupyter_ingress = runtime.ingress
        jupyter_token = runtime.token
        kernel_id = runtime.kernel_id
        has_runtime = jupyter_ingress and jupyter_token and kernel_id

        # 1. Fetch room session id
        try:
            url = re.sub(r"^ws", "http", DATALAYER_RTC_ROOM_WS_URL) + f"/{room_id}"
            session_id = await _fetch_session_id(url, token)
        except ValueError as e:
            return {"success": False, "message": str(e)}, HTTPStatus.BAD_REQUEST

        # 2. Start AI Agent
        qs = urlencode({"sessionId": session_id, "token": token})
        ws_url = f"{DATALAYER_RTC_ROOM_WS_URL}/{room_id}?{qs}"
        agent_request = PromptAgent(
            websocket_url=ws_url,
            username=user["uid"],
            path=room_id,
            runtime_client=KernelClient(
                kernel_id=kernel_id,
                server_url=jupyter_ingress,
                token=jupyter_token,
                username=user["uid"],
            )
            if has_runtime
            else None,
            log=logger,
        )
        logger.info("Starting AI agent for room [%s]…", room_id)
        agents.track_agent(room_id, agent_request)

    return {
        "success": True,
        "message": f"AI agent started for room '{room_id}'.",
    }


@router.get("/v1/ping", summary="Healthz ping")
async def ping_endpoint():
    logger.info("Ping")
    return { "ping": True }
