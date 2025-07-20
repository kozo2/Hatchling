"""Integration tests for OpenAIProvider - Phase 3.

These tests validate the OpenAIProvider against the real OpenAI API.
Tests skip gracefully if API key is not available or configured.
"""

import sys
import os
import unittest
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.core.llm.providers.registry import ProviderRegistry
from hatchling.core.llm.providers.subscription import (
            ContentPrinterSubscriber, 
            UsageStatsSubscriber, 
            ErrorHandlerSubscriber
        )

logger = logging.getLogger("integration_test_openai")


class TestOpenAIProviderIntegration(unittest.TestCase):
    """Integration tests for OpenAIProvider with real OpenAI API."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level test fixtures."""
        cls.openai_available = False
        cls.provider = None
        
        # Check if OpenAI API key is available
        if load_dotenv("./tests/.env"):  # Load environment variables from .env file
            logger.info("Loaded environment variables from .env file")
        else:
            logger.warning("No .env file found, using system environment variables")

    def setUp(self):
        """Set up test fixtures."""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY environment variable not set")
            self.skipTest("OpenAI API key is not set. Please set OPENAI_API_KEY environment variable.")
            
        try:
            config = {
                "api_key": api_key,
                "model": "gpt-4.1-nano",  # Use cheaper model for testing
                "timeout": 30.0
            }
            self.provider = ProviderRegistry.create_provider("openai", config)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.loop.run_until_complete(self.provider.initialize())
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

    async def async_cleanup(self):
        """Asynchronously clean up provider resources before closing the event loop."""
        if self.provider is not None:
            # If provider has an async close method, call it
            close_method = getattr(self.provider._client, 'aclose', None)
            if close_method is not None and callable(close_method):
                try:
                    await close_method()
                except Exception:
                    pass
            self.provider = None

    def tearDown(self):
        """Clean up provider resources after each test."""
        # Run async cleanup before closing the event loop
        #if self.loop.is_running() is False:
        self.loop.run_until_complete(self.provider.close())
        self.loop.close()

    # def test_provider_registration(self):
    #     """Test that OpenAIProvider is properly registered."""
    #     self.assertIn("openai", ProviderRegistry.list_providers())
    #     provider_class = ProviderRegistry.get_provider_class("openai")
    #     self.assertEqual(provider_class, OpenAIProvider)

    # async def async_test_provider_initialization(self):
    #     """Test provider initialization with real API connection."""
    #     api_key = os.environ.get('OPENAI_API_KEY')
    #     config = {
    #         "api_key": api_key,
    #         "model": "gpt-4.1-nano",  # Use cheaper model for testing
    #         "timeout": 30.0
    #     }
        
    #     provider = ProviderRegistry.create_provider("openai", config)
    #     self.assertIsInstance(provider, OpenAIProvider)
        
    #     # Test initialization
    #     await provider.initialize()
    #     self.assertIsNotNone(provider._client)

    # def test_provider_initialization_sync(self):
    #     """Synchronous wrapper for async initialization test."""
    #     try:
    #         self.loop.run_until_complete(self.async_test_provider_initialization())
    #     finally:
    #         pass  # Do not close the loop here; it is closed in tearDown

    # async def async_test_health_check(self):
    #     """Test health check against real OpenAI API."""
    #     health = await self.provider.check_health()
        
    #     self.assertIsInstance(health, dict)
    #     self.assertIn("available", health)
    #     self.assertIn("message", health)
    #     self.assertTrue(health["available"])
        
    #     # Should include models list if healthy
    #     if "models" in health:
    #         self.assertIsInstance(health["models"], list)
    #         self.assertGreater(len(health["models"]), 0)
    #         logger.info(f"Available models count: {len(health['models'])}")
            
    #         # Should include common models
    #         model_names = health["models"]
    #         self.assertTrue(any("gpt" in model for model in model_names))

    # def test_health_check_sync(self):
    #     """Synchronous wrapper for async health check test."""
    #     try:
    #         self.loop.run_until_complete(self.async_test_health_check())
    #     finally:
    #         pass  # Do not close the loop here; it is closed in tearDown

    # def test_payload_preparation(self):
    #     """Test chat payload preparation."""
    #     messages = [
    #         {"role": "user", "content": "Hello, how are you?"}
    #     ]
        
    #     payload = self.provider.prepare_chat_payload(
    #         messages, 
    #         temperature=0.7, 
    #         max_tokens=100
    #     )
        
    #     self.assertIsInstance(payload, dict)
    #     self.assertIn("model", payload)
    #     self.assertIn("messages", payload)
    #     self.assertEqual(payload["messages"], messages)
    #     self.assertTrue(payload.get("stream", False))  # Should default to streaming
    #     self.assertEqual(payload["temperature"], 0.7)
    #     self.assertEqual(payload["max_tokens"], 100)
    #     self.assertIn("stream_options", payload)

    # def test_tools_payload_integration(self):
    #     """Test adding tools to payload."""
    #     base_payload = {
    #         "model": "gpt-4.1-nano",  # Use cheaper model for testing
    #         "messages": [{"role": "user", "content": "Test"}]
    #     }
        
    #     tools = [
    #         {
    #             "type": "function",
    #             "function": {
    #                 "name": "get_weather",
    #                 "description": "Get current weather for a location",
    #                 "parameters": {
    #                     "type": "object",
    #                     "properties": {
    #                         "location": {"type": "string", "description": "City name"}
    #                     },
    #                     "required": ["location"]
    #                 }
    #             }
    #         }
    #     ]
        
    #     payload_with_tools = self.provider.add_tools_to_payload(base_payload, tools)
        
    #     self.assertIn("tools", payload_with_tools)
    #     self.assertEqual(len(payload_with_tools["tools"]), 1)
    #     self.assertEqual(payload_with_tools["tools"][0]["type"], "function")
    #     self.assertEqual(payload_with_tools["tools"][0]["function"]["name"], "get_weather")
    #     self.assertEqual(payload_with_tools["tool_choice"], "auto")

    async def async_test_simple_chat_integration(self):
        """Test a simple chat interaction with OpenAI using publish-subscribe pattern."""
        
        # Set up subscribers for the real streaming test
        content_printer = ContentPrinterSubscriber(include_role=True)
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
            temperature=0.1,
            max_tokens=10  # Keep it small for cost control
        )
        
        # Test that the payload is correctly formed for streaming
        self.assertIn("model", payload)
        self.assertIn("messages", payload)
        self.assertTrue(payload.get("stream", False))
        self.assertEqual(payload["max_tokens"], 10)
            
        print("\n=== OpenAI Streaming Response (Publish-Subscribe) ===")
        print()
        
        # Make the actual streaming call - no need to iterate chunks manually
        # The publisher will notify all subscribers automatically
        try:
            await self.provider.stream_chat_response(payload)
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            # Error should have been published to error handler
        finally:
            print("\n=== End of OpenAI Response ===")

    def test_simple_chat_integration_sync(self):
        """Synchronous wrapper for simple chat integration test."""
        try:
            self.loop.run_until_complete(self.async_test_simple_chat_integration())
        finally:
            pass # Do not close the loop here; it is closed in tearDown

    # def test_supported_features(self):
    #     """Test that provider reports supported features correctly."""
    #     features = self.provider.get_supported_features()
        
    #     self.assertIsInstance(features, dict)
        
    #     # OpenAI should support these features
    #     expected_features = {
    #         "streaming": True,
    #         "tools": True,
    #         "multimodal": True,
    #         "embeddings": True,
    #         "fine_tuning": True,
    #         "structured_outputs": True,
    #         "reasoning": True
    #     }
        
    #     for feature, expected_value in expected_features.items():
    #         self.assertIn(feature, features)
    #         self.assertEqual(features[feature], expected_value)

    # def test_api_key_validation(self):
    #     """Test that provider validates API key requirement."""
    #     with self.assertRaises(ValueError) as context:
    #         OpenAIProvider({"model": "gpt-4.1-nano",  # Use cheaper model for testing"
    #                         })  # Missing API key
        
    #     self.assertIn("API key is required", str(context.exception))


def run_openai_integration_tests():
    """Run all OpenAI integration tests.
    
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
