"""Integration tests for the complete tool call flow.

These tests validate the end-to-end tool call execution including:
1. Tool call detection from LLM responses
2. Event publishing and subscription
3. MCP tool execution
4. Response integration back to LLM
5. CLI chat integration with tool calls
"""

import sys
import unittest
import logging
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, call
from typing import List, Dict, Any

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.core.llm.streaming_management import (
    StreamEvent, StreamEventType, StreamPublisher, StreamSubscriber
)
from hatchling.mcp_utils.mcp_tool_execution import MCPToolExecution
from hatchling.mcp_utils.mcp_tool_call_subscriber import MCPToolCallSubscriber
from hatchling.core.llm.chat_session import ChatSession
from hatchling.config.llm_settings import ELLMProvider
from hatchling.ui.cli_chat import CLIChat
from hatchling.config.settings_registry import SettingsRegistry
from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus
from hatchling.core.llm.tool_management.tool_call_parse_strategies import (
    OpenAIToolCallParseStrategy, OllamaToolCallParseStrategy
)


class MockAppSettings:
    """Mock AppSettings for testing."""
    
    def __init__(self):
        self.llm = MagicMock()
        self.llm.provider_name = "openai"  # Use string directly, not MagicMock return_value
        self.llm.provider_enum = ELLMProvider.OPENAI
        self.llm.model = "gpt-4"
        self.llm.get_active_model.return_value = "gpt-4"
        self.openai = MagicMock()
        self.openai.api_key = "test-api-key"  # Add missing OpenAI API key
        self.tool_calling = MagicMock()
        self.tool_calling.max_iterations = 5
        self.tool_calling.max_working_time = 60
        self.paths = MagicMock()
        self.paths.envs_dir = Path(tempfile.mkdtemp())
        
        # Add ollama settings for OllamaProvider tests
        self.ollama = MagicMock()
        self.ollama.api_url = "http://localhost:11434"
        self.ollama.num_ctx = 2048
        self.ollama.repeat_last_n = 64
        self.ollama.repeat_penalty = 1.1
        self.ollama.temperature = 0.8
        self.ollama.seed = None
        self.ollama.num_predict = -1
        self.ollama.top_k = 40
        self.ollama.top_p = 0.9
        self.ollama.min_p = 0.0
        self.ollama.stop = None


class MockSettingsRegistry:
    """Mock settings registry for testing."""
    
    def __init__(self):
        self.settings = MockAppSettings()
    
    def get(self, key, default=None):
        return default
    
    def list_settings(self, filter_regex=None):
        """Mock list_settings method that returns basic test settings."""
        return [
            {
                "category_name": "llm",
                "category_display_name": "LLM Settings", 
                "category_description": "Large Language Model configuration",
                "name": "openai_api_key",
                "display_name": "OpenAI API Key",
                "current_value": "test-api-key",
                "default_value": "",
                "description": "API key for OpenAI services",
                "hint": "",
                "access_level": "NORMAL",
                "type": "str"
            },
            {
                "category_name": "ollama",
                "category_display_name": "Ollama Settings",
                "category_description": "Ollama local LLM configuration", 
                "name": "api_url",
                "display_name": "API URL",
                "current_value": "http://localhost:11434",
                "default_value": "http://localhost:11434",
                "description": "URL for Ollama API endpoint",
                "hint": "",
                "access_level": "NORMAL", 
                "type": "str"
            }
        ]


class ToolCallEventCollector(StreamSubscriber):
    """Test subscriber that collects tool call events for validation."""
    
    def __init__(self):
        self.events = []
        self.tool_call_events = []
        self.tool_result_events = []
        self.tool_error_events = []
    
    def get_subscribed_events(self):
        return [
            StreamEventType.TOOL_CALL,
            StreamEventType.TOOL_CALL_DISPATCHED,
            StreamEventType.TOOL_CALL_PROGRESS,
            StreamEventType.TOOL_CALL_RESULT,
            StreamEventType.TOOL_CALL_ERROR
        ]
    
    def on_event(self, event: StreamEvent) -> None:
        self.events.append(event)
        
        if event.type == StreamEventType.TOOL_CALL:
            self.tool_call_events.append(event)
        elif event.type == StreamEventType.TOOL_CALL_RESULT:
            self.tool_result_events.append(event)
        elif event.type == StreamEventType.TOOL_CALL_ERROR:
            self.tool_error_events.append(event)


class AsyncTestCase(unittest.TestCase):
    """Base test case with async support."""
    
    def run_async(self, async_test):
        """Helper to run async tests."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(async_test)
        finally:
            loop.close()


class TestToolCallFlowIntegration(AsyncTestCase):
    """Integration tests for the complete tool call flow."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_settings = MockAppSettings()
        self.event_collector = ToolCallEventCollector()
        
        # Setup tool execution with mocked logging
        with patch('hatchling.mcp_utils.mcp_tool_execution.logging_manager') as mock_logging:
            mock_logging.get_session.return_value = logging.getLogger("test")
            self.tool_execution = MCPToolExecution(self.mock_settings)
        
        # Subscribe event collector to tool execution events
        self.tool_execution.stream_publisher.subscribe(self.event_collector)
        
        # Setup tool call subscriber
        self.tool_call_subscriber = MCPToolCallSubscriber(self.tool_execution)
        
        # Setup logger
        self.logger = logging.getLogger("test_tool_call_flow")
        self.logger.setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up after each test method."""
        self.tool_execution.stream_publisher.clear_subscribers()
    
    def test_openai_tool_call_parsing_and_execution(self):
        """Test OpenAI tool call parsing and execution flow."""
        async def async_test():
            # Create OpenAI-style tool call event
            tool_call_event = StreamEvent(
                type=StreamEventType.TOOL_CALL,
                data={
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "test_function",
                        "arguments": '{"param1": "value1", "param2": 42}'
                    }
                },
                provider=ELLMProvider.OPENAI
            )
            
            # Mock the MCP manager's execute_tool method
            with patch('hatchling.mcp_utils.mcp_tool_execution.mcp_manager') as mock_mcp:
                mock_response = {"content": '{"result": "success", "data": "test_result"}'}
                mock_mcp.execute_tool = AsyncMock(return_value=[mock_response])
                
                # Process the tool call event
                self.tool_call_subscriber.on_event(tool_call_event)
                
                # Allow some time for async processing
                await asyncio.sleep(0.1)
                
                # Verify events were published
                events = self.event_collector.events
                self.assertGreater(len(events), 0, "Tool call events should be published")
                
                # Check for TOOL_CALL_DISPATCHED event
                dispatched_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_DISPATCHED]
                self.assertGreaterEqual(len(dispatched_events), 1, "Should have at least one dispatched event")
                
                # Find the correct dispatched event
                correct_event = None
                for event in dispatched_events:
                    if event.data.get("tool_id") == "call_123":
                        correct_event = event
                        break
                
                self.assertIsNotNone(correct_event, "Should find the correct tool call event")
                self.assertEqual(correct_event.data["function_name"], "test_function")
                self.assertEqual(correct_event.data["arguments"], {"param1": "value1", "param2": 42})
        
        self.run_async(async_test())
    
    def test_ollama_tool_call_parsing_and_execution(self):
        """Test Ollama tool call parsing and execution flow."""
        async def async_test():
            # Create Ollama-style tool call event
            tool_call_event = StreamEvent(
                type=StreamEventType.TOOL_CALL,
                data={
                    "tool_calls": [
                        {
                            "id": "call_456",
                            "function": {
                                "name": "test_function",
                                "arguments": {"param1": "value1", "param2": 42}
                            }
                        }
                    ]
                },
                provider=ELLMProvider.OLLAMA
            )
            
            # Mock the MCP manager's execute_tool method
            with patch('hatchling.mcp_utils.mcp_tool_execution.mcp_manager') as mock_mcp:
                mock_response = {"content": '{"result": "success", "data": "test_result"}'}
                mock_mcp.execute_tool = AsyncMock(return_value=[mock_response])
                
                # Process the tool call event
                self.tool_call_subscriber.on_event(tool_call_event)
                
                # Allow some time for async processing
                await asyncio.sleep(0.1)
                
                # Verify events were published
                events = self.event_collector.events
                self.assertGreater(len(events), 0, "Tool call events should be published")
                
                # Check for TOOL_CALL_DISPATCHED event
                dispatched_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_DISPATCHED]
                self.assertEqual(len(dispatched_events), 1, "Should have one dispatched event")
        
        self.run_async(async_test())
    
    def test_tool_execution_error_handling(self):
        """Test tool execution error handling and event publishing."""
        async def async_test():
            # Create tool call event
            tool_call_event = StreamEvent(
                type=StreamEventType.TOOL_CALL,
                data={
                    "id": "call_error",
                    "type": "function",
                    "function": {
                        "name": "error_function",
                        "arguments": '{"param": "value"}'
                    }
                },
                provider=ELLMProvider.OPENAI
            )
            
            # Mock the MCP manager to raise an exception
            with patch('hatchling.mcp_utils.mcp_tool_execution.mcp_manager') as mock_mcp:
                mock_mcp.execute_tool = AsyncMock(side_effect=Exception("Test error"))
                
                # Process the tool call event
                self.tool_call_subscriber.on_event(tool_call_event)
                
                # Allow some time for async processing
                await asyncio.sleep(0.1)
                
                # Verify error events were published
                error_events = [e for e in self.event_collector.events if e.type == StreamEventType.TOOL_CALL_ERROR]
                self.assertEqual(len(error_events), 1, "Should have one error event")
                
                error_event = error_events[0]
                self.assertEqual(error_event.data["tool_id"], "call_error")
                self.assertEqual(error_event.data["error"], "Test error")
                self.assertEqual(error_event.data["status"], "execution_error")
        
        self.run_async(async_test())
    
    def test_tool_payload_filtering_with_enabled_disabled_tools(self):
        """Test tool filtering occurs at payload level via add_tools_to_payload method."""
        async def async_test():
            # Mock a provider that implements add_tools_to_payload
            mock_provider = MagicMock()
            
            # Mock tool lifecycle subscriber to simulate enabled/disabled tools
            mock_tool_subscriber = MagicMock()
            
            # Setup mock tools - some enabled, some disabled
            all_tools = {
                "enabled_tool": MagicMock(name="enabled_tool"),
                "disabled_tool": MagicMock(name="disabled_tool")
            }
            enabled_tools = {
                "enabled_tool": MagicMock(provider_format={"name": "enabled_tool", "type": "function"})
            }
            
            mock_tool_subscriber.get_all_tools.return_value = all_tools
            mock_tool_subscriber.get_enabled_tools.return_value = enabled_tools
            mock_tool_subscriber.prettied_reason.return_value = "Tool is disabled for testing"
            
            # Test case 1: No specific tools requested (should use all enabled tools)
            payload = {"messages": []}
            
            with patch('hatchling.core.llm.providers.ollama_provider.ToolLifecycleSubscriber', return_value=mock_tool_subscriber):
                # Import here to use the patched subscriber
                from hatchling.core.llm.providers.ollama_provider import OllamaProvider
                
                # Create provider instance
                with patch('hatchling.core.llm.providers.ollama_provider.AsyncClient'):
                    with patch('hatchling.core.llm.providers.ollama_provider.mcp_manager'):
                        provider = OllamaProvider(self.mock_settings)
                        provider._toolLifecycle_subscriber = mock_tool_subscriber
                        
                        # Test filtering - should only include enabled tools
                        result = provider.add_tools_to_payload(payload)
                        
                        # Verify only enabled tools are in payload
                        self.assertIn("tools", result)
                        self.assertEqual(len(result["tools"]), 1)
                        self.assertEqual(result["tools"][0]["name"], "enabled_tool")
            
            # Test case 2: Specific tools requested including disabled one
            payload2 = {"messages": []}
            requested_tools = ["enabled_tool", "disabled_tool"]
            
            with patch('hatchling.core.llm.providers.ollama_provider.ToolLifecycleSubscriber', return_value=mock_tool_subscriber):
                from hatchling.core.llm.providers.ollama_provider import OllamaProvider
                
                with patch('hatchling.core.llm.providers.ollama_provider.AsyncClient'):
                    with patch('hatchling.core.llm.providers.ollama_provider.mcp_manager'):
                        provider = OllamaProvider(self.mock_settings)
                        provider._toolLifecycle_subscriber = mock_tool_subscriber
                        
                        # Should only include enabled tools, skip disabled ones
                        result2 = provider.add_tools_to_payload(payload2, requested_tools)
                        
                        # Verify only enabled tools are included
                        self.assertIn("tools", result2)
                        self.assertEqual(len(result2["tools"]), 1)
                        self.assertEqual(result2["tools"][0]["name"], "enabled_tool")
                        
                        # Verify warning was logged for disabled tool (check mock calls)
                        mock_tool_subscriber.prettied_reason.assert_called()
        
        self.run_async(async_test())
    
    def test_multiple_tool_calls_in_sequence(self):
        """Test handling multiple tool calls in sequence."""
        async def async_test():
            # Create multiple tool call events
            tool_calls = [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "function_1",
                        "arguments": '{"param": "value1"}'
                    }
                },
                {
                    "id": "call_2", 
                    "type": "function",
                    "function": {
                        "name": "function_2",
                        "arguments": '{"param": "value2"}'
                    }
                }
            ]
            
            with patch('hatchling.mcp_utils.mcp_tool_execution.mcp_manager') as mock_mcp:
                mock_response = {"content": '{"result": "success"}'}
                mock_mcp.execute_tool = AsyncMock(return_value=[mock_response])
                
                # Process each tool call
                for i, tool_call in enumerate(tool_calls):
                    event = StreamEvent(
                        type=StreamEventType.TOOL_CALL,
                        data=tool_call,
                        provider=ELLMProvider.OPENAI
                    )
                    self.tool_call_subscriber.on_event(event)
                
                # Allow time for processing
                await asyncio.sleep(0.2)
                
                # Verify all tool calls were processed
                dispatched_events = [e for e in self.event_collector.events if e.type == StreamEventType.TOOL_CALL_DISPATCHED]
                self.assertGreaterEqual(len(dispatched_events), 2, "Should process both tool calls")
                
                # Verify tool calls were processed (check for both call IDs in all events)
                all_tool_ids = [e.data.get("tool_id") for e in self.event_collector.events if e.data.get("tool_id")]
                self.assertIn("call_1", all_tool_ids)
                self.assertIn("call_2", all_tool_ids)
        
        self.run_async(async_test())


class TestChatSessionToolCallIntegration(AsyncTestCase):
    """Integration tests for ChatSession with tool call functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_settings = MockAppSettings()
        
        # Create event collector
        self.event_collector = ToolCallEventCollector()
        
        # Mock provider and chat session
        self.mock_provider = MagicMock()
        self.mock_provider.publisher = StreamPublisher("test_provider")
        
        # Subscribe to events
        self.mock_provider.publisher.subscribe(self.event_collector)
        
        # Setup chat session with mock provider
        self.chat_session = ChatSession()
        self.chat_session.provider = self.mock_provider
        
        self.logger = logging.getLogger("test_chat_integration")
    
    def test_chat_session_tool_call_integration(self):
        """Test ChatSession integration with tool call system."""
        async def async_test():
            # Mock the provider's stream_chat_response method
            async def mock_stream_response(payload, **kwargs):
                # Simulate LLM response with tool call
                tool_call_data = {
                    "id": "call_integration",
                    "type": "function", 
                    "function": {
                        "name": "integration_test",
                        "arguments": '{"test": "value"}'
                    }
                }
                
                # Publish tool call event
                self.mock_provider.publisher.publish(
                    StreamEventType.TOOL_CALL,
                    tool_call_data
                )
                
                # Also simulate content response
                yield {
                    "message": {
                        "role": "assistant",
                        "content": "I'll use the integration test tool."
                    }
                }
            
            self.mock_provider.stream_chat_response = mock_stream_response
            self.mock_provider.prepare_chat_payload.return_value = {"messages": []}
            self.mock_provider.add_tools_to_payload.return_value = {"messages": [], "tools": []}
            
            # Send a message that would trigger tool use
            # We need to iterate through the async generator instead of awaiting
            async for chunk in self.chat_session.provider.stream_chat_response({"messages": []}):
                pass  # Process chunks if needed
            
            # Verify tool call events were generated
            tool_call_events = [e for e in self.event_collector.events if e.type == StreamEventType.TOOL_CALL]
            self.assertEqual(len(tool_call_events), 1, "Should generate tool call event")
            
            event = tool_call_events[0]
            self.assertEqual(event.data["id"], "call_integration")
            self.assertEqual(event.data["function"]["name"], "integration_test")
        
        self.run_async(async_test())


class TestCLIChatToolCallIntegration(AsyncTestCase):
    """Integration tests for CLI chat with tool call functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_settings_registry = MockSettingsRegistry()
        
        # Create CLI chat instance
        self.cli_chat = CLIChat(self.mock_settings_registry)
        
        self.logger = logging.getLogger("test_cli_integration")
    
    def test_cli_chat_initialization_with_tool_system(self):
        """Test CLI chat initialization includes tool call system."""
        async def async_test():
            with patch('hatchling.core.llm.providers.registry.ProviderRegistry.get_provider') as mock_get_provider:
                with patch('hatchling.core.llm.model_manager_api.model_api') as mock_model_api:
                    with patch('hatchling.ui.cli_chat.mcp_manager') as mock_mcp:
                        with patch('hatchling.config.settings.AppSettings.get_instance') as mock_settings_instance:
                            # Mock settings instance to return our mock settings
                            mock_settings_instance.return_value = self.mock_settings_registry.settings
                            
                            # Mock successful initialization
                            mock_provider = MagicMock()
                            mock_provider.provider_name = "openai"  # Set as property, not method
                            mock_get_provider.return_value = mock_provider
                            mock_model_api.check_provider_health.return_value = (True, "Provider healthy")

                            mock_mcp.initialize = AsyncMock(return_value=True)
                            mock_mcp.disconnect_all = AsyncMock()
                            
                            # Initialize CLI chat
                            success = await self.cli_chat.initialize()
                            
                            # Verify initialization succeeded
                            self.assertTrue(success, "CLI chat should initialize successfully")
                            
                            # Verify MCP manager was initialized
                            mock_mcp.initialize.assert_called_once()
                            
                            # Verify chat session was created
                            self.assertIsNotNone(self.cli_chat.chat_session, "Chat session should be created")
                            
                            # Verify command handler was created
                            self.assertIsNotNone(self.cli_chat.cmd_handler, "Command handler should be created")
        
        self.run_async(async_test())
    
    def test_cli_chat_mcp_availability_check(self):
        """Test CLI chat MCP availability checking using event system."""
        async def async_test():
            with patch('hatchling.core.llm.providers.registry.ProviderRegistry.get_provider') as mock_get_provider:
                with patch('hatchling.core.llm.model_manager_api.model_api') as mock_model_api:
                    with patch('hatchling.config.settings.AppSettings.get_instance') as mock_settings_instance:
                        # Mock settings instance to return our mock settings
                        mock_settings_instance.return_value = self.mock_settings_registry.settings
                        
                        # Mock successful provider
                        mock_provider = MagicMock()
                        mock_provider.provider_name = "openai"  # Set as property, not method
                        mock_get_provider.return_value = mock_provider
                        mock_model_api.check_provider_health.return_value = (True, "Provider healthy")
                        
                        # Initialize CLI chat - it will use the real mcp_manager which will 
                        # publish events to the health subscriber
                        success = await self.cli_chat.initialize()
                        
                        # Should succeed regardless of MCP availability 
                        self.assertTrue(success, "CLI chat should initialize successfully")
                        
                        # Verify MCP health subscriber was created
                        self.assertIsNotNone(self.cli_chat.mcp_health_subscriber, "MCP health subscriber should be created")
                        
                        # Verify subscriber is subscribed to MCP events
                        subscribed_events = self.cli_chat.mcp_health_subscriber.get_subscribed_events()
                        expected_events = [
                            StreamEventType.MCP_SERVER_UP,
                            StreamEventType.MCP_SERVER_DOWN,
                            StreamEventType.MCP_SERVER_UNREACHABLE,
                            StreamEventType.MCP_SERVER_REACHABLE,
                            StreamEventType.MCP_TOOL_ENABLED,
                            StreamEventType.MCP_TOOL_DISABLED
                        ]
                        for event_type in expected_events:
                            self.assertIn(event_type, subscribed_events, f"Should subscribe to {event_type}")
        
        self.run_async(async_test())


class TestEndToEndToolCallFlow(AsyncTestCase):
    """End-to-end integration tests for the complete tool call flow."""
    
    def setUp(self):
        """Set up comprehensive test environment."""
        self.mock_settings = MockAppSettings()
        self.event_collector = ToolCallEventCollector()
        
        # Setup tool execution system
        with patch('hatchling.mcp_utils.mcp_tool_execution.logging_manager') as mock_logging:
            mock_logging.get_session.return_value = logging.getLogger("test")
            self.tool_execution = MCPToolExecution(self.mock_settings)
        
        self.tool_execution.stream_publisher.subscribe(self.event_collector)
        self.tool_call_subscriber = MCPToolCallSubscriber(self.tool_execution)
        
        # Setup publisher that simulates LLM provider
        self.llm_publisher = StreamPublisher(ELLMProvider.OPENAI)
        self.llm_publisher.subscribe(self.tool_call_subscriber)
        
        self.logger = logging.getLogger("test_e2e_flow")
    
    def tearDown(self):
        """Clean up test environment."""
        self.tool_execution.stream_publisher.clear_subscribers()
        self.llm_publisher.clear_subscribers()
    
    def test_complete_tool_call_workflow(self):
        """Test the complete tool call workflow from LLM to MCP and back."""
        async def async_test():
            # Step 1: Simulate LLM generating a tool call
            tool_call_data = {
                "id": "call_workflow_test",
                "type": "function",
                "function": {
                    "name": "workflow_test_function",
                    "arguments": '{"action": "test", "value": 123}'
                }
            }
            
            # Step 2: Mock MCP tool execution
            with patch('hatchling.mcp_utils.mcp_tool_execution.mcp_manager') as mock_mcp:
                mock_response = {
                    "content": '{"status": "success", "result": "workflow test completed", "data": {"processed": true}}'
                }
                mock_mcp.execute_tool = AsyncMock(return_value=[mock_response])
                
                # Step 3: Publish tool call event (simulating LLM provider)
                self.llm_publisher.publish(
                    StreamEventType.TOOL_CALL,
                    tool_call_data
                )
                
                # Step 4: Allow time for complete processing
                await asyncio.sleep(0.2)
                
                # Step 5: Verify the complete workflow
                events = self.event_collector.events
                
                # Should have dispatched event
                dispatched_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_DISPATCHED]
                self.assertGreaterEqual(len(dispatched_events), 1, "Should dispatch tool call")
                
                # Should have progress event
                progress_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_PROGRESS]
                self.assertGreaterEqual(len(progress_events), 1, "Should show progress")
                
                # Should have result event
                result_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_RESULT]
                self.assertGreaterEqual(len(result_events), 1, "Should provide result")
                
                # Verify MCP tool was called with correct parameters
                mock_mcp.execute_tool.assert_called_once_with(
                    "workflow_test_function",
                    {"action": "test", "value": 123}
                )
                
                # Verify result event contains expected data
                result_event = result_events[0]
                self.assertEqual(result_event.data["tool_id"], "call_workflow_test")
                self.assertEqual(result_event.data["status"], "success")
        
        self.run_async(async_test())
    
    def test_tool_call_error_recovery_workflow(self):
        """Test error recovery in the tool call workflow."""
        async def async_test():
            # Create tool call that will fail
            tool_call_data = {
                "id": "call_error_recovery",
                "type": "function",
                "function": {
                    "name": "failing_function",
                    "arguments": '{"will": "fail"}'
                }
            }
            
            # Mock MCP to fail first, then succeed
            with patch('hatchling.mcp_utils.mcp_tool_execution.mcp_manager') as mock_mcp:
                mock_mcp.execute_tool = AsyncMock(side_effect=Exception("Connection failed"))
                
                # Publish failing tool call
                self.llm_publisher.publish(
                    StreamEventType.TOOL_CALL,
                    tool_call_data
                )
                
                # Allow processing
                await asyncio.sleep(0.1)
                
                # Verify error was handled
                error_events = [e for e in self.event_collector.events if e.type == StreamEventType.TOOL_CALL_ERROR]
                self.assertEqual(len(error_events), 1, "Should handle error gracefully")
                
                error_event = error_events[0]
                self.assertEqual(error_event.data["tool_id"], "call_error_recovery")
                self.assertIn("Connection failed", error_event.data["error"])
        
        self.run_async(async_test())


def run_tool_call_flow_integration_tests():
    """Run all tool call flow integration tests.
    
    Returns:
        bool: True if all tests pass, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestToolCallFlowIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestChatSessionToolCallIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIChatToolCallIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndToolCallFlow))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_tool_call_flow_integration_tests()
    sys.exit(0 if success else 1)
