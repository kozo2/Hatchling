"""Registry for managing LLM providers.

This module provides a registry system for dynamically registering and
discovering LLM providers using the decorator pattern.
"""

from typing import Dict, Type, Optional, List
import logging

from hatchling.config.settings import AppSettings
from hatchling.config.llm_settings import ELLMProvider
from hatchling.core.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """Registry for managing LLM providers.
    
    This class provides a centralized registry for LLM providers,
    allowing dynamic registration and instantiation using the decorator pattern.
    """
    
    _providers: Dict[ELLMProvider, Type[LLMProvider]] = {}
    _instances: Dict[ELLMProvider, LLMProvider] = {}
    
    @classmethod
    def register(cls, provider_enum: ELLMProvider):
        """Decorator to register a provider class.
        
        Args:
            provider_enum (ELLMProvider): The enum name to register the provider under.

        Returns:
            Callable: Decorator function that registers the provider class.
            
        Example:
            @ProviderRegistry.register(ELLMProvider.OLLAMA)
            class OllamaProvider(LLMProvider):
                pass
        """
        def decorator(provider_class: Type[LLMProvider]):
            if not issubclass(provider_class, LLMProvider):
                raise ValueError(f"Provider class {provider_class.__name__} must inherit from LLMProvider")
            
            cls._providers[provider_enum] = provider_class
            logger.debug(f"Registered provider '{provider_enum}' -> {provider_class.__name__}")
            return provider_class
        return decorator
    
    @classmethod
    def create_provider(cls, provider_enum: ELLMProvider, settings: AppSettings = None) -> LLMProvider:
        """Create a provider instance by enum.
        
        Args:
            provider_enum (ELLMProvider): The enum of the provider to create.
            settings (AppSettings, optional): Application settings to pass to the provider.
                                            If None, providers will use the singleton instance.
            
        Returns:
            LLMProvider: An instance of the requested provider.
            
        Raises:
            ValueError: If the provider enum is not registered.
        """
        if provider_enum not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(f"Unknown provider: '{provider_enum}'. Available providers: {available}")

        instance = cls._providers[provider_enum](settings)
        logger.debug(f"Created provider instance: {provider_enum} -> {instance.__class__.__name__}")
        return instance
    
    @classmethod
    def get_provider_class(cls, provider_enum: ELLMProvider) -> Optional[Type[LLMProvider]]:
        """Get the provider class by enum without instantiating it.
        
        Args:
            provider_enum (ELLMProvider): The enum of the provider.

        Returns:
            Optional[Type[LLMProvider]]: The provider class, or None if not found.
        """
        return cls._providers.get(provider_enum)

    @classmethod
    def get_provider(cls, provider_enum: ELLMProvider, settings: Optional[AppSettings] = None) -> LLMProvider:
        """Get the provider instance for a given enum.
        
        Args:
            provider_enum (ELLMProvider): The enum of the provider to retrieve.
            settings (AppSettings, optional): Application settings to pass to the provider.
                                            If None, providers will use the singleton instance.
            
        Returns:
            LLMProvider: An instance of the requested provider.
            
        Raises:
            ValueError: If the provider is not registered.
        """
        if provider_enum not in cls._providers:
            raise ValueError(f"Provider '{provider_enum}' is not registered. Available providers: {list(cls._providers.keys())}")

        if provider_enum not in cls._instances:
            cls._instances[provider_enum] = cls.create_provider(provider_enum, settings)
        return cls._instances[provider_enum]

    @classmethod
    def list_providers(cls) -> List[ELLMProvider]:
        """List all registered provider names.
        
        Returns:
            List[ELLMProvider]: List of registered provider names.
        """
        return list(cls._providers.keys())
    
    @classmethod
    def is_registered(cls, provider_enum: ELLMProvider) -> bool:
        """Check if a provider is registered.
        
        Args:
            provider_enum (ELLMProvider): The provider enum to check.

        Returns:
            bool: True if the provider is registered, False otherwise.
        """
        return provider_enum in cls._providers

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered providers.
        
        This method is primarily useful for testing purposes.
        """
        cls._providers.clear()
        cls._instances.clear()
        logger.debug("Cleared provider registry")
