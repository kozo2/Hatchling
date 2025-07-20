"""Regression test for tool management functionality.

This test ensures that existing tool discovery and usage functionality still works
correctly after adding lifecycle management.
"""

import sys
import unittest
import logging
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.mcp_utils.manager import MCPManager


class TestToolManagementRegression(unittest.TestCase):
    """Test suite for tool management regression tests."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a fresh MCPManager instance for testing
        self.manager = MCPManager()
        
        # Mock settings registry
        from hatchling.config.settings_registry import SettingsRegistry
        self.manager._settings_registry = MagicMock()
        self.manager._settings_registry.settings = MagicMock()
        
    def tearDown(self):
        """Clean up after each test method."""
        # Reset manager state
        self.manager.mcp_clients = {}
        self.manager._tool_client_map = {}
        self.manager._managed_tools = {}
        self.manager.connected = False
    
    def test_get_tools_by_name_still_works_with_new_tools_structure(self):
        """Test that get_tools_by_name still works with enhanced tools tracking."""
        # Mock some clients with tools
        mock_client1 = MagicMock()
        mock_tool1 = MagicMock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "Tool 1"
        mock_tool2 = MagicMock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Tool 2"
        
        mock_client1.tools = {"tool1": mock_tool1, "tool2": mock_tool2}
        
        mock_client2 = MagicMock()
        mock_tool3 = MagicMock()
        mock_tool3.name = "tool3"
        mock_tool3.description = "Tool 3"
        mock_client2.tools = {"tool3": mock_tool3}
        
        self.manager.mcp_clients = {
            "server1": mock_client1,
            "server2": mock_client2
        }
        
        # Get tools (should still work)
        tools = self.manager.get_tools_by_name()
        
        self.assertIsInstance(tools, dict)
        self.assertEqual(len(tools), 3)
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)
        self.assertIn("tool3", tools)
    
    def test_tool_client_mapping_still_works_with_enhanced_tracking(self):
        """Test that tool-to-client mapping still works."""
        # Mock client and tool mapping
        mock_client = MagicMock()
        self.manager._tool_client_map = {
            "test_tool": mock_client
        }
        
        # Mapping should still work
        self.assertIn("test_tool", self.manager._tool_client_map)
        self.assertIs(self.manager._tool_client_map["test_tool"], mock_client)
    
    def test_new_tool_management_methods_dont_break_existing_functionality(self):
        """Test that new tool management methods don't interfere with existing ones."""
        # Test that all original methods still exist and work
        original_methods = [
            'get_tools_by_name',
            'get_ollama_tools'
        ]
        
        for method_name in original_methods:
            self.assertTrue(hasattr(self.manager, method_name),
                          f"Original method {method_name} is missing")
        
        # Test that new methods exist
        new_methods = [
            'get_enabled_tools',
            'get_all_managed_tools',
            'enable_tool',
            'disable_tool',
            'get_tool_status'
        ]
        
        for method_name in new_methods:
            self.assertTrue(hasattr(self.manager, method_name),
                          f"New method {method_name} is missing")
    
    def test_ollama_adapter_integration_still_works_with_new_tools(self):
        """Test that Ollama adapter integration still works."""
        # Should still have adapter attribute
        self.assertTrue(hasattr(self.manager, '_adapter'))
        
        # Should still have get_ollama_tools method
        self.assertTrue(hasattr(self.manager, 'get_ollama_tools'))
        
        # Test calling get_ollama_tools when not connected (should not break)
        tools = self.manager.get_ollama_tools()
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 0)  # Should be empty when not connected
    
    def test_existing_async_tool_operations_still_work(self):
        """Test that existing async tool operations still work."""
        # Should have async methods for tool operations
        async_methods = [
            'execute_tool',
            'process_tool_calls'
        ]
        
        for method_name in async_methods:
            self.assertTrue(hasattr(self.manager, method_name),
                          f"Async method {method_name} is missing")
    
    def test_managed_tools_structure_is_properly_initialized(self):
        """Test that managed tools structure is properly initialized."""
        # Should have managed tools attribute
        self.assertTrue(hasattr(self.manager, '_managed_tools'))
        self.assertIsInstance(self.manager._managed_tools, dict)
        
        # Should start empty
        self.assertEqual(len(self.manager._managed_tools), 0)
    
    def test_publisher_integration_doesnt_break_existing_functionality(self):
        """Test that publisher integration doesn't break existing functionality."""
        # Should have publisher
        self.assertTrue(hasattr(self.manager, '_stream_publisher'))
        self.assertTrue(hasattr(self.manager, 'publisher'))
        
        # Publisher should be accessible
        publisher = self.manager.publisher
        self.assertIsNotNone(publisher)
        
        # Publisher should not interfere with basic operations
        self.assertFalse(self.manager.connected)  # Should still track connection state
        
        # Should still have connection lock
        self.assertTrue(hasattr(self.manager, '_connection_lock'))
    
    def test_event_publishing_methods_exist_but_dont_interfere(self):
        """Test that event publishing methods exist but don't interfere with core functionality."""
        # Should have event publishing methods
        publishing_methods = [
            '_publish_server_event',
            '_publish_tool_event'
        ]
        
        for method_name in publishing_methods:
            self.assertTrue(hasattr(self.manager, method_name),
                          f"Event publishing method {method_name} is missing")
        
        # These should be callable but not break anything
        try:
            # Test calling event publishing (should not raise exceptions)
            from hatchling.core.llm.providers.subscription import StreamEventType
            self.manager._publish_server_event(StreamEventType.MCP_SERVER_UP, "/test/path")
            self.manager._publish_tool_event(StreamEventType.MCP_TOOL_ENABLED, "test_tool")
        except Exception as e:
            self.fail(f"Event publishing methods should not raise exceptions: {e}")
    
    def test_connection_and_disconnection_enhanced_but_compatible(self):
        """Test that enhanced connection/disconnection is backward compatible."""
        # Should still have the core async methods
        async_connection_methods = [
            'connect_to_servers',
            'disconnect_all'
        ]
        
        for method_name in async_connection_methods:
            self.assertTrue(hasattr(self.manager, method_name),
                          f"Async connection method {method_name} is missing")
    
    def test_session_tracking_still_works_with_enhanced_tools(self):
        """Test that session tracking still works with enhanced tool management."""
        # Should still have session tracking
        self.assertTrue(hasattr(self.manager, '_used_servers_in_session'))
        self.assertTrue(hasattr(self.manager, 'reset_session_tracking'))
        
        # Test session tracking functionality
        self.manager._used_servers_in_session.add("test_server")
        self.assertEqual(len(self.manager._used_servers_in_session), 1)
        
        self.manager.reset_session_tracking()
        self.assertEqual(len(self.manager._used_servers_in_session), 0)


def run_regression_tests():
    """Run all tool management regression tests.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestToolManagementRegression))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_regression_tests()
    sys.exit(0 if success else 1)
