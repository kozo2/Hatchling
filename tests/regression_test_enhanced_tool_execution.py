"""
This test ensures that existing tool execution functionality still works
correctly after adding event-driven architecture.
"""

import sys
import unittest
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_decorators import regression_test

from hatchling.mcp_utils.mcp_tool_execution import MCPToolExecution


class MockAppSettings:
    """Mock AppSettings for testing."""
    
    def __init__(self):
        self.llm = MagicMock()
        self.llm.provider_name.return_value = "openai"
        self.llm.get_active_model.return_value = "gpt-4"
        self.tool_calling = MagicMock()
        self.tool_calling.max_iterations = 5
        self.tool_calling.max_working_time = 60


class TestToolExecutionRegression(unittest.TestCase):
    """Test suite for tool execution regression tests."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_settings = MockAppSettings()
        
        # Mock the logging manager to avoid file system dependencies
        with patch('hatchling.mcp_utils.mcp_tool_execution.logging_manager') as mock_logging:
            mock_logging.get_session.return_value = logging.getLogger("test")
            self.tool_execution = MCPToolExecution(self.mock_settings)
    
    @regression_test
    def test_tool_execution_manager_renamed_to_mcp_tool_execution(self):
        """Test that the renamed class still provides the same interface."""
        # Verify the class exists and has expected attributes
        self.assertIsInstance(self.tool_execution, MCPToolExecution)
        self.assertTrue(hasattr(self.tool_execution, 'settings'))
        self.assertTrue(hasattr(self.tool_execution, 'current_tool_call_iteration'))
        self.assertTrue(hasattr(self.tool_execution, 'tool_call_start_time'))
        self.assertTrue(hasattr(self.tool_execution, 'root_tool_query'))
        self.assertTrue(hasattr(self.tool_execution, 'stream_publisher'))
    
    @regression_test
    def test_mcp_manager_integration_still_works(self):
        """Test that MCP manager integration still works as expected."""
        # MCPToolExecution should still integrate with mcp_manager for tool execution
        self.assertTrue(hasattr(self.tool_execution, 'execute_tool'))
        self.assertTrue(asyncio.iscoroutinefunction(self.tool_execution.execute_tool))
        
        # The core execute_tool method should still exist and be functional
        method = getattr(self.tool_execution, 'execute_tool')
        self.assertTrue(asyncio.iscoroutinefunction(method))
    
    @regression_test
    def test_tool_execution_workflow_still_works(self):
        """Test that tool execution workflow still works."""
        # Should have the core tool execution methods
        self.assertTrue(hasattr(self.tool_execution, 'execute_tool'))
        self.assertTrue(hasattr(self.tool_execution, 'execute_tool_sync'))
        # Execute_tool should be async, execute_tool_sync should be sync
        self.assertTrue(asyncio.iscoroutinefunction(self.tool_execution.execute_tool))
        self.assertFalse(asyncio.iscoroutinefunction(self.tool_execution.execute_tool_sync))
    
    @regression_test
    def test_reset_for_new_query_method_still_works(self):
        """Test that reset_for_new_query method still works."""
        self.assertTrue(hasattr(self.tool_execution, 'reset_for_new_query'))
        self.assertTrue(callable(getattr(self.tool_execution, 'reset_for_new_query')))
        
        # Test the functionality
        test_query = "Test query for regression"
        self.tool_execution.current_tool_call_iteration = 10  # Set non-zero value
        
        self.tool_execution.reset_for_new_query(test_query)
        
        # Verify reset behavior
        self.assertEqual(self.tool_execution.current_tool_call_iteration, 0)
        self.assertEqual(self.tool_execution.root_tool_query, test_query)
        self.assertIsNotNone(self.tool_execution.tool_call_start_time)
    
    @regression_test
    def test_execute_tool_method_still_exists_and_async(self):
        """Test that execute_tool method still exists and is async."""
        self.assertTrue(hasattr(self.tool_execution, 'execute_tool'))
        method = getattr(self.tool_execution, 'execute_tool')
        self.assertTrue(callable(method))
        self.assertTrue(asyncio.iscoroutinefunction(method))
    
    @patch('hatchling.core.llm.mcp_tool_execution.mcp_manager')
    async def test_execute_tool_basic_functionality_still_works(self, mock_mcp_manager):
        """Test that basic execute_tool functionality still works."""
        # Mock successful tool execution
        mock_response = {"content": "Test result"}
        mock_mcp_manager.process_tool_calls.return_value = [mock_response]
        
        # Execute tool
        result = await self.tool_execution.execute_tool(
            tool_id="regression_test_123",
            function_name="regression_test_function",
            arguments={"input": "test"}
        )
        
        # Verify result structure matches expected format
        self.assertIsInstance(result, dict)
        if result:  # If not None
            self.assertIn("role", result)
            self.assertIn("tool_call_id", result)
            self.assertIn("name", result)
            self.assertIn("content", result)
            self.assertEqual(result["role"], "tool")
            self.assertEqual(result["tool_call_id"], "regression_test_123")
            self.assertEqual(result["name"], "regression_test_function")
    
    @regression_test
    def test_execute_tool_sync_method_still_exists(self):
        """Test that execute_tool_sync method exists and is synchronous."""
        self.assertTrue(hasattr(self.tool_execution, 'execute_tool_sync'))
        method = getattr(self.tool_execution, 'execute_tool_sync')
        self.assertTrue(callable(method))
        self.assertFalse(asyncio.iscoroutinefunction(method))
    
    async def test_execute_tool_argument_handling_still_works(self):
        """Test that execute_tool handles arguments correctly through ToolCallParsedResult."""
        from hatchling.core.llm.data_structures import ToolCallParsedResult
        
        # Create a ToolCallParsedResult with test data
        tool_call = ToolCallParsedResult(
            tool_call_id="test_id",
            function_name="test_function",
            arguments={"param1": "value1", "param2": 42}
        )
        
        # Mock mcp_manager.execute_tool to avoid external dependencies
        with patch('hatchling.mcp_utils.mcp_tool_execution.mcp_manager') as mock_mcp_manager:
            mock_result = MagicMock()
            mock_result.isError = False
            mock_mcp_manager.execute_tool.return_value = mock_result
            
            # Test that execute_tool accepts the ToolCallParsedResult
            await self.tool_execution.execute_tool(tool_call)
            
            # Verify mcp_manager.execute_tool was called with correct parameters
            mock_mcp_manager.execute_tool.assert_called_once_with(
                tool_name="test_function",
                arguments={"param1": "value1", "param2": 42}
            )
    
    @regression_test
    def test_event_publisher_integration_still_works(self):
        """Test that stream publisher integration still works."""
        # The new interface should have stream_publisher property
        self.assertTrue(hasattr(self.tool_execution, 'stream_publisher'))
        
        # Should be able to access the publisher
        publisher = self.tool_execution.stream_publisher
        self.assertIsNotNone(publisher)
        
        # Should have the necessary methods for event publishing
        self.assertTrue(hasattr(publisher, 'publish'))
        self.assertTrue(hasattr(publisher, 'subscribe'))
    
    @regression_test
    def test_tool_calling_iteration_tracking_still_works(self):
        """Test that tool calling iteration tracking still works."""
        # Test initial state
        self.assertEqual(self.tool_execution.current_tool_call_iteration, 0)
        
        # Test manual increment (simulate what execute_tool does)
        original_iteration = self.tool_execution.current_tool_call_iteration
        self.tool_execution.current_tool_call_iteration += 1
        
        self.assertEqual(self.tool_execution.current_tool_call_iteration, original_iteration + 1)
    
    @regression_test
    def test_event_publishing_capabilities_still_work(self):
        """Test that event publishing capabilities still work."""
        # Should have internal event publishing method
        self.assertTrue(hasattr(self.tool_execution, '_event_publisher'))
        
        # Test that events can be published (basic functionality test)
        publisher = self.tool_execution.stream_publisher
        
        # Should not raise an exception when publishing events
        try:
            from hatchling.core.llm.streaming_management import StreamEventType
            publisher.publish(StreamEventType.MCP_TOOL_CALL_DISPATCHED, {"test": "data"})
        except Exception as e:
            self.fail(f"Event publishing should not raise exception: {e}")
    
    @regression_test
    def test_settings_integration_still_works(self):
        """Test that settings integration still works."""
        # Verify settings are stored and accessible
        self.assertEqual(self.tool_execution.settings, self.mock_settings)
        
        # Test that provider detection still works through settings
        provider = self.tool_execution.settings.llm.provider_name()
        self.assertEqual(provider, "openai")  # From our mock
        
        # Fix the model access for mock
        model = self.tool_execution.settings.llm.get_active_model()
        self.assertEqual(model, "gpt-4")  # From our mock
    
    @regression_test
    def test_new_event_publisher_doesnt_break_existing_functionality(self):
        """Test that the new EventPublisher doesn't interfere with existing functionality."""
        # Verify the stream publisher exists (new functionality)
        self.assertTrue(hasattr(self.tool_execution, 'stream_publisher'))
        self.assertTrue(hasattr(self.tool_execution, '_event_publisher'))
        
        # Verify that having a stream publisher doesn't break basic operations
        test_query = "Test query with publisher"
        self.tool_execution.reset_for_new_query(test_query)
        
        # Should still work normally
        self.assertEqual(self.tool_execution.root_tool_query, test_query)
        self.assertEqual(self.tool_execution.current_tool_call_iteration, 0)


def run_tool_execution_regression_tests():
    """Run all tool execution regression tests.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestToolExecutionRegression))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_tool_execution_regression_tests()
    sys.exit(0 if success else 1)
