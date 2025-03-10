# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import NbModelClient
from langchain.agents import AgentExecutor, tool

from jupyter_ai_agents.agents.base import RuntimeAgent
from jupyter_ai_agents.agents.utils import create_ai_agent
from jupyter_ai_agents.tools.tools import insert_execute_code_cell_tool, insert_markdown_cell_tool
from jupyter_ai_agents.utils import retrieve_cells_content

SYSTEM_PROMPT = """You are a powerful coding assistant.
Create and execute code in a notebook based on user instructions.
Add markdown cells to explain the code and structure the notebook clearly.
Assume that no packages are installed in the notebook, so install them using !pip install.
Ensure updates to cell indexing when new cells are inserted. Maintain the logical flow of execution by adjusting cell index as needed.
"""


def _create_agent(
    notebook: NbModelClient,
    kernel: KernelClient,
    model_provider: str,
    model_name: str,
    full_context: bool,
    current_cell_index: int,
) -> AgentExecutor:
    """From a given instruction, code and markdown cells are added to a notebook."""

    @tool
    def insert_execute_code_cell(cell_index: int, cell_content: str) -> str:
        """Add a Python code cell to the notebook at the given index with a content and execute it."""
        insert_execute_code_cell_tool(notebook, kernel, cell_content, cell_index)
        return "Code cell added and executed."

    @tool
    def insert_markdown_cell(cell_index: int, cell_content: str) -> str:
        """Add a Markdown cell to the notebook at the given index with a content."""
        insert_markdown_cell_tool(notebook, cell_content, cell_index)
        return "Markdown cell added."

    tools = [
        insert_execute_code_cell,
        insert_markdown_cell,
    ]

    if full_context:
        system_prompt_enriched = f"""
        {SYSTEM_PROMPT}

        Notebook content: {retrieve_cells_content(notebook)}
        """
    else:
        system_prompt_enriched = SYSTEM_PROMPT

    if current_cell_index != -1:
        system_prompt_final = f"""
        {system_prompt_enriched}

        Cell index on which the user instruction was given: {current_cell_index}
        """
    else:
        system_prompt_final = system_prompt_enriched

    return create_ai_agent(model_provider, model_name, system_prompt_final, tools)


async def prompt(
    notebook: NbModelClient,
    kernel: KernelClient,
    input: str,
    model_provider: str,
    model_name: str,
    full_context: bool,
    current_cell_index: int,
) -> list:
    agent = _create_agent(
        notebook, kernel, model_provider, model_name, full_context, current_cell_index
    )
    replies = []
    async for reply in agent.astream({"input": input}):
        replies.append(reply)
    return replies


class PromptAgent(RuntimeAgent):
    """AI Agent replying to user prompt."""

    model_provider = "azure-openai"
    model_name = "gpt-40-mini"
    full_context = False

    async def _on_user_prompt(
        self,
        cell_id: str,
        prompt_id: str,
        prompt: str,
        username: str | None = None,
        timestamp: int | None = None,
        **kwargs,
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
        document_client = self
        runtime_client = self.runtime_client

        current_cell_index = self.get_cell_index(cell_id)

        agent_executor = _create_agent(
            document_client,
            runtime_client,
            self.model_provider,
            self.model_name,
            self.full_context,
            current_cell_index,
        )

        output = None

        try:
            await self.notify("Thinking…", cell_id=cell_id)
            async for reply in agent_executor.astream({"input": prompt}):
                output = reply.get("output", "")
                if not output:
                    output = reply["messages"][-1].content
                self._log.debug(
                    "Got a reply for prompt [%s]: [%s].", prompt_id, (output or "")[:30]
                )
        finally:
            await self.notify("Done", cell_id=cell_id)
        return output
