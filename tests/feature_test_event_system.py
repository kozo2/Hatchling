"""Feature tests for event system functionality.

This test suite validates the streaming event system including event types,
event data structures, and event lifecycle management.
"""

import sys
import logging
import unittest
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_decorators import feature_test

logger = logging.getLogger("feature_test_event_system")


class TestEventSystem(unittest.TestCase):
    """Feature tests for streaming event system."""

    @feature_test
    def test_stream_event_type_enum(self):
        """Test that EventType enum contains expected values."""
        from hatchling.core.llm.event_system.stream_data import EventType

        # LLM Response Events
        self.assertEqual(EventType.CONTENT.value, "content",
                        "CONTENT event type should have correct value")
        self.assertEqual(EventType.ROLE.value, "role",
                        "ROLE event type should have correct value")
        self.assertEqual(EventType.FINISH.value, "finish",
                        "FINISH event type should have correct value")
        self.assertEqual(EventType.USAGE.value, "usage",
                        "USAGE event type should have correct value")
        self.assertEqual(EventType.ERROR.value, "error",
                        "ERROR event type should have correct value")

        # MCP Lifecycle Events
        self.assertEqual(EventType.MCP_SERVER_UP.value, "mcp_server_up",
                        "MCP_SERVER_UP event type should have correct value")
        self.assertEqual(EventType.MCP_SERVER_DOWN.value, "mcp_server_down",
                        "MCP_SERVER_DOWN event type should have correct value")
        self.assertEqual(EventType.MCP_TOOL_ENABLED.value, "mcp_tool_enabled",
                        "MCP_TOOL_ENABLED event type should have correct value")
        self.assertEqual(EventType.MCP_TOOL_DISABLED.value, "mcp_tool_disabled",
                        "MCP_TOOL_DISABLED event type should have correct value")

        # Tool Execution Events
        self.assertEqual(EventType.LLM_TOOL_CALL_REQUEST.value, "llm_tool_call_request",
                        "LLM_TOOL_CALL_REQUEST event type should have correct value")
        self.assertEqual(EventType.MCP_TOOL_CALL_DISPATCHED.value, "mcp_tool_call_dispatched",
                        "MCP_TOOL_CALL_DISPATCHED event type should have correct value")
        self.assertEqual(EventType.MCP_TOOL_CALL_RESULT.value, "mcp_tool_call_result",
                        "MCP_TOOL_CALL_RESULT event type should have correct value")
        self.assertEqual(EventType.MCP_TOOL_CALL_ERROR.value, "mcp_tool_call_error",
                        "MCP_TOOL_CALL_ERROR event type should have correct value")

        # Tool Chaining Events
        self.assertEqual(EventType.TOOL_CHAIN_START.value, "tool_chain_start",
                        "TOOL_CHAIN_START event type should have correct value")
        self.assertEqual(EventType.TOOL_CHAIN_END.value, "tool_chain_end",
                        "TOOL_CHAIN_END event type should have correct value")
        self.assertEqual(EventType.TOOL_CHAIN_ITERATION_START.value, "tool_chain_iteration_start",
                        "TOOL_CHAIN_ITERATION_START event type should have correct value")
        self.assertEqual(EventType.TOOL_CHAIN_ITERATION_END.value, "tool_chain_iteration_end",
                        "TOOL_CHAIN_ITERATION_END event type should have correct value")

    @feature_test
    def test_mcp_tool_status_enum(self):
        """Test that MCPToolStatus enum contains expected values."""
        from hatchling.mcp_utils.mcp_tool_data import MCPToolStatus

        self.assertEqual(MCPToolStatus.ENABLED.value, "enabled",
                        "ENABLED status should have correct value")
        self.assertEqual(MCPToolStatus.DISABLED.value, "disabled",
                        "DISABLED status should have correct value")

    @feature_test
    def test_stream_event_creation(self):
        """Test StreamEvent data structure creation and properties."""
        from hatchling.core.llm.event_system.stream_data import StreamEvent, EventType
        from hatchling.config.llm_settings import ELLMProvider

        # Create a test event
        event_data = {"content": "Test content"}
        event = StreamEvent(
            type=EventType.CONTENT,
            data=event_data,
            provider=ELLMProvider.OPENAI,
            request_id="test-request-123"
        )

        self.assertEqual(event.type, EventType.CONTENT,
                        "Event type should be set correctly")
        self.assertEqual(event.data, event_data,
                        "Event data should be set correctly")
        self.assertEqual(event.provider, ELLMProvider.OPENAI,
                        "Event provider should be set correctly")
        self.assertEqual(event.request_id, "test-request-123",
                        "Event request_id should be set correctly")
        self.assertIsNotNone(event.timestamp,
                            "Event timestamp should be automatically set")

    @feature_test
    def test_mcp_tool_info_creation(self):
        """Test MCPToolInfo data structure creation and properties."""
        from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason

        tool_info = MCPToolInfo(
            name="test_tool",
            description="A test tool",
            schema={"type": "function", "parameters": {}},
            server_path="/path/to/server",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )

        self.assertEqual(tool_info.name, "test_tool",
                        "Tool name should be set correctly")
        self.assertEqual(tool_info.description, "A test tool",
                        "Tool description should be set correctly")
        self.assertEqual(tool_info.status, MCPToolStatus.ENABLED,
                        "Tool status should be set correctly")
        self.assertEqual(tool_info.reason, MCPToolStatusReason.FROM_SERVER_UP,
                        "Tool status reason should be set correctly")
        self.assertIsNotNone(tool_info.last_updated,
                            "Tool last_updated should be automatically set")

    @feature_test
    def test_event_system_integration(self):
        """Test integration between different event system components."""
        from hatchling.core.llm.event_system.stream_data import StreamEvent, EventType
        from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason
        from hatchling.config.llm_settings import ELLMProvider

        # Create a tool info object
        tool_info = MCPToolInfo(
            name="integration_test_tool",
            description="Tool for integration testing",
            schema={"type": "function"},
            server_path="/test/server",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_USER_ENABLED
        )

        # Create an event that might use this tool info
        event = StreamEvent(
            type=EventType.MCP_TOOL_ENABLED,
            data={
                "tool_name": tool_info.name,
                "tool_info": tool_info
            },
            provider=ELLMProvider.OPENAI
        )

        self.assertEqual(event.type, EventType.MCP_TOOL_ENABLED,
                        "Event should have correct type")
        self.assertEqual(event.data["tool_name"], "integration_test_tool",
                        "Event should contain correct tool name")
        self.assertEqual(event.data["tool_info"].status, MCPToolStatus.ENABLED,
                        "Event should contain tool info with correct status")


def run_event_system_feature_tests() -> bool:
    """Run all event system feature tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEventSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_event_system_feature_tests()
    sys.exit(0 if success else 1)
    self.assertTrue(hasattr(EventType, event_name),
                    f"Missing MCP tool event: {event_name}")
    event_type = getattr(EventType, event_name)
    self.assertEqual(event_type.value, event_value,
                    f"Event {event_name} should have value {event_value}")
    
    @feature_test
    def test_tool_execution_events_defined(self):
        """Test that tool execution events are properly defined."""
        from hatchling.core.llm.event_system.event_subscribers_examples import EventType
        
        required_execution_events = [
            ('MCP_TOOL_CALL_DISPATCHED', 'mcp_tool_call_dispatched'),
            ('MCP_TOOL_CALL_RESULT', 'mcp_tool_call_result'),
            ('MCP_TOOL_CALL_ERROR', 'mcp_tool_call_error'),
            ('LLM_TOOL_CALL_REQUEST', 'llm_tool_call_request')
        ]
        
        for event_name, event_value in required_execution_events:
            self.assertTrue(hasattr(EventType, event_name),
                           f"Missing tool execution event: {event_name}")
            event_type = getattr(EventType, event_name)
            self.assertEqual(event_type.value, event_value,
                           f"Event {event_name} should have value {event_value}")

    @feature_test
    def test_mcp_tool_data_structures(self):
        """Test that MCP tool data structures are properly defined."""
        from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason
        
        # Test MCPToolStatus enum
        required_statuses = ['ENABLED', 'DISABLED', 'ERROR', 'UNKNOWN']
        for status in required_statuses:
            self.assertTrue(hasattr(MCPToolStatus, status),
                           f"Missing tool status: {status}")
        
        # Test MCPToolStatusReason enum
        required_reasons = ['USER_DISABLED', 'SERVER_ERROR', 'INVALID_SCHEMA', 'NONE']
        for reason in required_reasons:
            self.assertTrue(hasattr(MCPToolStatusReason, reason),
                           f"Missing status reason: {reason}")
        
        # Test MCPToolInfo data class
        tool_info = MCPToolInfo(
            name="test_tool",
            description="Test tool description",
            schema={"type": "object"},
            server_path="/test/path",
            status=MCPToolStatus.ENABLED,
            status_reason=MCPToolStatusReason.NONE
        )
        
        self.assertEqual(tool_info.name, "test_tool",
                        "MCPToolInfo should store name correctly")
        self.assertEqual(tool_info.description, "Test tool description",
                        "MCPToolInfo should store description correctly")
        self.assertEqual(tool_info.status, MCPToolStatus.ENABLED,
                        "MCPToolInfo should store status correctly")

    @feature_test
    def test_stream_event_creation(self):
        """Test that StreamEvent objects can be created correctly."""
        from hatchling.core.llm.event_system.event_subscribers_examples import StreamEvent, EventType
        from hatchling.core.llm.providers.base import ELLMProvider
        
        # Test creating a basic stream event
        event = StreamEvent(
            type=EventType.CONTENT,
            data={"content": "test content"},
            provider=ELLMProvider.OLLAMA,
            request_id="test_request_123"
        )
        
        self.assertEqual(event.type, EventType.CONTENT,
                        "Event should store type correctly")
        self.assertEqual(event.data["content"], "test content",
                        "Event should store data correctly")
        self.assertEqual(event.provider, ELLMProvider.OLLAMA,
                        "Event should store provider correctly")
        self.assertEqual(event.request_id, "test_request_123",
                        "Event should store request ID correctly")
        self.assertIsNotNone(event.timestamp,
                            "Event should have timestamp")

    @feature_test
    def test_event_type_comprehensive_coverage(self):
        """Test that all necessary event types are available."""
        from hatchling.core.llm.event_system.event_subscribers_examples import EventType
        
        # Core streaming events
        core_events = ['CONTENT', 'FINISH', 'ERROR', 'USAGE_STATS']
        for event in core_events:
            self.assertTrue(hasattr(EventType, event),
                           f"Missing core event type: {event}")
        
        # Tool call events
        tool_events = ['LLM_TOOL_CALL_REQUEST', 'MCP_TOOL_CALL_DISPATCHED', 
                      'MCP_TOOL_CALL_RESULT', 'MCP_TOOL_CALL_ERROR']
        for event in tool_events:
            self.assertTrue(hasattr(EventType, event),
                           f"Missing tool call event type: {event}")
        
        # MCP lifecycle events
        mcp_events = ['MCP_SERVER_UP', 'MCP_SERVER_DOWN', 'MCP_TOOL_ENABLED', 'MCP_TOOL_DISABLED']
        for event in mcp_events:
            self.assertTrue(hasattr(EventType, event),
                           f"Missing MCP lifecycle event type: {event}")


def run_event_system_tests() -> bool:
    """Run all event system feature tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEventSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_event_system_tests()
    sys.exit(0 if success else 1)
