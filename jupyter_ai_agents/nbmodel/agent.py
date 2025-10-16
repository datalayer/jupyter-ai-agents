# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""This module provides a base class AI agent to interact with collaborative Jupyter notebook."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from enum import IntEnum
from logging import Logger
from typing import Any, Literal, TypedDict, cast

from pycrdt import Awareness, Map

from jupyter_nbmodel_client._version import VERSION
from jupyter_nbmodel_client.client import REQUEST_TIMEOUT, NbModelClient


def timestamp() -> int:
    """Return the current timestamp in milliseconds since epoch."""
    return int(datetime.now(timezone.utc).timestamp() * 1000.0)


class AIMessageType(IntEnum):
    """Type of AI agent message."""

    ERROR = -1
    """Error message."""
    ACKNOWLEDGE = 0
    """Prompt is being processed."""
    REPLY = 1
    """AI reply."""


class PeerChanges(TypedDict):
    added: list[int]
    """List of peer ids added."""
    removed: list[int]
    """List of peer ids removed."""
    updated: list[int]
    """List of peer ids updated."""


class PeerEvent(TypedDict):
    # Only trigger on change to avoid high callback pressure
    # type: Literal["change", "update"]
    # """Event type; "change" if the peer state changes, "update" if the peer state is updated even if unchanged."""
    changes: PeerChanges
    """Peer changes."""
    origin: Literal["local"] | str
    """Event origin; "local" if emitted by itself, the peer id otherwise."""


# def _debug_print_changes(part: str, changes: Any) -> None:
#     print(f"{part}")

#     def print_change(changes):
#         if isinstance(changes, MapEvent):
#             print(f"{type(changes.target)} {changes.target} {changes.keys} {changes.path}")
#         elif isinstance(changes, ArrayEvent):
#             print(f"{type(changes.target)} {changes.target} {changes.delta} {changes.path}")
#         else:
#             print(changes)

#     if isinstance(changes, list):
#         for c in changes:
#             print_change(c)
#     else:
#         print_change(changes)


class BaseNbAgent(NbModelClient):
    """Base class to react to user prompt and notebook changes based on CRDT changes.

    Notes:
      - Agents are expected to extend this base class and override either
        - method:`async _on_user_prompt(self, cell_id: str, prompt: str, username: str | None = None) -> str | None`:
            Callback on user prompt, it may return an AI reply and must raise an error in case of failure
        - method:`async _on_cell_source_changes(self, cell_id: str, new_source: str, old_source: str, username: str | None = None) -> None`:
            Callback on cell source changes, it must raise an error in case of failure
      - Agents can sent transient messages to users through the method:`async notify(self, message: str, cell_id: str = "", message_type: AIMessageType = AIMessageType.ACKNOWLEDGE) -> None`

    Args:
        ws_url: Endpoint to connect to the collaborative Jupyter notebook.
        path: [optional] Notebook path relative to the server root directory; default None
        username: [optional] Client user name; default to environment variable USER
        timeout: [optional] Request timeout in seconds; default to environment variable REQUEST_TIMEOUT
        log: [optional] Custom logger; default local logger
        ws_max_body_size: [optional] Maximum WebSocket body size in bytes; default 16MB
        close_timeout: [optional] Timeout for propagating final changes on close; default to timeout value

    Examples:

    When connection to a Jupyter notebook server, you can leverage the get_jupyter_notebook_websocket_url
    helper:

    >>> from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
    >>> client = NbModelClient(
    >>>     get_jupyter_notebook_websocket_url(
    >>>         "http://localhost:8888",
    >>>         "path/to/notebook.ipynb",
    >>>         "your-server-token"
    >>>     )
    >>> )
    """

    user_agent: str = f"Datalayer-BaseNbAgent/{VERSION}"
    """User agent used to identify the nbmodel client type in the awareness state."""

    def __init__(
        self,
        websocket_url: str,
        path: str | None = None,
        username: str = os.environ.get("USER", "username"),
        timeout: float = REQUEST_TIMEOUT,
        log: Logger | None = None,
        ws_max_body_size: int | None = None,
        close_timeout: float | None = None,
    ) -> None:
        super().__init__(websocket_url, path, username, timeout, log, ws_max_body_size, close_timeout)
        self._doc_events: asyncio.Queue[dict] = asyncio.Queue()
        self._peer_events: asyncio.Queue[PeerEvent] = asyncio.Queue()

    async def run(self) -> None:
        self._doc.observe(self._on_notebook_changes)
        awareness_callback = cast(Awareness, self._doc.awareness).observe(self._on_peer_changes)
        doc_events_worker: asyncio.Task | None = None
        peer_events_worker: asyncio.Task | None = None
        try:
            doc_events_worker = asyncio.create_task(self._process_doc_events())
            peer_events_worker = asyncio.create_task(self._process_peer_events())
            await super().run()
        finally:
            self._log.info("Stop the agent.")
            cast(Awareness, self._doc.awareness).unobserve(awareness_callback)
            if doc_events_worker and not doc_events_worker.done():
                if not self._doc_events.empty():
                    await self._doc_events.join()
                if doc_events_worker.cancel():
                    await asyncio.wait([doc_events_worker])
            else:
                try:
                    while True:
                        self._doc_events.get_nowait()
                except asyncio.QueueEmpty:
                    ...

            if peer_events_worker and not peer_events_worker.done():
                if not self._peer_events.empty():
                    await self._peer_events.join()
                if peer_events_worker.cancel():
                    await asyncio.wait([peer_events_worker])
            else:
                try:
                    while True:
                        self._peer_events.get_nowait()
                except asyncio.QueueEmpty:
                    ...

    async def __handle_cell_source_changes(
        self,
        cell_id: str,
        new_source: str,
        old_source: str,
        username: str | None = None,
    ) -> None:
        self._log.info("Process user [%s] cell [%s] source changes.", username, cell_id)

        # # Acknowledge through awareness
        # await self.notify(
        #     "Analyzing source changes…",
        #     cell_id=cell_id,
        # )
        try:
            await self._on_cell_source_changes(cell_id, new_source, old_source, username)
        except asyncio.CancelledError:
            raise
        except BaseException as e:
            error_message = f"Error while analyzing cell source: {e!s}"
            self._log.error(error_message)
            # await self.notify(error_message, cell_id=cell_id, message_type=AIMessageType.ERROR)
        else:
            self._log.info("AI processed successfully cell [%s] source changes.", cell_id)
            # await self.notify(
            #     "Source changes analyzed.",
            #     cell_id=cell_id,
            # )

    async def __handle_user_prompt(
        self,
        cell_id: str,
        prompt_id: str,
        prompt: str,
        username: str | None = None,
        timestamp: int | None = None,
    ) -> None:
        self._log.info("Received user [%s] prompt [%s].", username, prompt_id)
        self._log.debug(
            "Prompt: timestamp [%s] / cell_id [%s] / prompt [%s]",
            timestamp,
            cell_id,
            prompt[:20],
        )

        # Acknowledge
        await self.save_ai_message(
            AIMessageType.ACKNOWLEDGE,
            "Requesting AI…",
            cell_id=cell_id,
            parent_id=prompt_id,
        )
        try:
            reply = await self._on_user_prompt(cell_id, prompt_id, prompt, username, timestamp)
        except asyncio.CancelledError:
            await self.save_ai_message(
                AIMessageType.ERROR,
                "Prompt request cancelled.",
                cell_id=cell_id,
                parent_id=prompt_id,
            )
            raise
        except BaseException as e:
            error_message = "Error while processing user prompt"
            self._log.error(error_message + " [%s].", prompt_id, exc_info=e)
            await self.save_ai_message(
                AIMessageType.ERROR,
                error_message + f": {e!s}",
                cell_id=cell_id,
                parent_id=prompt_id,
            )
        else:
            self._log.info("AI replied successfully to prompt [%s]: [%s]", prompt_id, reply)
            if reply is not None:
                await self.save_ai_message(
                    AIMessageType.REPLY, reply, cell_id=cell_id, parent_id=prompt_id
                )
            else:
                await self.save_ai_message(
                    AIMessageType.ACKNOWLEDGE,
                    "AI has successfully processed the prompt.",
                    cell_id=cell_id,
                    parent_id=prompt_id,
                )

    async def _process_doc_events(self) -> None:
        self._log.debug("Starting listening on document [%s] changes…", self.path)
        while True:
            try:
                event = await self._doc_events.get()
                event_type = event.pop("type")
                if event_type == "user":
                    await self.__handle_user_prompt(**event)
                if event_type == "source":
                    await self.__handle_cell_source_changes(**event)
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                self._log.error("Error while processing document events: %s", exc_info=e)
            else:
                # Sleep to get a chance to propagate changes through the websocket
                await asyncio.sleep(0)

    def _on_notebook_changes(
        self,
        part: Literal["state"] | Literal["meta"] | Literal["cells"] | str,
        all_changes: Any,
    ) -> None:
        # _debug_print_changes(part, all_changes)

        if part == "cells":
            for changes in all_changes:
                transaction_origin = changes.transaction.origin
                if transaction_origin == self._changes_origin:
                    continue
                else:
                    self._log.debug(
                        "Document changes from origin [%s] != agent origin [%s].",
                        transaction_origin,
                        self._changes_origin,
                    )
                path_length = len(changes.path)
                if path_length == 0:
                    # Change is on the cell list
                    for delta in changes.delta:
                        if "insert" in delta:
                            # New cells got added
                            for cell in delta["insert"]:
                                if "metadata" in cell:
                                    new_metadata = cell["metadata"]
                                    datalayer_ia = new_metadata.get("datalayer", {}).get("ai", {})
                                    prompts = datalayer_ia.get("prompts", [])
                                    prompt_ids = {prompt["id"] for prompt in prompts}
                                    new_prompts = prompt_ids.difference(
                                        message["parent_id"]
                                        for message in datalayer_ia.get("messages", [])
                                    )
                                    if new_prompts:
                                        for prompt in filter(
                                            lambda p: p.get("id") in new_prompts,
                                            prompts,
                                        ):
                                            self._doc_events.put_nowait(
                                                {
                                                    "type": "user",
                                                    "cell_id": cell["id"],
                                                    "prompt_id": prompt["id"],
                                                    "prompt": prompt["prompt"],
                                                    "username": prompt.get("user"),
                                                    "timestamp": prompt.get("timestamp"),
                                                }
                                            )
                                if "source" in cell:
                                    self._doc_events.put_nowait(
                                        {
                                            "type": "source",
                                            "cell_id": cell["id"],
                                            "new_source": cell["source"].to_py(),
                                            "old_source": "",
                                        }
                                    )
                elif path_length == 1:
                    # Change is on one cell
                    for key, change in changes.keys.items():
                        if key == "source":
                            if change["action"] == "add":
                                self._doc_events.put_nowait(
                                    {
                                        "type": "source",
                                        "cell_id": changes.target["id"],
                                        "new_source": change["newValue"],
                                        "old_source": change.get("oldValue", ""),
                                    }
                                )
                            elif change["action"] == "update":
                                self._doc_events.put_nowait(
                                    {
                                        "type": "source",
                                        "cell_id": changes.target["id"],
                                        "new_source": change["newValue"],
                                        "old_source": change["oldValue"],
                                    }
                                )
                            elif change["action"] == "delete":
                                self._doc_events.put_nowait(
                                    {
                                        "type": "source",
                                        "cell_id": changes.target["id"],
                                        "new_source": change.get("newValue", ""),
                                        "old_source": change["oldValue"],
                                    }
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
                                for prompt in filter(lambda p: p.get("id") in new_prompts, prompts):
                                    self._doc_events.put_nowait(
                                        {
                                            "type": "user",
                                            "cell_id": changes.target["id"],
                                            "prompt_id": prompt["id"],
                                            "prompt": prompt["prompt"],
                                            "username": prompt.get("user"),
                                            "timestamp": prompt.get("timestamp"),
                                        }
                                    )
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
                        if key == "datalayer":
                            new_metadata = change.get("newValue", {})
                            datalayer_ia = new_metadata.get("ai", {})
                            prompts = datalayer_ia.get("prompts")
                            prompt_ids = {prompt["id"] for prompt in prompts}
                            new_prompts = prompt_ids.difference(
                                message["parent_id"] for message in datalayer_ia.get("messages", [])
                            )
                            if new_prompts and change["action"] in {"add", "update"}:
                                for prompt in filter(lambda p: p.get("id") in new_prompts, prompts):
                                    self._doc_events.put_nowait(
                                        {
                                            "type": "user",
                                            "cell_id": self._doc.ycells[changes.path[0]]["id"],
                                            "prompt_id": prompt["id"],
                                            "prompt": prompt["prompt"],
                                            "username": prompt.get("user"),
                                            "timestamp": prompt.get("timestamp"),
                                        }
                                    )
                            # elif change["action"] == "delete":
                            #     ...

        # elif part == "meta":
        #     # FIXME handle notebook metadata

    def _reset_y_model(self) -> None:
        try:
            self._doc.unobserve()
        except AttributeError:
            pass
        finally:
            super()._reset_y_model()

    async def _on_user_prompt(
        self,
        cell_id: str,
        prompt_id: str,
        prompt: str,
        username: str | None = None,
        timestamp: int | None = None,
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
        username = username or self._username
        self._log.debug("New AI prompt sets by user [%s] in [%s]: [%s].", username, cell_id, prompt)

    async def _on_cell_source_changes(
        self,
        cell_id: str,
        new_source: str,
        old_source: str,
        username: str | None = None,
    ) -> None:
        username = username or self._username
        self._log.debug("New cell source sets by user [%s] in [%s].", username, cell_id)

    # async def _on_cell_outputs_changes(self, *args) -> None:
    #     print(args)

    async def _process_peer_events(self) -> None:
        while True:
            try:
                event = await self._peer_events.get()
                await self._on_peer_event(event)
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                self._log.error("Error while processing peer events: %s", exc_info=e)
            else:
                # Sleep to get a chance to propagate changes through the websocket
                await asyncio.sleep(0)

    def _on_peer_changes(self, event_type: str, changes: tuple[dict, Any]) -> None:
        if event_type != "udpate":
            self._peer_events.put_nowait(
                cast(PeerEvent, {"changes": changes[0], "origin": changes[1]})
            )

    async def _on_peer_event(self, event: PeerEvent) -> None:
        """Callback on peer awareness events."""
        self._log.debug(
            "New event from peer [%s]: %s", event["origin"], event["changes"]
        )

    def get_cell(self, cell_id: str) -> Map | None:
        """Find the cell with the given ID.

        If the cell cannot be found it will return ``None``.

        Args:
            cell_id: str
        Returns:
            Cell or None
        """
        for cell in self._doc.ycells:
            if cell["id"] == cell_id:
                return cast(Map, cell)

        return None

    def get_cell_index(self, cell_id: str) -> int:
        """Find the cell with the given ID.

        If the cell cannot be found it will return ``-1``.

        Args:
            cell_id: str
        Returns:
            Cell index or -1
        """
        for index, cell in enumerate(self._doc.ycells):
            if cell["id"] == cell_id:
                return index

        return -1

    async def save_ai_message(
        self,
        message_type: AIMessageType,
        message: str,
        cell_id: str = "",
        parent_id: str | None = None,
    ) -> None:
        """Update the document.

        If a message with the same ``parent_id`` already exists, it will be
        overwritten.

        Args:
            message_type: Type of message to insert in the document
            message: Message to insert
            cell_id: Cell targeted by the update; if empty, the notebook is the target
            parent_id: Parent message id
        """
        message_dict = {
            "parent_id": parent_id,
            "message": message,
            "type": int(message_type),
            "timestamp": timestamp(),
        }

        def set_message(metadata: dict, message: dict):
            dla = metadata.get("datalayer") or {"ai": {"prompts": [], "messages": []}}
            dlai = dla.get("ai", {"prompts": [], "messages": []})
            dlmsg = dlai.get("messages", [])

            messages = list(
                filter(
                    lambda m: not m.get("parent_id") or m["parent_id"] != parent_id,
                    dlmsg,
                )
            )
            messages.append(message)
            dlai["messages"] = messages
            dla["ai"] = dlai
            if "datalayer" in metadata:
                del metadata["datalayer"]  # FIXME upstream - update of key is not possible 😱
            metadata["datalayer"] = dla.copy()

        if cell_id:
            cell = self.get_cell(cell_id)
            if not cell:
                raise ValueError(f"Cell [{cell_id}] not found.")
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                if "metadata" not in cell:
                    cell["metadata"] = Map({"datalayer": {"ai": {"prompts": [], "messages": []}}})
                set_message(cell["metadata"], message_dict)
            self._log.debug("Add ai message in cell [%s] metadata: [%s].", cell_id, message_dict)

        else:
            notebook_metadata = self._doc._ymeta["metadata"]
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                set_message(notebook_metadata, message_dict)
            self._log.debug("Add ai message in notebook metadata: [%s].", cell_id, message_dict)

        # Sleep to get a chance to propagate the changes through the websocket
        await asyncio.sleep(0)

    async def notify(
        self,
        message: str,
        cell_id: str = "",
        message_type: AIMessageType = AIMessageType.ACKNOWLEDGE,
    ) -> None:
        """Send a transient message to users.

        Args:
            message: Notification message
            cell_id: Cell targeted by the notification; if empty the notebook is the target
        """
        self.set_local_state_field(
            "notification",
            {
                "message": message,
                "message_type": message_type,
                "timestamp": timestamp(),
                "cell_id": cell_id,
            },
        )
        # Sleep to get a chance to propagate the changes through the websocket
        await asyncio.sleep(0)
