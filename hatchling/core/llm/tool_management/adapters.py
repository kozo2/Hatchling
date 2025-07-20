"""Tool format adapters for converting MCP tools to provider-specific formats.

This module provides adapter classes that convert MCP tool schemas to the specific
formats required by different LLM providers (OpenAI, Ollama, etc.).
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo

logger = logging.getLogger(__name__)


class BaseMCPToolAdapter(ABC):
    """Base class for MCP tool format adapters."""
    
    def __init__(self, provider_name: str):
        """Initialize the adapter.
        
        Args:
            provider_name (str): Name of the LLM provider this adapter serves.
        """
        self.provider_name = provider_name
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{provider_name}]")
    
    @abstractmethod
    def convert_tool(self, tool_info: MCPToolInfo) -> Dict[str, Any]:
        """Convert an MCP tool to provider-specific format.

        `tool_info` is expected to be an in/out parameter 
        whose provider_format field will be set to the converted
        tool format.
        
        Args:
            tool_info (MCPToolInfo): MCP tool information to convert.
            
        Returns:
            Dict[str, Any]: Tool in provider-specific format.
        """
        pass
    
    def convert_tools(self, tools: Dict[str, MCPToolInfo]) -> List[Dict[str, Any]]:
        """Convert multiple MCP tools to provider-specific format.
        
        Args:
            tools (Dict[str, MCPToolInfo]): Dictionary of MCP tools to convert.
            
        Returns:
            List[Dict[str, Any]]: List of tools in provider-specific format.
        """
        converted_tools = []
        
        for tool_name, tool_info in tools.items():
            try:
                converted_tool = self.convert_tool(tool_info)
                if converted_tool:
                    converted_tools.append(converted_tool)
            except Exception as e:
                self.logger.error(f"Failed to convert tool {tool_name}: {e}")
        
        return converted_tools

class MCPToolAdapterRegistry:
    """Registry class for managing tool adapters for different providers."""
    
    _adapters: Dict[str, type] = {}
    _instances: Dict[str, BaseMCPToolAdapter] = {}
    
    @classmethod
    def register(cls, adapter_name: str):
        """Decorator to register a tool adapter class.
        
        Args:
            adapter_name (str): The name to register the adapter under.
            
        Returns:
            Callable: Decorator function that registers the adapter class.
        """
        def decorator(adapter_class: type):
            if not issubclass(adapter_class, BaseMCPToolAdapter):
                raise ValueError(f"Adapter class {adapter_class.__name__} must inherit from BaseMCPToolAdapter")
            
            cls._adapters[adapter_name] = adapter_class
            logger.debug(f"Registered tool adapter '{adapter_name}' -> {adapter_class.__name__}")
            return adapter_class
        return decorator
    
    @classmethod
    def create_adapter(cls, name: str) -> Optional[BaseMCPToolAdapter]:
        """Create an adapter instance for a specific provider.
        
        Args:
            name (str): The name of the provider to create an adapter for.
            
        Returns:
            Optional[BaseMCPToolAdapter]: An instance of the requested adapter, or None if not found.
        """
        if name not in cls._adapters:
            available = list(cls._adapters.keys())
            raise ValueError(f"Unknown adapter: '{name}'. Available adapters: {available}")
        
        # Create a new instance each time for now
        instance = cls._adapters[name](name)
        cls._instances[name] = instance
        return instance
    
    @classmethod
    def get_adapter_instance(cls, name: str) -> Optional[BaseMCPToolAdapter]:
        """Get an existing adapter instance by name.
        
        Args:
            name (str): The name of the provider to get the adapter for.
            
        Returns:
            Optional[BaseMCPToolAdapter]: The adapter instance, or None if not found.
        """
        return cls._instances.get(name)

    @classmethod
    def list_adapters(cls) -> List[str]:
        """List all registered adapter names.
        
        Returns:
            List[str]: List of registered adapter names.
        """
        return list(cls._adapters.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an adapter is registered.
        
        Args:
            name (str): The adapter name to check.
            
        Returns:
            bool: True if the adapter is registered, False otherwise.
        """
        return name in cls._adapters

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered adapters.
        
        This method is primarily useful for testing purposes.
        """
        cls._adapters.clear()
        cls._instances.clear()
        logger.debug("Cleared adapter registry")

@MCPToolAdapterRegistry.register("ollama")
class OllamaMCPToolAdapter(BaseMCPToolAdapter):
    """Adapter for converting MCP tools to Ollama function format."""
    
    def convert_tool(self, tool_info: MCPToolInfo) -> Dict[str, Any]:
        """Convert an MCP tool to Ollama function format.

        `tool_info` is an in/out parameter whose provider_format
        field will be set to the converted tool format.
        
        Args:
            tool_info (MCPToolInfo): MCP tool information to convert.
            
        Returns:
            Dict[str, Any]: Tool in Ollama function format.
        """
        try:
            # Ollama uses a similar format to OpenAI but with some differences
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool_info.name,
                    "description": tool_info.description,
                    "parameters": tool_info.schema
                }
            }
            
            # Cache the converted format in the tool info
            tool_info.provider_format = ollama_tool
            
            self.logger.debug(f"Converted tool {tool_info.name} to Ollama format")
            return ollama_tool
            
        except Exception as e:
            self.logger.error(f"Failed to convert tool {tool_info.name} to Ollama format: {e}")
            return {}

@MCPToolAdapterRegistry.register("openai")
class OpenAIMCPToolAdapter(BaseMCPToolAdapter):
    """Adapter for converting MCP tools to OpenAI function format."""
    
    def convert_tool(self, tool_info: MCPToolInfo) -> Dict[str, Any]:
        """Convert an MCP tool to OpenAI function format.
        
        Args:
            tool_info (MCPToolInfo): MCP tool information to convert.
            
        Returns:
            Dict[str, Any]: Tool in OpenAI function format.
        """
        try:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_info.name,
                    "description": tool_info.description,
                    "parameters": tool_info.schema.get("parameters", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            }
            
            # Cache the converted format in the tool info
            tool_info.provider_format = openai_tool
            
            self.logger.debug(f"Converted tool {tool_info.name} to OpenAI format")
            return openai_tool
            
        except Exception as e:
            self.logger.error(f"Failed to convert tool {tool_info.name} to OpenAI format: {e}")
            return {}
