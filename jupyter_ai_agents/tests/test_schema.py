# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""The labextension's settings schema (STUDIO A-19)."""

import json
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[2] / "schema" / "plugin.json"


def test_agent_chat_enabled_is_off_by_default():
    """Talking to deployed applications is a boolean setting, off by default."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    setting = schema["properties"]["agentChatEnabled"]
    assert setting["type"] == "boolean"
    assert setting["default"] is False


def test_acp_agent_enabled_is_off_by_default():
    """A runtime's harness over ACP (SHIELD SH-49) is a boolean setting, off by default."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    setting = schema["properties"]["acpAgentEnabled"]
    assert setting["type"] == "boolean"
    assert setting["default"] is False
