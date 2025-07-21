"""Development tests for LLMProvider base class - Phase 1.

These tests validate the basic functionality of the LLMProvider abstract base class
and its interface definition. This is part of Phase 1 implementation validation.
"""

import sys
import logging
import unittest
from abc import ABC
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("dev_test_llmprovider_base")


class TestLLMProviderBase(unittest.TestCase):
    """Unit tests for LLMProvider abstract base class and its interface."""

    def test_abstract_base_class(self):
        """Test that LLMProvider is properly defined as an abstract base class."""
        from hatchling.core.llm.providers.base import LLMProvider
        self.assertTrue(issubclass(LLMProvider, ABC), "LLMProvider should inherit from ABC")
        with self.assertRaises(TypeError) as cm:
            LLMProvider(None)
        self.assertIn("abstract", str(cm.exception).lower())

    def test_abstract_methods(self):
        """Test that all required abstract methods are defined and abstract."""
        from hatchling.core.llm.providers.base import LLMProvider
        expected_methods = [
            'initialize',
            'prepare_chat_payload',
            'add_tools_to_payload',
            'stream_chat_response',
            'check_health'
        ]
        for method_name in expected_methods:
            self.assertTrue(hasattr(LLMProvider, method_name), f"Missing method: {method_name}")
            method = getattr(LLMProvider, method_name)
            self.assertTrue(getattr(method, '__isabstractmethod__', False), f"Method {method_name} should be abstract")

    def test_concrete_methods(self):
        """Test that concrete utility methods work correctly."""
        from hatchling.core.llm.providers.base import LLMProvider

        class TestProvider(LLMProvider):
            async def initialize(self) -> bool:
                return True
            def prepare_chat_payload(self, messages, model):
                return {"model": model}
            def add_tools_to_payload(self, payload, tools):
                return payload
            async def stream_chat_response(self, session, payload, history, tool_executor, **kwargs):
                return "", [], []
            def _parse_and_publish_chunk(self, chunk):
                pass
            async def check_health(self):
                return {"available": True, "message": "OK"}

        provider = TestProvider({"test": "settings"})
        self.assertEqual(provider.settings, {"test": "settings"})
        self.assertEqual(provider.provider_name, "test")

        data_with_tools = {"message": {"tool_calls": [{"name": "test_tool"}]}}
        logger.info(f"[PASS] All abstract methods are properly defined")
        return True

def run_llm_provider_base_tests() -> bool:
    """Run all LLMProvider base class tests.
    
    Returns:
        bool: True if all tests pass, False otherwise.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestLLMProviderBase))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_llm_provider_base_tests()
    sys.exit(0 if success else 1)
