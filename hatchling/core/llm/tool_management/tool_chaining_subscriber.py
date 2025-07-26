"""Tool chaining subscriber for managing automatic tool calling chains.

This subscriber implements the intelligent tool calling logic that automatically
feeds tool results back to the LLM and asks if it has enough information to
answer the original query, enabling multi-step tool usage workflows.
"""

import asyncio
import time
import uuid
from json import dumps as json_dumps
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from hatchling.config.settings import AppSettings
from hatchling.core.llm.providers import ProviderRegistry
from hatchling.core.llm.streaming_management.stream_subscriber import StreamSubscriber
from hatchling.core.llm.streaming_management.stream_data import StreamEventType, StreamEvent
from hatchling.core.llm.streaming_management.stream_publisher import StreamPublisher
from hatchling.core.llm.tool_management.tool_result_collector_subscriber import ToolResultCollectorSubscriber
from hatchling.core.llm.tool_management import ToolCallParsedResult
from hatchling.core.chat.message_history import MessageHistory
from hatchling.core.logging.logging_manager import logging_manager
from hatchling.mcp_utils.mcp_tool_execution import MCPToolExecution
from hatchling.config.llm_settings import ELLMProvider


@dataclass
class ChainStatus:
    """Status information for tool chaining."""
    tool_chain_id: str
    initial_query: str
    current_iteration: int = 0
    max_iterations: int = 0
    current_tool: Optional[ToolCallParsedResult] = None
    start_time: float = field(default_factory=time.time)
    is_active: bool = True

class ToolChainingSubscriber(StreamSubscriber):
    """Manages automatic tool calling chains with intelligent continuation logic.
    
    This subscriber listens for tool completion events and automatically
    initiates follow-up LLM requests when tools have been executed, asking
    the LLM if it has enough information or needs to use more tools.
    """

    def __init__(self, settings: AppSettings = None, tool_execution: MCPToolExecution = None):
        """Initialize the tool chaining subscriber.
        
        Args:
            provider: The LLM provider instance.
            settings (AppSettings, optional): Application settings for tool calling limits and model info.
                                            If None, uses the singleton instance.
            tool_execution: The MCPToolExecution instance.
        """
        self._chain_lock = asyncio.Lock()

        self.settings = settings or AppSettings.get_instance()
        self.history = MessageHistory()
        self.tool_execution = tool_execution
        self.logger = logging_manager.get_session("ToolChainingSubscriber")
        
        # Create publisher for tool chaining events
        self.publisher = StreamPublisher()  # Default provider for chaining events
        
        # Chain tracking for event publishing
        self.tool_result_collector = ToolResultCollectorSubscriber()
        self.started = False  # Flag to track if the subscriber has started
        self.current_tool_chain_iteration = 1 # Initialize the current tool iteration
    
    def on_event(self, event: StreamEvent) -> None:
        """Handle tool execution events to trigger chaining.
        
        Args:
            event (StreamEvent): The event received.
        """
        # Debug: Log all events received
        self.logger.debug(f"ToolChainingSubscriber received event: {event.type} with data: {event.data}")
        
        # First, accumulate tool results
        # This holds info about the pending tool calls (just dispatched) and the results
        self.tool_result_collector.on_event(event)

        if event.type == StreamEventType.MCP_TOOL_CALL_DISPATCHED and len(self.tool_result_collector.tool_call_queue) == 1:
            
            self.started = True  # Mark that we have started processing tool calls
            
            # If we have a single dispatch in the queue, it means we are in the first tool call
            # and we can publish the start of the tool chain
            current_tool = None
            if self.tool_result_collector.tool_call_queue:
                _, _, current_tool = self.tool_result_collector.tool_call_queue[0]
                
            self.publisher.publish(
                event_type=StreamEventType.TOOL_CHAIN_START,
                data={
                    "tool_chain_id":  str(uuid.uuid4()),  # Unique ID for the tool chain
                    "initial_query": self.tool_execution.root_tool_query,
                    "current_iteration": self.current_tool_chain_iteration,
                    "max_iterations": self.settings.tool_calling.max_iterations,
                    "current_tool": current_tool,
                    "start_time": time.time(),
                    "is_active": True
                }
            )

        # Handle TOOL_CALL_RESULT - tool completed
        if event.type == StreamEventType.MCP_TOOL_CALL_RESULT:
            # First, let the tool result collector process the event
            # This will buffer the result until its dispatch is at the head of the queue
            
            # Now check if we have a ready pair to process in FIFO order
            ready_pair = self.tool_result_collector.get_next_ready_pair()
            if ready_pair:
                tool_call, tool_result = ready_pair
                self.logger.debug(f"Processing ready pair for tool_call_id: {tool_call.tool_call_id}")
                
                # Process this pair - trigger the next tool chain continuation
                self.logger.debug(f"Tool result received for tool call: {tool_call.tool_call_id} " +
                                    f"with result: {tool_result.to_dict()}")
                #asyncio.create_task(self._evaluate_tool_chain_continuation_with_pair(tool_call, tool_result))
                asyncio.create_task(self._chain_continuation_with_lock(tool_call, tool_result))
            else:
                self.logger.debug("Tool result received but no ready pair available yet (FIFO ordering)")
            
        # Handle FINISH events
        if event.type == StreamEventType.FINISH:
            # We will receive FINISH events when the LLM has completed its response
            # It may be after an LLM_TOOL_CALL_REQUEST in the case of generating a response
            # that lead to MCP_TOOL_CALL_DISPATCHED events, or it may be the final response
            # In the first case, it is only the closure of tool request and we can check
            # that we indeed have a tool call parsed in the collector
            if self.tool_result_collector.request_ids and self.tool_result_collector.request_ids[-1] == event.request_id:
                self.logger.debug(f"FINISH event received for request ID: {event.request_id} " +
                                  "matching the last tool call request ID. Therefore this " +
                                  "is a closure of the tool call request and there is nothing to do.")
            else:
                self.logger.debug(f"FINISH event received for request ID: {event.request_id} " +
                                  f"but it does not match the last tool call request ID: {self.tool_result_collector.request_ids}. Checking whether "
                                  "a tool result is expected...")
                # Check if there are unprocessed tool calls in the FIFO queue
                # If the queue has items but the buffer doesn't have matching results, we're waiting
                unprocessed_calls = any(tool_call_id not in self.tool_result_collector.tool_result_buffer 
                                      for tool_call_id, _, _ in self.tool_result_collector.tool_call_queue)
                
                if unprocessed_calls:
                    self.logger.debug("FINISH event received but tool results are still pending in FIFO queue. " +
                                      "Waiting for tool results to continue the chain.")
                else:
                    # No unprocessed tool calls, reset chaining state
                    self.logger.debug("FINISH event received and no tool results are pending. " +
                                        "Resetting chaining state and ready for new query.")
                    self.reset_for_new_query()
                return

    def get_subscribed_events(self) -> List[StreamEventType]:
        """Get the list of events this subscriber is interested in.
        
        Returns:
            List[StreamEventType]: List of event types to subscribe to.
        """
        return [
            StreamEventType.MCP_TOOL_CALL_DISPATCHED, # For the tool result collector
            StreamEventType.MCP_TOOL_CALL_ERROR,  # For tool result collection
            StreamEventType.MCP_TOOL_CALL_RESULT, # For both tool result collection and chaining
            StreamEventType.FINISH # To reset chaining state when final response is received
        ]

    async def _chain_continuation_with_lock(self, tool_call: ToolCallParsedResult, tool_result) -> None:
        """Evaluate whether to continue the tool calling chain with a specific call/result pair.
        
        This method implements the intelligent chaining logic using the provided FIFO pair,
        ensuring only one tool chain continuation happens at a time.
        
        Args:
            tool_call (ToolCallParsedResult): The tool call that was executed
            tool_result: The result of the tool call execution (or error)
        """
        # Use the lock to ensure only one continuation happens at a time
        async with self._chain_lock:
            self.logger.debug(f"Acquired chain lock for tool call: {tool_call.tool_call_id}")
            await self._evaluate_tool_chain_continuation_with_pair(tool_call, tool_result)
            self.logger.debug(f"Released chain lock for tool call: {tool_call.tool_call_id}")

    async def _evaluate_tool_chain_continuation_with_pair(self, tool_call: ToolCallParsedResult, tool_result) -> None:
        """Evaluate whether to continue the tool calling chain with a specific call/result pair.
        
        This method implements the intelligent chaining logic using the provided FIFO pair,
        ensuring only one tool chain continuation happens at a time.
        
        Args:
            tool_call (ToolCallParsedResult): The tool call that was executed
            tool_result: The result of the tool call execution (or error)
        """
        try:            
            # Publish TOOL_CHAIN_ITERATION event
            self.publisher.publish(
                event_type=StreamEventType.TOOL_CHAIN_ITERATION,
                data={
                    "iteration": self.current_tool_chain_iteration
                }
            )
            
            elapsed_time = time.time() - self.tool_execution.tool_call_start_time
            
            # Check if we've hit limits
            reached_max_iterations = (self.tool_execution.current_tool_call_iteration >= 
                                    self.settings.tool_calling.max_iterations)
            reached_time_limit = elapsed_time >= self.settings.tool_calling.max_working_time

            continuation_message = ""
                
            # Continue with sequential tool calling
            self.logger.debug(f"Evaluating tool chain continuation - iteration {self.current_tool_chain_iteration}")            

            # Hit limits, generate partial response
            if reached_max_iterations or reached_time_limit:
                limit_reason = ("max iterations" if reached_max_iterations else "time limit")
                self.logger.info(f"Tool calling chain stopped: reached {limit_reason}")

                # Message to notify the LLM about the limits, and to provide partial results
                continuation_message = (
                    f"We have reached the limit of {limit_reason} and cannot continue with more tool calls.\n"
                    "However, we have collected the tool results and should be able to provide a partial response.\n"
                    "Write a response based on the collected tool results.\n\n"
                    "Adapt the level of detail in your response based on the complexity of the tool calling chain.\n"
                    "Prefer conciseness, clarity, and accuracy of the response.\n"
                )
                
            else: # Chaining can continue, ask LLM if it needs more tools
                continuation_message = (
                    "Given the tool results, do you have enough information "
                    "to answer the original query of the user?\n"
                    "- If yes, write a response based on the collected tool results. "
                    "Adapt the level of detail in your response based on the complexity of the tool calling chain."
                    "Prefer conciseness, clarity, and accuracy of the response.\n"
                    "- If not, continue using tools or, if no tools meet your needs, you can write a response."
                )

            self.logger.debug(f"Tool chain continuation message: {continuation_message}")

            # TODO: We should handle this via strategies implemented similar to the tool call parsing strategies
            # For now, we will assume the last tool call and result are in the format expected
            if ProviderRegistry.get_current_provider(self.settings).provider_enum == ELLMProvider.OLLAMA:
                # It seems Ollama only recognizes a dictionary with "role", "content", and "tool_name"
                # as a tool result, so we need to convert the tool result to that format
                last_tool_call = self.tool_result_collector.last_tool_call.to_ollama_dict()
                last_tool_result = self.tool_result_collector.last_tool_result.to_ollama_dict()

            elif ProviderRegistry.get_current_provider(self.settings).provider_enum == ELLMProvider.OPENAI:
                # Now for OpenAI, we need to convert the tool result to OpenAI format
                # Open AI requires the last tool call
                last_tool_call = self.tool_result_collector.last_tool_call.to_openai_dict()
                last_tool_result = self.tool_result_collector.last_tool_result.to_openai_dict()

            self.logger.info(f"Tool result: {json_dumps(last_tool_result, indent=2)}")

            self.history.add_tool_call(last_tool_call)
            self.history.add_tool_result(last_tool_result)

            provider = ProviderRegistry.get_current_provider(self.settings)

            # Prepare payload for next iteration
            payload = provider.prepare_chat_payload(
                self.history.get_messages() + [{
                    "role": "user",
                    "content": continuation_message
                    }],
                self.settings.llm.model
            )
            
            # Add tools to payload
            if not (reached_max_iterations or reached_time_limit):
                payload = provider.add_tools_to_payload(payload)

            # Increment the tool call iteration
            self.tool_execution.current_tool_call_iteration += 1

            # Stream the continuation response
            await provider.stream_chat_response(payload)
                
        except Exception as e:
            self.logger.error(f"Error in tool chain continuation: {e}")
            self.publisher.publish(
                event_type=StreamEventType.TOOL_CHAIN_ERROR,
                data={
                    "error": str(e)
                },
            )        
    
    def reset_for_new_query(self) -> None:
        """Reset the chaining subscriber for a new query."""
        self.publisher.publish(
            event_type=StreamEventType.TOOL_CHAIN_END,
            data={"sussess": True, "total_iterations": self.tool_execution.current_tool_call_iteration}
        )
        # Reset the tool execution state
        self.current_tool_chain_iteration = 1
        self.tool_result_collector.reset()
        #self.history.clear()

