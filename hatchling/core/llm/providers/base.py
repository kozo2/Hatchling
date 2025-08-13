
"""Abstract base class for LLM providers.

Defines the interface and common utilities for all LLM provider implementations.
Ensures consistent interaction and feature discovery across different LLM services.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from hatchling.core.llm.streaming_management import StreamPublisher
from hatchling.core.llm.streaming_management.tool_lifecycle_subscriber import ToolLifecycleSubscriber
from hatchling.core.llm.streaming_management.stream_subscribers import StreamEvent
from hatchling.core.llm.data_structures import ToolCallParsedResult
from hatchling.config.settings import AppSettings
from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo

class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must implement this interface to ensure consistent
    functionality and feature discovery across different LLM services.
    """

    def __init__(self, settings: AppSettings = None):
        """Initialize the provider with configuration.
        
        Args:
            settings (AppSettings, optional): Configuration settings. 
                                            If None, uses the singleton instance.
        """
        self._settings = settings or AppSettings.get_instance()
        self._stream_publisher : Optional[StreamPublisher] = None
        self._toolLifecycle_subscriber: Optional[ToolLifecycleSubscriber] = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider's canonical name.

        Returns:
            str: The provider name (e.g., "openai", "ollama").
        """
        pass

    @property
    @abstractmethod
    def provider_enum(self) -> str:
        """Return the provider's enum name.

        Returns:
            str: The enum name of the provider (e.g., "OPENAI", "OLLAMA").
        """
        pass
    
    @property
    def publisher(self) -> StreamPublisher:
        """Return the stream event publisher for this provider.
        
        Returns:
            StreamPublisher: The publisher for streaming events.
        """
        return self._stream_publisher    

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider.

        This method should perform any necessary setup.

        Raises:
            Exception: If initialization fails.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the provider connection and clean up resources.

        This method should be called when the provider is no longer needed.
        It should release any resources and close connections gracefully.
        """
        pass
    

    @abstractmethod
    def prepare_chat_payload(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare a provider-specific chat request payload.

        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries in standard format.
            model (str): Model name to use.
            **kwargs: Additional provider-specific parameters (e.g., temperature, max_tokens).

        Returns:
            Dict[str, Any]: Provider-specific payload ready for API request.
        """
        pass
    

    @abstractmethod
    def add_tools_to_payload(
        self,
        payload: Dict[str, Any],
        tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add tools to the payload in provider-specific format.

        Args:
            payload (Dict[str, Any]): The base payload to modify.
            tools (Optional[List[str]]): Specific list of tool names to add to the payload.
                                         If None, all available and enabled tools are added.
                                         Among these provided tools, only those that are enabled will be added to the payload.

        Returns:
            Dict[str, Any]: Modified payload with tools added in provider format.
        """
        pass
    

    @abstractmethod
    async def stream_chat_response(
        self,
        payload: Dict[str, Any],
        **kwargs
    ):
        """Stream chat response from the provider.

        Args:
            payload (Dict[str, Any]): Provider-specific request payload.
            **kwargs: Additional provider-specific arguments (e.g., streaming, tool handling).

        Yields:
            Dict[str, Any]: Response chunks in standardized format.

        Raises:
            Exception: If streaming fails or client is not initialized.
        """
        pass
    
    @abstractmethod
    def _parse_and_publish_chunk(
        self,
        chunk: Any
    ):
        """Parse a response chunk and publish events to subscribers.

        Args:
            chunk (Any): Raw response chunk from the provider. The format depends on the provider.
            
        Raises:
            Exception: If chunk parsing fails or is invalid.
        """
        pass

    @abstractmethod
    async def check_health(self) -> dict:
        """Check provider health and availability.

        Returns:
            dict: Health status information (should include 'available' and 'message').
        """
        pass

    @abstractmethod
    def parse_tool_call(self, event: StreamEvent) -> Optional[ToolCallParsedResult]:
        """Parse a tool call event into a standardized format.

        Args:
            event (StreamEvent): The raw tool call event from the LLM provider.

        Returns:
            Optional[ToolCallParsedResult]: Normalized representation of the tool call, 
                                          or None if the event cannot be parsed.

        Raises:
            ValueError: If the event cannot be parsed as a valid tool call.
        """
        pass

    @abstractmethod
    def convert_tool(self, tool_info: MCPToolInfo) -> Dict[str, Any]:
        """Convert an MCP tool to provider-specific format.

        Args:
            tool_info (MCPToolInfo): MCP tool information to convert. This is expected
                                   to be an in/out parameter whose provider_format 
                                   field will be set to the converted tool format.

        Returns:
            Dict[str, Any]: Tool in provider-specific format.

        Raises:
            Exception: If tool conversion fails.
        """
        pass
