"""MCP Server Management API.

This module provides a clean, command-friendly API for managing MCP servers,
tools, and debugging operations. It wraps the MCPManager functionality with
a simplified interface suitable for CLI commands and user interaction.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from hatchling.mcp_utils.manager import mcp_manager, MCPToolInfo, MCPToolStatus
from hatchling.mcp_utils.mcp_tool_data import MCPToolStatusReason
from hatchling.core.logging.logging_manager import logging_manager
from hatchling.core.llm.event_system import StreamEventType


class MCPServerStatus(Enum):
    """Status of an MCP server connection."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""
    path: str
    status: MCPServerStatus
    tool_count: int
    enabled_tool_count: int
    last_connected: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class MCPToolSummary:
    """Summary information about an MCP tool."""
    name: str
    server_path: str
    status: MCPToolStatus
    description: Optional[str] = None
    last_updated: Optional[float] = None
    error_message: Optional[str] = None

logger = logging_manager.get_session("MCPServerAPI")

class MCPServerAPI:
    """Clean API for MCP server management and debugging.
    
    This class provides a simplified interface for:
    - Server connection management
    - Tool discovery and management
    - Manual tool execution for debugging
    - Server health monitoring
    """
    
    # =============================================================================
    # Server Management
    # =============================================================================

    @staticmethod
    async def connect_servers(server_paths: Optional[List[str]] = None) -> bool:
        """Connect to MCP servers.
        
        Args:
            server_paths (List[str]): List of paths to MCP server scripts.
            If None, connects to all configured servers.
            
        Returns:
            bool: True if at least one server connected successfully.
        """
        return await mcp_manager.connect_to_servers(server_paths)
    
    @staticmethod
    async def disconnect_all_servers() -> None:
        """Disconnect from all MCP servers."""
        await mcp_manager.disconnect_all()
    
    @staticmethod
    def get_server_list() -> List[MCPServerInfo]:
        """Get list of all configured MCP servers with their status.
        
        Returns:
            List[MCPServerInfo]: List of server information.
        """
        servers = []
        
        # Get connected servers
        for path, client in mcp_manager.mcp_clients.items():
            tool_count = len(client.tools)
            enabled_count = len([
                tool for tool in mcp_manager._managed_tools.values()
                if tool.server_path == path and tool.status == MCPToolStatus.ENABLED
            ])
            
            servers.append(MCPServerInfo(
                path=path,
                status=MCPServerStatus.CONNECTED,
                tool_count=tool_count,
                enabled_tool_count=enabled_count,
                last_connected=time.time()  # Approximate
            ))
        
        return servers
    
    @staticmethod
    def get_server_status(server_path: str) -> MCPServerInfo:
        """Get detailed status for a specific server.
        
        Args:
            server_path (str): Path to the MCP server script.
            
        Returns:
            MCPServerInfo: Server status information.
        """
        if server_path in mcp_manager.mcp_clients:
            client = mcp_manager.mcp_clients[server_path]
            tool_count = len(client.tools)
            enabled_count = len([
                tool for tool in mcp_manager._managed_tools.values()
                if tool.server_path == server_path and tool.status == MCPToolStatus.ENABLED
            ])
            
            return MCPServerInfo(
                path=server_path,
                status=MCPServerStatus.CONNECTED,
                tool_count=tool_count,
                enabled_tool_count=enabled_count,
                last_connected=time.time()
            )
        else:
            return MCPServerInfo(
                path=server_path,
                status=MCPServerStatus.DISCONNECTED,
                tool_count=0,
                enabled_tool_count=0,
                error_message="Server not connected"
            )
    
    # =============================================================================
    # Tool Management  
    # =============================================================================
    
    @staticmethod
    def get_all_tools() -> List[MCPToolSummary]:
        """Get list of all available MCP tools.
        
        Returns:
            List[MCPToolSummary]: List of tool summaries.
        """
        tools = []
        
        for tool_name, tool_info in mcp_manager.get_all_managed_tools().items():
            # Try to get tool description from the actual tool object
            description = None
            if tool_info.server_path in mcp_manager.mcp_clients:
                client = mcp_manager.mcp_clients[tool_info.server_path]
                tool_obj = client.tools.get(tool_name)
                if tool_obj and hasattr(tool_obj, 'description'):
                    description = tool_obj.description
            
            tools.append(MCPToolSummary(
                name=tool_name,
                server_path=tool_info.server_path,
                status=tool_info.status,
                description=description,
                last_updated=tool_info.last_updated
            ))
        
        return tools
    
    @staticmethod
    def get_enabled_tools() -> List[MCPToolSummary]:
        """Get list of enabled MCP tools.
        
        Returns:
            List[MCPToolSummary]: List of enabled tool summaries.
        """
        return [tool for tool in MCPServerAPI.get_all_tools() if tool.status == MCPToolStatus.ENABLED]
    
    @staticmethod
    def get_tools_by_server(server_path: str) -> List[MCPToolSummary]:
        """Get all tools provided by a specific server.
        
        Args:
            server_path (str): Path to the MCP server script.
            
        Returns:
            List[MCPToolSummary]: List of tools from the server.
        """
        return [tool for tool in MCPServerAPI.get_all_tools() if tool.server_path == server_path]
    
    @staticmethod
    def enable_tool(tool_name: str) -> bool:
        """Enable a specific tool.
        
        Args:
            tool_name (str): Name of the tool to enable.
            
        Returns:
            bool: True if tool was enabled successfully.
        """
        # Get managed tools directly instead of using manager method
        managed_tools = mcp_manager._managed_tools
        
        if tool_name not in managed_tools:
            logger.warning(f"Tool '{tool_name}' not found in managed tools")
            return False
            
        tool_info = managed_tools[tool_name]
        
        if tool_info.status == MCPToolStatus.ENABLED:
            logger.debug(f"Tool '{tool_name}' is already enabled")
            return True
            
        # Check if the server is still available
        if tool_info.server_path not in mcp_manager.mcp_clients:
            logger.warning(f"Cannot enable tool '{tool_name}' - server is not connected")
            return False
            
        # Enable the tool
        tool_info.status = MCPToolStatus.ENABLED
        tool_info.reason = MCPToolStatusReason.FROM_USER_ENABLED
        
        # Update timestamp
        import time
        tool_info.last_updated = time.time()
        
        # Publish event through manager's publisher
        mcp_manager._publish_tool_event(StreamEventType.MCP_TOOL_ENABLED, tool_name, tool_info)
        
        logger.info(f"Enabled tool: {tool_name}")
        return True
    
    @staticmethod
    def disable_tool(tool_name: str) -> bool:
        """Disable a specific tool.
        
        Args:
            tool_name (str): Name of the tool to disable.
            
        Returns:
            bool: True if tool was disabled successfully.
        """
        # Get managed tools directly instead of using manager method
        managed_tools = mcp_manager._managed_tools
        
        if tool_name not in managed_tools:
            logger.warning(f"Tool '{tool_name}' not found in managed tools")
            return False
            
        tool_info = managed_tools[tool_name]
        
        if tool_info.status == MCPToolStatus.DISABLED:
            logger.debug(f"Tool '{tool_name}' is already disabled")
            return False
            
        # Disable the tool
        tool_info.status = MCPToolStatus.DISABLED
        tool_info.reason = MCPToolStatusReason.FROM_USER_DISABLED
        
        # Update timestamp
        import time
        tool_info.last_updated = time.time()
        
        # Publish event through manager's publisher
        mcp_manager._publish_tool_event(StreamEventType.MCP_TOOL_DISABLED, tool_name, tool_info)
        
        logger.info(f"Disabled tool: {tool_name}")
        return True
    
    @staticmethod
    def get_tool_info(tool_name: str) -> Optional[MCPToolSummary]:
        """Get detailed information about a specific tool.
        
        Args:
            tool_name (str): Name of the tool.
            
        Returns:
            Optional[MCPToolSummary]: Tool information if found.
        """
        tool_info = mcp_manager.get_tool_status(tool_name)
        if not tool_info:
            return None
        
        # Get description from tool object
        description = None
        if tool_info.server_path in mcp_manager.mcp_clients:
            client = mcp_manager.mcp_clients[tool_info.server_path]
            tool_obj = client.tools.get(tool_name)
            if tool_obj and hasattr(tool_obj, 'description'):
                description = tool_obj.description
        
        return MCPToolSummary(
            name=tool_name,
            server_path=tool_info.server_path,
            status=tool_info.status,
            description=description,
            last_updated=tool_info.last_updated
        )
    
    # =============================================================================
    # Manual Tool Execution (Debugging)
    # =============================================================================
    
    @staticmethod
    async def execute_tool_manually(tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Any, Optional[str]]:
        """Execute an MCP tool manually for debugging purposes.
        
        Args:
            tool_name (str): Name of the tool to execute.
            arguments (Dict[str, Any]): Arguments to pass to the tool.
            
        Returns:
            Tuple[bool, Any, Optional[str]]: Success flag, result, and error message if any.
        """
        try:
            result = await mcp_manager.execute_tool(tool_name, arguments)
            return True, result, None
        except ConnectionError as e:
            return False, None, f"Connection error: {e}"
        except ValueError as e:
            return False, None, f"Tool not found: {e}"
        except Exception as e:
            return False, None, f"Execution error: {e}"
    
    @staticmethod
    def get_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the JSON schema for a tool's arguments.
        
        Args:
            tool_name (str): Name of the tool.
            
        Returns:
            Optional[Dict[str, Any]]: Tool schema if available.
        """
        tool_info = mcp_manager.get_tool_status(tool_name)
        if not tool_info or tool_info.server_path not in mcp_manager.mcp_clients:
            return None
        
        return tool_info.schema
    
    # =============================================================================
    # Health and Diagnostics
    # =============================================================================
    
    @staticmethod
    def get_health_summary() -> Dict[str, Any]:
        """Get overall health summary of MCP system.
        
        Returns:
            Dict[str, Any]: Health summary including server and tool counts.
        """
        servers = MCPServerAPI.get_server_list()
        all_tools = MCPServerAPI.get_all_tools()
        
        return {
            "connected_servers": len(servers),
            "total_tools": len(all_tools),
            "enabled_tools": len([t for t in all_tools if t.status == MCPToolStatus.ENABLED]),
            "disabled_tools": len([t for t in all_tools if t.status == MCPToolStatus.DISABLED]),
            "server_details": [
                {
                    "path": server.path,
                    "status": server.status.value,
                    "tools": server.tool_count,
                    "enabled_tools": server.enabled_tool_count
                }
                for server in servers
            ]
        }
    
    @staticmethod
    async def get_session_citations() -> Dict[str, Dict[str, str]]:
        """Get citations for all servers used in the current session.
        
        Returns:
            Dict[str, Dict[str, str]]: Server citations.
        """
        return await mcp_manager.get_citations_for_session()

    @staticmethod
    def reset_session_tracking() -> None:
        """Reset session tracking for citations."""
        mcp_manager.reset_session_tracking()
