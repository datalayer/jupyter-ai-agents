<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.io)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# 🪐 ✨ Jupyter AI Agents Examples

## AI Agent Server Example

In the underlying `jupyter-nbmodel-client` library, we define a [specification to set user prompts](https://github.com/datalayer/jupyter-nbmodel-client?tab=readme-ov-file#data-models) in the Notebook metadata.

You can create an AI Agent reacting to a user prompt set through that specification by inheriting from `jupyter_nbmodel_client.BaseNbAgent`.

```bash
# Run the AI Agent.
python ./main.py
```

```py
# Emulate user prompt.
from jupyter_nbmodel_client import get_jupyter_notebook_websocket_url

async with NbModelClient(
    get_datalayer_websocket_url(
        server_url="https://prod1.datalayer.run", # URL to Datalayer Run.
        room_id=room_id,                          # Notebook ID
        token=token,                              # Datalayer JWT authentication token
    )
) as client:
    client.add_code_cell("", metadata={"datalayer": {"ai": {"prompts":[{"id": str(uuid4()), "prompt": "hello"}]}}})
    await asyncio.sleep(0.2)  # The delay may be tuned to ensure the agent got the update and react prior to shutdown.
```
