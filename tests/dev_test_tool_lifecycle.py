"""Development test for Phase 3: Tool Lifecycle Management.

This test validates that ToolLifecycleSubscriber correctly manages tool caches
based on MCP events and that tool adapters work correctly.
"""

import sys
import unittest
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.core.llm.providers.subscription import (
    StreamEventType,
    StreamEvent,
    StreamPublisher,
    ToolLifecycleSubscriber,
    MCPToolStatus,
    MCPToolStatusReason,
    MCPToolInfo
)
from hatchling.core.llm.tool_management.adapters import (
    OpenAIMCPToolAdapter,
    OllamaMCPToolAdapter,
    MCPToolAdapterFactory
)


class TestToolLifecycleManagement(unittest.TestCase):
    """Test suite for tool lifecycle management."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.publisher = StreamPublisher("test_mcp_manager")
        self.lifecycle_subscriber = ToolLifecycleSubscriber("test_provider")
        self.publisher.subscribe(self.lifecycle_subscriber)
        
    def tearDown(self):
        """Clean up after each test method."""
        self.publisher.clear_subscribers()
    
    def test_tool_lifecycle_subscriber_initialization(self):
        """Test that ToolLifecycleSubscriber initializes correctly."""
        subscriber = ToolLifecycleSubscriber("test_provider")
        self.assertEqual(subscriber.provider_name, "test_provider")
        self.assertEqual(len(subscriber._tool_cache), 0)
        
        # Check subscribed events
        subscribed_events = subscriber.get_subscribed_events()
        expected_events = [
            StreamEventType.MCP_SERVER_UP,
            StreamEventType.MCP_SERVER_DOWN,
            StreamEventType.MCP_SERVER_UNREACHABLE,
            StreamEventType.MCP_SERVER_REACHABLE,
            StreamEventType.MCP_TOOL_ENABLED,
            StreamEventType.MCP_TOOL_DISABLED
        ]
        
        for event_type in expected_events:
            self.assertIn(event_type, subscribed_events)
    
    def test_tool_enabled_event_handling(self):
        """Test handling of tool enabled events."""
        # Publish a tool enabled event
        self.publisher.publish(StreamEventType.MCP_TOOL_ENABLED, {
            "tool_name": "test_tool",
            "tool_description": "A test tool",
            "tool_schema": {"type": "function", "parameters": {"type": "object"}},
            "server_path": "/path/to/server.py",
            "status": "enabled",
            "reason": "FROM_SERVER_UP"
        })
        
        # Check that tool was added to cache
        enabled_tools = self.lifecycle_subscriber.get_enabled_tools()
        self.assertEqual(len(enabled_tools), 1)
        self.assertIn("test_tool", enabled_tools)
        
        tool_info = enabled_tools["test_tool"]
        self.assertEqual(tool_info.name, "test_tool")
        self.assertEqual(tool_info.description, "A test tool")
        self.assertEqual(tool_info.server_path, "/path/to/server.py")
        self.assertEqual(tool_info.status, MCPToolStatus.ENABLED)
        self.assertEqual(tool_info.reason, MCPToolStatusReason.FROM_SERVER_UP)
    
    def test_tool_disabled_event_handling(self):
        """Test handling of tool disabled events."""
        # First enable a tool
        self.lifecycle_subscriber._tool_cache["test_tool"] = MCPToolInfo(
            name="test_tool",
            description="A test tool",
            schema={"type": "function"},
            server_path="/path/to/server.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        
        # Publish tool disabled event
        self.publisher.publish(StreamEventType.MCP_TOOL_DISABLED, {
            "tool_name": "test_tool",
            "reason": "FROM_USER_DISABLED"
        })
        
        # Check that tool status was updated
        all_tools = self.lifecycle_subscriber.get_all_tools()
        self.assertEqual(len(all_tools), 1)
        
        tool_info = all_tools["test_tool"]
        self.assertEqual(tool_info.status, MCPToolStatus.DISABLED)
        self.assertEqual(tool_info.reason, MCPToolStatusReason.FROM_USER_DISABLED)
        
        # Check that enabled tools list is empty
        enabled_tools = self.lifecycle_subscriber.get_enabled_tools()
        self.assertEqual(len(enabled_tools), 0)
    
    def test_server_down_event_handling(self):
        """Test handling of server down events."""
        # Add tools from two different servers
        self.lifecycle_subscriber._tool_cache = {
            "tool1": MCPToolInfo(
                name="tool1",
                description="Tool 1",
                schema={"type": "function"},
                server_path="/path/to/server1.py",
                status=MCPToolStatus.ENABLED,
                reason=MCPToolStatusReason.FROM_SERVER_UP
            ),
            "tool2": MCPToolInfo(
                name="tool2",
                description="Tool 2",
                schema={"type": "function"},
                server_path="/path/to/server2.py",
                status=MCPToolStatus.ENABLED,
                reason=MCPToolStatusReason.FROM_SERVER_UP
            )
        }
        
        # Publish server down event for server1
        self.publisher.publish(StreamEventType.MCP_SERVER_DOWN, {
            "server_path": "/path/to/server1.py"
        })
        
        # Check that only tool1 was disabled
        tool1 = self.lifecycle_subscriber._tool_cache["tool1"]
        tool2 = self.lifecycle_subscriber._tool_cache["tool2"]
        
        self.assertEqual(tool1.status, MCPToolStatus.DISABLED)
        self.assertEqual(tool1.reason, MCPToolStatusReason.FROM_SERVER_DOWN)
        
        self.assertEqual(tool2.status, MCPToolStatus.ENABLED)
        self.assertEqual(tool2.reason, MCPToolStatusReason.FROM_SERVER_UP)
    
    def test_server_unreachable_and_reachable_handling(self):
        """Test handling of server unreachable and reachable events."""
        # Add a tool from a server
        self.lifecycle_subscriber._tool_cache["test_tool"] = MCPToolInfo(
            name="test_tool",
            description="Test tool",
            schema={"type": "function"},
            server_path="/path/to/server.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        
        # Publish server unreachable event
        self.publisher.publish(StreamEventType.MCP_SERVER_UNREACHABLE, {
            "server_path": "/path/to/server.py",
            "error": "Connection timeout"
        })
        
        # Check that tool was disabled due to unreachable server
        tool_info = self.lifecycle_subscriber._tool_cache["test_tool"]
        self.assertEqual(tool_info.status, MCPToolStatus.DISABLED)
        self.assertEqual(tool_info.reason, MCPToolStatusReason.FROM_SERVER_UNREACHABLE)
        
        # Publish server reachable event
        self.publisher.publish(StreamEventType.MCP_SERVER_REACHABLE, {
            "server_path": "/path/to/server.py"
        })
        
        # Check that tool was re-enabled
        tool_info = self.lifecycle_subscriber._tool_cache["test_tool"]
        self.assertEqual(tool_info.status, MCPToolStatus.ENABLED)
        self.assertEqual(tool_info.reason, MCPToolStatusReason.FROM_SERVER_REACHABLE)
    
    def test_tool_count_reporting(self):
        """Test tool count reporting functionality."""
        # Add mix of enabled and disabled tools
        self.lifecycle_subscriber._tool_cache = {
            "enabled_tool1": MCPToolInfo(
                name="enabled_tool1",
                description="Enabled tool 1",
                schema={"type": "function"},
                server_path="/path/to/server.py",
                status=MCPToolStatus.ENABLED,
                reason=MCPToolStatusReason.FROM_SERVER_UP
            ),
            "enabled_tool2": MCPToolInfo(
                name="enabled_tool2", 
                description="Enabled tool 2",
                schema={"type": "function"},
                server_path="/path/to/server.py",
                status=MCPToolStatus.ENABLED,
                reason=MCPToolStatusReason.FROM_SERVER_UP
            ),
            "disabled_tool": MCPToolInfo(
                name="disabled_tool",
                description="Disabled tool",
                schema={"type": "function"},
                server_path="/path/to/server.py",
                status=MCPToolStatus.DISABLED,
                reason=MCPToolStatusReason.FROM_USER_DISABLED
            )
        }
        
        # Test tool counts
        counts = self.lifecycle_subscriber.get_tool_count()
        self.assertEqual(counts["enabled"], 2)
        self.assertEqual(counts["disabled"], 1)
    
    def test_cache_clear_functionality(self):
        """Test cache clearing functionality."""
        # Add tools to cache
        self.lifecycle_subscriber._tool_cache["test_tool"] = MCPToolInfo(
            name="test_tool",
            description="Test tool",
            schema={"type": "function"},
            server_path="/path/to/server.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        
        self.assertEqual(len(self.lifecycle_subscriber._tool_cache), 1)
        
        # Clear cache
        self.lifecycle_subscriber.clear_cache()
        self.assertEqual(len(self.lifecycle_subscriber._tool_cache), 0)


class TestToolAdapters(unittest.TestCase):
    """Test suite for tool format adapters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_tool = MCPToolInfo(
            name="example_function",
            description="An example function for testing",
            schema={
                "type": "function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Input text to process"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of iterations",
                            "default": 1
                        }
                    },
                    "required": ["input"]
                }
            },
            server_path="/path/to/server.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
    
    def test_openai_adapter(self):
        """Test OpenAI tool adapter."""
        adapter = OpenAIMCPToolAdapter("openai")
        converted = adapter.convert_tool(self.sample_tool)
        
        # Check structure
        self.assertEqual(converted["type"], "function")
        self.assertIn("function", converted)
        
        function = converted["function"]
        self.assertEqual(function["name"], "example_function")
        self.assertEqual(function["description"], "An example function for testing")
        self.assertIn("parameters", function)
        
        # Check that tool info was updated with provider format
        self.assertIsNotNone(self.sample_tool.provider_format)
        self.assertEqual(self.sample_tool.provider_format, converted)
    
    def test_ollama_adapter(self):
        """Test Ollama tool adapter."""
        adapter = OllamaMCPToolAdapter("ollama")
        converted = adapter.convert_tool(self.sample_tool)
        
        # Check structure (similar to OpenAI)
        self.assertEqual(converted["type"], "function")
        self.assertIn("function", converted)
        
        function = converted["function"]
        self.assertEqual(function["name"], "example_function")
        self.assertEqual(function["description"], "An example function for testing")
        self.assertIn("parameters", function)
        
        # Check that tool info was updated with provider format
        self.assertIsNotNone(self.sample_tool.provider_format)
        self.assertEqual(self.sample_tool.provider_format, converted)
    
    def test_adapter_factory(self):
        """Test tool adapter factory."""
        # Test creating supported adapters
        openai_adapter = MCPToolAdapterFactory.create_adapter("openai")
        self.assertIsInstance(openai_adapter, OpenAIMCPToolAdapter)
        
        ollama_adapter = MCPToolAdapterFactory.create_adapter("ollama")
        self.assertIsInstance(ollama_adapter, OllamaMCPToolAdapter)
        
        # Test case insensitivity
        openai_adapter2 = MCPToolAdapterFactory.create_adapter("OPENAI")
        self.assertIsInstance(openai_adapter2, OpenAIMCPToolAdapter)
        
        # Test unsupported provider
        unknown_adapter = MCPToolAdapterFactory.create_adapter("unknown")
        self.assertIsNone(unknown_adapter)
        
        # Test supported providers list
        providers = MCPToolAdapterFactory.get_supported_providers()
        self.assertIn("openai", providers)
        self.assertIn("ollama", providers)
    
    def test_convert_multiple_tools(self):
        """Test converting multiple tools."""
        adapter = OpenAIMCPToolAdapter("openai")
        
        # Create additional tool
        tool2 = MCPToolInfo(
            name="tool2",
            description="Second tool",
            schema={"type": "function", "parameters": {"type": "object"}},
            server_path="/path/to/server.py",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        
        tools = {
            "example_function": self.sample_tool,
            "tool2": tool2
        }
        
        converted_tools = adapter.convert_tools(tools)
        self.assertEqual(len(converted_tools), 2)
        
        # Check that both tools were converted
        tool_names = [t["function"]["name"] for t in converted_tools]
        self.assertIn("example_function", tool_names)
        self.assertIn("tool2", tool_names)


def run_tool_lifecycle_management_tests():
    """Run all tool lifecycle management tests.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestToolLifecycleManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestToolAdapters))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_tool_lifecycle_management_tests()
    sys.exit(0 if success else 1)
