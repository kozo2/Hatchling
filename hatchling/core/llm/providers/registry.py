"""Registry for managing LLM providers.

This module provides a registry system for dynamically registering and
discovering LLM providers using the decorator pattern.
"""

from typing import Dict, Type, Optional, List
import logging
from .base import LLMProvider


class ProviderRegistry:
    """Registry for managing LLM providers.
    
    This class provides a centralized registry for LLM providers,
    allowing dynamic registration and instantiation using the decorator pattern.
    """
    
    _providers: Dict[str, Type[LLMProvider]] = {}
    _instances: Dict[str, LLMProvider] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register a provider class.
        
        Args:
            name (str): The name to register the provider under.
            
        Returns:
            Callable: Decorator function that registers the provider class.
            
        Example:
            @ProviderRegistry.register("ollama")
            class OllamaProvider(LLMProvider):
                pass
        """
        def decorator(provider_class: Type[LLMProvider]):
            if not issubclass(provider_class, LLMProvider):
                raise ValueError(f"Provider class {provider_class.__name__} must inherit from LLMProvider")
            
            cls._providers[name] = provider_class
            logging.getLogger(__name__).debug(f"Registered provider '{name}' -> {provider_class.__name__}")
            return provider_class
        return decorator
    
    @classmethod
    def create_provider(cls, name: str, settings) -> LLMProvider:
        """Create a provider instance by name.
        
        Args:
            name (str): The name of the provider to create.
            settings: Application settings to pass to the provider.
            
        Returns:
            LLMProvider: An instance of the requested provider.
            
        Raises:
            ValueError: If the provider name is not registered.
        """
        if name not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(f"Unknown provider: '{name}'. Available providers: {available}")
        
        # Create a new instance each time for now
        # TODO: Consider caching instances if needed for performance
        instance = cls._providers[name](settings)
        logging.getLogger(__name__).debug(f"Created provider instance: {name}")
        return instance
    
    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type[LLMProvider]]:
        """Get the provider class by name without instantiating it.
        
        Args:
            name (str): The name of the provider.
            
        Returns:
            Optional[Type[LLMProvider]]: The provider class, or None if not found.
        """
        return cls._providers.get(name)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered provider names.
        
        Returns:
            List[str]: List of registered provider names.
        """
        return list(cls._providers.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a provider is registered.
        
        Args:
            name (str): The provider name to check.
            
        Returns:
            bool: True if the provider is registered, False otherwise.
        """
        return name in cls._providers
    
    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered providers.
        
        This method is primarily useful for testing purposes.
        """
        cls._providers.clear()
        cls._instances.clear()
        logging.getLogger(__name__).debug("Cleared provider registry")
