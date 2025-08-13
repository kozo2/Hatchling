"""CLI Event Subscriber for managing UI state and display."""

from typing import List, Optional
from dataclasses import dataclass
import time
from enum import IntFlag, auto
from pathlib import Path

from hatchling.config.settings import AppSettings
from hatchling.mcp_utils.mcp_tool_data import MCPToolInfo, MCPToolStatusReason
from hatchling.core.llm.providers.registry import ProviderRegistry

# TODO: The flag utility should be abstracted for the whole application
# in order to easily define FSM-like systems
class UIStateFlags(IntFlag):
    NONE = 0
    TOOL_CHAIN_ACTIVE = auto()
    CONTENT_STREAMING = auto()
    ERROR_DISPLAYED = auto()
    INFO_DISPLAYED = auto()
    USER_INPUT_READY = auto()

# TODO: The flag utility should be abstracted for the whole application
# in order to easily define FSM-like systems
class UIStateManager:
    """Utility for managing UI state flags."""
    def __init__(self):
        self.flags = UIStateFlags.USER_INPUT_READY

    def set(self, flag: UIStateFlags):
        self.flags |= flag

    def clear(self, flag: UIStateFlags):
        self.flags &= ~flag

    def is_set(self, flag: UIStateFlags) -> bool:
        return bool(self.flags & flag)

    def reset(self):
        self.flags = UIStateFlags.NONE

    def set_only(self, flag: UIStateFlags):
        self.flags = flag

from hatchling.core.llm.event_system.event_subscriber import EventSubscriber
from hatchling.core.llm.event_system.event_data import Event, EventType
from hatchling.core.logging.logging_manager import logging_manager
from prompt_toolkit import print_formatted_text as print_pt

@dataclass
class ServerStatus:
    """Status information for MCP servers and tools."""
    
    servers_up: int = 0
    servers_total: int = 0
    tools_enabled: int = 0
    tools_total: int = 0


@dataclass
class TokenStats:
    """Token usage statistics."""
    total_tokens: int = 0
    total_current: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    start_time: float = None
    end_time: float = None

class CLIEventSubscriber(EventSubscriber):
    """CLI Event Subscriber for managing UI state based on stream events.
    
    This subscriber maintains state for all UI elements:
    - Bottom toolbar: tool execution status and server/tool counts
    - Right prompt: LLM info and token statistics
    - Error/info overlays: transient messages
    
    Uses the Observer pattern to react to events and update UI state.
    """

    def __init__(self, settings: Optional[AppSettings] = None):
        """Initialize the CLI event subscriber with default state."""
        self.logger = logging_manager.get_session("CLIEventSubscriber")
        
        # UI State
        self.server_status = ServerStatus()
        self.token_stats = TokenStats()

        self.settings = settings or AppSettings.get_instance()
        
        # UI Control State
        self.toolbar_view_mode = "default"  # default, tools, servers
        self.right_prompt_view_mode = "default"  # default, tokens, model
        
        # Error/Info Display
        self.current_error: Optional[str] = None
        self.current_info: Optional[str] = None
        self.message_timeout: float = 5.0  # seconds
        self.last_message_time: float = 0.0
        
        # UI state flags manager
        self.ui_state = UIStateManager()

    def on_event(self, event: Event) -> None:
        """Handle stream events and update UI state.
        
        Args:
            event (Event): The event to handle.
        """

        try:
            # Tool Chaining Events
            if event.type == EventType.TOOL_CHAIN_START:
                self.logger.debug(f"Handling TOOL_CHAIN_START event: {event.data}")
                self._handle_tool_chain_start(event)
            elif event.type == EventType.TOOL_CHAIN_ITERATION_START:
                self._handle_tool_chain_iteration_start(event)
            elif event.type == EventType.TOOL_CHAIN_ITERATION_END:
                self._handle_tool_chain_iteration_end(event)
            elif event.type == EventType.TOOL_CHAIN_END:
                self.logger.debug(f"Handling TOOL_CHAIN_END event: {event.data}")
                self._handle_tool_chain_end(event)
            elif event.type == EventType.TOOL_CHAIN_LIMIT_REACHED:
                self.logger.debug(f"Handling TOOL_CHAIN_LIMIT_REACHED event: {event.data}")
                self._handle_tool_chain_limit_reached(event)
            elif event.type == EventType.TOOL_CHAIN_ERROR:
                self.logger.debug(f"Handling TOOL_CHAIN_ERROR event: {event.data}")
                self._handle_tool_chain_error(event)
            
            # Tool Execution Events
            elif event.type == EventType.LLM_TOOL_CALL_REQUEST:
                self.logger.debug(f"Handling LLM_TOOL_CALL_REQUEST event: {event.data}")
                self._handle_llm_tool_call_request(event)
            elif event.type == EventType.MCP_TOOL_CALL_DISPATCHED:
                self.logger.debug(f"Handling MCP_TOOL_CALL_DISPATCHED event: {event.data}")
                self._handle_mcp_tool_call_dispatched(event)
            elif event.type == EventType.MCP_TOOL_CALL_RESULT:
                self.logger.debug(f"Handling MCP_TOOL_CALL_RESULT event: {event.data}")
                self._handle_mcp_tool_call_result(event)
            elif event.type == EventType.MCP_TOOL_CALL_ERROR:
                self.logger.debug(f"Handling MCP_TOOL_CALL_ERROR event: {event.data}")
                self._handle_mcp_tool_call_error(event)
            
            # MCP Server Events
            elif event.type == EventType.MCP_SERVER_UP:
                self.logger.debug(f"Handling MCP_SERVER_UP event: {event.data}")
                self._handle_mcp_server_up(event)
            elif event.type == EventType.MCP_SERVER_DOWN:
                self.logger.debug(f"Handling MCP_SERVER_DOWN event: {event.data}")
                self._handle_mcp_server_down(event)
            elif event.type == EventType.MCP_TOOL_ENABLED:
                self.logger.debug(f"Handling MCP_TOOL_ENABLED event: {event.data}")
                self._handle_mcp_tool_enabled(event)
            elif event.type == EventType.MCP_TOOL_DISABLED:
                self.logger.debug(f"Handling MCP_TOOL_DISABLED event: {event.data}")
                self._handle_mcp_tool_disabled(event)
            
            # LLM Events
            elif event.type == EventType.CONTENT:
                #self.logger.debug(f"Handling CONTENT event: {event.data}")
                self._handle_content(event)
            elif event.type == EventType.USAGE:
                self.logger.debug(f"Handling USAGE event: {event.data}")
                self._handle_usage(event)
            elif event.type == EventType.ERROR:
                self.logger.debug(f"Handling ERROR event: {event.data}")
                self._handle_error(event)
            elif event.type == EventType.FINISH:
                self.logger.debug(f"Handling FINISH event: {event.data}")
                self._handle_finish(event)
            
        except Exception as e:
            self.logger.error(f"Error handling event {event.type.value}: {e}")

    def get_subscribed_events(self) -> List[EventType]:
        """Return list of event types this subscriber is interested in.
        
        Returns:
            List[EventType]: Event types for UI updates.
        """
        return [
            # Tool Chaining Events
            EventType.TOOL_CHAIN_START,
            EventType.TOOL_CHAIN_END,
            EventType.TOOL_CHAIN_LIMIT_REACHED,
            EventType.TOOL_CHAIN_ERROR,
            
            # Tool Execution Events
            EventType.LLM_TOOL_CALL_REQUEST,
            EventType.MCP_TOOL_CALL_DISPATCHED,
            EventType.MCP_TOOL_CALL_RESULT,
            EventType.MCP_TOOL_CALL_ERROR,
            
            # MCP Server Events
            EventType.MCP_SERVER_UP,
            EventType.MCP_SERVER_DOWN,
            EventType.MCP_TOOL_ENABLED,
            EventType.MCP_TOOL_DISABLED,
            
            # LLM Events
            EventType.CONTENT,
            EventType.USAGE,
            EventType.ERROR,
            EventType.FINISH,
        ]

    # Tool Chaining Event Handlers
    def _handle_tool_chain_start(self, event: Event) -> None:
        """Handle tool chain start event."""
        data = event.data
        self.ui_state.set(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.ui_state.clear(UIStateFlags.USER_INPUT_READY)
        self.logger.debug(f"Tool chain started - TOOL_CHAIN_ACTIVE set, USER_INPUT_READY cleared")
        # Truncating initial query if it's too long
        initial_query = data.get("initial_query", "No query")
        if isinstance(initial_query, str) and len(initial_query) > 100:
            initial_query = initial_query[:100] + "..."
        self._set_info(
            f"[{data.get('tool_chain_id', 'ID unknown')}]\n" +
            f"Tool chaining started for initial query: {initial_query}\n" +
            f" {data.get('max_iterations', 0)} iterations allowed.")

    def _handle_tool_chain_iteration_start(self, event: Event) -> None:
        """Handle tool chain iteration event."""
        data = event.data
        self._set_info(
            f"[{data.get('tool_chain_id', 'ID unknown')}]\n" +
            f"Step {data.get('iteration', -1)}/{data.get('max_iterations', 0)}:\n" +
            f"Feeding back result of {data.get('tool_name', 'unknown')} to LLM.")
        self.ui_state.set(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.ui_state.clear(UIStateFlags.USER_INPUT_READY)

    def _handle_tool_chain_iteration_end(self, event: Event) -> None:
        """Handle tool chain iteration event."""
        data = event.data
        self._set_info(
            f"[{data.get('tool_chain_id', 'ID unknown')}]\n" +
            f"Step {data.get('iteration', -1)}/{data.get('max_iterations', 0)}:\n" +
            f"Result of {data.get('tool_name', 'unknown')} processed by the LLM.")

    def _handle_tool_chain_end(self, event: Event) -> None:
        """Handle tool chain end event."""
        data = event.data
        
        success = data.get("success", True)
        # Truncating initial query if it's too long
        initial_query = data.get("initial_query", "No query")
        if isinstance(initial_query, str) and len(initial_query) > 100:
            initial_query = initial_query[:100] + "..."

        if success:
            self._set_info(
                f"[{data.get('tool_chain_id', 'ID unknown')}]\n" +
                f"Tool chaining completed successfully for initial query: {initial_query}\n" +
                f"Iteration: {data.get('iteration', 0)}/{data.get('max_iterations', 0)}, Total time: {data.get('elapsed_time', 0):.2f} seconds"
            )
        else:
            self._set_error(
                f"[{data.get('tool_chain_id', 'ID unknown')}]\n" +
                f"Tool chaining failed for initial query: {initial_query}\n" +
                f"Iteration: {data.get('iteration', 0)}/{data.get('max_iterations', 0)}, Total time: {data.get('elapsed_time', 0):.2f} seconds"
            )

        self.current_chain = None
        self.ui_state.clear(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.logger.debug(f"Tool chain ended - TOOL_CHAIN_ACTIVE cleared")

        self._handle_finish(event)

    def _handle_tool_chain_limit_reached(self, event: Event) -> None:
        """Handle tool chain limit reached event."""
        data = event.data
        self._set_info(
            f"[{data.get('tool_chain_id', 'ID unknown')}]\n" +
            f"Tool chaining stopped: {data.get('limit_type', 'unknown')} ({data.get('iterations', 0)} steps, {data.get('elapsed_time', 0):.2f} seconds elapsed)"
        )
        self.logger.debug(f"Tool chain limit reached - TOOL_CHAIN_ACTIVE cleared")

    def _handle_tool_chain_error(self, event: Event) -> None:
        """Handle tool chain error event."""
        data = event.data
        self._set_error(
            f"[{data.get('tool_chain_id', 'ID unknown')}]\n" +
            f"Tool chaining failed at step {data.get('iteration', 0)}: {data.get('error', 'Unknown error')}"
        )
        self.ui_state.clear(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.logger.debug(f"Tool chain error - TOOL_CHAIN_ACTIVE cleared")

    # Tool Execution Event Handlers
    def _handle_llm_tool_call_request(self, event: Event) -> None:
        """Handle LLM tool call request event."""
        data = event.data
        # Set tool is running
        provider = ProviderRegistry.get_provider(event.provider)
        parsed_tool_call = provider.parse_tool_call(event)
        self._set_info(
            f"[{parsed_tool_call.tool_call_id}]\n" +
            f"Tool call to {parsed_tool_call.function_name} requested with parameters:\n" +
            f"{', '.join([f'{k}={v}' for k, v in parsed_tool_call.arguments.items()])}"
        )


    def _handle_mcp_tool_call_dispatched(self, event: Event) -> None:
        """Handle MCP tool call dispatched event."""
        data = event.data
        self._set_info(
            f"[{data.get('tool_call_id', 'unknown')}]\n" +
            f"Tool {data.get('function_name', 'unknown')} dispatched with parameters:\n" +
            f"{', '.join([f'{k}={v}' for k, v in data.get('arguments', {}).items()])}"
        )

    def _handle_mcp_tool_call_result(self, event: Event) -> None:
        """Handle MCP tool call result event."""
        data = event.data
        # Truncate result if too long
        result = data.get("result", "No returned value")
        if isinstance(result, str) and len(result) > 100:
            result = result[:100] + "..."
        self._set_info(
            f"[{data.get('tool_call_id', 'unknown')}]\n" +
            f"Tool {data.get('function_name', 'unknown')} result: {result}"
        )

    def _handle_mcp_tool_call_error(self, event: Event) -> None:
        """Handle MCP tool call error event."""
        data = event.data
        tool_name = data.get("function_name", "unknown")
        error = data.get("error", "Unknown error")
        self._set_error(
            f"[{data.get('tool_call_id', 'ID unknown')}]\n" +
            f"Execution of tool {tool_name} failed: {error}"
        )
        self.current_tool = None
        # Don't clear any UI state flags here, as the tool call error
        # might be part of an ongoing tool chain. Hence we give the
        # LLM a chance to fix its mistake by retrying the tool call.
        # TODO: However, put up a warning
        #  TBD: Warning might be redundant with previous ones upstream
        #       in the code flow. 

    # MCP Server Event Handlers
    def _handle_mcp_server_up(self, event: Event) -> None:
        """Handle MCP server up event."""
        data = event.data
        self.server_status.servers_up += 1
        self.server_status.tools_total += data.get("tool_count", 0)
        server_path = data.get("server_path", "unknown")
        self._set_info(f"MCP server connected: {Path(server_path).name}")

    def _handle_mcp_server_down(self, event: Event) -> None:
        """Handle MCP server down event."""
        data = event.data
        self.server_status.servers_up -= 1
        self.server_status.tools_total -= data.get("tool_count", 0)
        server_path = data.get("server_path", "unknown")
        self._set_info(f"MCP server disconnected: {Path(server_path).name}")

    def _handle_mcp_tool_enabled(self, event: Event) -> None:
        """Handle MCP tool enabled event."""
        data = event.data
        self.server_status.tools_enabled += 1
        tool_info : MCPToolInfo = data.get("tool_info", {})
        self._set_info(f"Tool enabled: {tool_info.name} ({Path(tool_info.server_path).name})\n" +
                       f"\tDescription: {tool_info.description}\n" +
                       f"\tParameters: {', '.join([f'{k}={v}' for k, v in tool_info.schema.items()])}")

    def _handle_mcp_tool_disabled(self, event: Event) -> None:
        """Handle MCP tool disabled event."""
        data = event.data
        self.server_status.tools_enabled -= 1
        tool_info: MCPToolInfo = data.get("tool_info", {})
        if tool_info.reason == MCPToolStatusReason.FROM_SERVER_DOWN:
            self.server_status.tools_total -= 1 #If the server got disconnected, we decrement the tool count
        self._set_info(f"Tool disabled: {tool_info.name} ({Path(tool_info.server_path).name})")

    # LLM Event Handlers
    def _handle_usage(self, event: Event) -> None:
        """Handle usage statistics event.

        Args:
            event (Event): The event to handle.
        """
        usage_data = event.data.get("usage", {})
        self.token_stats.total_current = usage_data.get("total_tokens", 0)
        self.token_stats.total_tokens += self.token_stats.total_current
        self.token_stats.prompt_tokens = usage_data.get("prompt_tokens", 0)
        self.token_stats.completion_tokens = usage_data.get("completion_tokens", 0)
        # Optionally, print or log stats here if needed

    def _handle_content(self, event: Event) -> None:
        """Handle content event by accumulating content.

        Args:
            event (Event): The event to handle.
        """
        self.ui_state.clear(UIStateFlags.USER_INPUT_READY)
        self.ui_state.set(UIStateFlags.CONTENT_STREAMING)
        
        content = event.data.get("content", "")
        print_pt(content, end="", flush=True)

    def _handle_finish(self, event: Event) -> None:
        """Handle finish event.

        Args:
            event (Event): The event to handle.
        """
        if self.token_stats.start_time and not self.token_stats.end_time:
            self.token_stats.end_time = event.timestamp
        # Only if all other activities but content streaming are done
        # means that this finish event is the end of a content stream
        if self.ui_state.is_set(UIStateFlags.CONTENT_STREAMING):
            print() # new line
            if not self.ui_state.is_set(UIStateFlags.TOOL_CHAIN_ACTIVE):
                self.ui_state.clear(UIStateFlags.CONTENT_STREAMING)
                self.ui_state.set(UIStateFlags.USER_INPUT_READY)
                self.logger.debug("All content apparently finished, USER_INPUT_READY set")

    def _handle_error(self, event: Event) -> None:
        """Handle error event."""
        data = event.data
        error = data.get("error", "Unknown error")
        self._set_error(f"LLM Error: {error}")
        self.ui_state.clear(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.ui_state.set(UIStateFlags.USER_INPUT_READY)

    # UI State Management
    def _set_error(self, message: str) -> None:
        """Set error message with timestamp."""
        self.ui_state.set(UIStateFlags.ERROR_DISPLAYED)
        self.current_error = message
        self.current_info = None
        self.last_message_time = time.time()

    def _set_info(self, message: str) -> None:
        """Set info message with timestamp."""
        self.ui_state.set(UIStateFlags.INFO_DISPLAYED)
        self.current_info = message
        self.current_error = None
        self.last_message_time = time.time()

    def _clear_expired_messages(self) -> None:
        """Clear error/info messages after timeout."""
        if time.time() - self.last_message_time > self.message_timeout:
            self.current_error = None
            self.current_info = None

    # UI Display Methods
    def get_toolbar_text(self) -> str:
        """Get current toolbar text based on state and view mode."""
        self._clear_expired_messages()
        
        # Show error/info messages with priority
        if self.current_error:
            return f"❌ {self.current_error}"
        if self.current_info:
            return f"ℹ️ {self.current_info}"
    
        # Show server/tool status when idle
        return f"🌐 Servers: {self.server_status.servers_up} up | 🛠️ Tools: {self.server_status.tools_enabled} enabled / {self.server_status.tools_total} total"

    def get_right_prompt_text(self) -> str:
        """Get current right prompt text based on state and view mode."""
        duration = None
        tps = None
        if self.token_stats.start_time and self.token_stats.end_time and self.token_stats.completion_tokens > 0:
            duration = self.token_stats.end_time - self.token_stats.start_time
            tps = self.token_stats.completion_tokens / duration if duration > 0 else 0
        
        stats = ""
        if self.right_prompt_view_mode == "model":
            return f"🤖 {self.settings.llm.provider_name}\n{self.settings.llm.model}"
        
        if self.right_prompt_view_mode == "tokens":
            stats = f"📊 In: {self.token_stats.prompt_tokens}\nOut: {self.token_stats.completion_tokens}\nLast Query: {self.token_stats.total_current}"
            if tps is not None:
                stats += f"\n Rate: {tps:.1f}/s"
            stats += f"\nTotal: {self.token_stats.total_tokens}"
            return stats
        else:  # default
            stats = f"🤖 {self.settings.llm.model}\n📊 Last Query: {self.token_stats.total_current}"
            if tps is not None:
                stats += f"({tps:.1f}/s)"
            stats += f"\nTotal: {self.token_stats.total_tokens}"
            return stats

    def cycle_toolbar_view(self) -> None:
        """Cycle through toolbar view modes."""
        modes = ["default", "tools", "servers"]
        current_index = modes.index(self.toolbar_view_mode)
        self.toolbar_view_mode = modes[(current_index + 1) % len(modes)]

    def cycle_right_prompt_view(self) -> None:
        """Cycle through right prompt view modes."""
        modes = ["default", "tokens", "model"]
        current_index = modes.index(self.right_prompt_view_mode)
        self.right_prompt_view_mode = modes[(current_index + 1) % len(modes)]

    def is_ready_for_user_input(self) -> bool:
        """Check if the system is ready for user input using state flags."""
        # Not ready if tool chain or tool running
        not_ready_mask = UIStateFlags.TOOL_CHAIN_ACTIVE | UIStateFlags.CONTENT_STREAMING
        if self.ui_state.is_set(not_ready_mask):
            self.logger.debug(f"Not ready: {not_ready_mask} flag set:\n"
                              f" TOOL_CHAIN_ACTIVE={self.ui_state.is_set(UIStateFlags.TOOL_CHAIN_ACTIVE)}, "
                              f" CONTENT_STREAMING={self.ui_state.is_set(UIStateFlags.CONTENT_STREAMING)}")
            return False
        return self.ui_state.is_set(UIStateFlags.USER_INPUT_READY)

    def set_processing_user_message(self, processing: bool = True) -> None:
        """Set whether we're currently processing a user message using state flags.
        Args:
            processing (bool): True if processing, False if done.
        """
        if processing:
            self.ui_state.clear(UIStateFlags.USER_INPUT_READY)
            self.logger.debug("Set processing user message - USER_INPUT_READY cleared")
        else:
            self.ui_state.set(UIStateFlags.USER_INPUT_READY)
            self.logger.debug("Finished processing user message - USER_INPUT_READY set")
