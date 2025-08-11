"""Registry for managing tool call parsers for different LLM providers.

This module provides a registry system for dynamically registering and
discovering tool call parsers for LLM providers using the decorator pattern.
"""

import logging
from typing import Dict, Type, Optional, List
from .tool_call_parse_strategy import ToolCallParseStrategy
from hatchling.config.llm_settings import ELLMProvider

class ToolCallParseRegistry:
    """Registry for managing tool call parse strategies.
    
    This class provides a centralized registry for tool call parse strategies,
    allowing dynamic registration and instantiation using the decorator pattern.
    """
    
    _strategies: Dict[ELLMProvider, Type[ToolCallParseStrategy]] = {}
    _instances: Dict[ELLMProvider, ToolCallParseStrategy] = {}
    
    @classmethod
    def register(cls, provider: ELLMProvider):
        """Decorator to register a tool call parse strategy.
        
        Args:
            provider (ELLMProvider): The LLM provider for which this strategy is applicable.
            
        Returns:
            Callable: Decorator function that registers the strategy class.
        """
        def decorator(strategy_class: Type[ToolCallParseStrategy]):
            if not issubclass(strategy_class, ToolCallParseStrategy):
                raise ValueError(f"Strategy class {strategy_class.__name__} must inherit from ToolCallParseStrategy")
            
            cls._strategies[provider] = strategy_class
            logging.getLogger(__name__).debug(f"Registered tool call parse strategy for provider '{provider}' -> {strategy_class.__name__}")
            return strategy_class
        return decorator
    
    @classmethod
    def create_strategy(cls, provider: ELLMProvider) -> ToolCallParseStrategy:
        """Create a parse strategy instance by provider.
        
        Args:
            provider (ELLMProvider): The LLM provider for which to create the strategy.
            
        Returns:
            ToolCallParseStrategy: An instance of the requested parse strategy.
            
        Raises:
            ValueError: If the provider is not registered.
        """
        if provider not in cls._strategies:
            available = list(cls._strategies.keys())
            raise ValueError(f"Unknown provider: '{provider}'. Available providers: {available}")
        
        # Create a new instance each time for now
        instance = cls._strategies[provider]()
        cls._instances[provider] = instance
        logging.getLogger(__name__).debug(f"Created tool call parse strategy instance: {provider} -> {instance.__class__.__name__}")
        return instance
    
    @classmethod
    def get_strategy_class(cls, provider: ELLMProvider) -> Optional[Type[ToolCallParseStrategy]]:
        """Get the parse strategy class by provider without instantiating it.
        
        Args:
            provider (ELLMProvider): The LLM provider for which to get the strategy class.
            
        Returns:
            Optional[Type[ToolCallParseStrategy]]: The strategy class, or None if not found.
        """
        return cls._strategies.get(provider)
    
    @classmethod
    def get_strategy(cls, provider: ELLMProvider) -> ToolCallParseStrategy:
        """Get the parse strategy instance for a provider.
        
        Args:
            provider (ELLMProvider): The LLM provider for which to get the strategy instance.
            
        Returns:
            ToolCallParseStrategy: An instance of the requested parse strategy.

        Raises:
            ValueError: If the provider is not registered.
        """
        if provider not in cls._strategies:
            raise ValueError(f"Parse strategy for provider '{provider}' is not registered. Available providers: {list(cls._strategies.keys())}")

        if provider not in cls._instances:
            return cls.create_strategy(provider)

        return cls._instances[provider]

    @classmethod
    def list_strategies(cls) -> List[ELLMProvider]:
        """List all registered parse strategy providers.
        
        Returns:
            List[ELLMProvider]: List of registered provider enums.
        """
        return list(cls._strategies.keys())
    
    @classmethod
    def is_registered(cls, provider: ELLMProvider) -> bool:
        """Check if a parse strategy is registered for a provider.
        
        Args:
            provider (ELLMProvider): The provider to check.
            
        Returns:
            bool: True if the strategy is registered, False otherwise.
        """
        return provider in cls._strategies
    
    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered parse strategies.
        
        This method is primarily useful for testing purposes.
        """
        cls._strategies.clear()
        cls._instances.clear()
        logging.getLogger(__name__).debug("Cleared tool call parse strategy registry")