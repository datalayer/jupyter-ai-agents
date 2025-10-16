# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

import asyncio
import uuid
from unittest.mock import AsyncMock

from jupyter_nbmodel_client import NbModelClient
from jupyter_ai_agents.models.agent import BaseNbAgent


async def test_default_content(ws_server):
    room = uuid.uuid4().hex
    async with BaseNbAgent(f"{ws_server}/{room}") as agent:
        await asyncio.sleep(0)
        default_content = agent.as_dict()

    assert default_content == {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}


async def test_set_user_prompt(ws_server):
    room = uuid.uuid4().hex
    room_url = f"{ws_server}/{room}"
    async with NbModelClient(room_url) as client:
        async with BaseNbAgent(room_url) as agent:
            agent._on_user_prompt = AsyncMock(return_value="hello")
            idx = client.add_code_cell("print('hello')")
            client.set_cell_metadata(
                idx,
                "datalayer",
                {"ai": {"prompts": [{"id": "12345", "prompt": "Once upon a time"}]}},
            )

            await asyncio.sleep(0.5)

            content = agent.as_dict()
            assert content == {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {
                            "datalayer": {
                                "ai": {
                                    "messages": [
                                        {
                                            "message": "hello",
                                            "parent_id": "12345",
                                            "timestamp": content["cells"][0]["metadata"][
                                                "datalayer"
                                            ]["ai"]["messages"][0]["timestamp"],
                                            "type": 1,
                                        },
                                    ],
                                    "prompts": [{"id": "12345", "prompt": "Once upon a time"}],
                                }
                            }
                        },
                        "outputs": [],
                        "source": "print('hello')",
                        "id": client[idx]["id"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }

            assert agent._on_user_prompt.called
            args, kwargs = agent._on_user_prompt.call_args
            assert args == (
                client[idx]["id"],
                "12345",
                "Once upon a time",
                None,
                None,
            )


async def test_set_cell_with_user_prompt(ws_server):
    room = uuid.uuid4().hex
    room_url = f"{ws_server}/{room}"
    async with NbModelClient(room_url) as client:
        async with BaseNbAgent(room_url) as agent:
            agent._on_user_prompt = AsyncMock()
            client.add_code_cell(
                "print('hello')",
                metadata={
                    "datalayer": {
                        "ai": {"prompts": [{"id": "12345", "prompt": "Once upon a time"}]}
                    }
                },
            )

            await asyncio.sleep(0.5)

            content = agent.as_dict()
            assert content == {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {
                            "datalayer": {
                                "ai": {
                                    "messages": [
                                        {
                                            "message": None,
                                            "parent_id": "12345",
                                            "timestamp": content["cells"][0]["metadata"][
                                                "datalayer"
                                            ]["ai"]["messages"][0]["timestamp"],
                                            "type": 1,
                                        },
                                    ],
                                    "prompts": [{"id": "12345", "prompt": "Once upon a time"}],
                                }
                            }
                        },
                        "outputs": [],
                        "source": "print('hello')",
                        "id": client[0]["id"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }

            assert agent._on_user_prompt.called
            args, kwargs = agent._on_user_prompt.call_args
            assert args == (
                client[0]["id"],
                "12345",
                "Once upon a time",
                None,
                None,
            )
