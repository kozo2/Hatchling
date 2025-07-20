"""Development tests for Phase 2: Provider Implementation.

This module contains comprehensive tests for the OllamaProvider and OpenAIProvider
implementations to validate they correctly implement the LLMProvider interface.

These tests use mocking to avoid requiring actual API connections during development.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from hatchling.core.llm.providers import (
    LLMProvider, 
    ProviderRegistry
)

from hatchling.core.llm.providers.ollama_provider import OllamaProvider
from hatchling.core.llm.providers.openai_provider import OpenAIProvider


class TestProviderImplementations(unittest.TestCase):
    """Test concrete provider implementations."""
    
    def setUp(self):
        """Set up test environment."""
    
    def test_ollama_provider_registration(self):
        """Test that OllamaProvider registers correctly."""
        # Import should trigger registration
        from hatchling.core.llm.providers.ollama_provider import OllamaProvider
        
        # Check registration
        self.assertIn("ollama", ProviderRegistry._providers)
        self.assertEqual(ProviderRegistry._providers["ollama"], OllamaProvider)
    
    def test_openai_provider_registration(self):
        """Test that OpenAIProvider registers correctly."""  
        # Import should trigger registration
        from hatchling.core.llm.providers.openai_provider import OpenAIProvider
        
        # Check registration
        self.assertIn("openai", ProviderRegistry._providers)
        self.assertEqual(ProviderRegistry._providers["openai"], OpenAIProvider)
    
    @patch('hatchling.core.llm.providers.ollama_provider.AsyncClient')
    def test_ollama_provider_initialization(self, mock_async_client):
        """Test OllamaProvider initialization."""
        mock_client_instance = AsyncMock()
        mock_async_client.return_value = mock_client_instance
        
        config = {
            "host": "http://localhost:11434",
            "model": "llama2",
            "timeout": 30.0
        }
        
        provider = OllamaProvider(config)
        
        # Test properties
        self.assertEqual(provider.provider_name, "ollama")
        self.assertEqual(provider._host, "http://localhost:11434")
        self.assertEqual(provider._default_model, "llama2")
        self.assertEqual(provider._timeout, 30.0)
    
    def test_openai_provider_initialization(self):
        """Test OpenAIProvider initialization."""
        config = {
            "api_key": "test-key",
            "model": "gpt-4",
            "timeout": 30.0
        }
        
        provider = OpenAIProvider(config)
        
        # Test properties
        self.assertEqual(provider.provider_name, "openai")
        self.assertEqual(provider._api_key, "test-key")
        self.assertEqual(provider._default_model, "gpt-4")
        self.assertEqual(provider._timeout, 30.0)
    
    def test_openai_provider_requires_api_key(self):
        """Test that OpenAIProvider requires API key."""
        config = {"model": "gpt-4"}
        
        with self.assertRaises(ValueError) as context:
            OpenAIProvider(config)
        
        self.assertIn("API key is required", str(context.exception))
    
    @patch('hatchling.core.llm.providers.ollama_provider.AsyncClient')
    def test_ollama_prepare_chat_payload(self, mock_async_client):
        """Test OllamaProvider chat payload preparation."""
        config = {"model": "llama2"}
        provider = OllamaProvider(config)
        
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        payload = provider.prepare_chat_payload(messages, temperature=0.7)
        
        expected_payload = {
            "model": "llama2",
            "messages": messages,
            "stream": True,  # Default
            "options": {
                "temperature": 0.7
            }
        }
        
        self.assertEqual(payload, expected_payload)
    
    def test_openai_prepare_chat_payload(self):
        """Test OpenAIProvider chat payload preparation."""
        config = {"api_key": "test-key", "model": "gpt-4"}
        provider = OpenAIProvider(config)
        
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        payload = provider.prepare_chat_payload(
            messages, 
            temperature=0.7, 
            max_tokens=100
        )
        
        expected_payload = {
            "model": "gpt-4",
            "messages": messages,
            "stream": True,  # Default
            "temperature": 0.7,
            "max_tokens": 100,
            "stream_options": {"include_usage": True}
        }
        
        self.assertEqual(payload, expected_payload)
    
    @patch('hatchling.core.llm.providers.ollama_provider.AsyncClient')
    def test_ollama_add_tools_to_payload(self, mock_async_client):
        """Test OllamaProvider tool addition."""
        config = {"model": "llama2"}
        provider = OllamaProvider(config)
        
        base_payload = {
            "model": "llama2",
            "messages": []
        }
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather info",
                    "parameters": {"type": "object"}
                }
            }
        ]
        
        payload = provider.add_tools_to_payload(base_payload, tools)
        
        self.assertIn("tools", payload)
        self.assertEqual(len(payload["tools"]), 1)
        self.assertEqual(payload["tools"][0]["type"], "function")
        self.assertEqual(payload["tools"][0]["function"]["name"], "get_weather")
    
    def test_openai_add_tools_to_payload(self):
        """Test OpenAIProvider tool addition."""
        config = {"api_key": "test-key", "model": "gpt-4"}
        provider = OpenAIProvider(config)
        
        base_payload = {
            "model": "gpt-4",
            "messages": []
        }
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather info",
                    "parameters": {"type": "object"}
                }
            }
        ]
        
        payload = provider.add_tools_to_payload(base_payload, tools)
        
        self.assertIn("tools", payload)
        self.assertEqual(len(payload["tools"]), 1)
        self.assertEqual(payload["tools"][0]["type"], "function")
        self.assertEqual(payload["tool_choice"], "auto")  # Default tool choice
    
    @patch('hatchling.core.llm.providers.ollama_provider.AsyncClient')
    async def test_ollama_health_check_healthy(self, mock_async_client):
        """Test OllamaProvider health check when healthy."""
        mock_client_instance = AsyncMock()
        mock_client_instance.list.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "codellama"}
            ]
        }
        mock_async_client.return_value = mock_client_instance
        
        config = {"model": "llama2"}
        provider = OllamaProvider(config)
        provider._client = mock_client_instance
        
        health = await provider.check_health()
        
        self.assertTrue(health["available"])
        self.assertIn("healthy", health["message"])
        self.assertEqual(len(health["models"]), 2)
        self.assertIn("llama2", health["models"])
    
    @patch('hatchling.core.llm.providers.openai_provider.AsyncOpenAI')
    async def test_openai_health_check_healthy(self, mock_async_openai):
        """Test OpenAIProvider health check when healthy."""
        mock_client_instance = AsyncMock()
        mock_models_response = MagicMock()
        mock_models_response.data = [
            MagicMock(id="gpt-3.5-turbo"),
            MagicMock(id="gpt-4")
        ]
        mock_client_instance.models.list.return_value = mock_models_response
        mock_async_openai.return_value = mock_client_instance
        
        config = {"api_key": "test-key", "model": "gpt-4"}
        provider = OpenAIProvider(config)
        provider._client = mock_client_instance
        
        health = await provider.check_health()
        
        self.assertTrue(health["available"])
        self.assertIn("healthy", health["message"])
        self.assertEqual(len(health["models"]), 2)
        self.assertIn("gpt-4", health["models"])
    
    @patch('hatchling.core.llm.providers.ollama_provider.AsyncClient')
    async def test_ollama_health_check_unhealthy(self, mock_async_client):
        """Test OllamaProvider health check when unhealthy."""
        mock_client_instance = AsyncMock()
        mock_client_instance.list.side_effect = Exception("Connection refused")
        mock_async_client.return_value = mock_client_instance
        
        config = {"model": "llama2"}
        provider = OllamaProvider(config)
        provider._client = mock_client_instance
        
        health = await provider.check_health()
        
        self.assertFalse(health["available"])
        self.assertIn("unavailable", health["message"])
        self.assertIn("Connection refused", health["message"])
    
    def test_ollama_supported_features(self):
        """Test OllamaProvider supported features."""
        config = {"model": "llama2"}
        provider = OllamaProvider(config)
        
        features = provider.get_supported_features()
        
        expected_features = {
            "streaming": True,
            "tools": True,
            "multimodal": True,
            "embeddings": False,
            "fine_tuning": False
        }
        
        self.assertEqual(features, expected_features)
    
    def test_openai_supported_features(self):
        """Test OpenAIProvider supported features."""
        config = {"api_key": "test-key", "model": "gpt-4"}
        provider = OpenAIProvider(config)
        
        features = provider.get_supported_features()
        
        expected_features = {
            "streaming": True,
            "tools": True,
            "multimodal": True,
            "embeddings": True,
            "fine_tuning": True,
            "structured_outputs": True,
            "reasoning": True
        }
        
        self.assertEqual(features, expected_features)
    
    def test_ProviderRegistry_can_create_providers(self):
        """Test that registry can create provider instances."""
        # Register providers
        from hatchling.core.llm.providers.ollama_provider import OllamaProvider
        from hatchling.core.llm.providers.openai_provider import OpenAIProvider
        
        # Test Ollama provider creation
        with patch('hatchling.core.llm.providers.ollama_provider.AsyncClient'):
            ollama_config = {"model": "llama2"}
            ollama_provider = ProviderRegistry.create_provider("ollama", ollama_config)
            self.assertIsInstance(ollama_provider, OllamaProvider)
            self.assertEqual(ollama_provider.provider_name, "ollama")
        
        # Test OpenAI provider creation
        openai_config = {"api_key": "test-key", "model": "gpt-4"}
        openai_provider = ProviderRegistry.create_provider("openai", openai_config)
        self.assertIsInstance(openai_provider, OpenAIProvider)
        self.assertEqual(openai_provider.provider_name, "openai")
    
    def test_provider_abstract_methods_implemented(self):
        """Test that both providers implement all abstract methods."""
        # Check OllamaProvider
        with patch('hatchling.core.llm.providers.ollama_provider.AsyncClient'):
            ollama_provider = OllamaProvider({"model": "llama2"})
            
            # All abstract methods should be implemented
            self.assertTrue(hasattr(ollama_provider, 'initialize'))
            self.assertTrue(hasattr(ollama_provider, 'prepare_chat_payload'))
            self.assertTrue(hasattr(ollama_provider, 'add_tools_to_payload'))
            self.assertTrue(hasattr(ollama_provider, 'stream_chat_response'))
            self.assertTrue(hasattr(ollama_provider, 'check_health'))
            self.assertTrue(hasattr(ollama_provider, 'provider_name'))
        
        # Check OpenAIProvider
        openai_provider = OpenAIProvider({"api_key": "test-key", "model": "gpt-4"})
        
        # All abstract methods should be implemented
        self.assertTrue(hasattr(openai_provider, 'initialize'))
        self.assertTrue(hasattr(openai_provider, 'prepare_chat_payload'))
        self.assertTrue(hasattr(openai_provider, 'add_tools_to_payload'))
        self.assertTrue(hasattr(openai_provider, 'stream_chat_response'))
        self.assertTrue(hasattr(openai_provider, 'check_health'))
        self.assertTrue(hasattr(openai_provider, 'provider_name'))


if __name__ == '__main__':
    unittest.main()
