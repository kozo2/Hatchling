"""
Data structures and types for informing and processing streams of events
from LLM providers.
"""


from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from hatchling.config.llm_settings import ELLMProvider

class StreamEventType(Enum):
    """Types of events that can be published during streaming.
    
    This enum defines all possible event types in the streaming system,
    organized by category for clarity and extensibility.
    
    Event Flow for Tool Chaining:
    
    Application Start (not an event)

      - If user uses commands to manage MCP servers or tools, events are published:
        - MCP_SERVER_UP | MCP_SERVER_DOWN : MCP server connection established / closed
        - MCP_TOOL_ENABLED | MCP_TOOL_DISABLED : Tool enabled / disabled on MCP server

      - While the application is running, the connection to the MCP servers is checked periodically.
      This might lead to the following events:
        - MCP_SERVER_UNREACHABLE: MCP server cannot be reached

      - Once the user writes a prompt and sends it to the LLM, the
      following events might be published in response to the parsing of the LLM's response:

        [CONTENT | ROLE | FINISH | USAGE | ERROR | LLM_TOOL_CALL_REQUEST]

      - In response to the LLM_TOOL_CALL_REQUEST event, the following are published:

        MCP_TOOL_CALL_DISPATCHED

        [MCP_TOOL_CALL_ERROR]

        MCP_TOOL_CALL_RESULT

        TOOL_CHAIN_START (if tool chaining is initiated)

        TOOL_CHAIN_ITERATION_START (for each pair of tool calls/tool results)

        [TOOL_CHAIN_LIMIT_REACHED]

        --> LLM is queried again to react to the pair of tool call / tool result
            This might lead to the same events as above.
            The LLM is queried with different messages whether the limit was reached or not.
            Moreover, no tools are provided to the LLM if the limit was reached,
            in which case no more LLM_TOOL_CALL_REQUEST events are expected (hence terminating
            the tool chaining sequence).

        TOOL_CHAIN_ITERATION_END (after LLM has finished streaming its response in reaction to)

        [TOOL_CHAIN_ERROR]

        TOOL_CHAIN_END (if no more tool calls are requested by the LLM or iteration limit is reached)

    Application Ends (not an event)
        
    Event Payload Standards:
    
    LLM Response Events:
    - CONTENT: {"content": OBJ} # The OBJ varies by LLM provider
    - ROLE: {"role": str}
    - FINISH: {"finish_reason": str}
    - USAGE: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    - ERROR: {
            "error": {
                "message": str,
                "type": str
            }
    - LLM_TOOL_CALL_REQUEST: {
            "id": str,
            "function": {
                "name": str,
                "arguments": dict
                }
            }
    
    MCP Lifecycle Events:
    - MCP_SERVER_UP: {"server_path": str, "tool_count": int}
    - MCP_SERVER_DOWN: {"server_path": str}
    - MCP_SERVER_UNREACHABLE: {"server_path": str, "error": str}
    - MCP_TOOL_ENABLED: {"tool_name": str, "tool_info": MCPToolInfo}
    - MCP_TOOL_DISABLED: {"tool_name": str, "tool_info": MCPToolInfo}
    
    Tool Execution Events:
    - MCP_TOOL_CALL_DISPATCHED: {"tool_call_id": str, "function_name": str, "arguments": dict}
    - MCP_TOOL_CALL_RESULT: {"tool_call_id": str, "function_name": str, "arguments": dict, "result": any, "error": None}
    - MCP_TOOL_CALL_ERROR: {"tool_call_id": str, "function_name": str, "arguments": dict, "result": any, "error": str}
    
    Tool Chaining Events:
    - TOOL_CHAIN_START: {
                    "tool_chain_id": str uuid,
                    "initial_query": str,
                    "current_iteration": int,
                    "max_iterations": int,
                    "current_tool": str,
                    "start_time": int
                }
    - TOOL_CHAIN_ITERATION_START: {"tool_chain_id": str, "iteration": int, "max_iterations": int, "tool_name": str}
    - TOOL_CHAIN_ITERATION_END: {
                    "tool_chain_id": str,
                    "initial_query": str,
                    "success": bool,
                    "iteration": int,
                    "max_iterations": int,
                    "elapsed_time": float,
                    }
    - TOOL_CHAIN_END: {"success": bool, "total_iterations": int}
    - TOOL_CHAIN_LIMIT_REACHED: {"tool_chain_id": str, "limit_type": str, "iterations": int, "elapsed_time": float}
    - TOOL_CHAIN_ERROR: {"tool_chain_id": str, "error": str, "iteration": int}
    
    """
    
    # LLM Response Events
    CONTENT = "content"              # Text content from the model
    ROLE = "role"                   # Role assignment (assistant, user, etc.)
    FINISH = "finish"               # Stream completion with reason
    USAGE = "usage"                 # Token usage statistics
    ERROR = "error"                 # Error occurred during streaming
    # REFUSAL = "refusal"            # Model refused to answer
    # THINKING = "thinking"          # Model thinking process (for reasoning models)
    METADATA = "metadata"          # Additional metadata (fingerprint, etc.)
    
    # MCP Lifecycle Events
    MCP_SERVER_UP = "mcp_server_up"                    # MCP server connection established
    MCP_SERVER_DOWN = "mcp_server_down"                # MCP server connection lost
    MCP_SERVER_UNREACHABLE = "mcp_server_unreachable"  # MCP server cannot be reached
    MCP_SERVER_REACHABLE = "mcp_server_reachable"      # MCP server became reachable again
    MCP_TOOL_ENABLED = "mcp_tool_enabled"              # MCP tool was enabled
    MCP_TOOL_DISABLED = "mcp_tool_disabled"            # MCP tool was disabled
    
    # Tool Execution Events (LLM-side)
    LLM_TOOL_CALL_REQUEST = "llm_tool_call_request"    # LLM requests a tool/function call

    # Tool Execution Events (MCP-side)
    MCP_TOOL_CALL_DISPATCHED = "mcp_tool_call_dispatched"  # Tool call was dispatched to MCP for execution
    MCP_TOOL_CALL_RESULT = "mcp_tool_call_result"          # MCP tool call completed with result
    # MCP_TOOL_CALL_PROGRESS = "mcp_tool_call_progress"      # MCP tool call progress update
    MCP_TOOL_CALL_ERROR = "mcp_tool_call_error"            # MCP tool call failed with error
    
    # Tool Chaining Lifecycle Events
    TOOL_CHAIN_START = "tool_chain_start"              # Tool chaining sequence begins
    TOOL_CHAIN_ITERATION_START = "tool_chain_iteration_start"      # Start of a new tool chain iteration
    TOOL_CHAIN_ITERATION_END = "tool_chain_iteration_end"          # End of a tool chain iteration
    TOOL_CHAIN_END = "tool_chain_end"                  # Tool chaining sequence ends
    TOOL_CHAIN_LIMIT_REACHED = "tool_chain_limit_reached"  # Chaining stopped due to limits
    TOOL_CHAIN_ERROR = "tool_chain_error"              # Error during chaining



@dataclass
class StreamEvent:
    """Represents an event in the streaming response.
    
    This standardized event format allows different LLM providers to publish
    events in a consistent way, regardless of their native response format.

    """
    
    type: StreamEventType
    data: Dict[str, Any]
    provider: ELLMProvider
    request_id: Optional[str] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            import time
            self.timestamp = time.time()
