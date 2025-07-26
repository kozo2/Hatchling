"""Development test for Phase 1: Event System Foundation.

This test validates that all new MCP-related event types and data structures
are properly defined and can be imported correctly.
"""

import sys
import unittest
import logging
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.core.llm.streaming_management.stream_subscribers import StreamEventType
from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason


class TestStreamEventsFoundation(unittest.TestCase):
    """Test suite for new event system foundation components."""
    
    def test_mcp_lifecycle_events_defined(self):
        """Test that MCP lifecycle events are properly defined."""
        # Test MCP server events
        self.assertTrue(hasattr(StreamEventType, 'MCP_SERVER_UP'))
        self.assertEqual(StreamEventType.MCP_SERVER_UP.value, "mcp_server_up")
        
        self.assertTrue(hasattr(StreamEventType, 'MCP_SERVER_DOWN'))
        self.assertEqual(StreamEventType.MCP_SERVER_DOWN.value, "mcp_server_down")
        
        self.assertTrue(hasattr(StreamEventType, 'MCP_SERVER_UNREACHABLE'))
        self.assertEqual(StreamEventType.MCP_SERVER_UNREACHABLE.value, "mcp_server_unreachable")
        
        self.assertTrue(hasattr(StreamEventType, 'MCP_SERVER_REACHABLE'))
        self.assertEqual(StreamEventType.MCP_SERVER_REACHABLE.value, "mcp_server_reachable")
        
        # Test MCP tool events
        self.assertTrue(hasattr(StreamEventType, 'MCP_TOOL_ENABLED'))
        self.assertEqual(StreamEventType.MCP_TOOL_ENABLED.value, "mcp_tool_enabled")
        
        self.assertTrue(hasattr(StreamEventType, 'MCP_TOOL_DISABLED'))
        self.assertEqual(StreamEventType.MCP_TOOL_DISABLED.value, "mcp_tool_disabled")
    
    def test_tool_execution_events_defined(self):
        """Test that tool execution events are properly defined."""
        self.assertTrue(hasattr(StreamEventType, 'MCP_TOOL_CALL_DISPATCHED'))
        self.assertEqual(StreamEventType.MCP_TOOL_CALL_DISPATCHED.value, "MCP_TOOL_CALL_DISPATCHED")
        
        self.assertTrue(hasattr(StreamEventType, 'MCP_TOOL_CALL_RESULT'))
        self.assertEqual(StreamEventType.MCP_TOOL_CALL_RESULT.value, "MCP_TOOL_CALL_RESULT")
        
        self.assertTrue(hasattr(StreamEventType, 'MCP_TOOL_CALL_PROGRESS'))
        self.assertEqual(StreamEventType.MCP_TOOL_CALL_PROGRESS.value, "MCP_TOOL_CALL_PROGRESS")
        
        self.assertTrue(hasattr(StreamEventType, 'MCP_TOOL_CALL_ERROR'))
        self.assertEqual(StreamEventType.MCP_TOOL_CALL_ERROR.value, "tool_call_error")
    
    def test_mcp_tool_status_enum(self):
        """Test that MCPToolStatus enum is properly defined."""
        self.assertTrue(hasattr(MCPToolStatus, 'ENABLED'))
        self.assertEqual(MCPToolStatus.ENABLED.value, "enabled")
        
        self.assertTrue(hasattr(MCPToolStatus, 'DISABLED'))
        self.assertEqual(MCPToolStatus.DISABLED.value, "disabled")
        
        # Test that it's properly an enum
        self.assertIsInstance(MCPToolStatus.ENABLED, MCPToolStatus)
    
    def test_mcp_tool_status_reason_enum(self):
        """Test that MCPToolStatusReason enum is properly defined."""
        # Test enabled reasons
        self.assertTrue(hasattr(MCPToolStatusReason, 'FROM_SERVER_UP'))
        self.assertEqual(MCPToolStatusReason.FROM_SERVER_UP.value, "server_up")
        
        self.assertTrue(hasattr(MCPToolStatusReason, 'FROM_USER_ENABLED'))
        self.assertEqual(MCPToolStatusReason.FROM_USER_ENABLED.value, "user_enabled")
        
        self.assertTrue(hasattr(MCPToolStatusReason, 'FROM_SERVER_REACHABLE'))
        self.assertEqual(MCPToolStatusReason.FROM_SERVER_REACHABLE.value, "server_reachable")
        
        # Test disabled reasons
        self.assertTrue(hasattr(MCPToolStatusReason, 'FROM_SERVER_DOWN'))
        self.assertEqual(MCPToolStatusReason.FROM_SERVER_DOWN.value, "server_down")
        
        self.assertTrue(hasattr(MCPToolStatusReason, 'FROM_SERVER_UNREACHABLE'))
        self.assertEqual(MCPToolStatusReason.FROM_SERVER_UNREACHABLE.value, "unreachable")
        
        self.assertTrue(hasattr(MCPToolStatusReason, 'FROM_USER_DISABLED'))
        self.assertEqual(MCPToolStatusReason.FROM_USER_DISABLED.value, "user_disabled")
        
        self.assertTrue(hasattr(MCPToolStatusReason, 'FROM_SYSTEM_ERROR'))
        self.assertEqual(MCPToolStatusReason.FROM_SYSTEM_ERROR.value, "system_error")
    
    def test_mcp_tool_info_data_structure(self):
        """Test that MCPToolInfo dataclass is properly defined."""
        # Create a test MCPToolInfo instance
        tool_info = MCPToolInfo(
            name="test_tool",
            description="A test tool",
            schema={"type": "function", "parameters": {}},
            server_path="/path/to/server.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        
        # Test that all fields are set correctly
        self.assertEqual(tool_info.name, "test_tool")
        self.assertEqual(tool_info.description, "A test tool")
        self.assertEqual(tool_info.schema, {"type": "function", "parameters": {}})
        self.assertEqual(tool_info.server_path, "/path/to/server.py")
        self.assertEqual(tool_info.status, MCPToolStatus.ENABLED)
        self.assertEqual(tool_info.reason, MCPToolStatusReason.FROM_SERVER_UP)
        
        # Test that optional fields have defaults
        self.assertIsNone(tool_info.provider_format)
        
        # Test that timestamp is set automatically
        self.assertIsNotNone(tool_info.last_updated)
        self.assertIsInstance(tool_info.last_updated, float)
    
    def test_all_event_types_enumerable(self):
        """Test that all event types can be enumerated and are strings."""
        all_events = list(StreamEventType)
        
        # Should have existing events plus new MCP events
        self.assertGreaterEqual(len(all_events), 17)  # 9 original + 6 MCP lifecycle + 4 tool execution
        
        # All events should have string values
        for event in all_events:
            self.assertIsInstance(event.value, str)
        
        print(f"Total StreamEventType values: {len(all_events)}")
        print("All event types:")
        for event in sorted(all_events, key=lambda x: x.value):
            print(f"  - {event.name}: {event.value}")


def run_stream_events_foundation_tests():
    """Run all stream events foundation tests.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestStreamEventsFoundation))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_stream_events_foundation_tests()
    sys.exit(0 if success else 1)
