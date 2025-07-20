"""Tool format adapters for converting MCP tools to provider-specific formats.

This module provides adapter classes that convert MCP tool schemas to the specific
formats required by different LLM providers (OpenAI, Ollama, etc.).
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from hatchling.core.llm.providers.subscription import MCPToolInfo

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


class OllamaMCPToolAdapter(BaseMCPToolAdapter):
    """Adapter for converting MCP tools to Ollama function format."""
    
    def convert_tool(self, tool_info: MCPToolInfo) -> Dict[str, Any]:
        """Convert an MCP tool to Ollama function format.
        
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
                    "parameters": tool_info.schema.get("parameters", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            }
            
            # Cache the converted format in the tool info
            tool_info.provider_format = ollama_tool
            
            self.logger.debug(f"Converted tool {tool_info.name} to Ollama format")
            return ollama_tool
            
        except Exception as e:
            self.logger.error(f"Failed to convert tool {tool_info.name} to Ollama format: {e}")
            return {}


class MCPToolAdapterFactory:
    """Factory class for creating tool adapters for different providers."""
    
    _adapters: Dict[str, type] = {
        "openai": OpenAIMCPToolAdapter,
        "ollama": OllamaMCPToolAdapter
    }
    
    @classmethod
    def create_adapter(cls, provider_name: str) -> Optional[BaseMCPToolAdapter]:
        """Create a tool adapter for the specified provider.
        
        Args:
            provider_name (str): Name of the LLM provider.
            
        Returns:
            Optional[BaseMCPToolAdapter]: Tool adapter instance or None if not supported.
        """
        adapter_class = cls._adapters.get(provider_name.lower())
        if adapter_class:
            return adapter_class(provider_name)
        else:
            logger.warning(f"No tool adapter available for provider: {provider_name}")
            return None
    
    @classmethod
    def register_adapter(cls, provider_name: str, adapter_class: type) -> None:
        """Register a new tool adapter for a provider.
        
        Args:
            provider_name (str): Name of the LLM provider.
            adapter_class (type): Tool adapter class to register.
        """
        cls._adapters[provider_name.lower()] = adapter_class
        logger.info(f"Registered tool adapter for provider: {provider_name}")
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported provider names.
        
        Returns:
            List[str]: List of supported provider names.
        """
        return list(cls._adapters.keys())
