"""Publisher-Subscriber pattern for LLM streaming responses.

This module provides a flexible publish-subscribe system that allows different
components to subscribe to specific events from LLM streaming responses.
"""

import logging
from typing import Dict, Any, Callable, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason
logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of events that can be published during streaming."""
    
    # LLM Response Events
    CONTENT = "content"              # Text content from the model
    ROLE = "role"                   # Role assignment (assistant, user, etc.)
    TOOL_CALL = "tool_call"         # Tool/function call
    FINISH = "finish"               # Stream completion with reason
    USAGE = "usage"                 # Token usage statistics
    ERROR = "error"                 # Error occurred during streaming
    REFUSAL = "refusal"            # Model refused to answer
    THINKING = "thinking"          # Model thinking process (for reasoning models)
    METADATA = "metadata"          # Additional metadata (fingerprint, etc.)
    
    # MCP Lifecycle Events
    MCP_SERVER_UP = "mcp_server_up"                    # MCP server connection established
    MCP_SERVER_DOWN = "mcp_server_down"                # MCP server connection lost
    MCP_SERVER_UNREACHABLE = "mcp_server_unreachable"  # MCP server cannot be reached
    MCP_SERVER_REACHABLE = "mcp_server_reachable"      # MCP server became reachable again
    MCP_TOOL_ENABLED = "mcp_tool_enabled"              # MCP tool was enabled
    MCP_TOOL_DISABLED = "mcp_tool_disabled"            # MCP tool was disabled
    
    # Tool Execution Events
    TOOL_CALL_DISPATCHED = "tool_call_dispatched"      # Tool call was dispatched for execution
    TOOL_CALL_RESULT = "tool_call_result"              # Tool call completed with result
    TOOL_CALL_PROGRESS = "tool_call_progress"          # Tool call progress update
    TOOL_CALL_ERROR = "tool_call_error"                # Tool call failed with error



@dataclass
class StreamEvent:
    """Represents an event in the streaming response.
    
    This standardized event format allows different LLM providers to publish
    events in a consistent way, regardless of their native response format.
    """
    
    type: StreamEventType
    data: Dict[str, Any]
    provider: str
    request_id: Optional[str] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            import time
            self.timestamp = time.time()


class StreamSubscriber(ABC):
    """Abstract base class for stream event subscribers."""
    
    @abstractmethod
    def on_event(self, event: StreamEvent) -> None:
        """Handle a stream event.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        pass
    
    @abstractmethod
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return list of event types this subscriber is interested in.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        pass


class CallableSubscriber(StreamSubscriber):
    """A subscriber that wraps a callable function."""
    
    def __init__(self, callback: Callable[[StreamEvent], None], event_types: List[StreamEventType]):
        """Initialize callable subscriber.
        
        Args:
            callback (Callable[[StreamEvent], None]): Function to call on events.
            event_types (List[StreamEventType]): Event types to subscribe to.
        """
        self.callback = callback
        self.event_types = event_types
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle event by calling the callback function.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        try:
            self.callback(event)
        except Exception as e:
            logger.error(f"Error in callback subscriber: {e}")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        return self.event_types


class StreamPublisher:
    """Publisher for streaming events using the observer pattern."""
    
    def __init__(self, provider_name: str):
        """Initialize the publisher.
        
        Args:
            provider_name (str): Name of the LLM provider publishing events.
        """
        self.provider_name = provider_name
        self._subscribers: List[StreamSubscriber] = []
        self._active_request_id: Optional[str] = None
    
    def subscribe(self, subscriber: StreamSubscriber) -> None:
        """Subscribe to stream events.
        
        Args:
            subscriber (StreamSubscriber): Subscriber to add.
        """
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
            logger.debug(f"Added subscriber for events: {subscriber.get_subscribed_events()}")
    
    def unsubscribe(self, subscriber: StreamSubscriber) -> None:
        """Unsubscribe from stream events.
        
        Args:
            subscriber (StreamSubscriber): Subscriber to remove.
        """
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
            logger.debug("Removed subscriber")
    
    def clear_subscribers(self) -> None:
        """Remove all subscribers."""
        self._subscribers.clear()
        logger.debug("Cleared all subscribers")
    
    def set_request_id(self, request_id: str) -> None:
        """Set the current request ID for published events.
        
        Args:
            request_id (str): ID for the current request.
        """
        self._active_request_id = request_id
    
    def publish(self, event_type: StreamEventType, data: Dict[str, Any]) -> None:
        """Publish an event to all interested subscribers.
        
        Args:
            event_type (StreamEventType): Type of event to publish.
            data (Dict[str, Any]): Event data.
        """
        event = StreamEvent(
            type=event_type,
            data=data,
            provider=self.provider_name,
            request_id=self._active_request_id
        )
        
        for subscriber in self._subscribers:
            if event_type in subscriber.get_subscribed_events():
                try:
                    subscriber.on_event(event)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")


# Common subscriber implementations

class ContentPrinterSubscriber(StreamSubscriber):
    """Subscriber that prints content to console as it arrives."""
    
    def __init__(self, include_role: bool = False):
        """Initialize content printer.
        
        Args:
            include_role (bool): Whether to print role information.
        """
        self.include_role = include_role
        self._first_content = True
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle content and role events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.CONTENT:
            content = event.data.get("content", "")
            print(content, end="", flush=True)
        elif event.type == StreamEventType.ROLE and self.include_role:
            role = event.data.get("role", "")
            if self._first_content:
                print(f"[{role}] ", end="", flush=True)
                self._first_content = False
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        events = [StreamEventType.CONTENT]
        if self.include_role:
            events.append(StreamEventType.ROLE)
        return events


class UsageStatsSubscriber(StreamSubscriber):
    """Subscriber that tracks and reports usage statistics."""
    
    def __init__(self):
        """Initialize usage stats subscriber."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.start_time = None
        self.end_time = None
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle usage and timing events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.CONTENT and self.start_time is None:
            # Record start time on first content
            self.start_time = event.timestamp
        elif event.type == StreamEventType.USAGE:
            # Record final usage stats
            usage_data = event.data.get("usage", {})
            self.total_tokens = usage_data.get("total_tokens", 0)
            self.prompt_tokens = usage_data.get("prompt_tokens", 0)
            self.completion_tokens = usage_data.get("completion_tokens", 0)
            self.end_time = event.timestamp
            self._print_stats()
        elif event.type == StreamEventType.FINISH and self.start_time and not self.end_time:
            # If no usage event, record end time on finish
            self.end_time = event.timestamp
            self._print_stats()
    
    def _print_stats(self) -> None:
        """Print usage statistics and generation rate."""
        print(f"\n\n=== Usage Statistics ===")
        print(f"Total tokens: {self.total_tokens}")
        print(f"Prompt tokens: {self.prompt_tokens}")
        print(f"Completion tokens: {self.completion_tokens}")
        
        if self.start_time and self.end_time and self.completion_tokens > 0:
            duration = self.end_time - self.start_time
            tokens_per_second = self.completion_tokens / duration if duration > 0 else 0
            print(f"Generation time: {duration:.2f} seconds")
            print(f"Generation rate: {tokens_per_second:.2f} tokens/second")
        print("========================")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        return [StreamEventType.CONTENT, StreamEventType.USAGE, StreamEventType.FINISH]


class ErrorHandlerSubscriber(StreamSubscriber):
    """Subscriber that handles and reports errors."""
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle error events.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        if event.type == StreamEventType.ERROR:
            error_data = event.data.get("error", {})
            message = error_data.get("message", "Unknown error")
            error_type = error_data.get("type", "Unknown")
            print(f"\n\nStreaming Error ({error_type}): {message}")
        elif event.type == StreamEventType.REFUSAL:
            refusal = event.data.get("refusal", "")
            print(f"\n\nModel refused: {refusal}")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return subscribed event types.
        
        Returns:
            List[StreamEventType]: Event types to subscribe to.
        """
        return [StreamEventType.ERROR, StreamEventType.REFUSAL]

# MCP Tool Lifecycle Management Subscribers

class ToolLifecycleSubscriber(StreamSubscriber):
    """Subscriber that manages MCP tool lifecycle and maintains tool cache
    in the format required by the LLM provider.
    
    This subscriber listens for MCP server and tool lifecycle events and maintains
    a cache of all discovered tools with their current status. It provides methods
    to get enabled tools for use in LLM payloads.
    """
    
    def __init__(self, provider_name: str):
        """Initialize the tool lifecycle subscriber.
        
        Args:
            provider_name (str): Name of the LLM provider using this subscriber.
        """
        self.provider_name = provider_name
        self._tool_cache: Dict[str, MCPToolInfo] = {}
        self._mcp_tool_adapter = MCPToolAdapterRegistry.get_adapter_instance(provider_name)
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{provider_name}]")
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle MCP lifecycle events and update tool cache.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        try:
            if event.type == StreamEventType.MCP_SERVER_UP:
                self._handle_server_up_event(event)
            elif event.type == StreamEventType.MCP_SERVER_DOWN:
                self._handle_server_down_event(event)
            elif event.type == StreamEventType.MCP_SERVER_UNREACHABLE:
                self._handle_server_unreachable_event(event)
            elif event.type == StreamEventType.MCP_SERVER_REACHABLE:
                self._handle_server_reachable_event(event)
            elif event.type == StreamEventType.MCP_TOOL_ENABLED:
                self._handle_tool_enabled_event(event)
            elif event.type == StreamEventType.MCP_TOOL_DISABLED:
                self._handle_tool_disabled_event(event)
                
        except Exception as e:
            self.logger.error(f"Error handling event {event.type}: {e}")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return MCP lifecycle event types this subscriber is interested in.
        
        Returns:
            List[StreamEventType]: MCP lifecycle event types.
        """
        return [
            StreamEventType.MCP_SERVER_UP,
            StreamEventType.MCP_SERVER_DOWN,
            StreamEventType.MCP_SERVER_UNREACHABLE,
            StreamEventType.MCP_SERVER_REACHABLE,
            StreamEventType.MCP_TOOL_ENABLED,
            StreamEventType.MCP_TOOL_DISABLED
        ]
    
    def _handle_server_up_event(self, event: StreamEvent) -> None:
        """Handle server up event."""
        server_path = event.data.get("server_path", "")
        tool_count = event.data.get("tool_count", 0)
        
        self.logger.info(f"Server up: {server_path} with {tool_count} tools")
    
    def _handle_server_down_event(self, event: StreamEvent) -> None:
        """Handle server down event."""
        server_path = event.data.get("server_path", "")
        
        # Disable all tools from this server
        tools_disabled = 0
        for tool_info in self._tool_cache.values():
            if tool_info.server_path == server_path and tool_info.status == MCPToolStatus.ENABLED:
                tool_info.status = MCPToolStatus.DISABLED
                tool_info.reason = MCPToolStatusReason.FROM_SERVER_DOWN
                tools_disabled += 1
        
        self.logger.info(f"Server down: {server_path} - disabled {tools_disabled} tools")
    
    def _handle_server_unreachable_event(self, event: StreamEvent) -> None:
        """Handle server unreachable event."""
        server_path = event.data.get("server_path", "")
        error = event.data.get("error", "Unknown error")
        
        # Disable all tools from this server
        tools_disabled = 0
        for tool_info in self._tool_cache.values():
            if tool_info.server_path == server_path and tool_info.status == MCPToolStatus.ENABLED:
                tool_info.status = MCPToolStatus.DISABLED
                tool_info.reason = MCPToolStatusReason.FROM_SERVER_UNREACHABLE
                tools_disabled += 1
        
        self.logger.warning(f"Server unreachable: {server_path} ({error}) - disabled {tools_disabled} tools")
    
    def _handle_server_reachable_event(self, event: StreamEvent) -> None:
        """Handle server reachable event."""
        server_path = event.data.get("server_path", "")
        
        # Re-enable tools from this server that were disabled due to unreachability
        tools_enabled = 0
        for tool_info in self._tool_cache.values():
            if (tool_info.server_path == server_path and 
                tool_info.status == MCPToolStatus.DISABLED and
                tool_info.reason == MCPToolStatusReason.FROM_SERVER_UNREACHABLE):
                
                tool_info.status = MCPToolStatus.ENABLED
                tool_info.reason = MCPToolStatusReason.FROM_SERVER_REACHABLE
                tools_enabled += 1
        
        self.logger.info(f"Server reachable: {server_path} - re-enabled {tools_enabled} tools")
    
    def _handle_tool_enabled_event(self, event: StreamEvent) -> None:
        """Handle tool enabled event."""
        tool_name = event.data.get("tool_name", "")
        
        # Create or update tool info from event data
        if tool_name not in self._tool_cache:
            tool_info = event.data.get("mcp_tool_info", {})

            if not tool_info:
                self.logger.error(f"'Tool enabled event' missing 'mcp_tool_info' for tool '{tool_name}'")
                return
            
            # Convert tool to provider-specific format
            # Tool info is an in/out parameter in convert_tool
            # Hence, the provider_format field will be set
            # to the converted tool format
            self._mcp_tool_adapter.convert_tool(tool_info)

            self._tool_cache[tool_name] = tool_info
            self.logger.debug(f"Tool enabled: {tool_name}")
    
    def _handle_tool_disabled_event(self, event: StreamEvent) -> None:
        """Handle tool disabled event."""
        tool_name = event.data.get("tool_name", "")
        
        if tool_name in self._tool_cache:
            tool_info = self._tool_cache[tool_name]
            tool_info.status = MCPToolStatus.DISABLED
            
            if "reason" in event.data:
                try:
                    tool_info.reason = MCPToolStatusReason[event.data["reason"].upper()]
                except (KeyError, ValueError):
                    tool_info.reason = MCPToolStatusReason.FROM_SYSTEM_ERROR
            
            self.logger.debug(f"Tool disabled: {tool_name}")
    
    def get_enabled_tools(self) -> Dict[str, MCPToolInfo]:
        """Get all currently enabled tools.
        
        Returns:
            Dict[str, MCPToolInfo]: Dictionary mapping tool names to enabled tool info.
        """
        return {
            name: info for name, info in self._tool_cache.items()
            if info.status == MCPToolStatus.ENABLED
        }
    
    def get_all_tools(self) -> Dict[str, MCPToolInfo]:
        """Get all tools (enabled and disabled).
        
        Returns:
            Dict[str, MCPToolInfo]: Dictionary mapping tool names to all tool info.
        """
        return self._tool_cache.copy()
    
    def get_tool_count(self) -> Dict[str, int]:
        """Get count of enabled and disabled tools.
        
        Returns:
            Dict[str, int]: Dictionary with 'enabled' and 'disabled' counts.
        """
        enabled = sum(1 for info in self._tool_cache.values() 
                     if info.status == MCPToolStatus.ENABLED)
        disabled = len(self._tool_cache) - enabled
        
        return {"enabled": enabled, "disabled": disabled}
    
    def clear_cache(self) -> None:
        """Clear the tool cache."""
        self._tool_cache.clear()
        self.logger.debug("Tool cache cleared")
