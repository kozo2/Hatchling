"""Tool chaining subscriber for managing automatic tool calling chains.

This subscriber implements the intelligent tool calling logic that automatically
feeds tool results back to the LLM and asks if it has enough information to
answer the original query, enabling multi-step tool usage workflows.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from hatchling.config.settings import AppSettings
from hatchling.core.llm.providers import ProviderRegistry
from hatchling.core.llm.streaming_management.stream_subscriber import StreamSubscriber
from hatchling.core.llm.streaming_management.stream_data import StreamEventType, StreamEvent
from hatchling.core.llm.streaming_management.stream_publisher import StreamPublisher
from hatchling.core.llm.tool_management.tool_result_collector_subscriber import ToolResultCollectorSubscriber
from hatchling.core.llm.tool_management import ToolCallParsedResult
from hatchling.mcp_utils.mcp_tool_execution import ToolCallExecutionResult
from hatchling.core.chat.message_history_registry import MessageHistoryRegistry
from hatchling.core.logging.logging_manager import logging_manager
from hatchling.mcp_utils.mcp_tool_execution import MCPToolExecution

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

    def __init__(self, settings: AppSettings = None, tool_execution: MCPToolExecution = None, history_id: str = None):
        """Initialize the tool chaining subscriber.
        
        Args:
            provider: The LLM provider instance.
            settings (AppSettings, optional): Application settings for tool calling limits and model info.
                                            If None, uses the singleton instance.
            tool_execution: The MCPToolExecution instance.
        """
        self._chain_lock = asyncio.Lock()

        self.settings = settings or AppSettings.get_instance()
        self.history_id = history_id or str(uuid.uuid4())
        self.tool_execution = tool_execution
        self.logger = logging_manager.get_session("ToolChainingSubscriber")
        
        # Create publisher for tool chaining events
        self.publisher = StreamPublisher()  # Default provider for chaining events
        
        # Chain tracking for event publishing
        self.tool_result_collector = ToolResultCollectorSubscriber()

        self.tool_chain_id: str = None  # Unique ID for the tool chain
        self.start_time: float = 0.0  # Start time of the tool chain
        self.started = False  # Flag to track if the subscriber has started
        self.current_tool_chain_iteration = 0 
        self.chain_link_count = 0

    def on_event(self, event: StreamEvent) -> None:
        """Handle tool execution events to trigger chaining.
        
        Args:
            event (StreamEvent): The event received.
        """
        # Debug: Log all events received
        self.logger.debug(f"ToolChainingSubscriber received event: {event.type} with data: {event.data}")
        
        # First, accumulate tool results
        # This holds info about the pending tool calls (dispatched) and the results
        self.tool_result_collector.on_event(event)

        if event.type == StreamEventType.MCP_TOOL_CALL_DISPATCHED:

            if not self.started:
                self.logger.debug("Received MCP_TOOL_CALL_DISPATCHED event for the first time, starting tool chaining.")

                self.started = True  # Mark that we have started processing tool calls

                self.start_time = time.time()  # Record the start time of the tool chain
                self.tool_chain_id = str(uuid.uuid4())  # Generate a unique ID for the
                
                _, _, current_tool = self.tool_result_collector.tool_call_queue[0]
                    
                self.publisher.publish(
                    event_type=StreamEventType.TOOL_CHAIN_START,
                    data={
                        "tool_chain_id":  self.tool_chain_id,  # Unique ID for the tool chain
                        "initial_query": self.tool_execution.root_tool_query,
                        "current_iteration": self.current_tool_chain_iteration,
                        "max_iterations": self.settings.tool_calling.max_iterations,
                        "current_tool": current_tool,
                        "start_time": self.start_time
                    }
                )

        if event.type == StreamEventType.MCP_TOOL_CALL_RESULT or event.type == StreamEventType.MCP_TOOL_CALL_ERROR:
            # We have received a tool result or an error from the MCPToolExecution
            # We are also processing the errors in the tool chaining to let the
            # LLMs know that the tool call failed, and probably retry, or at least 
            # react to the error.

            # Acknowledge one round of tool chaining is about to start.
            # This is essential to detect when the tool chain really ends.
            self.chain_link_count += 1

            # Now check if we have a ready pair to process in FIFO order
            ready_pair = self.tool_result_collector.get_next_ready_pair()
            self.logger.debug(
                f"Next pair in FIFO order: {ready_pair} " +
                f"Tool result collector has {len(self.tool_result_collector.tool_call_queue)} tool calls in queue, " +
                f"and {len(self.tool_result_collector.tool_result_buffer)} results in buffer.")
            if ready_pair:
                tool_call, tool_result = ready_pair

                # Process this pair - trigger the next tool chain continuation
                self.logger.info(f"Tool result ({tool_call.tool_call_id}):\n" +
                                    f"{tool_result.to_dict()}")
                asyncio.create_task(self._chain_continuation_with_lock(tool_call, tool_result))
            else:
                self.logger.warning("Tool result received but no ready pair available yet (FIFO ordering)")
                self.chain_link_count -= 1

    def check_iteration_end(self):
        """
        Performs necessary checks and closure computation in case the tool chaining should be
        considered finished
        """

        # If the tool chain is active (i.e. started), and no more tool chaining is ongoing (chain_link_count is 0)
        # it means we can issue the TOOL_CHAIN_END event.
        if self.started:
            # Is this the FINISH event while chaining (i.e., the queue is not empty)?
            self.logger.debug("Received FINISH event checking tool call queue: " +
                              f"process count = {self.chain_link_count }, " +
                              f"has pending tool calls: {self.tool_result_collector.has_pending_tool_calls}"#, " +
                              )
            if self.chain_link_count == 0:
                self.logger.debug("Received FINISH event, proceeding with the end of the tool chain.")
                self.publisher.publish(
                    event_type=StreamEventType.TOOL_CHAIN_END,
                    data={
                        "tool_chain_id": self.tool_chain_id,
                        "initial_query": self.tool_execution.root_tool_query,
                        "success": True,
                        "iteration": self.current_tool_chain_iteration,
                        "max_iterations": self.settings.tool_calling.max_iterations,
                        "elapsed_time": time.time() - self.start_time,
                    }
                )
                self.reset()

    def get_subscribed_events(self) -> List[StreamEventType]:
        """Get the list of events this subscriber is interested in.
        
        Returns:
            List[StreamEventType]: List of event types to subscribe to.
        """
        return [
            StreamEventType.MCP_TOOL_CALL_DISPATCHED, # For the tool result collector
            StreamEventType.MCP_TOOL_CALL_ERROR,  # For tool result collection
            StreamEventType.MCP_TOOL_CALL_RESULT, # For both tool result collection and chaining
        ]

    async def _chain_continuation_with_lock(self, tool_call: ToolCallParsedResult, tool_result: ToolCallParsedResult ) -> None:
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

    async def _evaluate_tool_chain_continuation_with_pair(self, tool_call: ToolCallParsedResult, tool_result: ToolCallExecutionResult) -> None:
        """Evaluate whether to continue the tool calling chain with a specific call/result pair.
        
        This method implements the intelligent chaining logic using the provided FIFO pair,
        ensuring only one tool chain continuation happens at a time.

        Args:
            tool_call (ToolCallParsedResult): The tool call that was executed
            tool_result (ToolCallExecutionResult): The result of the tool call execution (or error)
        """
        try:
            # Publish TOOL_CHAIN_ITERATION_START event
            self.current_tool_chain_iteration += 1
            self.publisher.publish(
                event_type=StreamEventType.TOOL_CHAIN_ITERATION_START,
                data={
                    "tool_chain_id": self.tool_chain_id,
                    "iteration": self.current_tool_chain_iteration,
                    "max_iterations": self.settings.tool_calling.max_iterations,
                    "tool_name": tool_call.function_name
                }
            )

            # Check if we've hit limits
            reached_max_iterations = self.current_tool_chain_iteration > self.settings.tool_calling.max_iterations
            elapsed_time = time.time() - self.start_time
            reached_time_limit = elapsed_time >= self.settings.tool_calling.max_working_time

            provider = ProviderRegistry.get_current_provider(self.settings)
            payload = {}

            # Check if we can proceed with regard to the chaining limits
            if reached_max_iterations or reached_time_limit:
                limit_reason = ("max iterations" if reached_max_iterations else "time limit")
                self.logger.warning(f"Stopping tool call chain: reached {limit_reason}")

                # Message to notify the LLM about the limits, and to provide partial results
                # TODO: This should be configurable, e.g., via a setting or a prompt file.
                continuation_message = \
                    f"We have reached the limit of \"{limit_reason}\" and cannot continue with more tool calls.\n" + \
                    "However, tools have been called as part of the tool chaining pipeline.\n" + \
                    "Write a partial response adapted to the complexity of the partial tool chain.\n" + \
                    "Tell the user which tools you would have called next, if any.\n" + \
                    "Prefer conciseness, clarity, and accuracy of the response."

                self.publisher.publish(
                    event_type=StreamEventType.TOOL_CHAIN_LIMIT_REACHED,
                    data={
                        "tool_chain_id": self.tool_chain_id,
                        "limit_type": "max_iterations" if reached_max_iterations else "time_limit",
                        "iteration": self.current_tool_chain_iteration,
                        "elapsed_time": elapsed_time
                    }
                )

                payload = provider.prepare_chat_payload([{
                        "role": "system",
                        "content": continuation_message
                    }] +
                    MessageHistoryRegistry.get_or_create_history(self.history_id).get_provider_history(),
                    self.settings.llm.model
                )

                # We force the chain link count to 1 so that it will be 0 when decremented 
                # after the LLM has finished answering without tool calls. (See below after 
                # the `else`` statement)
                self.chain_link_count = 1

            else:
                # Continue with sequential tool calling
                self.logger.debug(f"Evaluating tool chain continuation - iteration {self.current_tool_chain_iteration}")            
            
                # TODO: This should be configurable, e.g., via a setting or a prompt file.
                continuation_message = \
                    "Focus on tool calling to create tool calling chains that enables you to answer the user's prompt effectively.\n" + \
                    "Maximize use of relevant tools to continue the chain.\n" + \
                    "Learn from the tool results, in particular errors, and adapt your tool calling strategy."

                # Prepare payload for next iteration
                payload = provider.prepare_chat_payload([{
                        "role": "system",
                        "content": continuation_message
                    }] +
                    MessageHistoryRegistry.get_or_create_history(self.history_id).get_provider_history(),
                    self.settings.llm.model
                )
                
                # Add tools to payload
                payload = provider.add_tools_to_payload(payload)

                # Increment the tool call iteration
                self.tool_execution.current_tool_call_iteration += 1

            self.logger.debug(f"Tool chain continuation with payload: {payload}")
            await provider.stream_chat_response(payload)

            # Processing of this iteration is done, send the info that the LLM has finished
            self.publisher.publish(
                event_type=StreamEventType.TOOL_CHAIN_ITERATION_END,
                data={
                    "tool_chain_id": self.tool_chain_id,
                    "iteration": self.current_tool_chain_iteration,
                    "max_iterations": self.settings.tool_calling.max_iterations,
                    "tool_name": tool_call.function_name,
                    "elapsed_time": elapsed_time
                }
            )

            # The event published above is a notification to external entities listening
            # to the tool chain that an iteration has finished.
            # For internal state management of the tool chain, however, we close track it
            # by decrementing the chain link count.
            self.chain_link_count -= 1

            # Finally, we perform the checks to see if everything has finished.
            self.check_iteration_end()
        
        except Exception as e:
            self.logger.error(f"Error in tool chain continuation: {e}")


            self.publisher.publish(
                event_type=StreamEventType.TOOL_CHAIN_ERROR,
                data={
                    "tool_chain_id": self.tool_chain_id,
                    "error": str(e),
                    "iteration": self.current_tool_chain_iteration,
                },
            )

            self.publisher.publish(
                event_type=StreamEventType.TOOL_CHAIN_END,
                data={
                    "tool_chain_id": self.tool_chain_id,
                    "initial_query": self.tool_execution.root_tool_query,
                    "success": False,
                    "iteration": self.current_tool_chain_iteration,
                    "max_iterations": self.settings.tool_calling.max_iterations,
                    "total_name": tool_call.function_name,
                    "elapsed_time": time.time() - self.start_time,
                }
            )

            # Reset the chaining subscriber for a new query
            self.reset() 
    
    def reset(self) -> None:
        """Reset the chaining subscriber for a new query."""
        # Reset the tool execution state
        self.started = False
        self.start_time = 0.0
        self.chain_link_count = 0
        self.current_tool_chain_iteration = 0
        self.tool_result_collector.reset()
