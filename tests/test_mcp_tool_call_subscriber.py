"""Tests for MCPToolCallSubscriber with strategy         # Use registry to get the strategy
        strategy = ToolCallParseRegistry.get_strategy(ELLMProvider.OLLAMA)
        subscriber = MCPToolCallSubscriber(self.mock_tool_execution)
        subscriber.on_event(ollama_event)

        self.mock_tool_execution.stream_publisher.publish.assert_called_once()
        args = self.mock_tool_execution.stream_publisher.publish.call_args[0].

This module contains integration tests for the MCPToolCallSubscriber
using different ToolCallParseStrategies.
"""

import sys
import logging
import unittest
import time
from unittest.mock import MagicMock, AsyncMock

from hatchling.core.llm.streaming_management import StreamEvent, StreamEventType

from hatchling.mcp_utils.mcp_tool_execution import MCPToolExecution
from hatchling.mcp_utils.mcp_tool_call_subscriber import MCPToolCallSubscriber
from hatchling.core.llm.tool_management import ToolCallParseRegistry
from hatchling.config.llm_settings import ELLMProvider


class TestMCPToolCallSubscriberRegistry(unittest.TestCase):
    """Test suite for MCPToolCallSubscriber using the registry-based strategy selection."""

    def setUp(self):
        self.mock_tool_execution = MagicMock(spec=MCPToolExecution)
        self.mock_tool_execution.stream_publisher = MagicMock()
        self.mock_tool_execution.stream_publisher.publish = MagicMock()
        self.mock_tool_execution.execute_tool_sync = MagicMock()

    def test_on_event_ollama(self):
        # Create a mock Ollama tool call event
        ollama_event = StreamEvent(
            type=StreamEventType.LLM_TOOL_CALL_REQUEST,
            data={
                "tool_calls": [
                    {
                        "id": "tool_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": {"city": "New York", "unit": "celsius"}
                        }
                    }
                ]
            },
            provider=ELLMProvider.OLLAMA,
            request_id="req_456",
            timestamp=time.time()
        )

        # Use registry to get the strategy
        strategy = ToolCallParseRegistry.get_strategy(ELLMProvider.OLLAMA)
        subscriber = MCPToolCallSubscriber(self.mock_tool_execution)
        subscriber.on_event(ollama_event)

        self.mock_tool_execution.stream_publisher.publish.assert_called_once()
        args = self.mock_tool_execution.stream_publisher.publish.call_args[0]
        self.assertEqual(args[0], StreamEventType.MCP_TOOL_CALL_DISPATCHED)
        self.assertEqual(args[1]["function_name"], "get_weather")
        self.assertEqual(args[1]["tool_id"], "tool_123")
        self.assertEqual(args[1]["arguments"]["city"], "New York")
        
        # Verify the sync wrapper was called
        self.mock_tool_execution.execute_tool_sync.assert_called_once_with(
            tool_id="tool_123",
            function_name="get_weather",
            arguments={"city": "New York", "unit": "celsius"}
        )

    def test_on_event_openai(self):
        # Create a mock OpenAI tool call event (first chunk)
        first_event = StreamEvent(
            type=StreamEventType.LLM_TOOL_CALL_REQUEST,
            data={
                "index": 0,
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "New'
                }
            },
            provider=ELLMProvider.OPENAI,
            request_id="req_789",
            timestamp=time.time()
        )

        # Use registry to get the strategy
        strategy = ToolCallParseRegistry.get_strategy(ELLMProvider.OPENAI)
        subscriber = MCPToolCallSubscriber(self.mock_tool_execution)
        subscriber.on_event(first_event)

        # Create a mock continuation event
        continuation_event = StreamEvent(
            type=StreamEventType.LLM_TOOL_CALL_REQUEST,
            data={
                "index": 0,
                "function": {
                    "arguments": ' York", "unit": "celsius"}'
                }
            },
            provider=ELLMProvider.OPENAI,
            request_id="req_789",
            timestamp=time.time()
        )

        # Reset the mock to clear the first call
        self.mock_tool_execution.stream_publisher.publish.reset_mock()
        subscriber.on_event(continuation_event)

        self.mock_tool_execution.stream_publisher.publish.assert_called_once()
        args = self.mock_tool_execution.stream_publisher.publish.call_args[0]
        self.assertEqual(args[0], StreamEventType.MCP_TOOL_CALL_DISPATCHED)
        self.assertEqual(args[1]["function_name"], "get_weather")
        self.assertEqual(args[1]["tool_id"], "call_abc123")
        self.assertEqual(args[1]["arguments"]["city"], "New York")


def run_registry_strategy_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestMCPToolCallSubscriberRegistry))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_registry_strategy_tests()
    sys.exit(0 if success else 1)
    
