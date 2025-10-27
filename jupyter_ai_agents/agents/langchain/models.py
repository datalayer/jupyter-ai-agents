# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RuntimeModel(BaseModel):
    ingress: Optional[str] = None
    token: Optional[str] = None
    kernel_id: Optional[str] = None
    jupyter_pod_name: Optional[str] = None


class NbModelAgentRequestModel(BaseModel):
    room_id: Optional[str] = None
    runtime: Optional[RuntimeModel] = None
