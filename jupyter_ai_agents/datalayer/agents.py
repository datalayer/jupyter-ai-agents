# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import asyncio
import logging
from collections import Counter

from jupyter_ai_agents.agents.base import RuntimeAgent

logger = logging.getLogger(__name__)

SPACER_AGENT = "DatalayerSpacer"

DELAY_FOR_STOPPING_AGENT = 20 * 60
"""Delay in seconds before stopping an agent."""


async def _stop_agent(agent: RuntimeAgent, room: str) -> None:
    try:
        if agent.runtime_client is not None:
            agent.runtime_client.stop()
        await agent.stop()
    except BaseException as e:
        logger.error("Failed to stop AI agent for room [%s].", room, exc_info=e)


class AIAgentManager:
    """AI Agents manager."""

    def __init__(self) -> None:
        self._agents: dict[str, RuntimeAgent] = {}
        self._background_tasks: list[asyncio.Task] = []
        self._agents_to_stop: set[str] = set()
        self._to_stop_counter: Counter[str] = Counter()

        # A usefull task will be set when the first agent is added.
        self._stop_task: asyncio.Task = asyncio.create_task(asyncio.sleep(0))

    def __contains__(self, key: str) -> bool:
        return key in self._agents

    def __getitem__(self, key: str) -> RuntimeAgent:
        return self._agents[key]

    async def _stop_lonely_agents(self) -> None:
        """Periodically check if an agent as connected peer.

        If it the only peer is the spacer server, kill the agent after
        some delay.
        """
        while True:
            await asyncio.sleep(DELAY_FOR_STOPPING_AGENT * 0.25)
            for key, agent in self._agents.items():
                peers = agent.get_connected_peers()
                if len(peers) == 1:
                    peer_state = agent.get_peer_state(peers[0]) or {}
                    if (
                        peer_state.get("user", {})
                        .get("agent", "")
                        .startswith(SPACER_AGENT)
                    ):
                        self._agents_to_stop.add(key)
                        self._to_stop_counter.update([key])

            to_stop = []
            for key, count in self._to_stop_counter.most_common():
                if count < 4:
                    break
                self._agents_to_stop.remove(key)
                to_stop.append(key)

            await asyncio.shield(
                asyncio.gather(
                    *(
                        _stop_agent(self._agents.pop(room), room)
                        for room in to_stop
                        if room in self._agents
                    )
                )
            )
            for key in to_stop:
                self._to_stop_counter.pop(key, None)
                logger.info("AI Agent for room [%s] stopped.", key)

    async def stop_all(self) -> None:
        """Stop all background tasks and reset the state."""
        if self._stop_task.cancel():
            await asyncio.wait([self._stop_task])

        all_tasks = asyncio.gather(*self._background_tasks)
        if all_tasks.cancel():
            await asyncio.wait([all_tasks])

        await asyncio.shield(
            asyncio.gather(
                *(_stop_agent(agent, room) for room, agent in self._agents.items())
            )
        )
        self._agents.clear()
        self._agents_to_stop.clear()
        self._to_stop_counter.clear()

    def get_user_agents(self, user: str) -> list[str]:
        return [k for k, a in self._agents.items() if a._username == user]

    def track_agent(self, key: str, agent: RuntimeAgent) -> None:
        """Add an agent and start it."""
        if self._stop_task.done():
            self._stop_task = asyncio.create_task(self._stop_lonely_agents())

        self._agents[key] = agent
        start = asyncio.create_task(agent.start())
        self._background_tasks.append(start)
        start.add_done_callback(lambda task: self._background_tasks.remove(task))
        if agent.runtime_client is not None:
            agent.runtime_client.start()

    async def forget_agent(self, key: str) -> None:
        if key in self:
            logger.info("Removing AI agent in room [%s].", key)
            agent = self._agents.pop(key)
            if key in self._agents_to_stop:
                self._agents_to_stop.remove(key)
            if key in self._to_stop_counter:
                self._to_stop_counter.pop(key)

            await _stop_agent(agent, key)
