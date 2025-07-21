"""
All the MCP utilities for Hatchling. Including Client-Server communication, tool execution, and event handling.
"""


from .mcp_tool_data import MCPToolInfo, MCPToolStatus, MCPToolStatusReason
from .client import MCPClient
from .manager import MCPManager, mcp_manager

__all__ = [
    "MCPToolInfo",
    "MCPToolStatus",
    "MCPToolStatusReason",
    "MCPClient",
    "MCPManager",
    "mcp_manager"
]