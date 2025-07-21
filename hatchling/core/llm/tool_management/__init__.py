"""Tool management module initialization."""

from .adapters import (
    BaseMCPToolAdapter,
    OpenAIMCPToolAdapter, 
    OllamaMCPToolAdapter,
    MCPToolAdapterRegistry,
)

from .tool_call_parse_strategy import ToolCallParseStrategy
from .tool_call_parse_registry import ToolCallParseRegistry

from .tool_call_parse_strategies import (
    OpenAIToolCallParseStrategy,
    OllamaToolCallParseStrategy
)

__all__ = [
    'BaseMCPToolAdapter',
    'OpenAIMCPToolAdapter',
    'OllamaMCPToolAdapter',
    'MCPToolAdapterRegistry',
    'ToolCallParseRegistry',
    'ToolCallParseStrategy',
    'OpenAIToolCallParseStrategy',
    'OllamaToolCallParseStrategy'
]
