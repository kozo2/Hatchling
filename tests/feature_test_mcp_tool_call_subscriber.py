"""Tests for MCPToolCallSubscriber with provider-based strategy selection.

This module contains integration tests for the MCPToolCallSubscriber
using provider methods directly instead of the registry pattern.
"""

import sys
import logging
import unittest
import time
from unittest.mock import MagicMock

from tests.test_decorators import feature_test, requires_api_key

from hatchling.core.llm.event_system import Event, EventType

from hatchling.mcp_utils.mcp_tool_execution import MCPToolExecution
from hatchling.mcp_utils.mcp_tool_call_subscriber import MCPToolCallSubscriber
from hatchling.core.llm.providers.registry import ProviderRegistry
from hatchling.config.llm_settings import ELLMProvider


class TestMCPToolCallSubscriberRegistry(unittest.TestCase):
    """Test suite for MCPToolCallSubscriber using provider-based strategy selection."""

    def setUp(self):
        self.mock_tool_execution = MagicMock(spec=MCPToolExecution)
        self.mock_tool_execution.stream_publisher = MagicMock()
        self.mock_tool_execution.stream_publisher.publish = MagicMock()
        
        # Configure execute_tool_sync to simulate the real behavior of publishing MCP_TOOL_CALL_DISPATCHED
        def mock_execute_tool_sync(parsed_tool_call):
            # Simulate what the real execute_tool_sync -> execute_tool would do
            self.mock_tool_execution.stream_publisher.publish(
                EventType.MCP_TOOL_CALL_DISPATCHED, 
                parsed_tool_call.to_dict()
            )
            
        self.mock_tool_execution.execute_tool_sync = MagicMock(side_effect=mock_execute_tool_sync)

    @feature_test
    def test_on_event_ollama(self):
        # Create a mock Ollama tool call event
        ollama_event = Event(
            type=EventType.LLM_TOOL_CALL_REQUEST,
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

        # Use provider to get the strategy
        provider = ProviderRegistry.get_provider(ELLMProvider.OLLAMA)
        parsed_tool_call = provider.parse_tool_call(ollama_event)
        
        subscriber = MCPToolCallSubscriber(self.mock_tool_execution)
        subscriber.on_event(ollama_event)

        self.mock_tool_execution.stream_publisher.publish.assert_called_once()
        args = self.mock_tool_execution.stream_publisher.publish.call_args[0]
        self.assertEqual(args[0], EventType.MCP_TOOL_CALL_DISPATCHED)
        self.assertEqual(args[1]["function_name"], "get_weather")
        self.assertEqual(args[1]["tool_call_id"], "tool_123")
        self.assertEqual(args[1]["arguments"]["city"], "New York")
        
        # Verify the sync wrapper was called
        self.mock_tool_execution.execute_tool_sync.assert_called_once()

    @feature_test
    @requires_api_key
    def test_on_event_openai(self):
        # Create a mock OpenAI tool call event (first chunk)
        first_event = Event(
            type=EventType.LLM_TOOL_CALL_REQUEST,
            data={
                "tool_call": {
                    "index": 0,
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city": "New'
                    }
                }
            },
            provider=ELLMProvider.OPENAI,
            request_id="req_789",
            timestamp=time.time()
        )

        # Use provider to get the strategy
        provider = ProviderRegistry.get_provider(ELLMProvider.OPENAI)
        subscriber = MCPToolCallSubscriber(self.mock_tool_execution)
        subscriber.on_event(first_event)

        # Create a mock continuation event
        continuation_event = Event(
            type=EventType.LLM_TOOL_CALL_REQUEST,
            data={
                "tool_call": {
                    "index": 0,
                    "function": {
                        "arguments": ' York", "unit": "celsius"}'
                    }
                }
            },
            provider=ELLMProvider.OPENAI,
            request_id="req_890",  # Different request ID to avoid being skipped
            timestamp=time.time()
        )

        # Reset the mock to clear the first call
        self.mock_tool_execution.stream_publisher.publish.reset_mock()
        subscriber.on_event(continuation_event)

        self.mock_tool_execution.stream_publisher.publish.assert_called_once()
        args = self.mock_tool_execution.stream_publisher.publish.call_args[0]
        self.assertEqual(args[0], EventType.MCP_TOOL_CALL_DISPATCHED)
        self.assertEqual(args[1]["function_name"], "")  # No function name in continuation
        self.assertEqual(args[1]["tool_call_id"], "unknown")  # No ID in continuation  
        # The arguments will be in _raw due to invalid JSON
        self.assertTrue("_raw" in args[1]["arguments"])


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
    
