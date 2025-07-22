
"""Abstract base class for LLM providers.

Defines the interface and common utilities for all LLM provider implementations.
Ensures consistent interaction and feature discovery across different LLM services.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from hatchling.core.llm.streaming_management import StreamPublisher
from hatchling.core.llm.streaming_management.tool_lifecycle_subscriber import ToolLifecycleSubscriber
from hatchling.config.settings import AppSettings

class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must implement this interface to ensure consistent
    functionality and feature discovery across different LLM services.
    """

    def __init__(self, settings: AppSettings):
        """Initialize the provider with configuration."""
        self._settings = settings
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
    def publisher(self) -> StreamPublisher:
        """Return the stream event publisher for this provider.
        
        Returns:
            StreamPublisher: The publisher for streaming events.
        """
        return self._stream_publisher    

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider and verify connectivity.

        This method should perform any necessary setup and verify that the
        provider can be used (e.g., check connectivity, validate configuration).

        Raises:
            Exception: If initialization fails or configuration is invalid.
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
    

    @property
    def supported_models(self) -> List[str]:
        """Return list of supported models for this provider.

        Returns:
            List[str]: List of model names supported by this provider.
        """
        return []

    def get_supported_features(self) -> Dict[str, bool]:
        """Get supported features of this provider.

        Returns:
            Dict[str, bool]: Dictionary of supported features (e.g., streaming, tools).
        """
        return {}
    

    def has_tool_calls(self, data: Dict[str, Any]) -> bool:
        """Check if the response data contains tool calls.

        Args:
            data (Dict[str, Any]): Response data from the LLM.

        Returns:
            bool: True if the data contains tool calls, False otherwise.
        """
        return (
            "message" in data and
            "tool_calls" in data["message"] and
            bool(data["message"]["tool_calls"])
        )
    

    def has_message_content(self, data: Dict[str, Any]) -> bool:
        """Check if the response data contains message content.

        Args:
            data (Dict[str, Any]): Response data from the LLM.

        Returns:
            bool: True if the data contains message content, False otherwise.
        """
        return "message" in data and "content" in data["message"]
