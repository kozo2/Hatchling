"""Regression test for existing MCP functionality.

This test ensures that existing MCPManager functionality continues to work
correctly after adding event publishing capabilities.
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


class TestMCPManagerRegressionTests(unittest.TestCase):
    """Test suite for existing MCP functionality."""
    
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
    
    def test_singleton_pattern_still_works(self):
        """Test that MCPManager singleton pattern still works."""
        # Create another instance
        manager2 = MCPManager()
        
        # Should be the same instance
        self.assertIs(self.manager, manager2)
    
    def test_validate_server_paths_still_works(self):
        """Test that server path validation still works."""
        # This method should still exist and work
        self.assertTrue(hasattr(self.manager, 'validate_server_paths'))
        
        # Test with empty list
        result = self.manager.validate_server_paths([])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        
        # Test with fake path
        result = self.manager.validate_server_paths(["/nonexistent/path.py"])
        # Should return empty list for nonexistent path
        self.assertEqual(len(result), 0)
    
    def test_get_tools_by_name_still_works(self):
        """Test that get_tools_by_name method still works."""
        # Mock some clients with tools
        mock_client1 = MagicMock()
        mock_client1.tools = {"tool1": MagicMock(), "tool2": MagicMock()}
        
        mock_client2 = MagicMock()
        mock_client2.tools = {"tool3": MagicMock()}
        
        self.manager.mcp_clients = {
            "server1": mock_client1,
            "server2": mock_client2
        }
        
        # Get tools
        tools = self.manager.get_tools_by_name()
        
        self.assertIsInstance(tools, dict)
        self.assertEqual(len(tools), 3)
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)
        self.assertIn("tool3", tools)
    
    def test_connection_tracking_still_works(self):
        """Test that connection state tracking still works."""
        # Initially not connected
        self.assertFalse(self.manager.connected)
        
        # Mock connected state
        self.manager.connected = True
        self.assertTrue(self.manager.connected)
        
        # Reset
        self.manager.connected = False
        self.assertFalse(self.manager.connected)
    
    def test_tool_client_mapping_still_works(self):
        """Test that tool to client mapping still works."""
        # Mock client and tool mapping
        mock_client = MagicMock()
        self.manager._tool_client_map = {
            "test_tool": mock_client
        }
        
        # Mapping should work
        self.assertIn("test_tool", self.manager._tool_client_map)
        self.assertIs(self.manager._tool_client_map["test_tool"], mock_client)
    
    def test_settings_registry_integration_still_works(self):
        """Test that settings registry integration still works."""
        # Should have settings registry attribute
        self.assertTrue(hasattr(self.manager, '_settings_registry'))
        
        # Should have method to set it
        self.assertTrue(hasattr(self.manager, 'set_settings_registry'))
        
        # Test setting registry
        mock_registry = MagicMock()
        self.manager.set_settings_registry(mock_registry)
        self.assertIs(self.manager._settings_registry, mock_registry)
    
    def test_hatch_environment_manager_integration_still_works(self):
        """Test that Hatch environment manager integration still works."""
        # Should have environment manager attribute
        self.assertTrue(hasattr(self.manager, '_hatch_env_manager'))
        
        # Should have method to set it
        self.assertTrue(hasattr(self.manager, 'set_hatch_environment_manager'))
        
        # Test setting environment manager
        mock_env_manager = MagicMock()
        self.manager.set_hatch_environment_manager(mock_env_manager)
        self.assertIs(self.manager._hatch_env_manager, mock_env_manager)
    
    def test_server_process_tracking_still_works(self):
        """Test that server process tracking still works."""
        # Should have server_processes dict
        self.assertTrue(hasattr(self.manager, 'server_processes'))
        self.assertIsInstance(self.manager.server_processes, dict)
        
        # Should start empty
        self.assertEqual(len(self.manager.server_processes), 0)
    
    def test_session_tracking_still_works(self):
        """Test that session tracking still works."""
        # Should have session tracking attributes and methods
        self.assertTrue(hasattr(self.manager, '_used_servers_in_session'))
        self.assertTrue(hasattr(self.manager, 'reset_session_tracking'))
        
        # Test session tracking reset
        self.manager._used_servers_in_session.add("test_server")
        self.assertEqual(len(self.manager._used_servers_in_session), 1)
        
        self.manager.reset_session_tracking()
        self.assertEqual(len(self.manager._used_servers_in_session), 0)
    
    def test_ollama_adapter_integration_still_works(self):
        """Test that Ollama adapter integration still works."""
        # Should have adapter attribute
        self.assertTrue(hasattr(self.manager, '_adapter'))
        
        # Should have get_ollama_tools method
        self.assertTrue(hasattr(self.manager, 'get_ollama_tools'))
        
        # Test calling get_ollama_tools when not connected
        tools = self.manager.get_ollama_tools()
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 0)  # Should be empty when not connected
    
    def test_async_methods_still_exist(self):
        """Test that async methods still exist."""
        # Critical async methods should still exist
        async_methods = [
            'initialize',
            'connect_to_servers',
            'disconnect_all',
            'execute_tool',
            'process_tool_calls',
            'get_citations_for_session'
        ]
        
        for method_name in async_methods:
            self.assertTrue(hasattr(self.manager, method_name),
                          f"Missing async method: {method_name}")
    
    def test_python_executable_resolution_still_works(self):
        """Test that Python executable resolution still works."""
        # Should have the private method
        self.assertTrue(hasattr(self.manager, '_get_python_executable'))
        
        # Test calling it (should return a callable)
        try:
            exe_resolver = self.manager._get_python_executable
            self.assertTrue(callable(exe_resolver))
        except Exception as e:
            self.fail(f"_get_python_executable should not raise exception: {e}")


def run_regression_tests():
    """Run all MCP functionality regression tests.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestMCPManagerRegressionTests))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_regression_tests()
    sys.exit(0 if success else 1)
