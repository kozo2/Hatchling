"""CLI Event Subscriber for managing UI state and display."""


import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import time
from enum import IntFlag, auto
class UIStateFlags(IntFlag):
    NONE = 0
    TOOL_CHAIN_ACTIVE = auto()
    TOOL_RUNNING = auto()
    CONTENT_STREAMING = auto()
    ERROR_DISPLAYED = auto()
    INFO_DISPLAYED = auto()
    USER_INPUT_READY = auto()

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

from hatchling.core.llm.tool_management.tool_chaining_subscriber import ChainStatus
from hatchling.core.llm.streaming_management.stream_subscriber import StreamSubscriber
from hatchling.core.llm.streaming_management.stream_data import StreamEvent, StreamEventType
from hatchling.core.logging.logging_manager import logging_manager
from prompt_toolkit import print_formatted_text as print_pt
from prompt_toolkit.patch_stdout import patch_stdout


@dataclass
class ToolStatus:
    """Status information for currently executing tools."""
    
    name: str
    parameters: Dict[str, Any]
    call_id: str
    server_name: Optional[str] = None
    progress: float = 0.0
    start_time: float = field(default_factory=time.time)

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


@dataclass
class LLMStatus:
    """LLM provider and model information."""
    
    provider_name: str = "Unknown"
    model_name: str = "Unknown"
    api_base: str = "Unknown"

class CLIEventSubscriber(StreamSubscriber):
    """CLI Event Subscriber for managing UI state based on stream events.
    
    This subscriber maintains state for all UI elements:
    - Bottom toolbar: tool execution status and server/tool counts
    - Right prompt: LLM info and token statistics
    - Error/info overlays: transient messages
    
    Uses the Observer pattern to react to events and update UI state.
    """

    def __init__(self):
        """Initialize the CLI event subscriber with default state."""
        self.logger = logging_manager.get_session("CLIEventSubscriber")
        
        # UI State
        self.current_chain: Optional[ChainStatus] = None
        self.current_tool: Optional[ToolStatus] = None
        self.server_status = ServerStatus()
        self.token_stats = TokenStats()
        self.llm_status = LLMStatus()
        
        # UI Control State
        self.toolbar_view_mode = "default"  # default, tools, servers
        self.right_prompt_view_mode = "default"  # default, tokens, model
        
        # Error/Info Display
        self.current_error: Optional[str] = None
        self.current_info: Optional[str] = None
        self.message_timeout: float = 5.0  # seconds
        self.last_message_time: float = 0.0
        
        # Content handling for output
        self.content_buffer: str = ""
        self.content_ready_for_display: bool = False
        # UI state flags manager
        self.ui_state = UIStateManager()

    def on_event(self, event: StreamEvent) -> None:
        """Handle stream events and update UI state.
        
        Args:
            event (StreamEvent): The event to handle.
        """

        try:
            # Tool Chaining Events
            if event.type == StreamEventType.TOOL_CHAIN_START:
                self.logger.debug(f"Handling TOOL_CHAIN_START event: {event.data}")
                self._handle_tool_chain_start(event)
            elif event.type == StreamEventType.TOOL_CHAIN_ITERATION:
                self.logger.debug(f"Handling TOOL_CHAIN_ITERATION event: {event.data}")
                self._handle_tool_chain_iteration(event)
            elif event.type == StreamEventType.TOOL_CHAIN_END:
                self.logger.debug(f"Handling TOOL_CHAIN_END event: {event.data}")
                self._handle_tool_chain_end(event)
            elif event.type == StreamEventType.TOOL_CHAIN_LIMIT_REACHED:
                self.logger.debug(f"Handling TOOL_CHAIN_LIMIT_REACHED event: {event.data}")
                self._handle_tool_chain_limit_reached(event)
            elif event.type == StreamEventType.TOOL_CHAIN_ERROR:
                self.logger.debug(f"Handling TOOL_CHAIN_ERROR event: {event.data}")
                self._handle_tool_chain_error(event)
            
            # Tool Execution Events
            elif event.type == StreamEventType.LLM_TOOL_CALL_REQUEST:
                self.logger.debug(f"Handling LLM_TOOL_CALL_REQUEST event: {event.data}")
                self._handle_llm_tool_call_request(event)
            elif event.type == StreamEventType.MCP_TOOL_CALL_DISPATCHED:
                self.logger.debug(f"Handling MCP_TOOL_CALL_DISPATCHED event: {event.data}")
                self._handle_mcp_tool_call_dispatched(event)
            elif event.type == StreamEventType.MCP_TOOL_CALL_RESULT:
                self.logger.debug(f"Handling MCP_TOOL_CALL_RESULT event: {event.data}")
                self._handle_mcp_tool_call_result(event)
            elif event.type == StreamEventType.MCP_TOOL_CALL_PROGRESS:
                self.logger.debug(f"Handling MCP_TOOL_CALL_PROGRESS event: {event.data}")
                self._handle_mcp_tool_call_progress(event)
            elif event.type == StreamEventType.MCP_TOOL_CALL_ERROR:
                self.logger.debug(f"Handling MCP_TOOL_CALL_ERROR event: {event.data}")
                self._handle_mcp_tool_call_error(event)
            
            # MCP Server Events
            elif event.type == StreamEventType.MCP_SERVER_UP:
                self.logger.debug(f"Handling MCP_SERVER_UP event: {event.data}")
                self._handle_mcp_server_up(event)
            elif event.type == StreamEventType.MCP_SERVER_DOWN:
                self.logger.debug(f"Handling MCP_SERVER_DOWN event: {event.data}")
                self._handle_mcp_server_down(event)
            elif event.type == StreamEventType.MCP_TOOL_ENABLED:
                self.logger.debug(f"Handling MCP_TOOL_ENABLED event: {event.data}")
                self._handle_mcp_tool_enabled(event)
            elif event.type == StreamEventType.MCP_TOOL_DISABLED:
                self.logger.debug(f"Handling MCP_TOOL_DISABLED event: {event.data}")
                self._handle_mcp_tool_disabled(event)
            
            # LLM Events
            elif event.type == StreamEventType.CONTENT:
                #self.logger.debug(f"Handling CONTENT event: {event.data}")
                self._handle_content(event)
            elif event.type == StreamEventType.USAGE:
                self.logger.debug(f"Handling USAGE event: {event.data}")
                self._handle_usage(event)
            elif event.type == StreamEventType.ERROR:
                self.logger.debug(f"Handling ERROR event: {event.data}")
                self._handle_error(event)
            elif event.type == StreamEventType.FINISH:
                self.logger.debug(f"Handling FINISH event: {event.data}")
                self._handle_finish(event)
            
        except Exception as e:
            self.logger.error(f"Error handling event {event.type.value}: {e}")

    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return list of event types this subscriber is interested in.
        
        Returns:
            List[StreamEventType]: Event types for UI updates.
        """
        return [
            # Tool Chaining Events
            StreamEventType.TOOL_CHAIN_START,
            StreamEventType.TOOL_CHAIN_ITERATION,
            StreamEventType.TOOL_CHAIN_END,
            StreamEventType.TOOL_CHAIN_LIMIT_REACHED,
            StreamEventType.TOOL_CHAIN_ERROR,
            
            # Tool Execution Events
            StreamEventType.LLM_TOOL_CALL_REQUEST,
            StreamEventType.MCP_TOOL_CALL_DISPATCHED,
            StreamEventType.MCP_TOOL_CALL_RESULT,
            StreamEventType.MCP_TOOL_CALL_PROGRESS,
            StreamEventType.MCP_TOOL_CALL_ERROR,
            
            # MCP Server Events
            StreamEventType.MCP_SERVER_UP,
            StreamEventType.MCP_SERVER_DOWN,
            StreamEventType.MCP_TOOL_ENABLED,
            StreamEventType.MCP_TOOL_DISABLED,
            
            # LLM Events
            StreamEventType.CONTENT,
            StreamEventType.USAGE,
            StreamEventType.ERROR,
            StreamEventType.FINISH,
        ]

    # Tool Chaining Event Handlers
    def _handle_tool_chain_start(self, event: StreamEvent) -> None:
        """Handle tool chain start event."""
        data = event.data
        self.current_chain = ChainStatus(**event.data)
        self.ui_state.set(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.ui_state.clear(UIStateFlags.USER_INPUT_READY)
        self.logger.debug(f"Tool chain started - TOOL_CHAIN_ACTIVE set, USER_INPUT_READY cleared")
        self._set_info(f"Tool chain started: {self.current_chain.initial_query[:50]}...")

    def _handle_tool_chain_iteration(self, event: StreamEvent) -> None:
        """Handle tool chain iteration event."""
        data = event.data
        if self.current_chain:
            self.current_chain.current_iteration = data.get("iteration", 0)
            tool_name = data.get("tool_name", "unknown")
            self._set_info(f"Tool chain step {self.current_chain.current_iteration}/{self.current_chain.max_iterations}: {tool_name}")
            self.ui_state.set(UIStateFlags.TOOL_CHAIN_ACTIVE)
            self.ui_state.clear(UIStateFlags.USER_INPUT_READY)

    def _handle_tool_chain_end(self, event: StreamEvent) -> None:
        """Handle tool chain end event."""
        data = event.data
        success = data.get("success", False)
        iterations = data.get("total_iterations", 0)
        if success:
            self._set_info(f"Tool chain completed successfully ({iterations} steps)")
        else:
            self._set_error(f"Tool chain failed after {iterations} steps")
        self.current_chain = None
        self.current_tool = None
        self.ui_state.clear(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.ui_state.set(UIStateFlags.USER_INPUT_READY)
        self.logger.debug(f"Tool chain ended - TOOL_CHAIN_ACTIVE cleared, USER_INPUT_READY set")

    def _handle_tool_chain_limit_reached(self, event: StreamEvent) -> None:
        """Handle tool chain limit reached event."""
        data = event.data
        limit_type = data.get("limit_type", "unknown")
        iterations = data.get("iterations", 0)
        self._set_error(f"Tool chain stopped: {limit_type} limit reached ({iterations} steps)")
        self.ui_state.clear(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.ui_state.set(UIStateFlags.USER_INPUT_READY)
        self.logger.debug(f"Tool chain limit reached - TOOL_CHAIN_ACTIVE cleared, USER_INPUT_READY set")

    def _handle_tool_chain_error(self, event: StreamEvent) -> None:
        """Handle tool chain error event."""
        data = event.data
        error = data.get("error", "Unknown error")
        iteration = data.get("iteration", 0)
        self._set_error(f"Tool chain error at step {iteration}: {error}")
        self.current_chain = None
        self.current_tool = None
        self.ui_state.clear(UIStateFlags.TOOL_CHAIN_ACTIVE)
        self.ui_state.set(UIStateFlags.USER_INPUT_READY)
        self.logger.debug(f"Tool chain error - TOOL_CHAIN_ACTIVE cleared, USER_INPUT_READY set")

    # Tool Execution Event Handlers
    def _handle_llm_tool_call_request(self, event: StreamEvent) -> None:
        """Handle LLM tool call request event."""
        data = event.data
        self.current_tool = ToolStatus(
            name=data.get("tool_name", "unknown"),
            parameters=data.get("parameters", {}),
            call_id=data.get("call_id", "unknown")
        )
        # Only set not ready for user input if we're not in a tool chain
        # (tool chains manage this state themselves)
        # if not self.current_chain:
        #     self.ready_for_user_input = False

    def _handle_mcp_tool_call_dispatched(self, event: StreamEvent) -> None:
        """Handle MCP tool call dispatched event."""
        data = event.data
        if self.current_tool and self.current_tool.call_id == data.get("call_id"):
            self.current_tool.server_name = data.get("server_name", "unknown")

    def _handle_mcp_tool_call_result(self, event: StreamEvent) -> None:
        """Handle MCP tool call result event."""
        data = event.data
        if self.current_tool and self.current_tool.call_id == data.get("call_id"):
            execution_time = data.get("execution_time", 0.0)
            self._set_info(f"Tool {self.current_tool.name} completed ({execution_time:.2f}s)")
            # if not self.current_chain:  # Only clear if not in a chain
            #     self.current_tool = None
            #     # Only set ready for user input if we're not in a tool chain
            #     self.ready_for_user_input = True

    def _handle_mcp_tool_call_progress(self, event: StreamEvent) -> None:
        """Handle MCP tool call progress event."""
        data = event.data
        if self.current_tool and self.current_tool.call_id == data.get("call_id"):
            self.current_tool.progress = data.get("progress", 0.0)

    def _handle_mcp_tool_call_error(self, event: StreamEvent) -> None:
        """Handle MCP tool call error event."""
        data = event.data
        tool_name = data.get("tool_name", "unknown")
        error = data.get("error", "Unknown error")
        self._set_error(f"Tool {tool_name} failed: {error}")
        self.current_tool = None
        # Only set ready for user input if we're not in a tool chain
        # if not self.current_chain:
        #     self.ready_for_user_input = True

    # MCP Server Event Handlers
    def _handle_mcp_server_up(self, event: StreamEvent) -> None:
        """Handle MCP server up event."""
        data = event.data
        self.server_status.servers_up = data.get("server_count", 0)
        self.server_status.tools_total = data.get("tool_count", 0)
        server_name = data.get("server_name", "unknown")
        self._set_info(f"MCP server connected: {server_name}")

    def _handle_mcp_server_down(self, event: StreamEvent) -> None:
        """Handle MCP server down event."""
        data = event.data
        self.server_status.servers_up = data.get("server_count", 0)
        self.server_status.tools_total = data.get("tool_count", 0)
        server_name = data.get("server_name", "unknown")
        self._set_error(f"MCP server disconnected: {server_name}")

    def _handle_mcp_tool_enabled(self, event: StreamEvent) -> None:
        """Handle MCP tool enabled event."""
        data = event.data
        self.server_status.tools_enabled = data.get("enabled_count", 0)
        self.server_status.tools_total = data.get("total_count", 0)

    def _handle_mcp_tool_disabled(self, event: StreamEvent) -> None:
        """Handle MCP tool disabled event."""
        data = event.data
        self.server_status.tools_enabled = data.get("enabled_count", 0)
        self.server_status.tools_total = data.get("total_count", 0)

    # LLM Event Handlers
    def _handle_usage(self, event: StreamEvent) -> None:
        """Handle usage statistics event.

        Args:
            event (StreamEvent): The event to handle.
        """
        usage_data = event.data.get("usage", {})
        self.token_stats.total_current = usage_data.get("total_tokens", 0)
        self.token_stats.total_tokens += self.token_stats.total_current
        self.token_stats.prompt_tokens = usage_data.get("prompt_tokens", 0)
        self.token_stats.completion_tokens = usage_data.get("completion_tokens", 0)
        # Optionally, print or log stats here if needed

    def _handle_content(self, event: StreamEvent) -> None:
        """Handle content event by accumulating content.

        Args:
            event (StreamEvent): The event to handle.
        """
        self.ui_state.clear(UIStateFlags.USER_INPUT_READY)
        if not self.ui_state.is_set(UIStateFlags.CONTENT_STREAMING):
            self.ui_state.set(UIStateFlags.CONTENT_STREAMING)
            self.content_buffer = ""
        with patch_stdout():
            content = event.data.get("content", "")
            print_pt(content, end="", flush=True)

    def _handle_finish(self, event: StreamEvent) -> None:
        """Handle finish event.

        Args:
            event (StreamEvent): The event to handle.
        """
        if self.token_stats.start_time and not self.token_stats.end_time:
            self.token_stats.end_time = event.timestamp
        # Only if all other activities but content streaming are done
        # means that this finish event is the end of a content stream
        if self.ui_state.is_set(UIStateFlags.CONTENT_STREAMING) and not \
              self.ui_state.is_set(UIStateFlags.TOOL_CHAIN_ACTIVE) and \
              not self.ui_state.is_set(UIStateFlags.TOOL_RUNNING):
                self.ui_state.clear(UIStateFlags.CONTENT_STREAMING)
                self.ui_state.set(UIStateFlags.USER_INPUT_READY)
                self.logger.debug("All content apparently finished, USER_INPUT_READY set")

    def _handle_error(self, event: StreamEvent) -> None:
        """Handle error event."""
        data = event.data
        error = data.get("error", "Unknown error")
        self._set_error(f"LLM Error: {error}")

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
        
        # Show tool execution status
        if self.current_tool:
            params_str = ", ".join([f"{k}='{v}'" for k, v in list(self.current_tool.parameters.items())[:2]])
            if len(self.current_tool.parameters) > 2:
                params_str += "..."
            
            if self.current_chain:
                return f"🔧 Running: {self.current_tool.name}({params_str}) [Step {self.current_chain.current_iteration}/{self.current_chain.max_iterations}]"
            else:
                progress = f" ({self.current_tool.progress:.0%})" if self.current_tool.progress > 0 else ""
                return f"🔧 Running: {self.current_tool.name}({params_str}){progress}"
        
        # Show server/tool status when idle
        return f"🌐 Servers: {self.server_status.servers_up} up | 🛠️ Tools: {self.server_status.tools_enabled} enabled / {self.server_status.tools_total} total"

    def get_right_prompt_text(self) -> str:
        """Get current right prompt text based on state and view mode."""
        duration = None
        tps = None
        if self.token_stats.start_time and self.token_stats.end_time and self.token_stats.completion_tokens > 0:
            duration = self.token_stats.end_time - self.token_stats.start_time
            tps = self.token_stats.completion_tokens / duration if duration > 0 else 0
        if self.right_prompt_view_mode == "tokens":
            stats = f"In: {self.token_stats.prompt_tokens} | Out: {self.token_stats.completion_tokens} | Total: {self.token_stats.total_current}"
            if tps is not None:
                stats += f" | Rate: {tps:.1f}/s"
            stats += f" | Session: {self.token_stats.total_tokens}"
            return stats
        elif self.right_prompt_view_mode == "model":
            return f"Provider: {self.llm_status.provider_name} | Model: {self.llm_status.model_name}"
        else:  # default
            stats = f"🤖 {self.llm_status.model_name} | 📊 In: {self.token_stats.prompt_tokens} | Out: {self.token_stats.completion_tokens}"
            if tps is not None:
                stats += f" | Rate: {tps:.1f}/s"
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

    def update_llm_status(self, provider_name: str, model_name: str, api_base: str = "Unknown") -> None:
        """Update LLM status information."""
        self.llm_status.provider_name = provider_name
        self.llm_status.model_name = model_name
        self.llm_status.api_base = api_base

    # Content Management Methods
    def get_accumulated_content(self) -> str:
        """Get the accumulated content for display.
        
        Returns:
            str: The accumulated content from streaming.
        """
        return self.content_buffer

    def clear_content_buffer(self) -> None:
        """Clear the content buffer after display."""
        self.content_buffer = ""
        self.content_ready_for_display = False

    def is_content_ready(self) -> bool:
        """Check if content is ready for display (streaming finished).
        
        Returns:
            bool: True if content is ready for display.
        """
        return self.content_ready_for_display

    def is_ready_for_user_input(self) -> bool:
        """Check if the system is ready for user input using state flags."""
        # Not ready if tool chain or tool running
        not_ready_mask = UIStateFlags.TOOL_CHAIN_ACTIVE | UIStateFlags.TOOL_RUNNING | UIStateFlags.CONTENT_STREAMING
        if self.ui_state.is_set(not_ready_mask):
            self.logger.debug(f"Not ready: {not_ready_mask} flag set")
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
