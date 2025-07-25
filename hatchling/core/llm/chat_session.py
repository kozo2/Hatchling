import logging
from typing import List, Dict, Any

from hatchling.core.logging.logging_manager import logging_manager
from hatchling.core.chat.message_history import MessageHistory
from hatchling.core.llm.streaming.tool_result_collector_subscriber import ToolResultCollectorSubscriber
from hatchling.core.llm.streaming.tool_chaining_subscriber import ToolChainingSubscriber
from hatchling.core.llm.providers import ProviderRegistry
from hatchling.core.llm.streaming_management import (
    ContentPrinterSubscriber, 
    UsageStatsSubscriber, 
    ErrorHandlerSubscriber,
    ContentAccumulatorSubscriber
)
from hatchling.config.settings import AppSettings
from hatchling.mcp_utils import mcp_manager
from hatchling.mcp_utils.mcp_tool_execution import MCPToolExecution
from hatchling.mcp_utils.mcp_tool_call_subscriber import MCPToolCallSubscriber

class ChatSession:
    def __init__(self, settings: AppSettings = None):
        """Initialize a chat session with the specified settings.
        
        Args:
            settings (AppSettings, optional): Configuration settings for the chat session. 
                                            If None, uses the singleton instance.
        """
        self.settings = settings or AppSettings.get_instance()
        # Unified logger naming: ChatSession-provider-model
        self.logger = logging_manager.get_session(
            f"ChatSession-{self.settings.llm.provider_name}-{self.settings.llm.model}",
            formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        # Initialize MCPToolExecution for execution of tool calls from LLM providers
        self.tool_execution = MCPToolExecution()
        # Initialize message components
        self.history = MessageHistory(self.logger)

        # Set up subscribers for the streaming response
        # ContentPrinterSubscriber prints the response streamed results to the console
        self.content_printer = ContentPrinterSubscriber(include_role=False)
        # ContentAccumulatorSubscriber collects the streamed response content
        self.content_collector = ContentAccumulatorSubscriber()
        # UsageStatsSubscriber collects usage statistics for the session
        self.usage_stats = UsageStatsSubscriber()
        # ErrorHandlerSubscriber handles any errors that occur during streaming
        # and logs them appropriately
        self.error_handler = ErrorHandlerSubscriber()

        # Create tool chaining subscriber for automatic tool calling chains
        self._tool_chaining_subscriber = ToolChainingSubscriber(
            self.settings, self.history, self.tool_execution
        )
        self.tool_execution.stream_publisher.subscribe(self._tool_chaining_subscriber)
        # Create and subscribe the MCP tool call subscriber for LLM tool calls
        self._tool_call_subscriber = MCPToolCallSubscriber(self.tool_execution)
        
        
        # Initializing all connections of subscribers to instances of LLM providers
        for _provider_enum in ProviderRegistry.list_providers():
            self.logger.debug(f"Initializing streaming subscriptions for : {_provider_enum.value}")
            _provider = ProviderRegistry.get_provider(_provider_enum, self.settings)

            # Subscribe to provider's publisher
            self.logger.debug("Subscribed to LLM provider's stream publisher (content, usage stats, error handling)")
            _provider.publisher.subscribe(self.content_printer)
            _provider.publisher.subscribe(self.content_collector)
            _provider.publisher.subscribe(self.usage_stats)
            _provider.publisher.subscribe(self.error_handler)
            self.logger.debug("Created MCPToolCallSubscriber for handling tool calls")
            _provider.publisher.subscribe(self._tool_call_subscriber)
    
    async def send_message(self, user_message: str) -> None:
        """Send the current message history to the LLM provider and stream the response.
        
        Args:
            user_message (str): The user's message to process.
        """
        # Add user message to history
        self.history.add_user_message(user_message)

        # Get current provider based on settings
        provider = ProviderRegistry.get_current_provider(self.settings)
        
        # Reset tool calling counters and collectors for a new user message
        self.tool_execution.reset_for_new_query(user_message)
        self._tool_chaining_subscriber.reset_for_new_query()

        # Prepare payload using provider abstraction
        payload = provider.prepare_chat_payload(
            self.history.get_messages(), 
            self.settings.llm.model
        )
        
        # Add tools to payload
        # TODO: Currently, we are adding everything to the payload as we are not specifying
        # tools in add_tools_to_payload.
        # In the future, we must allow users to specify tools directly in the query.
        payload = provider.add_tools_to_payload(payload)
        
        # Stream the response using provider abstraction
        await provider.stream_chat_response(payload)
        
        # Update message history with the response
        # Note: Tool calls are handled by MCPToolCallSubscriber through events
        self.history.add_assistant_message(self.content_collector.full_response)
        self.content_collector.reset()  # Reset collector for next message