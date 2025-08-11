"""LLM Provider abstraction package.

This package provides a provider abstraction layer for different LLM services,
allowing the system to work with multiple providers (OpenAI, Ollama, etc.)
through a common interface.
"""

from .base import LLMProvider
from .registry import ProviderRegistry

# Import providers to ensure they register themselves
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider

__all__ = [
    'LLMProvider', 
    'ProviderRegistry', 
    'OllamaProvider',
    'OpenAIProvider'
]
