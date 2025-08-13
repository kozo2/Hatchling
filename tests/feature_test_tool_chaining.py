"""Feature tests for ToolChainingSubscriber and tool chaining event-driven workflows.

These tests use mocks to simulate event-driven tool chaining, verify event publishing, and check state management.
"""

import unittest
import time
from unittest.mock import MagicMock, patch
from hatchling.core.llm.tool_management.tool_chaining_subscriber import ToolChainingSubscriber
from hatchling.core.llm.event_system.stream_data import EventType, Event
from tests.test_decorators import feature_test

class TestToolChainingFeature(unittest.TestCase):
    """Feature tests for tool chaining event-driven logic."""

    @feature_test
    def test_tool_chaining_subscriber_initialization_and_events(self):
        """Test ToolChainingSubscriber initializes and handles events for tool chaining."""
        mock_tool_execution = MagicMock()
        mock_tool_execution.root_tool_query = "Test query"
        mock_settings = MagicMock()
        mock_settings.tool_calling.max_iterations = 5
        subscriber = ToolChainingSubscriber(settings=mock_settings, tool_execution=mock_tool_execution)
        self.assertIsInstance(subscriber, ToolChainingSubscriber)
        self.assertFalse(subscriber.started)
        self.assertEqual(subscriber.chain_link_count, 0)
        event_data = {"tool_call_id": "abc", "function_name": "test_func", "arguments": {}}
        event = Event(type=EventType.MCP_TOOL_CALL_DISPATCHED, data=event_data, provider=MagicMock())
        subscriber.tool_result_collector.tool_call_queue = [(None, None, event_data)]
        with patch.object(subscriber.publisher, 'publish') as mock_publish:
            subscriber.on_event(event)
            self.assertTrue(subscriber.started)
            self.assertEqual(subscriber.chain_link_count, 1)
            mock_publish.assert_called()

    @feature_test
    def test_tool_chaining_subscriber_handles_result_and_error(self):
        """Test ToolChainingSubscriber processes result and error events and manages chain state."""
        mock_tool_execution = MagicMock()
        mock_tool_execution.root_tool_query = "Test query"
        mock_settings = MagicMock()
        mock_settings.tool_calling.max_iterations = 5
        subscriber = ToolChainingSubscriber(settings=mock_settings, tool_execution=mock_tool_execution)
        subscriber.started = True
        subscriber.chain_link_count = 1
        tool_call = MagicMock()
        tool_result = MagicMock()
        subscriber.tool_result_collector.get_next_ready_pair = MagicMock(return_value=(tool_call, tool_result))
        event = Event(type=EventType.MCP_TOOL_CALL_RESULT, data={}, provider=MagicMock())
        with patch.object(subscriber, 'logger'), \
             patch.object(subscriber, 'check_iteration_end'), \
             patch('asyncio.create_task') as mock_create_task:
            subscriber.on_event(event)
            mock_create_task.assert_called()

    @feature_test
    def test_tool_chaining_subscriber_check_iteration_end(self):
        """Test check_iteration_end publishes TOOL_CHAIN_END when chain is finished."""
        mock_tool_execution = MagicMock()
        mock_tool_execution.root_tool_query = "Test query"
        mock_settings = MagicMock()
        mock_settings.tool_calling.max_iterations = 5
        subscriber = ToolChainingSubscriber(settings=mock_settings, tool_execution=mock_tool_execution)
        subscriber.started = True
        subscriber.chain_link_count = 0
        subscriber.tool_chain_id = "chainid"
        subscriber.start_time = time.time() - 2
        with patch.object(subscriber.publisher, 'publish') as mock_publish:
            subscriber.check_iteration_end()
            mock_publish.assert_called()
