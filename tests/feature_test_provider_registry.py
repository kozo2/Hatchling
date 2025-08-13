"""Feature tests for provider registry functionality.

This test suite validates the provider registry system including registration,
instantiation, discovery, and error handling of LLM providers.
"""

import sys
import logging
import unittest
from pathlib import Path
from enum import Enum

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_decorators import feature_test
from tests.test_data_utils import test_data

logger = logging.getLogger("feature_test_provider_registry")


class TestProviderEnum(Enum):
    """Test provider enum for registry testing."""
    TEST_PROVIDER = "test_provider"
    PROVIDER_A = "provider_a"
    PROVIDER_B = "provider_b"


def create_test_provider_class(name="test"):
    """Create a test provider class with all required methods."""
    from hatchling.core.llm.providers.base import LLMProvider
    
    class TestProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return name
        
        @property
        def provider_enum(self) -> str:
            return name.upper()
        
        def initialize(self) -> None:
            pass
        
        async def close(self) -> None:
            pass
        
        def prepare_chat_payload(self, messages, model, **kwargs):
            return {"model": model, "messages": messages}
        
        def add_tools_to_payload(self, payload, tools=None):
            if tools:
                payload["tools"] = tools
            return payload
        
        async def stream_chat_response(self, payload, **kwargs):
            yield {"content": f"{name} response"}
        
        def _parse_and_publish_chunk(self, chunk):
            pass
        
        async def check_health(self):
            return {"available": True, "message": f"{name} OK"}
        
        def parse_tool_call(self, event):
            """Mock implementation of parse_tool_call."""
            from hatchling.core.llm.data_structures import ToolCallParsedResult
            return ToolCallParsedResult(
                tool_call_id="test_id",
                function_name="test_function",
                arguments={}
            )
        
        def convert_tool(self, tool_info):
            """Mock implementation of convert_tool."""
            return {"type": "function", "function": {"name": tool_info.name}}
    
    return TestProvider


class TestProviderRegistry(unittest.TestCase):
    """Feature tests for ProviderRegistry registration and management."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        # Store the original registry state to restore after test
        self.original_providers = ProviderRegistry._providers.copy()
        self.original_instances = ProviderRegistry._instances.copy()
        
        # Clear registry before each test to ensure isolation
        ProviderRegistry.clear_registry()

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        # Restore the original registry state to avoid state leakage
        ProviderRegistry._providers.clear()
        ProviderRegistry._instances.clear()
        ProviderRegistry._providers.update(self.original_providers)
        ProviderRegistry._instances.update(self.original_instances)

    @feature_test
    def test_provider_registration(self):
        """Test provider registration using decorator."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        
        TestProvider = create_test_provider_class("test")
        ProviderRegistry.register(TestProviderEnum.TEST_PROVIDER)(TestProvider)

        self.assertTrue(ProviderRegistry.is_registered(TestProviderEnum.TEST_PROVIDER),
                       "Provider should be registered after decoration")
        self.assertIn(TestProviderEnum.TEST_PROVIDER, ProviderRegistry.list_providers(),
                     "Provider should appear in provider list")

    @feature_test
    def test_provider_instantiation(self):
        """Test provider instantiation from registry."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        from hatchling.core.llm.providers.base import LLMProvider
        
        TestProvider = create_test_provider_class("test")
        ProviderRegistry.register(TestProviderEnum.TEST_PROVIDER)(TestProvider)

        test_settings = test_data.get_test_settings()
        provider = ProviderRegistry.create_provider(TestProviderEnum.TEST_PROVIDER, test_settings)
        
        self.assertIsInstance(provider, LLMProvider,
                             "Created provider should be instance of LLMProvider")
        self.assertEqual(provider._settings, test_settings,
                        "Provider should receive correct settings")

    @feature_test
    def test_registry_error_handling(self):
        """Test registry error handling for invalid cases."""
        from hatchling.core.llm.providers.registry import ProviderRegistry

        # Test unknown provider using a enum that's not registered
        class UnknownEnum(Enum):
            UNKNOWN = "unknown"
            
        with self.assertRaises(ValueError) as cm:
            ProviderRegistry.create_provider(UnknownEnum.UNKNOWN, {})
        self.assertIn("Unknown provider", str(cm.exception),
                     "Should raise ValueError for unknown provider")

    @feature_test
    def test_registry_utilities(self):
        """Test registry utility methods."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        
        # Test empty registry
        self.assertEqual(len(ProviderRegistry.list_providers()), 0,
                        "Empty registry should return empty list")
        
        class NonExistentEnum(Enum):
            NONEXISTENT = "nonexistent"
            
        self.assertFalse(ProviderRegistry.is_registered(NonExistentEnum.NONEXISTENT),
                        "Should return False for unregistered provider")

        # Register a provider and test utilities
        TestProvider = create_test_provider_class("test")
        ProviderRegistry.register(TestProviderEnum.TEST_PROVIDER)(TestProvider)

        self.assertEqual(len(ProviderRegistry.list_providers()), 1,
                        "Registry should contain one provider after registration")
        self.assertTrue(ProviderRegistry.is_registered(TestProviderEnum.TEST_PROVIDER),
                       "Should find registered provider")

    @feature_test
    def test_multiple_provider_registration(self):
        """Test registration of multiple providers."""
        from hatchling.core.llm.providers.registry import ProviderRegistry
        
        ProviderA = create_test_provider_class("provider_a")
        ProviderB = create_test_provider_class("provider_b")
        
        ProviderRegistry.register(TestProviderEnum.PROVIDER_A)(ProviderA)
        ProviderRegistry.register(TestProviderEnum.PROVIDER_B)(ProviderB)

        providers = ProviderRegistry.list_providers()
        self.assertEqual(len(providers), 2,
                        "Should register multiple providers")
        self.assertIn(TestProviderEnum.PROVIDER_A, providers,
                     "Should contain first provider")
        self.assertIn(TestProviderEnum.PROVIDER_B, providers,
                     "Should contain second provider")


def run_provider_registry_feature_tests() -> bool:
    """Run all provider registry feature tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProviderRegistry)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_provider_registry_feature_tests()
    sys.exit(0 if success else 1)
