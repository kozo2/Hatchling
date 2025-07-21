"""Development tests for ProviderRegistry - Phase 1.

These tests validate the provider registry functionality including registration,
instantiation, and discovery of LLM providers.
"""

import sys
import logging
import unittest
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("dev_test_provider_registry")


class TestProviderRegistry(unittest.TestCase):
    """Unit tests for ProviderRegistry registration, instantiation, and utilities."""

    def test_registry_import(self):
        """Test that ProviderRegistry and LLMProvider can be imported."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        from hatchling.core.llm.providers.base import LLMProvider
        self.assertIsNotNone(ProviderRegistry)
        self.assertIsNotNone(LLMProvider)

    def test_provider_registration(self):
        """Test provider registration using decorator."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        from hatchling.core.llm.providers.base import LLMProvider

        ProviderRegistry.clear_registry()

        @ProviderRegistry.register("test_provider")
        class TestProvider(LLMProvider):
            async def initialize(self) -> bool:
                return True
            def prepare_chat_payload(self, messages, model):
                return {"model": model, "messages": messages}
            def add_tools_to_payload(self, payload, tools):
                return payload
            async def stream_chat_response(self, session, payload, history, tool_executor, **kwargs):
                return "test response", [], []
            async def check_health(self):
                return {"available": True, "message": "OK"}
            def _parse_and_publish_chunk(self, chunk):
                pass

        self.assertTrue(ProviderRegistry.is_registered("test_provider"))
        self.assertIn("test_provider", ProviderRegistry.list_providers())
        provider_class = ProviderRegistry.get_provider_class("test_provider")
        self.assertIs(provider_class, TestProvider)

    def test_provider_instantiation(self):
        """Test provider instantiation from registry."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        from hatchling.core.llm.providers.base import LLMProvider

        if not ProviderRegistry.is_registered("test_provider"):
            @ProviderRegistry.register("test_provider")
            class TestProvider(LLMProvider):
                async def initialize(self) -> bool:
                    return True
                def prepare_chat_payload(self, messages, model):
                    return {"model": model, "messages": messages}
                def add_tools_to_payload(self, payload, tools):
                    return payload
                async def stream_chat_response(self, session, payload, history, tool_executor, **kwargs):
                    return "test response", [], []
                async def check_health(self):
                    return {"available": True, "message": "OK"}
                def _parse_and_publish_chunk(self, chunk):
                    pass

        test_settings = {"api_url": "http://test.com"}
        provider = ProviderRegistry.create_provider("test_provider", test_settings)
        self.assertIsInstance(provider, LLMProvider)
        self.assertEqual(provider.settings, test_settings)
        self.assertEqual(provider.provider_name, "test")

    def test_error_handling(self):
        """Test registry error handling for invalid cases."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        from hatchling.core.llm.providers.base import LLMProvider

        with self.assertRaises(ValueError) as cm:
            ProviderRegistry.create_provider("nonexistent_provider", {})
        self.assertIn("Unknown provider", str(cm.exception))
        self.assertIn("Available providers", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            @ProviderRegistry.register("invalid_provider")
            class NotAProvider:
                pass
        self.assertIn("must inherit from LLMProvider", str(cm.exception))

    def test_registry_utilities(self):
        """Test registry utility methods."""
        from hatchling.core.llm.providers.registry import ProviderRegistry

        providers = ProviderRegistry.list_providers()
        self.assertIsInstance(providers, list)
        if providers:
            first_provider = providers[0]
            self.assertTrue(ProviderRegistry.is_registered(first_provider))
        self.assertFalse(ProviderRegistry.is_registered("definitely_not_registered"))
        self.assertIsNone(ProviderRegistry.get_provider_class("nonexistent"))

def run_provider_registry_tests():
    """Run all provider registry tests.

    Returns:
        bool: True if all tests pass, False otherwise.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestProviderRegistry))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_provider_registry_tests()
    sys.exit(0 if success else 1)
