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
    1. LLM_TOOL_CALL_REQUEST: LLM requests a tool execution
    2. MCP_MCP_TOOL_CALL_DISPATCHED: Backend dispatches the call to MCP server
    3. MCP_MCP_TOOL_CALL_PROGRESS: (Optional) Progress updates during execution
    4. MCP_MCP_TOOL_CALL_RESULT/ERROR: Tool execution completes
    5. TOOL_CHAIN_ITERATION: If chaining continues, iteration event is fired
    6. TOOL_CHAIN_END: When the chain completes or reaches limits
    
    Legacy events (TOOL_CALL_*) are maintained for backward compatibility.
    """
    
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
    
    # Tool Execution Events (LLM-side)
    LLM_TOOL_CALL_REQUEST = "llm_tool_call_request"    # LLM requests a tool/function call
    
    # Tool Execution Events (MCP-side)
    MCP_TOOL_CALL_DISPATCHED = "mcp_tool_call_dispatched"  # Tool call was dispatched to MCP for execution
    MCP_TOOL_CALL_RESULT = "mcp_tool_call_result"          # MCP tool call completed with result
    MCP_TOOL_CALL_PROGRESS = "mcp_tool_call_progress"      # MCP tool call progress update
    MCP_TOOL_CALL_ERROR = "mcp_tool_call_error"            # MCP tool call failed with error
    
    # Tool Chaining Lifecycle Events
    TOOL_CHAIN_START = "tool_chain_start"              # Tool chaining sequence begins
    TOOL_CHAIN_ITERATION = "tool_chain_iteration"      # Each step/iteration in the chain
    TOOL_CHAIN_END = "tool_chain_end"                  # Tool chaining sequence ends
    TOOL_CHAIN_LIMIT_REACHED = "tool_chain_limit_reached"  # Chaining stopped due to limits
    TOOL_CHAIN_ERROR = "tool_chain_error"              # Error during chaining



@dataclass
class StreamEvent:
    """Represents an event in the streaming response.
    
    This standardized event format allows different LLM providers to publish
    events in a consistent way, regardless of their native response format.
    
    Event Payload Standards for UI Consumption:
    
    LLM Response Events:
    - CONTENT: {"content": str, "delta": str (optional)}
    - ROLE: {"role": str}
    - TOOL_CALL: {"name": str, "arguments": dict, "id": str}
    - FINISH: {"reason": str, "stop_reason": str}
    - USAGE: {"input_tokens": int, "output_tokens": int, "total_tokens": int, "tokens_per_second": float}
    - ERROR: {"error": str, "error_code": str, "details": dict}
    
    MCP Lifecycle Events:
    - MCP_SERVER_UP: {"server_name": str, "server_count": int, "tool_count": int}
    - MCP_SERVER_DOWN: {"server_name": str, "server_count": int, "tool_count": int}
    - MCP_TOOL_ENABLED: {"tool_name": str, "server_name": str, "enabled_count": int, "total_count": int}
    - MCP_TOOL_DISABLED: {"tool_name": str, "server_name": str, "enabled_count": int, "total_count": int}
    
    Tool Execution Events:
    - LLM_TOOL_CALL_REQUEST: {"tool_name": str, "parameters": dict, "call_id": str}
    - MCP_MCP_TOOL_CALL_DISPATCHED: {"tool_name": str, "parameters": dict, "call_id": str, "server_name": str}
    - MCP_MCP_TOOL_CALL_RESULT: {"tool_name": str, "result": any, "call_id": str, "execution_time": float}
    - MCP_MCP_TOOL_CALL_PROGRESS: {"tool_name": str, "progress": float, "message": str, "call_id": str}
    - MCP_MCP_TOOL_CALL_ERROR: {"tool_name": str, "error": str, "call_id": str, "error_code": str}
    
    Tool Chaining Events:
    - TOOL_CHAIN_START: {"chain_id": str, "initial_query": str, "max_iterations": int}
    - TOOL_CHAIN_ITERATION: {"chain_id": str, "iteration": int, "max_iterations": int, "tool_name": str}
    - TOOL_CHAIN_END: {"chain_id": str, "total_iterations": int, "reason": str, "success": bool}
    - TOOL_CHAIN_LIMIT_REACHED: {"chain_id": str, "limit_type": str, "limit_value": any, "iterations": int}
    - TOOL_CHAIN_ERROR: {"chain_id": str, "error": str, "iteration": int, "error_code": str}
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
