"""LLM Provider abstraction package.

This package provides a provider abstraction layer for different LLM services,
allowing the system to work with multiple providers (OpenAI, Ollama, etc.)
through a common interface.
"""

from .base import LLMProvider
from .registry import ProviderRegistry

__all__ = [
    'LLMProvider', 
    'ProviderRegistry', 
]
