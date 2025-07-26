"""Message history management module for chat interfaces.

Provides functionality for tracking, storing, and managing chat message history
including user messages, assistant responses, and tool interactions.
"""

from typing import List, Dict, Any, Optional
from hatchling.core.logging.logging_manager import logging_manager

from hatchling.core.llm.tool_management.tool_result_collector_subscriber import ToolCallParsedResult, ToolCallExecutionResultLight

class MessageHistory:
    """Simple manager for chat message history without any complex optimizations."""
    
    def __init__(self):
        """Initialize an empty message history."""
        self.messages: List[Dict[str, Any]] = []
        self.logger = logging_manager.get_session("MessageHistory")
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the history.
        
        Args:
            content (str): The message content.
        """
        self.add_custom_content_message("user", content)
        self.logger.debug(f"MessageHistory - Added user message: {content}")
    
    def add_custom_content_message(self, role: str, content: str) -> None:
        """Add a custom message to the history.
        
        Args:
            role (str): The role of the message sender (e.g., "system", "user", "assistant").
            content (str): The message content.
        """
        self.messages.append({"role": role, "content": content})
        self.logger.debug(f"MessageHistory - Added custom message from {role}: {content}")
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the history.
        
        Args:
            content (str): The message content.
            tool_calls (List[Dict[str, Any]], optional): Optional list of tool calls.
        """
        self.add_custom_content_message("assistant", content)
        self.logger.debug(f"MessageHistory - Added assistant message: {content}")

    def add_tool_call(self, tool_call: Dict[str, str]) -> None:
        """Add a parsed tool call to the message history.

        Args:
            tool_call (Dict[str, str]): The parsed tool call to add as a dict in a format expected by the LLM provider.
        """

        self.messages.append({"role": "assistant", "tool_calls": [tool_call]})
        self.logger.debug(f"MessageHistory - Added tool call: {tool_call}")

    def add_tool_result(self, tool_result: Dict[str, str]) -> None:
        """Add a tool execution result to the message history.

        Args:
            tool_result (Dict[str, str]): The tool execution result to add as a dict in a format expected by the LLM provider.
        """
        
        self.messages.append({"role": "tool", **tool_result})
        self.logger.debug(f"MessageHistory - Added tool call result: {tool_result}")

    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages.
        
        Returns:
            List[Dict[str, Any]]: List of message dictionaries.
        """
        return self.messages
    
    def copy(self) -> 'MessageHistory':
        """Create a copy of this message history.
        
        Returns:
            MessageHistory: A new MessageHistory with the same messages.
        """
        new_history = MessageHistory(self.logger)
        new_history.messages = self.messages.copy()
        return new_history
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []
        
        self.logger.info("MessageHistory - Cleared!")
    
    def __len__(self) -> int:
        """Get the number of messages.
        
        Returns:
            int: The number of messages in the history.
        """
        return len(self.messages)