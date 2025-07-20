"""Ollama provider implementation for LLM abstraction layer.

This module provides the OllamaProvider class that implements the LLMProvider interface
for the Ollama local inference server using the official ollama Python client.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, AsyncIterator, Union
from ollama import AsyncClient

from .base import LLMProvider
from .registry import ProviderRegistry
from .subscription import StreamPublisher, StreamEventType, ToolLifecycleSubscriber
from hatchling.mcp_utils.manager import mcp_manager

logger = logging.getLogger(__name__)

@ProviderRegistry.register("ollama")
class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference.
    
    This provider uses the Ollama AsyncClient to communicate with a local or remote
    Ollama inference server. It supports streaming responses, tool calling, and
    multiple model architectures available through Ollama.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Ollama provider.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - host (str, optional): Ollama server URL. Defaults to "http://localhost:11434".
                - timeout (float, optional): Request timeout in seconds. Defaults to 30.0.
                - model (str, optional): Default model name. Defaults to "llama2".
                - stream (bool, optional): Enable streaming responses. Defaults to True.
                - **kwargs: Additional parameters passed to AsyncClient.
        """
        super().__init__(config)
        self._client: Optional[AsyncClient] = None
        self._host = config.get("host", "http://localhost:11434")
        self._timeout = config.get("timeout", 30.0)
        self._default_model = config.get("model", "llama3.2")
        self._stream_enabled = config.get("stream", True)

        self._toolLifecycle_subscriber = ToolLifecycleSubscriber("ollama")
        
        # Store additional client options
        self._client_options = {
            key: value for key, value in config.items()
            if key not in ["host", "timeout", "model", "stream"]
        }
        
        logger.debug(f"Initialized OllamaProvider with host: {self._host}, model: {self._default_model}")
    
    @property
    def provider_name(self) -> str:
        """Return the provider name.
        
        Returns:
            str: The provider name "ollama".
        """
        return "ollama"
    
    async def initialize(self) -> None:
        """Initialize the Ollama async client and verify connection.
        
        Raises:
            ConnectionError: If unable to connect to Ollama server.
            ValueError: If configuration is invalid.
        """
        try:
            self._stream_publisher = StreamPublisher("ollama")
            mcp_manager.publisher.subscribe(self._toolLifecycle_subscriber)

            self._client = AsyncClient(
                host=self._host,
                timeout=self._timeout,
                **self._client_options
            )
            
            # Test connection by checking if server is available
            await self._client.list()  # This will raise an exception if server is unavailable
            
            logger.info(f"Successfully connected to Ollama server at {self._host}")
            
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
    
    def prepare_chat_payload(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare chat payload for Ollama API format.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries.
            model (str, optional): Model name to use. Uses default if not provided.
            **kwargs: Additional chat parameters.
        
        Returns:
            Dict[str, Any]: Formatted payload for Ollama chat API.
        """
        # Use provided model or fallback to default
        selected_model = model or self._default_model
        
        # Base payload structure
        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": kwargs.get("stream", self._stream_enabled)
        }
        
        # Add optional parameters if provided
        optional_params = [
            "format", "options", "template", "system", "context", 
            "raw", "keep_alive"
        ]
        
        for param in optional_params:
            if param in kwargs:
                payload[param] = kwargs[param]
        
        # Handle options parameter (model-specific settings)
        if "options" not in payload and any(
            key in kwargs for key in ["temperature", "top_p", "top_k", "num_predict"]
        ):
            payload["options"] = {}
            
            # Map common parameters to Ollama options
            param_mapping = {
                "temperature": "temperature",
                "top_p": "top_p", 
                "top_k": "top_k",
                "max_tokens": "num_predict",
                "num_predict": "num_predict"
            }
            
            for param, ollama_param in param_mapping.items():
                if param in kwargs:
                    payload["options"][ollama_param] = kwargs[param]
        
        logger.debug(f"Prepared Ollama chat payload for model: {selected_model}")
        return payload
    
    def add_tools_to_payload(
        self, 
        payload: Dict[str, Any], 
        tools: List[str]
    ) -> Dict[str, Any]:
        """Add tool definitions to the Ollama chat payload.
        
        Args:
            payload (Dict[str, Any]): Base chat payload.
            tools (List[str]): List of tool names.
        
        Returns:
            Dict[str, Any]: Updated payload with tools.
        """
        if not tools:
            return payload
        
        # Convert tools to Ollama format
        ollama_tools = []
        all_tools = self._toolLifecycle_subscriber.get_all_tools()
        enabled_tools = self._toolLifecycle_subscriber.get_enabled_tools()
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
            
        # Add tools to payload
        payload["tools"] = ollama_tools

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
