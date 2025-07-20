"""Integration tests for OllamaProvider - Phase 3.

These tests validate the OllamaProvider against a real Ollama instance.
Tests skip gracefully if Ollama is not available or configured.
"""

import sys
import os
import unittest
import logging
import asyncio
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatchling.core.llm.providers.registry import ProviderRegistry
from hatchling.core.llm.providers.ollama_provider import OllamaProvider
from hatchling.core.llm.providers.subscription import (
    ContentPrinterSubscriber,
    UsageStatsSubscriber,
    ErrorHandlerSubscriber
)

logger = logging.getLogger("integration_test_ollama")


class TestOllamaProviderIntegration(unittest.TestCase):
    """Integration tests for OllamaProvider with real Ollama instance."""
        
    def setUp(self):
        """Set up test fixtures."""
        # Check if Ollama is available
        try:
            config = {
                "host": "http://localhost:11434",
                "model": "llama3.2",  # Default model for testing
                "timeout": 30.0
            }
            self.provider = ProviderRegistry.create_provider("ollama", config)
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
        config = {
            "host": "http://localhost:11434",
            "model": "llama3.2",
            "timeout": 30.0
        }
        
        provider = ProviderRegistry.create_provider("ollama", config)
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
        
        payload = self.provider.prepare_chat_payload(messages, temperature=0.7)
        
        self.assertIsInstance(payload, dict)
        self.assertIn("model", payload)
        self.assertIn("messages", payload)
        self.assertEqual(payload["messages"], messages)
        self.assertTrue(payload.get("stream", False))  # Should default to streaming
        self.assertEqual(payload["options"]["temperature"], 0.7)

    def test_tools_payload_integration(self):
        """Test adding tools to payload."""
        base_payload = {
            "model": "llama3.2",
            "messages": [{"role": "user", "content": "Test"}]
        }
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name"}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        payload_with_tools = self.provider.add_tools_to_payload(base_payload, tools)
        
        self.assertIn("tools", payload_with_tools)
        self.assertEqual(len(payload_with_tools["tools"]), 1)
        self.assertEqual(payload_with_tools["tools"][0]["function"]["name"], "get_weather")

    async def async_test_simple_chat_integration(self):
        """Test a simple chat interaction with Ollama.

        Sends a prompt to Ollama and streams the response, asserting that a response is received.
        """

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
        payload = self.provider.prepare_chat_payload(messages, temperature=0.1, num_predict=10)

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
