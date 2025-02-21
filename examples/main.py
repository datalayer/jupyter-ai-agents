# Copyright (c) 2023-2024 Datalayer, Inc.
#
# Datalayer License

from __future__ import annotations

import asyncio
import os

from .agent_example import PromptAgent

from jupyter_nbmodel_client import get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient


async def main():
    websocket_url = get_jupyter_notebook_websocket_url(
        server_url="http://localhost:8888",
        token="MY_TOKEN",
        path="test.ipynb"
    )
    with KernelClient(server_url="http://localhost:8888", token="MY_TOKEN") as kernel:
        async with PromptAgent(
            websocket_url = websocket_url,
            path = "test.ipynb",
            runtime_client = kernel,
            username = os.environ.get("USER", "username"),
        ):
            while True:
                await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
