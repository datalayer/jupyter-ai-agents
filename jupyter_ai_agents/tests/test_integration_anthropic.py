#!/usr/bin/env python
# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

# Integration test for Anthropic provider

import os
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestAnthropicIntegration(unittest.TestCase):
    """Test the integration of Anthropic provider with Jupyter AI Agents."""

    def setUp(self):
        # Skip tests if ANTHROPIC_API_KEY is not set
        if "ANTHROPIC_API_KEY" not in os.environ:
            self.skipTest("ANTHROPIC_API_KEY environment variable not set")

    @patch("langchain_anthropic.ChatAnthropic")
    def test_create_anthropic_agent(self, mock_chat_anthropic):
        """Test creating an Anthropic agent with tools."""
        # Import here to avoid import errors if dependencies aren't installed
        from langchain_core.tools import tool
        from jupyter_ai_agents.providers import create_anthropic_agent
        
        # Setup mock ChatAnthropic
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm
        
        # Define a simple test tool
        @tool
        def greet(name: str) -> str:
            """Greet someone by name."""
            return f"Hello, {name}!"
        
        # Create the agent
        agent = create_anthropic_agent(
            model_name="claude-3-haiku-20240307",
            system_prompt="You are a helpful assistant.",
            tools=[greet]
        )
        
        # Verify the agent was created correctly
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, "AnthropicToolAgent")
        self.assertTrue(hasattr(agent, "agent"))
        self.assertTrue(hasattr(agent, "tools"))
        
        # Verify tools were set correctly
        self.assertEqual(len(agent.tools), 1)
        self.assertEqual(agent.tools[0].name, "greet")
        
        # Verify the model was created with the right parameters
        mock_chat_anthropic.assert_called_once_with(model="claude-3-haiku-20240307")

    @patch("langchain.agents.agent.AgentExecutor.invoke")
    @patch("langchain_anthropic.ChatAnthropic")
    def test_simplified_tool_invocation(self, mock_chat_anthropic, mock_agent_invoke):
        """Test that tool invocation works correctly with mocked invoke."""
        from langchain_core.tools import tool
        from jupyter_ai_agents.providers import create_anthropic_agent
        
        # Define a test tool
        @tool
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers together."""
            return a * b
        
        # Setup mock for invoke response
        mock_agent_output = [{"text": "The result of multiplying 6 and 7 is 42."}]
        mock_agent_invoke.return_value = {"output": mock_agent_output}
        
        # Setup mock LLM
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm
        
        # Create the agent
        agent = create_anthropic_agent(
            model_name="claude-3-haiku-20240307",
            system_prompt="You are a helpful assistant.",
            tools=[multiply]
        )
        
        # Test invoking the agent
        result = agent.invoke({"input": "What is 6 * 7?"})
        
        # Check the result
        self.assertIn("output", result)
        self.assertEqual(result["output"], mock_agent_output)
        
        # Verify invoke was called with the right parameter
        mock_agent_invoke.assert_called_once()

if __name__ == "__main__":
    unittest.main() 