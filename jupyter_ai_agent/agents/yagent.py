# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""This module provides a base class agent to interact with collaborative Jupyter notebook."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Literal, cast

from jupyter_nbmodel_client import NbModelClient
from pycrdt import Map


class AIMessageType(IntEnum):
    ACKNOWLEDGE = 0
    """Prompt is being processed."""
    SUGGESTION = 1
    """Message suggesting a new cell content."""
    EXPLANATION = 2
    """Message explaining a content."""


class BaseYNotebookAgent(NbModelClient):
    # FIXME implement username retrieval

    def _on_notebook_changes(
        self, part: Literal["state"] | Literal["meta"] | Literal["cells"] | str, changes: Any
    ) -> None:
        if part == "cells":
            path_length = len(changes.path)
            if path_length == 0:
                # TODO Change is on the cell list
                # for delta in changes.delta:
                ...
            elif path_length == 1:
                # Change is on one cell
                for key, change in changes.keys.items():
                    if key == "source":
                        if change["action"] == "add":
                            self._on_cell_source_changes(
                                changes.target["id"], change["newValue"], change.get("oldValue", "")
                            )
                        elif change["action"] == "update":
                            self._on_cell_source_changes(
                                changes.target["id"], change["newValue"], change["oldValue"]
                            )
                        elif change["action"] == "delete":
                            self._on_cell_source_changes(
                                changes.target["id"], change.get("newValue"), change["oldValue"]
                            )
                    elif key == "metadata":
                        new_metadata = change.get("newValue", {})
                        datalayer_ia = new_metadata.get("datalayer", {}).get("ai", {})
                        prompts = datalayer_ia.get("prompts", [])
                        prompt_ids = {prompt["id"] for prompt in prompts}
                        new_prompts = prompt_ids.difference(
                            message["parent_id"] for message in datalayer_ia.get("messages", [])
                        )
                        if new_prompts and change["action"] in {"add", "update"}:
                            for prompt in filter(lambda p: p.get("id"), prompts):
                                self._on_user_prompt(changes.target["id"], prompt)
                        # elif change["action"] == "delete":
                        #     ...
                    # elif key == "outputs":
                    #     # TODO
                    #     ...
            elif (
                path_length == 2
                and isinstance(changes.path[0], int)
                and changes.path[1] == "metadata"
            ):
                # Change in cell metadata
                for key, change in changes.keys.items():
                    if key != "datalayer":
                        new_metadata = change.get("newValue", {})
                        datalayer_ia = new_metadata.get("ai", {})
                        prompt = datalayer_ia.get("prompt")
                        messages = datalayer_ia.get("messages")
                        if prompt and not messages and change["action"] in {"add", "update"}:
                            self._on_user_prompt(changes.target["id"], prompt)
                        # elif change["action"] == "delete":
                        #     ...

        # elif part == "meta":
        #     # FIXME handle notebook metadata

        # print(f"{part}")

        # def print_change(changes):
        #     if isinstance(changes, MapEvent):
        #         print(f"{type(changes.target)} {changes.target} {changes.keys} {changes.path}")
        #     elif isinstance(changes, ArrayEvent):
        #         print(f"{type(changes.target)} {changes.target} {changes.delta} {changes.path}")
        #     else:
        #         print(changes)

        # if isinstance(changes, list):
        #     for c in changes:
        #         print_change(c)
        # else:
        #     print_change(changes)

    def _reset_y_model(self) -> None:
        self._doc.unobserve()
        super()._reset_y_model()
        self._doc.observe(self._on_notebook_changes)

    def _on_user_prompt(self, cell_id: str, prompt: str, username: str | None = None) -> None:
        username = username or self._username
        self._log.debug("New AI prompt sets by user [%s] in [%s]: [%s].", username, cell_id, prompt)

    def _on_cell_source_changes(
        self, cell_id: str, new_source: str, old_source: str, username: str | None = None
    ) -> None:
        username = username or self._username
        self._log.debug("New cell source sets by user [%s] in [%s].", username, cell_id, new_source)

    # def _on_cell_outputs_changes(self, *args) -> None:
    #     print(args)

    def get_cell(self, cell_id: str) -> Map | None:
        """Find the cell with the given ID.

        If the cell cannot be found it will return ``None``.

        Args:
            cell_id: str
        Returns:
            Cell or None
        """
        for index, cell in enumerate(self):
            if cell["id"] == cell_id:
                return cast(Map, self._doc.ycells[index])

        return None

    def update_document(
        self, prompt: dict, message_type: AIMessageType, message: str, cell_id: str = ""
    ) -> None:
        """Update the document.

        Args:
            prompt: User prompt
            message_type: Type of message to insert in the document
            message: Message to insert
            cell_id: Cell targeted by the update; if empty, the notebook is the target
        """
        message_dict = {"parent_id": prompt["id"], "message": message, "type": message_type}

        def set_message(metadata: Map, message: dict):
            if "datalayer" not in metadata:
                metadata["datalayer"] = {"ai": {"prompts": [], "messages": []}}
            elif "ai" not in metadata["datalayer"]:
                metadata["datalayer"] = {"ai": {"prompts": [], "messages": []}}
            elif "messages" not in metadata["datalayer"]["ai"]:
                metadata["datalayer"]["ai"] = {"messages": []}

            metadata["datalayer"]["ai"]["messages"].append(message)

            metadata["datalayer"] = metadata["datalayer"].copy()

        if cell_id:
            cell = self.get_cell(cell_id)
            if not cell:
                raise ValueError(f"Cell [{cell_id}] not found.")
            if "metadata" not in cell:
                cell["metadata"] = Map({"datalayer": {"ai": {"prompts": [], "messages": []}}})
            set_message(cell["metadata"], message_dict)

        else:
            notebook_metadata = self._doc._ymeta["metadata"]
            set_message(notebook_metadata, message_dict)

    # def notify(self, message: str, cell_id: str = "") -> None:
    #     """Send a transient message to users.

    #     Args:
    #         message: Notification message
    #         cell_id: Cell targeted by the notification; if empty the notebook is the target
    #     """
