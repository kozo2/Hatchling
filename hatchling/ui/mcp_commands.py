"""MCP Server Management Commands.

This module provides CLI commands for managing MCP servers, tools, and debugging.
Commands follow the format 'mcp:action:target' for clarity and consistency.
"""

import json
from typing import Dict, Any, Optional

from hatchling.ui.abstract_commands import AbstractCommands
from hatchling.mcp_utils.mcp_server_api import MCPServerAPI
from hatchling.mcp_utils.mcp_tool_data import MCPToolStatus
from hatchling.config.i18n import translate

class MCPCommands(AbstractCommands):
    """CLI commands for MCP server and tool management."""
    
    def _register_commands(self) -> None:
        """Register all MCP-related commands."""

        self.commands = {
            'mcp:server:list': {
                'handler': self._cmd_server_list,
                'description': translate('commands.mcp.server_list_description'),
                'is_async': False,
                'args': {}
            },
            'mcp:server:status': {
                'handler': self._cmd_server_status,
                'description': translate('commands.mcp.server_status_description'),
                'is_async': False,
                'args': {
                    'server_path': {
                        'positional': True,
                        'completer_type': 'none',
                        'description': translate('commands.mcp.server_path_arg_description'),
                        'required': True
                    }
                }
            },
            'mcp:server:connect': {
                'handler': self._cmd_server_connect,
                'description': translate('commands.mcp.server_connect_description'),
                'is_async': True,
                'args': {
                    'server_paths': {
                        'positional': True,
                        'completer_type': 'none',
                        'description': translate('commands.mcp.server_paths_arg_description'),
                        'required': False
                    }
                }
            },
            'mcp:server:disconnect': {
                'handler': self._cmd_server_disconnect,
                'description': translate('commands.mcp.server_disconnect_description'),
                'is_async': True,
                'args': {}
            },
            'mcp:tool:list': {
                'handler': self._cmd_tool_list,
                'description': translate('commands.mcp.tool_list_description'),
                'is_async': False,
                'args': {
                    'server_path': {
                        'positional': False,
                        'completer_type': 'none',
                        'description': translate('commands.mcp.server_path_arg_description_optional'),
                        'required': False
                    }
                }
            },
            'mcp:tool:info': {
                'handler': self._cmd_tool_info,
                'description': translate('commands.mcp.tool_info_description'),
                'is_async': False,
                'args': {
                    'tool_name': {
                        'positional': True,
                        'completer_type': 'none',
                        'description': translate('commands.mcp.tool_name_arg_description'),
                        'required': True
                    }
                }
            },
            'mcp:tool:enable': {
                'handler': self._cmd_tool_enable,
                'description': translate('commands.mcp.tool_enable_description'),
                'is_async': False,
                'args': {
                    'tool_name': {
                        'positional': True,
                        'completer_type': 'none',
                        'description': translate('commands.mcp.tool_name_arg_description_enable'),
                        'required': True
                    }
                }
            },
            'mcp:tool:disable': {
                'handler': self._cmd_tool_disable,
                'description': translate('commands.mcp.tool_disable_description'),
                'is_async': False,
                'args': {
                    'tool_name': {
                        'positional': True,
                        'completer_type': 'none',
                        'description': translate('commands.mcp.tool_name_arg_description_disable'),
                        'required': True
                    }
                }
            },
            # 'mcp:tool:execute': {
            #     'handler': self._cmd_tool_execute,
            #     'description': translate('commands.mcp.tool_execute_description'),
            #     'is_async': True,
            #     'args': {
            #         'tool_name': {
            #             'positional': True,
            #             'completer_type': 'none',
            #             'description': translate('commands.mcp.tool_name_arg_description_execute'),
            #             'required': True
            #         }
            #     }
            # },
            # 'mcp:tool:schema': {
            #     'handler': self._cmd_tool_schema,
            #     'description': translate('commands.mcp.tool_schema_description'),
            #     'is_async': False,
            #     'args': {
            #         'tool_name': {
            #             'positional': True,
            #             'completer_type': 'none',
            #             'description': translate('commands.mcp.tool_name_arg_description'),
            #             'required': True
            #         }
            #     }
            # },
            'mcp:health': {
                'handler': self._cmd_health,
                'description': translate('commands.mcp.health_description'),
                'is_async': False,
                'args': {}
            },
            # 'mcp:citations': {
            #     'handler': self._cmd_citations,
            #     'description': translate('commands.mcp.citations_description'),
            #     'is_async': True,
            #     'args': {}
            # },
            # 'mcp:reset': {
            #     'handler': self._cmd_reset,
            #     'description': translate('commands.mcp.reset_description'),
            #     'is_async': False,
            #     'args': {}
            # }
        }
    def _cmd_server_list(self, args: str) -> bool:
        """List all configured MCP servers and their status.
        
        Args:
            args (str): Unused arguments.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            servers = MCPServerAPI.get_server_list()
            
            if not servers:
                print("No MCP servers configured.")
                return True
            
            print("MCP Servers:")
            for server in servers:
                status_display = server.status.value.upper()
                tool_info = f"({server.enabled_tool_count}/{server.tool_count} tools enabled)"
                print(f"  {server.path} - {status_display} {tool_info}")
                
        except Exception as e:
            self.logger.error(f"Error in server list command: {e}")
            
        return True
    
    def _cmd_server_status(self, args: str) -> bool:
        """Show detailed status for a specific MCP server.
        
        Args:
            args (str): Server path argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            server_path = args.strip()
            if not server_path:
                print("Error: Server path is required")
                return True
                
            server_info = MCPServerAPI.get_server_status(server_path)
            
            print(f"Server: {server_info.path}")
            print(f"  Status: {server_info.status.value.upper()}")
            print(f"  Tools: {server_info.enabled_tool_count}/{server_info.tool_count} enabled")
            
            if server_info.error_message:
                print(f"  Error: {server_info.error_message}")
                
            if server_info.last_connected:
                import time
                connected_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                             time.localtime(server_info.last_connected))
                print(f"  Last Connected: {connected_time}")
                
        except Exception as e:
            self.logger.error(f"Error in server status command: {e}")
            
        return True
    
    async def _cmd_server_connect(self, args: str) -> bool:
        """Connect to MCP servers.
        
        Args:
            args (str): Comma-separated server paths. If
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            server_paths_str = args.strip()
            if not server_paths_str:
                server_paths = None
            else:
                server_paths = [path.strip() for path in server_paths_str.split(',')]
            
            success = await MCPServerAPI.connect_servers(server_paths)
            
            if success:
                print("Successfully connected to MCP servers")
            else:
                print("Failed to connect to MCP servers")
                
        except Exception as e:
            self.logger.error(f"Error connecting to servers: {e}")
            
        return True
    
    async def _cmd_server_disconnect(self, args: str) -> bool:
        """Disconnect from all MCP servers.
        
        Args:
            args (str): Unused arguments.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            print("Disconnecting from all MCP servers...")
            await MCPServerAPI.disconnect_all_servers()
            print("Disconnected from all MCP servers")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from servers: {e}")

        return True
    
    # =============================================================================
    # Tool Management Commands
    # =============================================================================
    
    def _cmd_tool_list(self, args: str) -> bool:
        """List all available MCP tools.
        
        Args:
            args (str): Optional server path filter.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            server_path_filter = args.strip() if args.strip() else None
            
            if server_path_filter:
                tools = MCPServerAPI.get_tools_by_server(server_path_filter)
                print(f"MCP Tools from {server_path_filter}:")
            else:
                tools = MCPServerAPI.get_all_tools()
                print("All MCP Tools:")
            
            if not tools:
                print("  No tools found")
                return True
            
            # Group by server for better organization
            by_server = {}
            for tool in tools:
                if tool.server_path not in by_server:
                    by_server[tool.server_path] = []
                by_server[tool.server_path].append(tool)
            
            for server_path, server_tools in by_server.items():
                if not server_path_filter:  # Only show server headers when not filtering
                    print(f"  Server: {server_path}")
                    
                for tool in server_tools:
                    status = "ENABLED" if tool.status == MCPToolStatus.ENABLED else "DISABLED"
                    description = f" - {tool.description}" if tool.description else ""
                    indent = "    " if not server_path_filter else "  "
                    print(f"{indent}{tool.name} ({status}){description}")
                    
        except Exception as e:
            print(f"Error listing tools: {e}")
            self.logger.error(f"Error in tool list command: {e}")
            
        return True
    
    def _cmd_tool_info(self, args: str) -> bool:
        """Show detailed information about a specific tool.
        
        Args:
            args (str): Tool name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            tool_name = args.strip()
            if not tool_name:
                print("Error: Tool name is required")
                return True
                
            tool_info = MCPServerAPI.get_tool_info(tool_name)
            
            if not tool_info:
                print(f"Tool '{tool_name}' not found")
                return True
            
            print(f"Tool: {tool_info.name}")
            print(f"  Server: {tool_info.server_path}")
            print(f"  Status: {tool_info.status.value.upper()}")
            
            if tool_info.description:
                print(f"  Description: {tool_info.description}")
                
            if tool_info.last_updated:
                import time
                updated_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                           time.localtime(tool_info.last_updated))
                print(f"  Last Updated: {updated_time}")
                
        except Exception as e:
            self.logger.error(f"Error getting tool info: {e}")

        return True
    
    def _cmd_tool_enable(self, args: str) -> bool:
        """Enable a specific MCP tool.
        
        Args:
            args (str): Tool name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            tool_name = args.strip()
            if not tool_name:
                print("Error: Tool name is required")
                return True
                
            MCPServerAPI.enable_tool(tool_name)
                
        except Exception as e:
            print(f"Error enabling tool: {e}")
            self.logger.error(f"Error in tool enable command: {e}")
            
        return True
    
    def _cmd_tool_disable(self, args: str) -> bool:
        """Disable a specific MCP tool.
        
        Args:
            args (str): Tool name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            tool_name = args.strip()
            if not tool_name:
                print("Error: Tool name is required")
                return True
                
            success = MCPServerAPI.disable_tool(tool_name)
            
            if success:
                print(f"Tool '{tool_name}' disabled successfully")
            else:
                print(f"Failed to disable tool '{tool_name}' (already disabled or not found)")
                
        except Exception as e:
            self.logger.error(f"Error disabling tool: {e}")

        return True
    
    async def _cmd_tool_execute(self, args: str) -> bool:
        """Execute an MCP tool manually for debugging.
        
        Args:
            args (str): Tool name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            tool_name = args.strip()
            if not tool_name:
                print("Error: Tool name is required")
                return True
            
            # Get tool schema to guide argument input
            schema = MCPServerAPI.get_tool_schema(tool_name)
            if not schema:
                print(f"Tool '{tool_name}' not found or schema unavailable")
                return True
            
            print(f"Executing tool: {tool_name}")
            print("Tool arguments schema:")
            print(json.dumps(schema, indent=2))
            
            # Parse arguments dynamically based on schema
            arguments = await self._parse_tool_arguments(schema)
            if arguments is None:
                print("Execution cancelled")
                return True
            
            print(f"Executing with arguments: {json.dumps(arguments, indent=2)}")
            
            # Execute the tool
            success, result, error = await MCPServerAPI.execute_tool_manually(tool_name, arguments)
            
            if success:
                print("Execution successful:")
                if isinstance(result, (dict, list)):
                    print(json.dumps(result, indent=2))
                else:
                    print(str(result))
            else:
                print(f"Execution failed: {error}")
                
        except Exception as e:
            self.logger.error(f"Error executing tool: {e}")

        return True
    
    def _cmd_tool_schema(self, args: str) -> bool:
        """Show the JSON schema for a tool's arguments.
        
        Args:
            args (str): Tool name argument.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            tool_name = args.strip()
            if not tool_name:
                print("Error: Tool name is required")
                return True
                
            schema = MCPServerAPI.get_tool_schema(tool_name)
            
            if not schema:
                print(f"Schema not available for tool '{tool_name}'")
                return True
            
            print(f"Schema for tool '{tool_name}':")
            print(json.dumps(schema, indent=2))
            
        except Exception as e:
            self.logger.error(f"Error getting tool schema: {e}")

        return True
    
    # =============================================================================
    # System Commands
    # =============================================================================
    
    def _cmd_health(self, args: str) -> bool:
        """Show overall MCP system health summary.
        
        Args:
            args (str): Unused arguments.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            health = MCPServerAPI.get_health_summary()
            
            print("MCP System Health:")
            print(f"  Connected Servers: {health['connected_servers']}")
            print(f"  Total Tools: {health['total_tools']}")
            print(f"  Enabled Tools: {health['enabled_tools']}")
            print(f"  Disabled Tools: {health['disabled_tools']}")
            
            if health['server_details']:
                print("\nServer Details:")
                for server in health['server_details']:
                    print(f"  {server['path']} ({server['status']}) - {server['enabled_tools']}/{server['tools']} tools")
                    
        except Exception as e:
            self.logger.error(f"Error getting health summary: {e}")

        return True
    
    async def _cmd_citations(self, args: str) -> bool:
        """Show MCP server citations for current session.
        
        Args:
            args (str): Unused arguments.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            citations = await MCPServerAPI.get_session_citations()
            
            if not citations:
                print("No MCP servers used in current session")
                return True
            
            print("MCP Server Citations:")
            for server_path, citation_info in citations.items():
                print(f"  {server_path}:")
                for key, value in citation_info.items():
                    print(f"    {key}: {value}")
                    
        except Exception as e:
            self.logger.error(f"Error getting citations: {e}")

        return True
    
    def _cmd_reset(self, args: str) -> bool:
        """Reset MCP session tracking.
        
        Args:
            args (str): Unused arguments.
            
        Returns:
            bool: True to continue the chat session.
        """
        try:
            MCPServerAPI.reset_session_tracking()
            print("MCP session tracking reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting session tracking: {e}")

        return True
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    async def _parse_tool_arguments(self, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse tool arguments interactively based on JSON schema.
        
        Args:
            schema (Dict[str, Any]): The JSON schema for the tool arguments.
            
        Returns:
            Optional[Dict[str, Any]]: Parsed arguments or None if cancelled.
        """
        try:
            arguments = {}
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            print("\nEnter arguments (press Enter with empty value to skip optional args):")
            
            for prop_name, prop_schema in properties.items():
                is_required = prop_name in required
                prop_type = prop_schema.get('type', 'string')
                description = prop_schema.get('description', '')
                
                # Show prompt
                required_marker = "*" if is_required else ""
                type_hint = f" ({prop_type})" if prop_type != 'string' else ""
                desc_hint = f" - {description}" if description else ""
                
                while True:
                    user_input = input(f"  {prop_name}{required_marker}{type_hint}{desc_hint}: ").strip()
                    
                    # Handle empty input
                    if not user_input:
                        if is_required:
                            print(f"    Error: {prop_name} is required")
                            continue
                        else:
                            break  # Skip optional parameter
                    
                    # Handle cancellation
                    if user_input.lower() in ['cancel', 'quit', 'exit']:
                        return None
                    
                    # Convert value based on type
                    try:
                        converted_value = self._convert_argument_value(user_input, prop_type, prop_schema)
                        arguments[prop_name] = converted_value
                        break
                        
                    except ValueError as e:
                        self.logger.error(f"Invalid value for {prop_name}: {e}")
                        continue
            
            return arguments
            
        except KeyboardInterrupt:
            self.logger.info("Tool argument input cancelled by user")
            return None
    
    def _convert_argument_value(self, value: str, prop_type: str, prop_schema: Dict[str, Any]) -> Any:
        """Convert string input to the appropriate type based on schema.
        
        Args:
            value (str): User input value.
            prop_type (str): Expected property type.
            prop_schema (Dict[str, Any]): Full property schema.
            
        Returns:
            Any: Converted value.
            
        Raises:
            ValueError: If conversion fails.
        """
        if prop_type == 'string':
            return value
        elif prop_type == 'number':
            try:
                return float(value)
            except ValueError:
                self.logger.error(f"Error parsing {value} as number: must be a valid float")
        elif prop_type == 'integer':
            try:
                return int(value)
            except ValueError:
                self.logger.error(f"Error parsing {value} as integer: must be a valid integer")
        elif prop_type == 'boolean':
            if value.lower() in ['true', '1', 'yes', 'y']:
                return True
            elif value.lower() in ['false', '0', 'no', 'n']:
                return False
            else:
                self.logger.error(f"Error parsing {value} as boolean: must be true/false or 1/0")
        elif prop_type == 'array':
            # Simple array parsing - split by comma
            try:
                if value.startswith('[') and value.endswith(']'):
                    # JSON array format
                    return json.loads(value)
                else:
                    # Comma-separated values
                    return [item.strip() for item in value.split(',') if item.strip()]
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing {value} as array: {e}")
        elif prop_type == 'object':
            # Parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing {value} as object: {e}")
        else:
            # Default to string for unknown types
            return value
