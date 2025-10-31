<!--
  ~ Copyright (c) 2024-2025 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.io)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# 🪐 ✨ Jupyter AI Agents

[![Github Actions Status](https://github.com/datalayer/jupyter-ai-agents/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-ai-agents/actions/workflows/build.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-ai-agents)](https://pypi.org/project/jupyter-ai-agents)

🪐 ✨ AI Agents for JupyterLab with 🛠️ MCP tools - Chat interface for intelligent notebook interaction, code execution, and workspace management.

## 💬 Chat Interface

Experience seamless AI-powered assistance directly within JupyterLab through our intuitive chat interface:

![Jupyter AI Agents Chat 1](https://assets.datalayer.tech/jupyter-ai-agents/jupyter-ai-agents-chat-1.png)

The chat interface is built using [Pydantic AI](https://github.com/pydantic/pydantic-ai) for robust AI agent orchestration and [Vercel AI UI](https://github.com/vercel/ai) for the user interface components.

### MCP Server Integration

By default, the [Jupyter MCP Server](https://github.com/datalayer/jupyter-mcp-server) is started as a Jupyter server extension, providing access to all Jupyter MCP server tools directly through the chat interface. This enables the AI agent to interact with notebooks, execute code, manage files, and perform various Jupyter operations seamlessly.

![Jupyter AI Agents Chat 2](https://assets.datalayer.tech/jupyter-ai-agents/jupyter-ai-agents-chat-2.png)

### Getting Started with Chat

Currently, we support **Anthropic Claude Sonnet 4.0** as the AI model. To get started:

1. **Set up your environment:**
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

2. **Install Jupyter AI Agents:**
   ```bash
   pip install jupyter_ai_agents
   pip uninstall -y pycrdt datalayer_pycrdt
   pip install datalayer_pycrdt==0.12.17
   ```

3. **Launch JupyterLab with the required configuration:**
   ```bash
   jupyter lab \
     --JupyterMCPServerExtensionApp.document_url local \
     --JupyterMCPServerExtensionApp.runtime_url local \
     --JupyterMCPServerExtensionApp.start_new_runtime True \
     --ServerApp.disable_check_xsrf True \
     --IdentityProvider.token MY_TOKEN \
     --port 4040
   ```

4. **Access the chat interface** through the right panel in JupyterLab.

### What's Coming Next

We're actively working on expanding the capabilities of Jupyter AI Agents:

- 🚀 **More LLM Providers**: Integration with additional AI model providers
- ⚙️ **MCP Configuration**: Enhanced MCP server configuration options
- 🔧 **Extended Tool Access**: Chat access to tools from other MCP servers
- 🛠️ **Enhanced Features**: And much more!

Check out our [GitHub Issues](https://github.com/datalayer/jupyter-ai-agents/issues) to see what we're working on. **Contributions are welcome!**

> **Note**: The documentation at https://jupyter-ai-agents.datalayer.tech will be updated soon to reflect the new chat features and capabilities.


<details>
<summary><strong>🖥️ CLI Usage</strong></summary>

## CLI Usage

You can also use Jupyter AI Agents through the command line interface for automated notebook operations.

![Jupyter AI Agents CLI](https://assets.datalayer.tech/jupyter-ai-agent/ai-agent-prompt-demo-terminal.gif)


### Basic Installation

To install Jupyter AI Agents, run the following command:

```bash
pip install jupyter_ai_agents
pip uninstall -y pycrdt datalayer_pycrdt
pip install datalayer_pycrdt==0.12.17
```

Or clone this repository and install it from source:

```bash
git clone https://github.com/datalayer/jupyter-ai-agents
cd jupyter-ai-agents
pip install -e .
```

### JupyterLab Setup

The Jupyter AI Agents can directly interact with JupyterLab. The modifications made by the Jupyter AI Agents can be seen in real-time thanks to [Jupyter Real Time Collaboration](https://jupyterlab.readthedocs.io/en/stable/user/rtc.html). Make sure you have JupyterLab installed with the Collaboration extension:

```bash
pip install jupyterlab==4.4.1 jupyter-collaboration==4.0.2
```

We ask you to take additional actions to overcome limitations and bugs of the pycrdt library. Ensure you create a new shell after running the following commands:

```bash
pip uninstall -y pycrdt datalayer_pycrdt
pip install datalayer_pycrdt==0.12.17
```
### Examples

We put here a quick example for a Out-Kernel Stateless Agent via CLI helping your JupyterLab session.

Start JupyterLab, setting a `port` and a `token` to be reused by the agent, and create a notebook `notebook.ipynb`.

```bash
# make jupyterlab
jupyter lab --port 8888 --IdentityProvider.token MY_TOKEN
```

Jupyter AI Agents supports multiple AI model providers (more information can be found on [this documentation page](https://jupyter-ai-agents.datalayer.tech/docs/models)).

The following takes you through an example with the Azure OpenAI provider. Read the [Azure Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai) to get the needed credentials and make sure you define them in the following `.env` file.

```bash
cat << EOF >>.env
OPENAI_API_VERSION="..."
AZURE_OPENAI_ENDPOINT="..."
AZURE_OPENAI_API_KEY="..."
EOF
```

**Prompt Agent**

To use the Jupyter AI Agents, an easy way is to launch a CLI (update the Azure deployment name based on your setup).

```bash
# Prompt agent example.
# make jupyter-ai-agents-prompt
jupyter-ai-agents prompt \
  --url http://localhost:8888 \
  --token MY_TOKEN \
  --model-provider azure-openai \
  --model-name gpt-4o-mini \
  --path notebook.ipynb \
  --input "Create a matplotlib example"
```

![Jupyter AI Agents](https://assets.datalayer.tech/jupyter-ai-agent/ai-agent-prompt-demo-terminal.gif)

**Explain Error Agent**

```bash
# Explain Error agent example.
# make jupyter-ai-agents-explain-error
jupyter-ai-agents explain-error \
  --url http://localhost:8888 \
  --token MY_TOKEN \
  --model-provider azure-openai \
  --model-name gpt-4o-mini \
  --path notebook.ipynb
```

![Jupyter AI Agents](https://assets.datalayer.tech/jupyter-ai-agent/ai-agent-explainerror-demo-terminal.gif)


### About the Technology

Jupyter AI Agents empowers **AI** models to **interact** with and **modify Jupyter Notebooks**. The agent is equipped with tools such as adding code cells, inserting markdown cells, executing code, enabling it to modify the notebook comprehensively based on user instructions or by reacting to the Jupyter notebook events.

This Agent is **innovative** as it is designed to **operate on the entire Notebook**, not just at the cell level, enabling more comprehensive and seamless modifications.

The Agent can also run separately from the Jupyter server as the communication is achieved through RTC via the [Jupyter NbModel Client](https://github.com/datalayer/jupyter-nbmodel-client) and the [Jupyter Kernel Client](https://github.com/datalayer/jupyter-kernel-client).

```
Jupyter AI Agents <---> JupyterLab
       |
       | RTC (Real Time Collaboration)
       |
Jupyter Clients
```
</details>

## Contributing

### Development install

```bash
# Clone the repo to your local environment
# Change directory to the jupyter_ai_agents directory
# Install package in development mode - will automatically enable
# The server extension.
pip install -e ".[test,lint,typing]"
```

### Running Tests

Install dependencies:

```bash
pip install -e ".[test]"
```

To run the python tests, use:

```bash
pytest
```

### Development uninstall

```bash
pip uninstall jupyter_ai_agents
```

### Packaging the library

See [RELEASE](RELEASE.md).
