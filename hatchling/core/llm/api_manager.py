import json
from typing import List, Dict, Tuple, Any
import logging
import aiohttp
from hatchling.core.logging.logging_manager import logging_manager
from hatchling.config.settings import AppSettings
from hatchling.core.chat.message_history import MessageHistory

class APIManager:
    """Manages API communication with the LLM."""
    
    def __init__(self, settings: AppSettings):
        """Initialize the API manager.
        
        Args:
            settings: The application settings
        """
        self.settings = settings
        self.logger = logging_manager.get_session("APIManager",
                                      formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def prepare_request_payload(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare the request payload for the LLM API.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            The prepared payload.
        """
        payload = {
            "model": self.settings.llm.model,
            "messages": messages,
            "stream": True  # Always stream
        }
        self.logger.debug(f"Prepared payload: {json.dumps(payload)}")
        return payload
    
    def add_tools_to_payload(self, payload: Dict[str, Any], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add tools to the payload if provided.
        
        Args:
            payload: The original payload.
            tools: List of tools to add
            
        Returns:
            The payload with tools added.
        """
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            self.logger.debug(f"Added {len(tools)} tools to payload: {tools}")
        return payload
    
    def has_tool_calls(self, data: Dict[str, Any]) -> bool:
        """Check if the data contains tool calls.
        
        Args:
            data: The data to check from the LLM.
            
        Returns:
            True if the data contains tool calls, False otherwise.
        """
        return ("message" in data and 
                "tool_calls" in data["message"] and 
                data["message"]["tool_calls"])
    
    def has_message_content(self, data: Dict[str, Any]) -> bool:
        """Check if the data contains message content.
        
        Args:
            data: The data to check.
            
        Returns:
            True if the data contains message content, False otherwise.
        """
        return "message" in data and "content" in data["message"]
    
    async def process_response_data(self,
                                    data: Dict[str, Any],
                                    message_tool_calls: List,
                                    tool_executor
                                    ) -> Tuple[str, List]:
        """Process response data and extract content and tool calls.
        
        Args:
            data (Dict[str, Any]): The response data to process from the LLM.
            message_tool_calls (List): List of processed tool calls.
            tool_executor: The tool execution manager to handle tool calls.
            
        Returns:
            Tuple[str, List]: A tuple containing:
                - str: The extracted content from the response
                - List: The collected tool results
        """
        content = ""
        tool_results = []
        
        # Process tool calls if present
        if self.has_tool_calls(data):
            tool_calls_result = await tool_executor.handle_streaming_tool_calls(data, message_tool_calls)
            if tool_calls_result:
                tool_results.extend(tool_calls_result)
        
        # Extract message content
        if self.has_message_content(data):
            content = data["message"]["content"]
        
        return content, tool_results
    
    async def stream_response(self, 
                              session: aiohttp.ClientSession, 
                              payload: Dict[str, Any], 
                              history: MessageHistory,
                              tool_executor,
                              print_output: bool = True, 
                              prefix: str = None, 
                              update_history: bool = True) -> Tuple[str, List, List]:
        """Stream a response from the API and handle common processing.
        
        Args:
            session: The aiohttp client session to use.
            payload: The request payload to send to the API.
            history: The message history to update
            tool_executor (ToolExecutionManager): Tool execution manager
            print_output: Whether to print the output to the console
            prefix: Optional prefix to print before the response.
            update_history: Whether to update message history with the response.
            
        Returns:
            Tuple containing (full_response, message_tool_calls, tool_results).
        """
        full_response = ""
        message_tool_calls = []
        tool_results = []
        
        if prefix and print_output:
            print(prefix)
            
        async with session.post(f"{self.settings.llm.api_url}/chat", json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                self.logger.error(f"Error: {response.status}, {error_text}")
                raise Exception(f"Error: {response.status}, {error_text}")
            
            async for line in response.content.iter_any():
                if not line:
                    continue
                
                try:
                    line_text = line.decode('utf-8').strip()
                    if not line_text:
                        continue
                    
                    # Debug log the raw response
                    self.logger.debug(f"Raw response: {line_text}")
                    
                    # Parse the JSON response
                    data = json.loads(line_text)
                    
                    # Process the response data
                    content, current_tool_results = await self.process_response_data(data, message_tool_calls, tool_executor)

                    if current_tool_results:
                        tool_results.extend(current_tool_results)
                    elif content:
                        if print_output:
                            print(content, end="", flush=True)
                        full_response += content
                    
                    # Check if this is the last message
                    if data.get("done", False):
                        if print_output:
                            print()  # Add a newline after completion
                        break
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing response: {e}")
        
        # Update message history if requested
        if update_history and history:
            history.update_message_history(full_response, message_tool_calls, tool_results)
        
        return full_response, message_tool_calls, tool_results