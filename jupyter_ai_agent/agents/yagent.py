"""This module provides a base class agent to interact with collaborative Jupyter notebook."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Literal, cast
from pycrdt import MapEvent, ArrayEvent

from jupyter_nbmodel_client import NbModelClient


class AIMessageType(IntEnum):
    SUGGESTION = 1
    """Message suggesting a new cell content."""
    EXPLANATION = 2
    """Message explaining a content."""


class BaseYNotebookAgent(NbModelClient):
    def _on_notebook_changes(
        self, part: Literal["state"] | Literal["meta"] | Literal["cells"], changes: Any
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
                        ...
                    elif key == "outputs":
                        ...
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

    def _on_user_prompt(self, cell_id: str, prompt: str) -> None: ...

    def _on_cell_source_changes(self, cell_id: str, new_source: str, old_source: str) -> None: ...

    def _on_cell_outputs_changes(self, *args) -> None:
        print(args)

    def cell_id_to_index(self, cell_id: str) -> int:
        """Find the index of the cell with the given ID.

        If the cell cannot be found it will return -1.

        Args:
            cell_id: str
        Returns:
            Cell index
        """
        for index, cell in enumerate(self):
            if cell["id"] == cell_id:
                return index

        return -1

    def update_document(self, message_type: AIMessageType, message: str, cell_id: str = "") -> None:
        """Update the document.

        Args:
            message_type: Type of message to insert in the document
            message: Message to insert
            cell_id: Cell targeted by the update; if empty, the notebook is the target
        """

    def notify(self, message: str, cell_id: str = "") -> None:
        """Send a transient message to users.

        Args:
            message: Notification message
            cell_id: Cell targeted by the notification; if empty the notebook is the target
        """
