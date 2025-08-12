"""Tests for tool call parsing strategies.

This module contains tests for the ToolCallParseStrategy implementations.
"""

import sys
import unittest
import time
import logging

from tests.test_decorators import feature_test

from hatchling.core.llm.streaming_management import StreamEvent, StreamEventType
from hatchling.core.llm.tool_management import ToolCallParseRegistry
from hatchling.config.llm_settings import ELLMProvider

class TestToolCallParseStrategiesRegistry(unittest.TestCase):
    """Test suite for tool call parsing strategies using the registry."""

    @feature_test
    def test_ollama_parse_strategy(self):

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
        strategy = ToolCallParseRegistry.get_strategy(ELLMProvider.OLLAMA)
        result = strategy.parse_tool_call(ollama_event)
        self.assertEqual(result["tool_id"], "tool_123")
        self.assertEqual(result["function_name"], "get_weather")
        self.assertIsInstance(result["arguments"], dict)
        self.assertEqual(result["arguments"]["city"], "New York")
        self.assertEqual(result["arguments"]["unit"], "celsius")

    @feature_test
    def test_ollama_parse_strategy_with_string_args(self):

        ollama_event = StreamEvent(
            type=StreamEventType.LLM_TOOL_CALL_REQUEST,
            data={
                "tool_calls": [
                    {
                        "id": "tool_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "New York", "unit": "celsius"}'
                        }
                    }
                ]
            },
            provider=ELLMProvider.OLLAMA,
            request_id="req_456",
            timestamp=time.time()
        )
        strategy = ToolCallParseRegistry.get_strategy(ELLMProvider.OLLAMA)
        result = strategy.parse_tool_call(ollama_event)
        self.assertEqual(result["tool_id"], "tool_123")
        self.assertEqual(result["function_name"], "get_weather")
        self.assertIsInstance(result["arguments"], dict)
        self.assertEqual(result["arguments"]["city"], "New York")
        self.assertEqual(result["arguments"]["unit"], "celsius")

    @feature_test
    def test_openai_parse_strategy_first_chunk(self):

        openai_event = StreamEvent(
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
            provider=ELLMProvider.OPENAI.value,
            request_id="req_789",
            timestamp=time.time()
        )
        strategy = ToolCallParseRegistry.get_strategy(ELLMProvider.OPENAI)
        result = strategy.parse_tool_call(openai_event)
        self.assertEqual(result["tool_id"], "call_abc123")
        self.assertEqual(result["function_name"], "get_weather")
        self.assertIsInstance(result["arguments"], dict)
        self.assertTrue("_partial" in result["arguments"])

    @feature_test
    def test_openai_parse_strategy_continuation(self):

        strategy = ToolCallParseRegistry.get_strategy(ELLMProvider.OPENAI)

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
            provider=ELLMProvider.OPENAI.value,
            request_id="req_789",
            timestamp=time.time()
        )
        strategy.parse_tool_call(first_event)

        continuation_event = StreamEvent(
            type=StreamEventType.LLM_TOOL_CALL_REQUEST,
            data={
                "index": 0,
                "function": {
                    "arguments": ' York", "unit": "celsius"}'
                }
            },
            provider=ELLMProvider.OPENAI.value,
            request_id="req_789",
            timestamp=time.time()
        )
        result = strategy.parse_tool_call(continuation_event)
        self.assertEqual(result["tool_id"], "call_abc123")
        self.assertEqual(result["function_name"], "get_weather")
        self.assertIsInstance(result["arguments"], dict)
        self.assertEqual(result["arguments"]["city"], "New York")
        self.assertEqual(result["arguments"]["unit"], "celsius")

    @feature_test
    def test_deprecated_function_call_format(self):

        deprecated_event = StreamEvent(
            type=StreamEventType.LLM_TOOL_CALL_REQUEST,
            data={
                "function_call": {
                    "name": "get_weather",
                    "arguments": '{"city": "New York", "unit": "celsius"}'
                },
                "deprecated": True
            },
            provider=ELLMProvider.OPENAI.value,
            request_id="req_789",
            timestamp=time.time()
        )
        strategy = ToolCallParseRegistry.get_strategy(ELLMProvider.OPENAI)
        result = strategy.parse_tool_call(deprecated_event)
        self.assertEqual(result["tool_id"], "function_call")
        self.assertEqual(result["function_name"], "get_weather")
        self.assertIsInstance(result["arguments"], dict)
        self.assertEqual(result["arguments"]["city"], "New York")
        self.assertEqual(result["arguments"]["unit"], "celsius")

def run_registry_strategy_tests():
    """Run the test suite for tool call parse strategies using the registry."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestToolCallParseStrategiesRegistry))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_registry_strategy_tests()
    sys.exit(0 if success else 1)
