"""Message history management module for chat interfaces.

Provides functionality for tracking, storing, and managing chat message history
including user messages, assistant responses, and tool interactions.
"""

from typing import List, Dict, Any, Optional
from hatchling.core.logging.logging_manager import logging_manager
from hatchling.core.llm.event_system import EventSubscriber, StreamEvent, StreamEventType
from hatchling.config.llm_settings import ELLMProvider

from hatchling.core.llm.data_structures import ToolCallParsedResult
from hatchling.mcp_utils.mcp_tool_execution import ToolCallExecutionResult

class MessageHistory(EventSubscriber):
    """Event-driven message history manager with canonical and provider-specific histories.
    
    Maintains a canonical (provider-agnostic) history and dynamically generates
    provider-specific histories based on the current LLM provider.
    """
    
    def __init__(self):
        """Initialize an empty message history with dual-history support."""
        # Canonical history storing all events in normalized format
        self.canonical_history: List[Dict[str, Any]] = []
        
        # Provider-specific history generated on demand
        self.provider_history: List[Dict[str, Any]] = []
        
        # Current provider tracking for regeneration
        self._current_provider: Optional[ELLMProvider] = None
        
        # Content buffer for assistant message assembly
        self._content_buffer: str = ""
        
        self.logger = logging_manager.get_session("MessageHistory")
    
    def get_subscribed_events(self) -> List[StreamEventType]:
        """Return list of event types this subscriber handles.
        
        Returns:
            List[StreamEventType]: Event types for message history management.
        """
        return [
            # LLM Response Events
            StreamEventType.CONTENT,
            StreamEventType.FINISH,
            # Tool Execution Events
            StreamEventType.MCP_TOOL_CALL_DISPATCHED,
            StreamEventType.MCP_TOOL_CALL_RESULT,
            StreamEventType.MCP_TOOL_CALL_ERROR,
        ]
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle stream events and update canonical history.
        
        Args:
            event (StreamEvent): The event to handle.
        """
        try:
            # Check for provider change and regenerate provider history if needed
            if event.provider != self._current_provider:
                self._current_provider = event.provider
                self._regenerate_provider_history()
                self.logger.debug(f"Provider changed to {event.provider}, regenerated provider history")
            
            if event.type == StreamEventType.CONTENT:
                self._handle_content_event(event)
            elif event.type == StreamEventType.FINISH:
                self._handle_finish_event(event)
            elif event.type == StreamEventType.MCP_TOOL_CALL_DISPATCHED:
                self._handle_tool_call_dispatched_event(event)
            elif event.type == StreamEventType.MCP_TOOL_CALL_RESULT:
                self._handle_tool_call_result_event(event)
            elif event.type == StreamEventType.MCP_TOOL_CALL_ERROR:
                self._handle_tool_call_error_event(event)
                
        except Exception as e:
            self.logger.error(f"Error handling event {event.type}: {e}")
    
    def _handle_content_event(self, event: StreamEvent) -> None:
        """Handle CONTENT events by buffering content for assistant message assembly.
        
        Args:
            event (StreamEvent): The CONTENT event.
        """
        content = event.data.get("content", "")
        self._content_buffer += content
        #self.logger.debug(f"Buffered content: {len(content)} chars (total buffer: {len(self._content_buffer)})")
    
    def _handle_finish_event(self, event: StreamEvent) -> None:
        """Handle FINISH events by finalizing assistant message from buffer.
        
        Args:
            event (StreamEvent): The FINISH event.
        """
        if self._content_buffer:
            # Add complete assistant message to canonical history
            canonical_entry = {
                "type": "assistant",
                "data": {
                    "role": "assistant",
                    "content": self._content_buffer
                }
            }
            self.canonical_history.append(canonical_entry)
            
            # Add to provider-specific history
            provider_entry = {"role": "assistant", "content": self._content_buffer}
            self.provider_history.append(provider_entry)
            
            self.logger.debug(f"Added assistant message: {len(self._content_buffer)} chars")
            self._content_buffer = ""  # Reset buffer

    def _handle_tool_call_dispatched_event(self, event: StreamEvent) -> None:
        """Handle MCP_TOOL_CALL_DISPATCHED events by adding tool calls to history.
        
        Args:
            event (StreamEvent): The MCP_TOOL_CALL_DISPATCHED event.
        """
        # Create ToolCallParsedResult from event data
        tool_call = ToolCallParsedResult(
            tool_call_id=event.data.get("tool_call_id", ""),
            function_name=event.data.get("function_name", ""),
            arguments=event.data.get("arguments", {})
        )
        
        # Add to canonical history
        canonical_entry = {
            "type": "tool_call",
            "data": tool_call
        }
        self.canonical_history.append(canonical_entry)
        
        # Add to provider-specific history based on current provider
        # TODO: We should handle this via strategies implemented similar to the tool call parsing strategies
        # For now, we will assume the last tool call and result are in the format expected
        if self._current_provider == ELLMProvider.OPENAI:
            provider_entry = {"role": "assistant", "tool_calls": [tool_call.to_openai_dict()]}
        elif self._current_provider == ELLMProvider.OLLAMA:
            provider_entry = {"role": "assistant", "tool_calls": [tool_call.to_ollama_dict()]}
        else:
            # Default format
            provider_entry = {"role": "assistant", "tool_calls": [tool_call.to_dict()]}
        
        self.provider_history.append(provider_entry)
        
        self.logger.debug(f"Added tool call: {tool_call.function_name}")
    
    def _handle_tool_call_result_event(self, event: StreamEvent) -> None:
        """Handle MCP_TOOL_CALL_RESULT events by adding tool results to history.
        
        Args:
            event (StreamEvent): The MCP_TOOL_CALL_RESULT event.
        """
        # Create ToolCallExecutionResult from event data  
        tool_result = ToolCallExecutionResult(**event.data)
        
        # Add to canonical history
        canonical_entry = {
            "type": "tool_result",
            "data": tool_result
        }
        self.canonical_history.append(canonical_entry)
        
        # Add to provider-specific history based on current provider
        if self._current_provider == ELLMProvider.OPENAI:
            provider_entry = {"role": "tool", **tool_result.to_openai_dict()}
        elif self._current_provider == ELLMProvider.OLLAMA:
            provider_entry = {"role": "tool", **tool_result.to_ollama_dict()}
        else:
            # Default format
            provider_entry = {"role": "tool", **tool_result.to_dict()}
        
        self.provider_history.append(provider_entry)
        
        self.logger.debug(f"Added tool result for: {tool_result.function_name}")
    
    def _handle_tool_call_error_event(self, event: StreamEvent) -> None:
        """Handle MCP_TOOL_CALL_ERROR events by adding error results to history.
        
        Args:
            event (StreamEvent): The MCP_TOOL_CALL_ERROR event.
        """
        # Create ToolCallExecutionResult with error from event data
        tool_result = ToolCallExecutionResult(**event.data)
        
        # Add to canonical history
        canonical_entry = {
            "type": "tool_result",
            "data": tool_result
        }
        self.canonical_history.append(canonical_entry)
        
        # Add to provider-specific history based on current provider
        if self._current_provider == ELLMProvider.OPENAI:
            provider_entry = {"role": "tool", **tool_result.to_openai_dict()}
        elif self._current_provider == ELLMProvider.OLLAMA:
            provider_entry = {"role": "tool", **tool_result.to_ollama_dict()}
        else:
            # Default format
            provider_entry = {"role": "tool", **tool_result.to_dict()}
        
        self.provider_history.append(provider_entry)
        
        self.logger.debug(f"Added tool error for: {tool_result.function_name}")
    
    def _regenerate_provider_history(self) -> None:
        """Regenerate provider-specific history from canonical history."""
        self.provider_history = []
        
        for entry in self.canonical_history:
            entry_type = entry["type"]
            
            if entry_type == "user":
                provider_entry = entry["data"]
            elif entry_type == "assistant":
                provider_entry = entry["data"]
            elif entry_type == "tool_call":
                tool_call = entry["data"]
                if self._current_provider == ELLMProvider.OPENAI:
                    provider_entry = {"role": "assistant", "tool_calls": [tool_call.to_openai_dict()]}
                elif self._current_provider == ELLMProvider.OLLAMA:
                    provider_entry = {"role": "assistant", "tool_calls": [tool_call.to_ollama_dict()]}
                else:
                    provider_entry = {"role": "assistant", "tool_calls": [tool_call.to_dict()]}
            elif entry_type == "tool_result":
                tool_result = entry["data"]
                if self._current_provider == ELLMProvider.OPENAI:
                    provider_entry = {"role": "tool", **tool_result.to_openai_dict()}
                elif self._current_provider == ELLMProvider.OLLAMA:
                    provider_entry = {"role": "tool", **tool_result.to_ollama_dict()}
                else:
                    provider_entry = {"role": "tool", **tool_result.to_dict()}
            else:
                continue  # Skip unknown entry types
            
            self.provider_history.append(provider_entry)
        
        self.logger.debug(f"Regenerated provider history: {len(self.provider_history)} entries")
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the history.
        
        Args:
            content (str): The message content.
        """
        # Add to canonical history
        canonical_entry = {
            "type": "user",
            "data": {
                "role": "user",
                "content": content
            }
        }
        self.canonical_history.append(canonical_entry)
        
        # Add to provider-specific history
        provider_entry = {"role": "user", "content": content}
        self.provider_history.append(provider_entry)
        
        self.logger.debug(f"MessageHistory - Added user message: {content}")

    def get_canonical_history(self) -> List[Dict[str, Any]]:
        """Get the canonical (provider-agnostic) history.
        
        Returns:
            List[Dict[str, Any]]: List of canonical history entries.
        """
        return self.canonical_history
    
    def get_provider_history(self, provider: Optional[ELLMProvider] = None) -> List[Dict[str, Any]]:
        """Get provider-specific history, optionally for a different provider.
        
        Args:
            provider (Optional[ELLMProvider]): Provider to format for. If None, uses current provider.
            
        Returns:
            List[Dict[str, Any]]: List of messages formatted for the specified provider.
        """
        if provider is None or provider == self._current_provider:
            self.logger.debug(f"Returning current provider ({self._current_provider.value}) history")
            return self.provider_history
        
        # Generate history for different provider without changing current state
        self.logger.debug(f"Generating history for provider: {provider.value}")
        temp_history = []
        
        for entry in self.canonical_history:
            entry_type = entry["type"]
            
            if entry_type == "user":
                temp_history.append(entry["data"])
            elif entry_type == "assistant":
                temp_history.append(entry["data"])
            elif entry_type == "tool_call":
                tool_call = entry["data"]
                if provider == ELLMProvider.OPENAI:
                    temp_history.append({"role": "assistant", "tool_calls": [tool_call.to_openai_dict()]})
                elif provider == ELLMProvider.OLLAMA:
                    temp_history.append({"role": "assistant", "tool_calls": [tool_call.to_ollama_dict()]})
                else:
                    temp_history.append({"role": "assistant", "tool_calls": [tool_call.to_dict()]})
            elif entry_type == "tool_result":
                tool_result = entry["data"]
                if provider == ELLMProvider.OPENAI:
                    temp_history.append({"role": "tool", **tool_result.to_openai_dict()})
                elif provider == ELLMProvider.OLLAMA:
                    temp_history.append({"role": "tool", **tool_result.to_ollama_dict()})
                else:
                    temp_history.append({"role": "tool", **tool_result.to_dict()})
        
        return temp_history
    
    def copy(self) -> 'MessageHistory':
        """Create a copy of this message history.
        
        Returns:
            MessageHistory: A new MessageHistory with the same canonical and provider histories.
        """
        new_history = MessageHistory()
        new_history.canonical_history = self.canonical_history.copy()
        new_history.provider_history = self.provider_history.copy()
        new_history._current_provider = self._current_provider
        new_history._content_buffer = self._content_buffer
        return new_history
    
    def clear(self) -> None:
        """Clear all histories."""
        self.canonical_history = []
        self.provider_history = []
        self._content_buffer = ""
        self._current_provider = None
        
        self.logger.info("MessageHistory - Cleared!")
    
    def __len__(self) -> int:
        """Get the number of entries in canonical history.
        
        Returns:
            int: The number of entries in the canonical history.
        """
        return len(self.canonical_history)