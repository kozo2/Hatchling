"""
Data structures and types for informing and processing streams of events
from LLM providers.
"""


from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from hatchling.config.llm_settings import ELLMProvider

class StreamEventType(Enum):
    """Types of events that can be published during streaming."""
    
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
    
    # Tool Execution Events
    TOOL_CALL_DISPATCHED = "tool_call_dispatched"      # Tool call was dispatched for execution
    TOOL_CALL_RESULT = "tool_call_result"              # Tool call completed with result
    TOOL_CALL_PROGRESS = "tool_call_progress"          # Tool call progress update
    TOOL_CALL_ERROR = "tool_call_error"                # Tool call failed with error



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
