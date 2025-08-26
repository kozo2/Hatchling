"""Integration tests for OpenAIProvider.

This module contains integration tests that validate the OpenAIProvider against the real OpenAI API.
Tests skip gracefully if API key is not available or configured properly.

The tests cover:
- Provider registration and initialization
- Health checks against real API
- Chat payload preparation and streaming
- Tool integration with MCP system
- Error handling and resource cleanup

Requirements:
- OPENAI_API_KEY environment variable must be set
- Internet connectivity for API access
"""

import sys
import os
import json
import time
import unittest
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test decorators
from tests.test_decorators import slow_test, requires_api_key, integration_test, requires_external_service


from hatchling.config.openai_settings import OpenAISettings
from hatchling.config.settings import AppSettings
from hatchling.config.llm_settings import ELLMProvider
from hatchling.mcp_utils.mcp_tool_lifecycle_subscriber import ToolLifecycleSubscriber
from hatchling.core.llm.providers.registry import ProviderRegistry
from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason
from hatchling.core.llm.event_system import (
    EventSubscriber,
    ContentPrinterSubscriber,
    UsageStatsSubscriber,
    ErrorHandlerSubscriber,
    EventPublisher,
    EventType,
    Event
)
from hatchling.mcp_utils.mcp_tool_lifecycle_subscriber import ToolLifecycleSubscriber
from hatchling.core.llm.providers.openai_provider import OpenAIProvider

logger = logging.getLogger("integration_test_openai")

# Load environment variables for API key
env_path = Path(__file__).parent / ".env"
if load_dotenv(env_path):
    logger.info("Loaded environment variables from .env file")
else:
    logger.warning("No .env file found, using system environment variables")

class TestStreamToolCallSubscriber(EventSubscriber):
    """Test subscriber for streaming tool calls.
    
    This subscriber reconstructs OpenAI-style tool call arguments that may be 
    fragmented across multiple streaming events.
    """
    
    def __init__(self):
        """Initialize the subscriber with empty tool call buffers."""
        super().__init__()

    def on_event(self, event: Event) -> None:
        """Handle incoming stream events, reconstructing OpenAI-style tool call arguments if fragmented.
        
        Args:
            event (Event): The streaming event to process
        """

        if event.type == EventType.LLM_TOOL_CALL_REQUEST:
            # OpenAI-style: first chunk has 'type' == 'function', then subsequent have type None and 'arguments' fragments
            tool_call = event.data.get("tool_call", {})
            print(f"Received tool call: {tool_call}")
        elif event.type == EventType.CONTENT:
            content = event.data.get("content", "")
            role = event.data.get("role", "assistant")
            print(f"Content from {role}: {content}")
        elif event.type == EventType.USAGE:
            usage = event.data.get("usage", {})
            print(f"Usage stats: {usage}")
        else:
            logger.warning(f"Unexpected event type: {event.type}")
    
    def get_subscribed_events(self):
        """Return list of events this subscriber is interested in.
        
        Returns:
            list: List of EventType values this subscriber handles
        """
        return [EventType.LLM_TOOL_CALL_REQUEST, EventType.CONTENT, EventType.USAGE, EventType.FINISH]


class TestOpenAIProviderIntegration(unittest.TestCase):
    """Integration tests for OpenAIProvider with real OpenAI API.
    
    These tests require:
    - OPENAI_API_KEY environment variable
    - Internet connectivity
    - OpenAI API accessibility
    """

    @classmethod
    def setUpClass(cls):
        """Set up class-level test fixtures.
        
        Note: Individual test setup is handled in setUp() for proper isolation.
        """
        cls.openai_available = False
        cls.provider = None

    def setUp(self):
        """Set up test fixtures for each test method.
        
        Validates OpenAI API key availability and initializes provider.
        Skips tests if OpenAI is not properly configured.
        """
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY environment variable not set")
            self.skipTest("OpenAI API key is not set. Please set OPENAI_API_KEY environment variable.")
            
        try:
            openai_settings = OpenAISettings(api_key=api_key, timeout=30.0)
            app_settings = AppSettings(openai=openai_settings)
            self.provider = ProviderRegistry.create_provider(ELLMProvider.OPENAI, app_settings)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # Provider initializes automatically in constructor, so we just check health
            health = self.loop.run_until_complete(self.provider.check_health())
            self.openai_available = health.get("available", False)
            if self.openai_available:
                logger.info("OpenAI API is available for integration testing")
            else:
                logger.warning(f"OpenAI health check failed: {health.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.warning(f"OpenAI not available for integration testing: {e}")
            self.openai_available = False

        if not self.openai_available:
            self.skipTest("OpenAI API is not available or not configured properly. Set OPENAI_API_KEY environment variable.")

    def tearDown(self):
        """Clean up provider resources after each test.
        
        Ensures proper cleanup of the event loop and provider connections.
        """
        if hasattr(self, 'loop') and self.loop:
            try:
                self.loop.run_until_complete(self.provider.close())
            except Exception as e:
                logger.warning(f"Error during provider cleanup: {e}")
            finally:
                self.loop.close()

    @integration_test
    @requires_api_key
    def test_provider_registration(self):
        """Test that OpenAIProvider is properly registered in the provider registry.
        
        Validates that the OpenAI provider is available and correctly mapped in the registry.
        """
        self.assertIn(ELLMProvider.OPENAI, ProviderRegistry.list_providers(), 
                     "OpenAI provider should be registered in provider registry")
        provider_class = ProviderRegistry.get_provider_class(ELLMProvider.OPENAI)
        self.assertEqual(provider_class, OpenAIProvider,
                        "Provider registry should return OpenAIProvider class for OPENAI enum")

    async def async_test_provider_initialization(self):
        """Test provider initialization with real API connection.
        
        Validates that the provider can be properly initialized and establishes
        a working connection to the OpenAI API.
        """
        api_key = os.environ.get('OPENAI_API_KEY')
        openai_settings = OpenAISettings(api_key=api_key, timeout=30.0)
        app_settings = AppSettings(openai=openai_settings)
        provider = ProviderRegistry.create_provider(ELLMProvider.OPENAI, app_settings)
        self.assertIsInstance(provider, OpenAIProvider,
                             "Provider should be instance of OpenAIProvider")
        
        # Test initialization (provider initializes automatically in constructor)
        self.assertIsNotNone(provider._client,
                            "Provider client should be initialized after creation")

    @integration_test
    @requires_api_key
    @requires_external_service("openai")
    def test_provider_initialization_sync(self):
        """Synchronous wrapper for async initialization test."""
        try:
            self.loop.run_until_complete(self.async_test_provider_initialization())
        except Exception as e:
            self.fail(f"Provider initialization test failed: {e}")

    async def async_test_health_check(self):
        """Test health check against real OpenAI API.
        
        Validates that the provider can successfully communicate with OpenAI
        and retrieve model information.
        """
        health = await self.provider.check_health()
        
        self.assertIsInstance(health, dict, "Health check should return a dictionary")
        self.assertIn("available", health, "Health check should include 'available' field")
        self.assertIn("message", health, "Health check should include 'message' field")
        self.assertTrue(health["available"], "OpenAI API should be available for testing")
        
        # Should include models list if healthy
        if "models" in health:
            self.assertIsInstance(health["models"], list, "Models should be returned as a list")
            self.assertGreater(len(health["models"]), 0, "Should have at least one model available")
            logger.info(f"Available models count: {len(health['models'])}")
            
            # Should include common models
            model_names = health["models"]
            self.assertTrue(any("gpt" in model for model in model_names),
                          "Should include GPT models in available models list")

    @integration_test
    @requires_api_key
    @requires_external_service("openai")
    def test_health_check_sync(self):
        """Synchronous wrapper for async health check test."""
        try:
            self.loop.run_until_complete(self.async_test_health_check())
        except Exception as e:
            self.fail(f"Health check test failed: {e}")

    @integration_test
    @requires_api_key
    def test_payload_preparation(self):
        """Test chat payload preparation for API requests.
        
        Validates that the provider correctly formats chat payloads with all
        required parameters for the OpenAI API.
        """
        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        payload = self.provider.prepare_chat_payload(
            messages, 
            "gpt-4.1-nano",
            temperature=0.7, 
            max_completion_tokens=100
        )
        
        self.assertIsInstance(payload, dict, "Payload should be a dictionary")
        self.assertIn("model", payload, "Payload should include model parameter")
        self.assertIn("messages", payload, "Payload should include messages parameter")
        self.assertEqual(payload["messages"], messages, "Messages should be preserved in payload")
        self.assertTrue(payload.get("stream", False), "Should default to streaming mode")
        self.assertEqual(payload["temperature"], 0.7, "Temperature should be set correctly")
        self.assertEqual(payload["max_completion_tokens"], 100, "Max tokens should be set correctly")
        self.assertIn("stream_options", payload, "Stream options should be included for streaming")

    async def async_test_tools_payload_integration(self):
        """Test adding tools to payload and MCP tool lifecycle integration.
        
        This test validates the complete tool integration workflow including:
        - Tool enabling/disabling via MCP events
        - Tool payload integration
        - Streaming tool call responses
        """
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
        event = Event(
            type=EventType.MCP_TOOL_ENABLED,
            data=event_data,
            provider=ELLMProvider.OPENAI,
            request_id=None,
            timestamp=time.time()
        )

        # Create and subscribe ToolLifecycleSubscriber
        # Use the provider's existing ToolLifecycleSubscriber instead of creating a new one
        tls = self.provider._toolLifecycle_subscriber
        tool_call_subscriber = TestStreamToolCallSubscriber()
        self.provider.publisher.subscribe(tool_call_subscriber)
        mcp_activity_mock_publisher = EventPublisher()
        mcp_activity_mock_publisher.subscribe(tls)
        mcp_activity_mock_publisher.publish(EventType.MCP_TOOL_ENABLED, event.data)

        enabled_tools = tls.get_enabled_tools()
        self.assertIn(tool_name, enabled_tools, f"Tool '{tool_name}' should be enabled after event")
        self.assertEqual(enabled_tools[tool_name].description, tool_info.description,
                        "Tool description should match the provided tool info")
        self.assertEqual(enabled_tools[tool_name].schema, tool_info.schema,
                        "Tool schema should match the provided tool info")
        self.assertEqual(enabled_tools[tool_name].status, MCPToolStatus.ENABLED,
                        "Tool status should be ENABLED")

        # Now test add_tools_to_payload using enabled tools from ToolLifecycleSubscriber
        messages = [{"role": "user", "content": "Compute 789+654."}]
        payload = self.provider.prepare_chat_payload(messages, "gpt-4.1-nano", temperature=0.1, max_completion_tokens=50)
        payload_with_tools = self.provider.add_tools_to_payload(payload.copy(), [tool_name])

        self.assertIn("model", payload, "Base payload should include model")
        self.assertIn("messages", payload, "Base payload should include messages")
        self.assertIn("tools", payload_with_tools, "Enhanced payload should include tools")
        self.assertEqual(tool_name, payload_with_tools["tools"][0]["function"]["name"],
                        f"Tool function name should be '{tool_name}'")
        self.assertTrue(payload.get("stream", False), "Payload should be configured for streaming")

        print("=== Starting chat response stream ===")
        print()
        try:
            await self.provider.stream_chat_response(payload_with_tools)
        except Exception as e:
            self.fail(f"Streaming with tools failed: {e}")
        finally:
            print("=== Chat response stream completed ===")
            
        self.assertIn("tools", payload_with_tools, "Payload should retain tools after streaming")
        self.assertEqual(len(payload_with_tools["tools"]), 1, "Should have exactly one tool configured")
        self.assertEqual(payload_with_tools["tools"][0]["function"]["name"], tool_name,
                        f"Tool name should remain '{tool_name}'")

        # Simulate disabling the tool
        disable_event = Event(
            type=EventType.MCP_TOOL_DISABLED,
            data={
                "tool_name": tool_name,
                "reason": "FROM_USER_DISABLED"
            },
            provider=ELLMProvider.OPENAI,
            request_id=None,
            timestamp=time.time()
        )
        mcp_activity_mock_publisher.publish(EventType.MCP_TOOL_DISABLED, disable_event.data)
        enabled_tools_after = tls.get_enabled_tools()
        self.assertNotIn(tool_name, enabled_tools_after, 
                        f"Tool '{tool_name}' should be disabled after disable event")

    @integration_test
    @requires_api_key
    @requires_external_service("openai")
    @slow_test
    def test_tools_payload_integration_sync(self):
        """Synchronous wrapper for tools payload integration test."""
        try:
            self.loop.run_until_complete(self.async_test_tools_payload_integration())
        except Exception as e:
            self.fail(f"Tools payload integration test failed: {e}")

    async def async_test_simple_chat_integration(self):
        """Test a simple chat interaction with OpenAI using publish-subscribe pattern.
        
        This test validates the complete streaming workflow including:
        - Subscriber setup and event handling
        - Chat payload preparation
        - Streaming response processing
        - Error handling during streaming
        """
        
        # Set up subscribers for the real streaming test
        content_printer = ContentPrinterSubscriber()  # Remove include_role parameter
        usage_stats = UsageStatsSubscriber()
        error_handler = ErrorHandlerSubscriber()
        
        # Subscribe to streaming events
        self.provider.publisher.subscribe(content_printer)
        self.provider.publisher.subscribe(usage_stats)
        self.provider.publisher.subscribe(error_handler)
        
        messages = [
            {"role": "user", "content": "Greetings!"}
        ]
        
        payload = self.provider.prepare_chat_payload(
            messages, 
            "gpt-4.1-nano",
            temperature=0.1,
            max_completion_tokens=10  # Keep it small for cost control
        )
        
        # Test that the payload is correctly formed for streaming
        self.assertIn("model", payload, "Payload should include model parameter")
        self.assertIn("messages", payload, "Payload should include messages parameter")
        self.assertTrue(payload.get("stream", False), "Payload should be configured for streaming")
        self.assertEqual(payload["max_completion_tokens"], 10, "Max tokens should be set for cost control")
            
        print("\n=== OpenAI Streaming Response (Publish-Subscribe) ===")
        print()
        
        # Make the actual streaming call - no need to iterate chunks manually
        # The publisher will notify all subscribers automatically
        try:
            await self.provider.stream_chat_response(payload)
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            self.fail(f"Chat streaming should not raise exceptions: {e}")
        finally:
            print("\n=== End of OpenAI Response ===")

    @integration_test
    @requires_api_key
    @requires_external_service("openai")
    @slow_test
    def test_simple_chat_integration_sync(self):
        """Synchronous wrapper for simple chat integration test."""
        try:
            self.loop.run_until_complete(self.async_test_simple_chat_integration())
        except Exception as e:
            self.fail(f"Simple chat integration test failed: {e}")

    @integration_test
    @requires_api_key
    def test_api_key_validation(self):
        """Test that provider validates API key requirement.

        Ensures that initializing OpenAIProvider without an API key raises appropriate error.
        This validates the provider's input validation and error handling.
        """
        with self.assertRaises(ValueError) as context:
            # Create AppSettings without API key to test validation
            invalid_openai_settings = OpenAISettings(api_key=None)
            invalid_app_settings = AppSettings(openai=invalid_openai_settings)
            OpenAIProvider(invalid_app_settings)
        self.assertIn("OpenAI API key is required", str(context.exception),
                     "Should raise ValueError for missing API key configuration")


def run_openai_integration_tests():
    """Run all OpenAI integration tests.
    
    This function executes the complete OpenAI provider integration test suite.
    Tests are automatically skipped if OpenAI API key is not configured.
    
    Returns:
        bool: True if all tests pass or are skipped, False if any fail.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestOpenAIProviderIntegration))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Consider skipped tests as success for integration tests
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_openai_integration_tests()
    sys.exit(0 if success else 1)
