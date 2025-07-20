from typing import Dict, Any, Callable, List, Optional
from enum import Enum
from dataclasses import dataclass


class MCPToolStatus(Enum):
    """Status of an MCP tool in the lifecycle management system."""
    
    ENABLED = "enabled"      # Tool is available for use
    DISABLED = "disabled"    # Tool is not available for use


class MCPToolStatusReason(Enum):
    """Reasons why an MCP tool has a particular status."""
    
    # Enabled reasons
    FROM_SERVER_UP = "server_up"              # Tool enabled because server came online
    FROM_USER_ENABLED = "user_enabled"        # Tool explicitly enabled by user
    FROM_SERVER_REACHABLE = "server_reachable"  # Tool enabled because server became reachable
    
    # Disabled reasons  
    FROM_SERVER_DOWN = "server_down"          # Tool disabled because server went down
    FROM_SERVER_UNREACHABLE = "unreachable"  # Tool disabled because server is unreachable
    FROM_USER_DISABLED = "user_disabled"     # Tool explicitly disabled by user
    FROM_SYSTEM_ERROR = "system_error"       # Tool disabled due to system error


@dataclass
class MCPToolInfo:
    """Information about an MCP tool in the lifecycle management system."""
    
    name: str                           # Tool name
    description: str                    # Tool description  
    schema: Dict[str, Any]             # Tool schema/definition
    server_path: str                   # Path to the MCP server providing this tool
    status: MCPToolStatus              # Current status (enabled/disabled)
    reason: MCPToolStatusReason        # Reason for current status
    provider_format: Optional[Dict[str, Any]] = None  # Cached provider-specific format
    last_updated: Optional[float] = None              # Timestamp of last status update
    
    def __post_init__(self):
        """Set last_updated timestamp if not provided."""
        if self.last_updated is None:
            import time
            self.last_updated = time.time()