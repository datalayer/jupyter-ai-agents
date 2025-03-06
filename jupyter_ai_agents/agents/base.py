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
        if self._runtime_client:
            self._runtime_client.stop()
        self._runtime_client = client

    async def stop(self) -> None:
        await super().stop()
        if self._runtime_client:
            self._runtime_client.stop()


