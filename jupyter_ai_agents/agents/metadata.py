# Copyright (c) 2023-2024 Datalayer, Inc.
#
# Datalayer License

from __future__ import annotations

import logging
import os
from logging import Logger

from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import BaseNbAgent
from jupyter_nbmodel_client.constants import REQUEST_TIMEOUT
from langchain.agents import tool

from jupyter_ai_agents.agents import prompt as prompt_agent
from jupyter_ai_agents.providers.azure_openai import create_azure_openai_agent
from jupyter_ai_agents.tools import (
    insert_execute_code_cell_tool,
    insert_markdown_cell_tool,
)

AZURE_MODEL_NAME = "gpt-40-mini"

logger = logging.getLogger(__name__)


class RuntimeAgent(BaseNbAgent):
    """A base notebook agent connected to a runtime client."""

    def __init__(
        self,
        websocket_url: str,
        path: str | None = None,
        runtime_client: KernelClient | None = None,
        username: str = os.environ.get("USER", "username"),
        timeout: float = REQUEST_TIMEOUT,
        log: Logger | None = None,
    ) -> None:
        super().__init__(websocket_url, path, username, timeout, log)
        self._runtime_client: KernelClient | None = runtime_client

    @property
    def runtime_client(self) -> KernelClient | None:
        """Runtime client"""
        return self._runtime_client

    @runtime_client.setter
    def runtime_client(self, client: KernelClient) -> None:
        self._runtime_client = client

    async def stop(self) -> None:
        await super().stop()
        if self._runtime_client:
            self._runtime_client.stop()


class PromptAgent(RuntimeAgent):
    """AI Agent replying to user prompt."""

    async def _on_user_prompt(
        self,
        cell_id: str,
        prompt_id: str,
        prompt: str,
        username: str | None = None,
        timestamp: int | None = None,
        **kwargs,
    ) -> str | None:
        """Callback on user prompt.

        Args:
            cell_id: Cell ID on which an user prompt is set; empty if the user prompt is at the notebook level.
            prompt_id: Prompt unique ID
            prompt: User prompt
            username: User name
            timestamp: Prompt creation timestamp

        Returns:
            Optional agent reply to display to the user.
        """
        document_client = self
        runtime_client = self.runtime_client

        @tool("insert_execute_code_cell")
        def insert_execute_code_cell(cell_index: int, cell_content: str) -> str:
            """Add a Python code cell to the notebook at the given index with a content and execute it."""
            insert_execute_code_cell_tool(document_client, runtime_client, cell_content, cell_index)
            return "Code cell added and executed."

        @tool("insert_markdown_cell")
        def insert_markdown_cell(cell_index: int, cell_content: str) -> str:
            """Add a Markdown cell to the notebook at the given index with a content."""
            insert_markdown_cell_tool(document_client, cell_content, cell_index)
            return "Markdown cell added."

        tools = [] if runtime_client is None else [insert_execute_code_cell, insert_markdown_cell]

        system_prompt_enriched = prompt_agent.SYSTEM_PROMPT
        current_cell_index = self.get_cell_index(cell_id)

        if current_cell_index != -1:
            system_prompt_final = f"""
            {system_prompt_enriched}
            
            Cell index on which the user instruction was given: {current_cell_index}
            """
        else:
            system_prompt_final = system_prompt_enriched

        self._log.debug(str(os.environ))
        agent_executor = create_azure_openai_agent(AZURE_MODEL_NAME, system_prompt_final, tools)

        output = None

        async for reply in agent_executor.astream({"input": prompt}):
            output = reply.get("output", "")
            if not output:
                output = reply["messages"][-1].content
            self._log.debug("Got a reply for prompt [%s]: [%s].", prompt_id, (output or "")[:30])
        return output
