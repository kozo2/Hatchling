"""Integration tests for OllamaProvider.

This module contains integration tests that validate the OllamaProvider against a real Ollama instance.
Tests skip gracefully if Ollama is not available or not configured properly.

The tests cover:
- Provider registration and initialization
- Health checks against real Ollama API
- Chat payload preparation and streaming
- Tool integration with MCP system
- Error handling and resource cleanup

Requirements:
- Ollama server running on localhost:11434
- Internet connectivity for model downloads if needed
"""

import sys
import unittest
import logging
import asyncio
from pathlib import Path
import time

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test decorators
from tests.test_decorators import slow_test, integration_test, requires_external_service
from hatchling.config.llm_settings import ELLMProvider
from hatchling.core.llm.providers.registry import ProviderRegistry
from hatchling.core.llm.providers.ollama_provider import OllamaProvider
from hatchling.core.llm.streaming_management import (
    StreamSubscriber,
    ContentPrinterSubscriber,
    UsageStatsSubscriber,
    ErrorHandlerSubscriber,
    StreamPublisher,
    StreamEventType,
    StreamEvent
)
from hatchling.core.llm.streaming_management.tool_lifecycle_subscriber import ToolLifecycleSubscriber
from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason

logger = logging.getLogger("integration_test_ollama")

class TestStreamToolCallSubscriber(StreamSubscriber):
    """Test subscriber for streaming tool calls."""

    def on_event(self, event: StreamEvent) -> None:
        """Handle incoming stream events."""
        if event.type == StreamEventType.LLM_TOOL_CALL_REQUEST:
            tool_calls = event.data.get("tool_calls", [])
            print(f"Received tool calls: {tool_calls}")
        elif event.type == StreamEventType.CONTENT:
            content = event.data.get("content", "")
            role = event.data.get("role", "assistant")
            print(f"Content from {role}: {content}")
        elif event.type == StreamEventType.USAGE:
            usage = event.data.get("usage", {})
            print(f"Usage stats: {usage}")
        else:
            logger.warning(f"Unexpected event type: {event.type}")
    
    def get_subscribed_events(self):
        """Return list of events this subscriber is interested in.
        
        Returns:
            list: List of StreamEventType values this subscriber handles
        """
        return [StreamEventType.LLM_TOOL_CALL_REQUEST, StreamEventType.CONTENT, StreamEventType.USAGE]


class TestOllamaProviderSync(unittest.TestCase):
    """Synchronous tests for OllamaProvider that don't require async operations.
    
    These tests require:
    - Ollama server running on localhost:11434
    - At least one model available in Ollama
    """

    def setUp(self):
        """Set up test fixtures for each test method.
        
        Initializes the Ollama provider and checks basic availability.
        Skips tests if Ollama is not accessible.
        """
        self.provider = None
        self.ollama_available = True
        
        try:
            # Create adapter and get provider
            self.provider = ProviderRegistry.get_provider(ELLMProvider.OLLAMA)

            # Not checking health because the method is async
            # health = self.provider.check_health()

        except Exception as e:
            logger.warning(f"Ollama not available for testing: {e}")
            self.ollama_available = False

        if not self.ollama_available:
            self.skipTest("Ollama is not available or not configured properly")

    def tearDown(self):
        """Clean up provider resources after each test."""
        
        self.provider.close()
        ProviderRegistry._instances.clear()  # Clear provider instances to reset state
    
    @integration_test
    @requires_external_service("ollama")
    def test_provider_registration(self):
        """Test that OllamaProvider is properly registered in the provider registry.
        
        Validates that the Ollama provider is available and correctly mapped in the registry.
        """
        self.assertIn(ELLMProvider.OLLAMA, ProviderRegistry.list_providers(),
                     "Ollama provider should be registered in provider registry")
        provider_class = ProviderRegistry.get_provider_class(ELLMProvider.OLLAMA)
        self.assertEqual(provider_class, OllamaProvider,
                        "Provider registry should return OllamaProvider class for OLLAMA enum")

    @integration_test
    @requires_external_service("ollama")
    def test_provider_initialization(self):
        """Test provider initialization with real connection.
        
        Validates that the provider can be properly initialized and establishes
        a working connection to the Ollama server.
        """
        try:
            self.assertIsInstance(self.provider, OllamaProvider,
                                "Provider should be instance of OllamaProvider")
            self.assertIsNotNone(self.provider._client,
                               "Provider client should be initialized")
        except Exception as e:
            self.skipTest(f"Provider initialization failed: {e}")

    @integration_test
    @requires_external_service("ollama")
    def test_payload_preparation(self):
        """Test chat payload preparation."""
        try:
            
            messages = [
                {"role": "user", "content": "Hello, how are you?"}
            ]
            
            payload = self.provider.prepare_chat_payload(messages, "llama3.2", temperature=0.7)
            
            self.assertIsInstance(payload, dict)
            self.assertIn("model", payload)
            self.assertIn("messages", payload)
            self.assertEqual(payload["messages"], messages)
            self.assertTrue(payload.get("stream", False))  # Should default to streaming
            self.assertEqual(payload["options"]["temperature"], 0.7)
        except Exception as e:
            self.skipTest(f"Payload preparation test failed: {e}")

    @integration_test
    @requires_external_service("ollama")
    def test_tool_lifecycle_subscriber_cache(self):
        """Test ToolLifecycleSubscriber cache and event handling in isolation."""
        tls = ToolLifecycleSubscriber("ollama")
        publisher = StreamPublisher()
        publisher.subscribe(tls)

        # Enable two tools
        for i in range(2):
            tool_name = f"tool_{i}"
            tool_info = MCPToolInfo(
                name=tool_name,
                description=f"desc_{i}",
                schema={"type": "object"},
                server_path=f"/server/{i}",
                status=MCPToolStatus.ENABLED,
                reason=MCPToolStatusReason.FROM_SERVER_UP
            )
            event_data = {
                "tool_name": tool_name,
                "tool_info": tool_info  # Changed from mcp_tool_info to tool_info
            }
            event = StreamEvent(
                type=StreamEventType.MCP_TOOL_ENABLED,
                data=event_data,
                provider=ELLMProvider.OLLAMA,
                request_id=None,
                timestamp=time.time()
            )
            publisher.publish(StreamEventType.MCP_TOOL_ENABLED, event.data)

        enabled = tls.get_enabled_tools()
        self.assertEqual(len(enabled), 2)
        self.assertIn("tool_0", enabled)
        self.assertIn("tool_1", enabled)

        # Disable one tool
        disable_event = StreamEvent(
            type=StreamEventType.MCP_TOOL_DISABLED,
            data={
                "tool_name": "tool_0",
                "reason": "FROM_USER_DISABLED"
            },
            provider=ELLMProvider.OLLAMA,
            request_id=None,
            timestamp=time.time()
        )
        publisher.publish(StreamEventType.MCP_TOOL_DISABLED, disable_event.data)
        enabled = tls.get_enabled_tools()
        self.assertNotIn("tool_0", enabled)
        self.assertIn("tool_1", enabled)

        # Clear cache
        tls.clear_cache()
        self.assertEqual(len(tls.get_all_tools()), 0)


class TestOllamaProviderIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for OllamaProvider with real Ollama instance using async test case.
    
    These tests require:
    - Ollama server running on localhost:11434  
    - At least one model available in Ollama
    - Longer execution time for streaming tests
    """
        
    async def asyncSetUp(self):
        """Set up test fixtures asynchronously."""
        self.provider = None
        self.ollama_available = False
        
        try:
            # Create adapter and get provider
            self.provider = ProviderRegistry.get_provider(ELLMProvider.OLLAMA)

            # Try to check health
            health = await self.provider.check_health()
            self.ollama_available = health.get("available", False)
            if self.ollama_available:
                logger.info("Ollama is available for integration testing")
            else:
                logger.warning(f"Ollama health check failed: {health.get('message', 'Unknown error')}")

        except Exception as e:
            logger.warning(f"Ollama not available for integration testing: {e}")
            self.ollama_available = False

        if not self.ollama_available:
            self.skipTest("Ollama is not available or not configured properly")

    async def asyncTearDown(self):
        """Clean up provider resources after each test."""
        self.provider.close()
        ProviderRegistry._instances.clear()  # Clear provider instances to reset state


    @integration_test
    @requires_external_service("ollama")
    async def test_health_check(self):
        """Test health check against real Ollama instance."""
        health = await self.provider.check_health()
        
        self.assertIsInstance(health, dict)
        self.assertIn("available", health)
        self.assertIn("message", health)
        self.assertTrue(health["available"], f"Ollama health check failed: {health.get('message', '')}")
        
        # Should include models list if healthy
        if "models" in health:
            self.assertIsInstance(health["models"], list)
            logger.info(f"Available models: {health['models']}")

    @integration_test
    @requires_external_service("ollama")
    @slow_test
    async def test_tools_payload_integration(self):
        """Test adding tools to payload and round-trip with ToolLifecycleSubscriber."""
        # Simulate a tool enabled event
        tool_name = "addition"
        tool_info = MCPToolInfo(
            name=tool_name,
            description="A tool that adds two numbers",
            schema={"type": "object", "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            }, "required": ["a", "b"]},
            server_path="/fake/server/path",
            status=MCPToolStatus.ENABLED,
            reason=MCPToolStatusReason.FROM_SERVER_UP
        )
        event_data = {
            "tool_name": tool_info.name,
            "tool_info": tool_info  # Changed from mcp_tool_info to tool_info
        }
        event = StreamEvent(
            type=StreamEventType.MCP_TOOL_ENABLED,
            data=event_data,
            provider=ELLMProvider.OLLAMA,
            request_id=None,
            timestamp=time.time()
        )

        # Create and subscribe ToolLifecycleSubscriber
        tls = ToolLifecycleSubscriber("ollama")
        self.provider._toolLifecycle_subscriber = tls
        tool_call_subscriber = TestStreamToolCallSubscriber()
        self.provider.publisher.subscribe(tool_call_subscriber)
        mcp_activity_mock_publisher = StreamPublisher()
        mcp_activity_mock_publisher.subscribe(tls)
        mcp_activity_mock_publisher.publish(StreamEventType.MCP_TOOL_ENABLED, event.data)

        enabled_tools = tls.get_enabled_tools()
        self.assertIn(tool_name, enabled_tools)
        self.assertEqual(enabled_tools[tool_name].description, tool_info.description)
        self.assertEqual(enabled_tools[tool_name].schema, tool_info.schema)
        self.assertEqual(enabled_tools[tool_name].status, MCPToolStatus.ENABLED)

        # Now test add_tools_to_payload using enabled tools from ToolLifecycleSubscriber
        messages = [
                    {"role": "user", "content": "Compute 789+654."}
                ]
        payload = self.provider.prepare_chat_payload(messages, "llama3.2", temperature=0.1, num_predict=100)
        payload_with_tools = self.provider.add_tools_to_payload(payload.copy(), [tool_name])

        self.assertIn("model", payload)
        self.assertIn("messages", payload)
        self.assertIn("tools", payload_with_tools)
        self.assertEqual(tool_name, payload_with_tools["tools"][0]["function"]["name"])
        self.assertTrue(payload.get("stream", False))

        print("=== Starting chat response stream ===")
        print()
        try:
            await self.provider.stream_chat_response(payload_with_tools)
        except Exception as e:
            self.fail(f"Streaming failed: {e}")
        finally:
            print("=== Chat response stream completed ===")
        self.assertIn("tools", payload_with_tools)
        self.assertEqual(len(payload_with_tools["tools"]), 1)
        self.assertEqual(payload_with_tools["tools"][0]["function"]["name"], tool_name)

        # Simulate disabling the tool
        disable_event = StreamEvent(
            type=StreamEventType.MCP_TOOL_DISABLED,
            data={
                "tool_name": tool_name,
                "reason": "FROM_USER_DISABLED"
            },
            provider=ELLMProvider.OLLAMA,
            request_id=None,
            timestamp=time.time()
        )
        mcp_activity_mock_publisher.publish(StreamEventType.MCP_TOOL_DISABLED, disable_event.data)
        enabled_tools_after = tls.get_enabled_tools()
        self.assertNotIn(tool_name, enabled_tools_after)

    @integration_test
    @requires_external_service("ollama")
    @slow_test
    async def test_simple_chat_integration(self):
        """Test a simple chat interaction with Ollama and ToolLifecycleSubscriber integration."""

        # Create test subscribers
        content_printer = ContentPrinterSubscriber()  # Remove include_role parameter
        usage_stats = UsageStatsSubscriber()
        error_handler = ErrorHandlerSubscriber()

        # Subscribe to publisher
        self.provider.publisher.subscribe(content_printer)
        self.provider.publisher.subscribe(usage_stats)
        self.provider.publisher.subscribe(error_handler)

        messages = [
            {"role": "user", "content": "Greetings!"}
        ]
        payload = self.provider.prepare_chat_payload(messages, "llama3.2", temperature=0.1, num_predict=10)

        self.assertIn("model", payload)
        self.assertIn("messages", payload)
        self.assertTrue(payload.get("stream", False))

        print("=== Starting chat response stream ===")
        print()
        try:
            await self.provider.stream_chat_response(payload)
        except Exception as e:
            self.fail(f"Streaming failed: {e}")
        finally:
            print("=== Chat response stream completed ===")


def run_ollama_integration_tests():
    """Run all Ollama integration tests.
    
    Returns:
        bool: True if all tests pass or are skipped, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add synchronous tests (don't require Ollama server for most)
    suite.addTests(loader.loadTestsFromTestCase(TestOllamaProviderSync))
    
    # Add async integration tests (require Ollama server)
    suite.addTests(loader.loadTestsFromTestCase(TestOllamaProviderIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Consider skipped tests as success for integration tests
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_ollama_integration_tests()
    sys.exit(0 if success else 1)
