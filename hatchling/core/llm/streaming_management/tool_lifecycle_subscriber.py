import logging
from typing import Dict, List

from .stream_data import StreamEvent, StreamEventType
from .stream_subscriber import StreamSubscriber
from hatchling.mcp_utils import MCPToolInfo, MCPToolStatus, MCPToolStatusReason
from hatchling.core.llm.tool_management import MCPToolAdapterRegistry


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
        self._mcp_tool_adapter = MCPToolAdapterRegistry.get_adapter(provider_name)
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

    def prettied_reason(self, reason: MCPToolStatusReason) -> str:
        """Get a prettified string representation of the tool status reason.
        
        Args:
            reason (MCPToolStatusReason): The reason to prettify.
        
        Returns:
            str: Prettified reason string.
        """
        if reason == MCPToolStatusReason.FROM_SERVER_UP:
            return "Enabled at server startup"
        elif reason == MCPToolStatusReason.FROM_USER_ENABLED:
            return "Enabled by user (while server is up and reachable)"
        elif reason == MCPToolStatusReason.FROM_SERVER_REACHABLE:
            return "Server is reachable again after being down or unreachable"
        elif reason == MCPToolStatusReason.FROM_SERVER_DOWN:
            return "Server is down"
        elif reason == MCPToolStatusReason.FROM_SERVER_UNREACHABLE:
            return "Server is unreachable"
        elif reason == MCPToolStatusReason.FROM_USER_DISABLED:
            return "Tool disabled by user"
        elif reason == MCPToolStatusReason.FROM_SYSTEM_ERROR:
            return "System error occurred"
        else:
            return str(reason.value)
