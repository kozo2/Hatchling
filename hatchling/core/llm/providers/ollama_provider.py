"""Ollama provider implementation for LLM abstraction layer.

This module provides the OllamaProvider class that implements the LLMProvider interface
for the Ollama local inference server using the official ollama Python client.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from ollama import AsyncClient

from .base import LLMProvider
from .registry import ProviderRegistry
from hatchling.config.settings import AppSettings
from hatchling.config.llm_settings import ELLMProvider
from hatchling.core.llm.streaming_management.stream_publisher import StreamPublisher
from hatchling.core.llm.streaming_management.stream_data import StreamEventType
from hatchling.core.llm.streaming_management.tool_lifecycle_subscriber import ToolLifecycleSubscriber
from hatchling.mcp_utils.manager import mcp_manager

logger = logging.getLogger(__name__)

@ProviderRegistry.register(ELLMProvider.OLLAMA)
class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference.
    
    This provider uses the Ollama AsyncClient to communicate with a local or remote
    Ollama inference server. It supports streaming responses, tool calling, and
    multiple model architectures available through Ollama.
    """
    
    def __init__(self, settings: AppSettings = None):
        """Initialize the Ollama provider.
        
        Args:
            settings (AppSettings, optional): Application settings containing Ollama configuration.
                                            If None, uses the singleton instance.

        Raises:
            ValueError: If Ollama settings are invalid or missing required fields.
        """
        super().__init__(settings)
        self._client: Optional[AsyncClient] = None
        self.initialize()
        
        logger.debug(f"Initialized OllamaProvider with host: {self._settings.ollama.api_base}")
    
    @property
    def provider_name(self) -> str:
        """Return the provider name.
        
        Returns:
            str: The provider name "ollama" (from ELLMProvider enum).
        """
        return ELLMProvider.OLLAMA.value
    
    def initialize(self) -> None:
        """Initialize the Ollama async client and verify connection.
        
        Raises:
            ConnectionError: If unable to connect to Ollama server.
            ValueError: If configuration is invalid.
        """
        try:
            self._client = AsyncClient(host=self._settings.ollama.api_base)
            self._toolLifecycle_subscriber = ToolLifecycleSubscriber(ELLMProvider.OLLAMA.value)
            self._stream_publisher = StreamPublisher(ELLMProvider.OLLAMA)
            mcp_manager.publisher.subscribe(self._toolLifecycle_subscriber)
            
            logger.info(f"Successfully connected to Ollama server at {self._settings.ollama.api_base}")
            
        except Exception as e:
            error_msg = f"Failed to initialize Ollama client: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        
    def close(self) -> None:
        """Close the Ollama client connection and clean up resources.
        
        This method should be called when the provider is no longer needed.
        It will close the AsyncClient connection gracefully.
        """
        mcp_manager.publisher.unsubscribe(self._toolLifecycle_subscriber)
        self._stream_publisher.clear_subscribers()
    
    def prepare_chat_payload(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare chat payload for Ollama API format.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries.
            model (str): Model name to use.
            **kwargs: Additional chat parameters.
        
        Returns:
            Dict[str, Any]: Formatted payload for Ollama chat API.
        """
        # Base payload structure
        payload = {
            "model": model,
            "messages": messages,
            "stream": kwargs.get("stream", True)
        }
        
        # Add optional parameters if provided
        optional_params = [
            "format", "template", "system", "context", 
            "raw", "keep_alive"
        ]
        
        for param in optional_params:
            if param in kwargs:
                payload[param] = kwargs[param]
        
        # Build options from settings with kwargs override
        options = {}
        
        # Map settings to Ollama options
        settings_mapping = {
            "num_ctx": self._settings.ollama.num_ctx,
            "repeat_last_n": self._settings.ollama.repeat_last_n,
            "repeat_penalty": self._settings.ollama.repeat_penalty,
            "temperature": self._settings.ollama.temperature,
            "seed": self._settings.ollama.seed,
            "num_predict": self._settings.ollama.num_predict,
            "top_k": self._settings.ollama.top_k,
            "top_p": self._settings.ollama.top_p,
            "min_p": self._settings.ollama.min_p,
        }
        
        if self._settings.ollama.stop:
            options["stop"] = self._settings.ollama.stop
        
        # Apply settings defaults
        for key, value in settings_mapping.items():
            options[key] = kwargs.get(key, value)
        
        # Map common parameters to Ollama options with kwargs override
        param_mapping = {
            "max_tokens": "num_predict",
        }
        
        for param, ollama_param in param_mapping.items():
            if param in kwargs:
                options[ollama_param] = kwargs[param]
        
        if options:
            payload["options"] = options
        
        logger.debug(f"Prepared Ollama chat payload for model: {model}")
        return payload
    
    def add_tools_to_payload(
        self, 
        payload: Dict[str, Any], 
        tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add tool definitions to the Ollama chat payload.
        
        Args:
            payload (Dict[str, Any]): Base chat payload.
            tools (Optional[List[str]]): Specific list of tool names to add to the payload. If None, all available and enabled tools are added.
                                         If provided, only the specified tools that are enabled will be added to the payload.
        Returns:
            Dict[str, Any]: Updated payload with tools.
        """
        
        # Convert tools to Ollama format
        ollama_tools = []
        all_tools = self._toolLifecycle_subscriber.get_all_tools()
        enabled_tools = self._toolLifecycle_subscriber.get_enabled_tools()

        # If no specific tools provided, use all enabled tools
        if tools is None:
            ollama_tools = [
                tool.provider_format for tool in enabled_tools.values()
            ]

        else:
            for tool_name in tools:
                # Ensure the function definition exists in the tool cache
                if not tool_name in all_tools:
                    error_msg = f"Function definition for {tool_name} not found in tool cache"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                if not tool_name in enabled_tools:
                    warning_msg = f"Function {tool_name} is disabled with reason: {self._toolLifecycle_subscriber.prettied_reason(all_tools[tool_name].reason)}" 
                    logger.warning(warning_msg)
                    continue #skipping disabled tools
                
                ollama_tools.append(enabled_tools[tool_name].provider_format)
        
        if ollama_tools:
            # Add tools to payload
            payload["tools"] = ollama_tools
            logger.debug(f"Added {len(ollama_tools)} tools to Ollama payload")

        return payload
    
    async def stream_chat_response(
        self, 
        payload: Dict[str, Any]
    ):
        """Stream chat response from Ollama with publish-subscribe events.
        
        Args:
            payload (Dict[str, Any]): Chat request payload.
        
        Raises:
            RuntimeError: If client is not initialized.
            Exception: If streaming fails.
        """
        if not self._client:
            raise RuntimeError("Ollama client not initialized. Call initialize() first.")
        
        try:
            # Ensure streaming is enabled for this request
            payload["stream"] = True

            # Generate a unique request ID for this streaming session
            request_id = str(uuid.uuid4())
            self._stream_publisher.set_request_id(request_id)
            
            # Stream the response
            response_stream = await self._client.chat(**payload)
            async for chunk in response_stream:
                # Parse chunk and publish events to subscribers
                self._parse_and_publish_chunk(chunk)
                    
        except Exception as e:
            error_msg = f"Error streaming from Ollama: {str(e)}"
            logger.error(error_msg)
            
            # Publish error event
            self._stream_publisher.publish(
                StreamEventType.ERROR,
                {
                    "error": {"message": error_msg, "type": "ollama_streaming_error"},
                    "request_id": request_id
                }
            )
            raise
    
    
    def _parse_and_publish_chunk(self, chunk: Any) -> None:
        """Parse Ollama chunk and publish events to subscribers.
        
        Args:
            chunk (Any): Raw chunk from Ollama API. Typically a Dict[str, Any] with keys like "message", "done", etc.
            
        Returns:
            Any: Standardized chunk format.
        """
        try:
            
            # Handle content (message delta)
            if "message" in chunk:
                message = chunk["message"]
                if "role" in message:
                    # Publish role event
                    self._stream_publisher.publish(
                        StreamEventType.ROLE,
                        {"role": message["role"]}
                    )
                
                if "content" in message and message["content"]:
                    content = message["content"]
                    # Publish content event
                    self._stream_publisher.publish(
                        StreamEventType.CONTENT,
                        {"content": content}
                    )
            
            # Handle completion state
            if chunk.get("done", False):
                # Publish finish event
                self._stream_publisher.publish(
                    StreamEventType.FINISH,
                    {"finish_reason": "stop"}
                )
                
                # Handle usage stats if available in final chunk
                if "eval_count" in chunk or "prompt_eval_count" in chunk:
                    usage = {
                        "prompt_tokens": chunk.get("prompt_eval_count", 0),
                        "completion_tokens": chunk.get("eval_count", 0),
                        "total_tokens": chunk.get("prompt_eval_count", 0) + chunk.get("eval_count", 0)
                    }
                    # Publish usage event
                    self._stream_publisher.publish(
                        StreamEventType.USAGE,
                        {"usage": usage}
                    )
            
            # Handle tool calls (if supported in future Ollama versions)
            if "message" in chunk and "tool_calls" in chunk["message"]:
                tool_calls = chunk["message"]["tool_calls"]
                # Publish tool calls
                self._stream_publisher.publish(
                    StreamEventType.TOOL_CALL,
                    {"tool_calls": tool_calls}
                )
            
        except Exception as e:
            error_msg = f"Error parsing Ollama chunk: {str(e)}"
            logger.error(error_msg)
            
            # Publish error event
            self._stream_publisher.publish(
                StreamEventType.ERROR,{"error": {"message": error_msg, "type": "chunk_parsing_error"}}
            )
    

    async def check_health(self) -> Dict[str, Union[bool, str]]:
        """Check if Ollama server is healthy and accessible.
        
        Returns:
            Dict[str, Union[bool, str]]: Health status information containing:
                - available (bool): Whether the service is available
                - message (str): Descriptive status message
                - models (List[str], optional): Available models if accessible
        """
        if not self._client:
            return {
                "available": False,
                "message": "Ollama client not initialized"
            }
        
        try:
            # Test connection by listing available models
            models_response = await self._client.list()
            models = [model.get("name", "unknown") for model in models_response.get("models", [])]
            
            return {
                "available": True,
                "message": f"Ollama server healthy with {len(models)} models available",
                "models": models
            }
            
        except Exception as e:
            return {
                "available": False,
                "message": f"Ollama server unavailable: {str(e)}"
            }
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Get supported features of this provider.
        
        Returns:
            Dict[str, bool]: Dictionary of supported features.
        """
        return {
            "streaming": True,
            "tools": True,
            "multimodal": True,  # Depends on model
            "embeddings": False,  # Not implemented in this provider
            "fine_tuning": False
        }
