# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import typer
import asyncio
import os

from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

from jupyter_ai_agents.agents.langchain.prompt_agent import prompt as prompt_agent
from jupyter_ai_agents.agents.langchain.explain_error_agent import explain_error as explain_error_agent


app = typer.Typer(help="The Jupyter AI Agents application.")


@app.command()
def prompt(
    url: str = typer.Option("http://localhost:8888", help="URL to the Jupyter Server."),
    token: str = typer.Option("", help="Jupyter Server token."),
    path: str = typer.Option("", help="Jupyter Notebook path."),
    agent: str = typer.Option("prompt", help="Agent name."),
    input: str = typer.Option("", help="Input."),
    model_provider: str = typer.Option("github-copilot", help="Model provider can be 'azure-openai', 'github-copilot', or 'openai'."),
    openai_api_version: str = typer.Option(os.environ.get("OPENAI_API_VERSION", None), help="OpenAI API version."),
    azure_openai_version: str = typer.Option(os.environ.get("AZURE_OPENAI_VERSION", None), help="Azure OpenAI version."),
    azure_openai_api_key: str = typer.Option(os.environ.get("AZURE_OPENAI_API_KEY", None), help="Azure OpenAI key."),
    openai_api_key: str = typer.Option(os.environ.get("OPENAI_API_KEY", None), help="OpenAI API key."),
    anthropic_api_key: str = typer.Option(os.environ.get("ANTHROPIC_API_KEY", None), help="Anthropic API key."),
    github_token: str = typer.Option(os.environ.get("GITHUB_TOKEN", None), help="Github token."),
    model_name: str = typer.Option("gpt-4o", help="Model name (deployment name for Azure/OpenAI/Copilot)."),
    current_cell_index: int = typer.Option(-1, help="Index of the cell where the prompt is asked."),
    full_context: bool = typer.Option(False, help="Flag to provide the full notebook context to the AI model."),
):
    """From a given instruction, code and markdown cells are added to a notebook."""
    async def _run():
        kernel = KernelClient(server_url=url, token=token)
        kernel.start()
        notebook = NbModelClient(get_jupyter_notebook_websocket_url(server_url=url, token=token, path=path))
        await notebook.start()
        try:
            reply = await prompt_agent(notebook, kernel, input, model_provider, model_name, full_context, current_cell_index)
            # Print only the final summary or message
            if isinstance(reply, list) and reply:
                last = reply[-1]
                if isinstance(last, dict) and 'output' in last:
                    typer.echo(last['output'])
                elif isinstance(last, dict) and 'messages' in last and last['messages']:
                    # LangChain style: last message content
                    msg = last['messages'][-1]
                    if hasattr(msg, 'content'):
                        typer.echo(msg.content)
                    elif isinstance(msg, dict) and 'content' in msg:
                        typer.echo(msg['content'])
                    else:
                        typer.echo(msg)
                else:
                    typer.echo(last)
            else:
                typer.echo(reply)
        finally:
            await notebook.stop()
            kernel.stop()
    asyncio.run(_run())

@app.command()
def explain_error(
    url: str = typer.Option("http://localhost:8888", help="URL to the Jupyter Server."),
    token: str = typer.Option("", help="Jupyter Server token."),
    path: str = typer.Option("", help="Jupyter Notebook path."),
    agent: str = typer.Option("prompt", help="Agent name."),
    input: str = typer.Option("", help="Input."),
    model_provider: str = typer.Option("github-copilot", help="Model provider can be 'azure-openai', 'github-copilot', or 'openai'."),
    openai_api_version: str = typer.Option(os.environ.get("OPENAI_API_VERSION", None), help="OpenAI API version."),
    azure_openai_version: str = typer.Option(os.environ.get("AZURE_OPENAI_VERSION", None), help="Azure OpenAI version."),
    azure_openai_api_key: str = typer.Option(os.environ.get("AZURE_OPENAI_API_KEY", None), help="Azure OpenAI key."),
    openai_api_key: str = typer.Option(os.environ.get("OPENAI_API_KEY", None), help="OpenAI API key."),
    anthropic_api_key: str = typer.Option(os.environ.get("ANTHROPIC_API_KEY", None), help="Anthropic API key."),
    github_token: str = typer.Option(os.environ.get("GITHUB_TOKEN", None), help="Github token."),
    model_name: str = typer.Option("gpt-4o", help="Model name (deployment name for Azure/OpenAI/Copilot)."),
    current_cell_index: int = typer.Option(-1, help="Index of the cell where the prompt is asked."),
):
    """Explain and correct an error in a notebook based on the prior cells."""
    async def _run():
        kernel = KernelClient(server_url=url, token=token)
        kernel.start()
        notebook = NbModelClient(get_jupyter_notebook_websocket_url(server_url=url, token=token, path=path))
        await notebook.start()
        try:
            reply = await explain_error_agent(notebook, kernel, model_provider, model_name, current_cell_index)
            # Print only the final summary or message
            if isinstance(reply, list) and reply:
                last = reply[-1]
                if isinstance(last, dict) and 'output' in last:
                    typer.echo(last['output'])
                elif isinstance(last, dict) and 'messages' in last and last['messages']:
                    msg = last['messages'][-1]
                    if hasattr(msg, 'content'):
                        typer.echo(msg.content)
                    elif isinstance(msg, dict) and 'content' in msg:
                        typer.echo(msg['content'])
                    else:
                        typer.echo(msg)
                else:
                    typer.echo(last)
            else:
                typer.echo(reply)
        finally:
            await notebook.stop()
            kernel.stop()
    asyncio.run(_run())


def main():
    app()


if __name__ == "__main__":
    main()
