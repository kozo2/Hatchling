"""Integration tests for OllamaProvider - Phase 3.

These tests validate the OllamaProvider against a real Ollama instance.
Tests skip gracefully if Ollama is not available or configured.
"""

import sys
import unittest
import logging
import asyncio
from pathlib import Path
import time

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from hatchling.config.settings import OllamaSettings
from hatchling.core.llm.tool_management.adapters import MCPToolAdapterRegistry
from hatchling.core.llm.providers.registry import ProviderRegistry
from hatchling.core.llm.providers.ollama_provider import OllamaProvider
from hatchling.core.llm.providers.subscription import (
    StreamSubscriber,
    ContentPrinterSubscriber,
    UsageStatsSubscriber,
    ErrorHandlerSubscriber,
    ToolLifecycleSubscriber,
    StreamPublisher,
    StreamEventType,
    StreamEvent
)
from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason

logger = logging.getLogger("integration_test_ollama")

class TestStreamToolCallSubscriber(StreamSubscriber):
    """Test subscriber for streaming tool calls."""

    def on_event(self, event: StreamEvent) -> None:
        """Handle incoming stream events."""
        if event.type == StreamEventType.TOOL_CALL:
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
        return [StreamEventType.TOOL_CALL, StreamEventType.CONTENT, StreamEventType.USAGE]

class TestOllamaProviderIntegration(unittest.TestCase):
    """Integration tests for OllamaProvider with real Ollama instance."""
        
    def setUp(self):
        """Set up test fixtures."""
        # Check if Ollama is available
        try:
            MCPToolAdapterRegistry.create_adapter("ollama")
            settings = OllamaSettings(ollama_ip="localhost", ollama_port=11434, timeout=30.0)
            self.provider = ProviderRegistry.create_provider("ollama", settings)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.loop.run_until_complete(self.provider.initialize())
            # Try to check health
            health = self.loop.run_until_complete(self.provider.check_health())
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

    def tearDown(self):
        """Clean up provider resources after each test."""
        self.loop.close()

    def test_provider_registration(self):
        """Test that OllamaProvider is properly registered."""
        self.assertIn("ollama", ProviderRegistry.list_providers())
        provider_class = ProviderRegistry.get_provider_class("ollama")
        self.assertEqual(provider_class, OllamaProvider)

    async def async_test_provider_initialization(self):
        """Test provider initialization with real connection."""
        settings = OllamaSettings(ollama_ip="localhost", ollama_port=11434, timeout=30.0)
        provider = ProviderRegistry.create_provider("ollama", settings)
        self.assertIsInstance(provider, OllamaProvider)
        
        # Test initialization
        await provider.initialize()
        self.assertIsNotNone(provider._client)

    def test_provider_initialization_sync(self):
        """Synchronous wrapper for async initialization test."""
        try:
            self.loop.run_until_complete(self.async_test_provider_initialization())
        finally:
            pass # Do not close the loop here; it is closed in tearDown

    async def async_test_health_check(self):
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

    def test_health_check_sync(self):
        """Synchronous wrapper for async health check test."""
        try:
            self.loop.run_until_complete(self.async_test_health_check())
        finally:
            pass  # Do not close the loop here; it is closed in tearDown

    def test_payload_preparation(self):
        """Test chat payload preparation."""
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

    async def async_test_tools_payload_integration(self):
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
            "mcp_tool_info": tool_info
        }
        event = StreamEvent(
            type=StreamEventType.MCP_TOOL_ENABLED,
            data=event_data,
            provider="ollama",
            request_id=None,
            timestamp=time.time()
        )

        # Create and subscribe ToolLifecycleSubscriber
        tls = ToolLifecycleSubscriber("ollama")
        self.provider._toolLifecycle_subscriber = tls
        tool_call_subscriber = TestStreamToolCallSubscriber()
        self.provider.publisher.subscribe(tool_call_subscriber)
        mcp_activity_mock_publisher = StreamPublisher("ollama")
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
            provider="ollama",
            request_id=None,
            timestamp=time.time()
        )
        mcp_activity_mock_publisher.publish(StreamEventType.MCP_TOOL_DISABLED, disable_event.data)
        enabled_tools_after = tls.get_enabled_tools()
        self.assertNotIn(tool_name, enabled_tools_after)
    
    def test_tools_payload_integration_sync(self):
        """Synchronous wrapper for tools payload integration test."""
        try:
            self.loop.run_until_complete(self.async_test_tools_payload_integration())
        finally:
            pass

    async def async_test_simple_chat_integration(self):
        """Test a simple chat interaction with Ollama and ToolLifecycleSubscriber integration."""

        # Create test subscribers
        content_printer = ContentPrinterSubscriber(include_role=True)
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

    def test_tool_lifecycle_subscriber_cache(self):
        """Test ToolLifecycleSubscriber cache and event handling in isolation."""
        tls = ToolLifecycleSubscriber("ollama")
        publisher = StreamPublisher("ollama")
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
                "mcp_tool_info": tool_info
            }
            event = StreamEvent(
                type=StreamEventType.MCP_TOOL_ENABLED,
                data=event_data,
                provider="ollama",
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
            provider="ollama",
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

    def test_simple_chat_integration_sync(self):
        """Synchronous wrapper for simple chat integration test."""
        try:
            self.loop.run_until_complete(self.async_test_simple_chat_integration())
        finally:
            pass # Do not close the loop here; it is closed in tearDown

    def test_supported_features(self):
        """Test that provider reports supported features correctly."""
        features = self.provider.get_supported_features()
        
        self.assertIsInstance(features, dict)
        
        # Ollama should support these features
        expected_features = {
            "streaming": True,
            "tools": True,
            "multimodal": True,
            "embeddings": False,
            "fine_tuning": False
        }
        
        for feature, expected_value in expected_features.items():
            self.assertIn(feature, features)
            self.assertEqual(features[feature], expected_value)


def run_ollama_integration_tests():
    """Run all Ollama integration tests.
    
    Returns:
        bool: True if all tests pass or are skipped, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestOllamaProviderIntegration))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Consider skipped tests as success for integration tests
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_ollama_integration_tests()
    sys.exit(0 if success else 1)
