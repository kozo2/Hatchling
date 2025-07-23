"""Registry for managing LLM providers.

This module provides a registry system for dynamically registering and
discovering LLM providers using the decorator pattern.
"""

from typing import Dict, Type, Optional, List
import logging

from hatchling.config.settings import AppSettings
from hatchling.core.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)

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
            logger.debug(f"Registered provider '{name}' -> {provider_class.__name__}")
            return provider_class
        return decorator
    
    @classmethod
    def create_provider(cls, name: str, settings: AppSettings = None) -> LLMProvider:
        """Create a provider instance by name.
        
        Args:
            name (str): The name of the provider to create.
            settings (AppSettings, optional): Application settings to pass to the provider.
                                            If None, providers will use the singleton instance.
            
        Returns:
            LLMProvider: An instance of the requested provider.
            
        Raises:
            ValueError: If the provider name is not registered.
        """
        if name not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(f"Unknown provider: '{name}'. Available providers: {available}")
        
        instance = cls._providers[name](settings)
        logger.debug(f"Created provider instance: {name}")
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
    def get_provider(cls, name: str, settings: Optional[AppSettings] = None) -> LLMProvider:
        """Get the provider instance for a given name.
        
        Args:
            name (str): The name of the provider to retrieve.
            settings (AppSettings, optional): Application settings to pass to the provider.
                                            If None, providers will use the singleton instance.
            
        Returns:
            LLMProvider: An instance of the requested provider.
            
        Raises:
            ValueError: If the provider is not registered.
        """
        if name not in cls._providers:
            raise ValueError(f"Provider '{name}' is not registered. Available providers: {list(cls._providers.keys())}")

        if name not in cls._instances:
            cls._instances[name] = cls.create_provider(name, settings)
        return cls._instances[name]
    
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
        logger.debug("Cleared provider registry")
