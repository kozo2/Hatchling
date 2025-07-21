"""Development test for Phase 2: Enhanced MCPManager with Event Publishing.

This test validates that MCPManager can publish lifecycle events and manage
tool states with proper event publishing.
"""

import sys
import unittest
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.mcp_utils.manager import MCPManager
from hatchling.core.llm.providers.subscription import (
    StreamEventType,
    StreamSubscriber,
    MCPToolStatus,
    MCPToolStatusReason
)


class TestEventSubscriber(StreamSubscriber):
    """Test subscriber to capture published events."""
    
    def __init__(self):
        """Initialize test subscriber."""
        self.received_events = []
        
    def on_event(self, event) -> None:
        """Handle a stream event by storing it."""
        self.received_events.append(event)
        
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return all MCP-related event types."""
        return [
            StreamEventType.MCP_SERVER_UP,
            StreamEventType.MCP_SERVER_DOWN,
            StreamEventType.MCP_SERVER_UNREACHABLE,
            StreamEventType.MCP_SERVER_REACHABLE,
            StreamEventType.MCP_TOOL_ENABLED,
            StreamEventType.MCP_TOOL_DISABLED
        ]
    
    def clear_events(self):
        """Clear received events."""
        self.received_events.clear()


class TestEnhancedMCPManagerEventPublishing(unittest.TestCase):
    """Test suite for enhanced MCPManager event publishing."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a fresh MCPManager instance for testing
        self.manager = MCPManager()
        
        # Create test subscriber
        self.test_subscriber = TestEventSubscriber()
        self.manager.publisher.subscribe(self.test_subscriber)
        
        # Mock settings registry
        self.manager._settings_registry = MagicMock()
        self.manager._settings_registry.settings = MagicMock()
        
    def tearDown(self):
        """Clean up after each test method."""
        self.manager.publisher.clear_subscribers()
        
        # Reset manager state
        self.manager.mcp_clients = {}
        self.manager._tool_client_map = {}
        self.manager._managed_tools = {}
        self.manager.connected = False
    
    def test_publisher_property_access(self):
        """Test that publisher property is accessible."""
        publisher = self.manager.publisher
        self.assertIsNotNone(publisher)
        self.assertEqual(publisher.provider_name, "mcp_manager")
    
    def test_server_event_publishing_methods(self):
        """Test server event publishing helper methods."""
        # Test publishing server up event
        self.manager._publish_server_event(
            StreamEventType.MCP_SERVER_UP, 
            "/path/to/server.py",
            tool_count=5
        )
        
        # Check that event was published
        self.assertEqual(len(self.test_subscriber.received_events), 1)
        event = self.test_subscriber.received_events[0]
        
        self.assertEqual(event.type, StreamEventType.MCP_SERVER_UP)
        self.assertEqual(event.provider, "mcp_manager")
        self.assertEqual(event.data["server_path"], "/path/to/server.py")
        self.assertEqual(event.data["tool_count"], 5)
        
        # Clear events and test server down
        self.test_subscriber.clear_events()
        
        self.manager._publish_server_event(
            StreamEventType.MCP_SERVER_DOWN,
            "/path/to/server.py"
        )
        
        self.assertEqual(len(self.test_subscriber.received_events), 1)
        event = self.test_subscriber.received_events[0]
        
        self.assertEqual(event.type, StreamEventType.MCP_SERVER_DOWN)
        self.assertEqual(event.data["server_path"], "/path/to/server.py")
    
    def test_tool_event_publishing_methods(self):
        """Test tool event publishing helper methods."""
        # Create a mock MCPToolInfo
        from hatchling.core.llm.providers.subscription import MCPToolInfo
        
        tool_info = MCPToolInfo(
            name="test_tool",
            description="A test tool",
            schema={"type": "function"},
            server_path="/path/to/server.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        
        # Test publishing tool enabled event
        self.manager._publish_tool_event(
            StreamEventType.MCP_TOOL_ENABLED,
            "test_tool",
            tool_info
        )
        
        # Check that event was published
        self.assertEqual(len(self.test_subscriber.received_events), 1)
        event = self.test_subscriber.received_events[0]
        
        self.assertEqual(event.type, StreamEventType.MCP_TOOL_ENABLED)
        self.assertEqual(event.data["tool_name"], "test_tool")
        self.assertEqual(event.data["tool_description"], "A test tool")
        self.assertEqual(event.data["server_path"], "/path/to/server.py")
        self.assertEqual(event.data["status"], "enabled")
        self.assertEqual(event.data["reason"], "server_up")
    
    def test_tool_enable_disable_functionality(self):
        """Test tool enable/disable functionality with events."""
        # First, manually add a tool to managed tools
        from hatchling.core.llm.providers.subscription import MCPToolInfo
        
        tool_info = MCPToolInfo(
            name="test_tool",
            description="A test tool",
            schema={"type": "function"},
            server_path="/path/to/server.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        
        self.manager._managed_tools["test_tool"] = tool_info
        
        # Mock that server is connected
        mock_client = MagicMock()
        self.manager.mcp_clients["/path/to/server.py"] = mock_client
        
        # Test disabling tool
        result = self.manager.disable_tool("test_tool")
        self.assertTrue(result)
        
        # Check that tool status was updated
        updated_info = self.manager.get_tool_status("test_tool")
        self.assertEqual(updated_info.status, MCPToolStatus.DISABLED)
        self.assertEqual(updated_info.reason, MCPToolStatusReason.FROM_USER_DISABLED)
        
        # Check that event was published
        self.assertEqual(len(self.test_subscriber.received_events), 1)
        event = self.test_subscriber.received_events[0]
        self.assertEqual(event.type, StreamEventType.MCP_TOOL_DISABLED)
        
        # Clear events and test enabling tool
        self.test_subscriber.clear_events()
        
        result = self.manager.enable_tool("test_tool")
        self.assertTrue(result)
        
        # Check that tool status was updated
        updated_info = self.manager.get_tool_status("test_tool")
        self.assertEqual(updated_info.status, MCPToolStatus.ENABLED)
        self.assertEqual(updated_info.reason, MCPToolStatusReason.FROM_USER_ENABLED)
        
        # Check that event was published
        self.assertEqual(len(self.test_subscriber.received_events), 1)
        event = self.test_subscriber.received_events[0]
        self.assertEqual(event.type, StreamEventType.MCP_TOOL_ENABLED)
    
    def test_tool_management_queries(self):
        """Test tool status query methods."""
        from hatchling.core.llm.providers.subscription import MCPToolInfo
        
        # Add test tools
        enabled_tool = MCPToolInfo(
            name="enabled_tool",
            description="An enabled tool",
            schema={"type": "function"},
            server_path="/path/to/server1.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        
        disabled_tool = MCPToolInfo(
            name="disabled_tool",
            description="A disabled tool",
            schema={"type": "function"},
            server_path="/path/to/server2.py",
            status=MCPToolStatus.DISABLED,
            reason=MCPToolStatusReason.FROM_USER_DISABLED
        )
        
        self.manager._managed_tools["enabled_tool"] = enabled_tool
        self.manager._managed_tools["disabled_tool"] = disabled_tool
        
        # Test get_enabled_tools
        enabled_tools = self.manager.get_enabled_tools()
        self.assertEqual(len(enabled_tools), 1)
        self.assertIn("enabled_tool", enabled_tools)
        self.assertNotIn("disabled_tool", enabled_tools)
        
        # Test get_all_managed_tools
        all_tools = self.manager.get_all_managed_tools()
        self.assertEqual(len(all_tools), 2)
        self.assertIn("enabled_tool", all_tools)
        self.assertIn("disabled_tool", all_tools)
        
        # Test get_tool_status
        status = self.manager.get_tool_status("enabled_tool")
        self.assertIsNotNone(status)
        self.assertEqual(status.status, MCPToolStatus.ENABLED)
        
        status = self.manager.get_tool_status("nonexistent_tool")
        self.assertIsNone(status)
    
    def test_enable_disable_edge_cases(self):
        """Test edge cases for tool enable/disable."""
        # Test enabling nonexistent tool
        result = self.manager.enable_tool("nonexistent_tool")
        self.assertFalse(result)
        
        # Test disabling nonexistent tool
        result = self.manager.disable_tool("nonexistent_tool")
        self.assertFalse(result)
        
        # Add a tool but no server
        from hatchling.core.llm.providers.subscription import MCPToolInfo
        
        tool_info = MCPToolInfo(
            name="orphaned_tool",
            description="Tool without server",
            schema={"type": "function"},
            server_path="/path/to/missing_server.py",
            status=MCPToolStatus.DISABLED,
            reason=MCPToolStatusReason.FROM_SERVER_DOWN
        )
        
        self.manager._managed_tools["orphaned_tool"] = tool_info
        
        # Try to enable tool without server connection
        result = self.manager.enable_tool("orphaned_tool")
        self.assertFalse(result)  # Should fail because server is not connected


def run_mcp_manager_event_publishing_tests():
    """Run all MCPManager event publishing tests.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedMCPManagerEventPublishing))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_mcp_manager_event_publishing_tests()
    sys.exit(0 if success else 1)
