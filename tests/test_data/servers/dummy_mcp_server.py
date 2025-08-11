#!/usr/bin/env python3
"""
Dummy MCP server for integration testing.

This is a minimal MCP server that provides basic tools for testing
the tool execution and event system integration.
"""

import json
import sys
import asyncio
from typing import Any, Dict


class DummyMCPServer:
    """A minimal MCP server for testing purposes."""
    
    def __init__(self):
        self.tools = {
            "test_function": {
                "description": "A simple test function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "First parameter"},
                        "param2": {"type": "integer", "description": "Second parameter"}
                    },
                    "required": ["param1"]
                }
            },
            "echo_function": {
                "description": "Echo back the input",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "message": {"type": "string", "description": "Message to echo"}
                    },
                    "required": ["message"]
                }
            },
            "failing_function": {
                "description": "A function that always fails for error testing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "will": {"type": "string", "description": "This will fail"}
                    }
                }
            }
        }
    
    def handle_list_tools(self) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "tools": [
                {
                    "name": name,
                    "description": tool["description"],
                    "inputSchema": tool["parameters"]
                }
                for name, tool in self.tools.items()
            ]
        }
    
    def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        if name not in self.tools:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                "isError": True
            }
        
        if name == "failing_function":
            return {
                "content": [{"type": "text", "text": "This function always fails for testing"}],
                "isError": True
            }
        
        if name == "echo_function":
            message = arguments.get("message", "No message provided")
            return {
                "content": [{"type": "text", "text": f"Echo: {message}"}],
                "isError": False
            }
        
        if name == "test_function":
            param1 = arguments.get("param1", "default")
            param2 = arguments.get("param2", 0)
            return {
                "content": [{"type": "text", "text": f"Test executed with param1={param1}, param2={param2}"}],
                "isError": False
            }
        
        return {
            "content": [{"type": "text", "text": f"Tool {name} executed successfully"}],
            "isError": False
        }
    
    async def run(self):
        """Run the dummy MCP server."""
        while True:
            try:
                line = input()
                if not line:
                    break
                
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                
                if method == "tools/list":
                    response = self.handle_list_tools()
                elif method == "tools/call":
                    response = self.handle_call_tool(
                        params.get("name"),
                        params.get("arguments", {})
                    )
                else:
                    response = {"error": f"Unknown method: {method}"}
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except EOFError:
                break
            except Exception as e:
                error_response = {"error": f"Server error: {str(e)}"}
                print(json.dumps(error_response))
                sys.stdout.flush()


if __name__ == "__main__":
    server = DummyMCPServer()
    asyncio.run(server.run())
