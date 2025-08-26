"""Feature tests for LLM provider base class and interface.

This test suite validates the LLM provider abstract base class interface
and ensures that provider implementations follow the expected contract.
"""

import sys
import logging
import unittest
from abc import ABC
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_decorators import feature_test
from tests.test_data_utils import test_data

logger = logging.getLogger("feature_test_llm_provider_base")


class TestLLMProviderBase(unittest.TestCase):
    """Feature tests for LLM provider base class interface."""

    @feature_test
    def test_abstract_base_class(self):
        """Test that LLMProvider is properly defined as an abstract base class."""
        from hatchling.core.llm.providers.base import LLMProvider
        self.assertTrue(issubclass(LLMProvider, ABC), 
                       "LLMProvider should inherit from ABC for proper abstraction")
        
        with self.assertRaises(TypeError) as cm:
            LLMProvider(None)
        self.assertIn("abstract", str(cm.exception).lower(),
                     "Should not allow instantiation of abstract base class")

    @feature_test
    def test_abstract_methods_defined(self):
        """Test that all required abstract methods are defined and abstract."""
        from hatchling.core.llm.providers.base import LLMProvider
        
        expected_methods = [
            'initialize',
            'close',
            'prepare_chat_payload',
            'add_tools_to_payload',
            'stream_chat_response',
            '_parse_and_publish_chunk',
            'check_health',
            'provider_name',
            'provider_enum'
        ]
        
        for method_name in expected_methods:
            self.assertTrue(hasattr(LLMProvider, method_name), 
                           f"Missing required method: {method_name}")
            method = getattr(LLMProvider, method_name)
            self.assertTrue(getattr(method, '__isabstractmethod__', False), 
                           f"Method {method_name} should be abstract")

    @feature_test
    def test_concrete_implementation_interface(self):
        """Test that concrete implementations follow the expected interface."""
        from hatchling.core.llm.providers.base import LLMProvider

        class TestProvider(LLMProvider):
            @property
            def provider_name(self) -> str:
                return "test"
            
            @property
            def provider_enum(self) -> str:
                return "TEST"
            
            def initialize(self) -> None:
                pass
            
            async def close(self) -> None:
                pass
            
            def prepare_chat_payload(self, messages, model, **kwargs):
                return {"model": model, "messages": messages}
            
            def add_tools_to_payload(self, payload, tools):
                if tools:
                    payload["tools"] = tools
                return payload
            
            async def stream_chat_response(self, payload, **kwargs):
                yield {"content": "test response"}
            
            def _parse_and_publish_chunk(self, chunk):
                pass
            
            async def check_health(self):
                return {"available": True, "message": "OK"}
            
            def llm_to_hatchling_tool_call(self, event):
                """Mock implementation of llm_to_hatchling_tool_call."""
                from hatchling.core.llm.data_structures import ToolCallParsedResult
                return ToolCallParsedResult(
                    tool_call_id="test_id",
                    function_name="test_function",
                    arguments={}
                )
            
            def mcp_to_provider_tool(self, tool_info):
                """Mock implementation of mcp_to_provider_tool."""
                return {"type": "function", "function": {"name": tool_info.name}}
            
            def hatchling_to_llm_tool_call(self, tool_call):
                """Mock implementation of hatchling_to_llm_tool_call."""
                return {
                    "id": tool_call.tool_call_id,
                    "function": {
                        "name": tool_call.function_name,
                        "arguments": tool_call.arguments
                    }
                }
            
            def hatchling_to_provider_tool_result(self, tool_result):
                """Mock implementation of hatchling_to_provider_tool_result."""
                return {
                    "tool_call_id": tool_result.tool_call_id,
                    "content": str(tool_result.result)
                }
        
        # Should be able to instantiate concrete implementation
        test_settings = test_data.get_test_settings()
        provider = TestProvider(test_settings)
        
        self.assertIsInstance(provider, LLMProvider,
                             "Concrete implementation should be instance of LLMProvider")
        self.assertEqual(provider._settings, test_settings,
                        "Provider should store settings correctly")

    @feature_test
    def test_provider_name_derivation(self):
        """Test that provider name is correctly derived from implementation."""
        from hatchling.core.llm.providers.base import LLMProvider

        class OllamaProvider(LLMProvider):
            @property
            def provider_name(self) -> str:
                return "ollama"
            
            @property
            def provider_enum(self) -> str:
                return "OLLAMA"
            
            def initialize(self) -> None:
                pass
            
            async def close(self) -> None:
                pass
            
            def prepare_chat_payload(self, messages, model, **kwargs):
                return {"model": model, "messages": messages}
            
            def add_tools_to_payload(self, payload, tools):
                return payload
            
            async def stream_chat_response(self, payload, **kwargs):
                yield {"content": "test response"}
            
            def _parse_and_publish_chunk(self, chunk):
                pass
            
            async def check_health(self):
                return {"available": True, "message": "OK"}
            
            def llm_to_hatchling_tool_call(self, event):
                """Mock implementation of llm_to_hatchling_tool_call."""
                from hatchling.core.llm.data_structures import ToolCallParsedResult
                return ToolCallParsedResult(
                    tool_call_id="test_id",
                    function_name="test_function", 
                    arguments={}
                )
            
            def mcp_to_provider_tool(self, tool_info):
                """Mock implementation of mcp_to_provider_tool."""
                return {"type": "function", "function": {"name": tool_info.name}}
            
            def hatchling_to_llm_tool_call(self, tool_call):
                """Mock implementation of hatchling_to_llm_tool_call."""
                return {
                    "id": tool_call.tool_call_id,
                    "function": {
                        "name": tool_call.function_name,
                        "arguments": tool_call.arguments
                    }
                }
            
            def hatchling_to_provider_tool_result(self, tool_result):
                """Mock implementation of hatchling_to_provider_tool_result."""
                return {
                    "tool_call_id": tool_result.tool_call_id,
                    "content": str(tool_result.result)
                }

        provider = OllamaProvider({})
        self.assertEqual(provider.provider_name, "ollama",
                        "Provider name should be implemented correctly")


def run_llm_provider_base_feature_tests() -> bool:
    """Run all LLM provider base feature tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLLMProviderBase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_llm_provider_base_feature_tests()
    sys.exit(0 if success else 1)
