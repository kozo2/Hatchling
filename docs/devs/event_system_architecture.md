
# Event System Architecture

This article is about:

- The detailed event-driven architecture in Hatchling
- How publishers and subscribers coordinate LLM, tool, and UI workflows
- Event types, payloads, and real-world event flows
- Practical deployment and integration patterns

## Overview

Hatchling's event system is a robust publish-subscribe architecture that enables real-time, decoupled communication between LLM providers, tool management, and user interfaces. It supports streaming, tool chaining, error handling, and system-wide coordination, allowing new features and integrations without modifying core logic.

## Architecture and Components

### Publisher-Subscriber Pattern

At the core is the `EventPublisher`, which manages a list of `EventSubscriber` instances. Publishers emit events of specific types, and subscribers register interest in those types. This pattern allows any component to react to events without direct dependencies.

**Key Classes:**

- [`EventPublisher`](../../../hatchling/core/llm/event_system/event_publisher.py): Manages subscribers and distributes events
- [`EventSubscriber`](../../../hatchling/core/llm/event_system/event_subscriber.py): Abstract base for all subscribers; must implement `on_event` and `get_subscribed_events`
- [`Event`](../../../hatchling/core/llm/event_system/event_data.py): Standardized event object with type, data, provider, request_id, and timestamp
- [`EventType`](../../../hatchling/core/llm/event_system/event_data.py): The enum of all the use cases of events in Hatchling.

### Event Types and Payloads

Events are categorized by functional area. Each event type has a well-defined payload structure. Below are the main categories and examples:

#### LLM Response Events

- `CONTENT`: `{ "content": str }` — Text content streamed from the LLM
- `ROLE`: `{ "role": str }` — Role assignment (assistant, user, tool)
- `FINISH`: `{ "finish_reason": str }` — End of streaming
- `USAGE`: `{ "prompt_tokens": int, "completion_tokens": int, "total_tokens": int }` — Token usage stats
- `ERROR`: `{ "error": { "message": str, "type": str } }` — Error details
- `LLM_TOOL_CALL_REQUEST`: `{ "id": str, "function": { "name": str, "arguments": dict } }` — LLM requests a tool call

#### MCP Lifecycle Events

- `MCP_SERVER_UP`: `{ "server_path": str, "tool_count": int }`
- `MCP_SERVER_DOWN`: `{ "server_path": str }`
- `MCP_SERVER_UNREACHABLE`: `{ "server_path": str, "error": str }`
- `MCP_TOOL_ENABLED`: `{ "tool_name": str, "tool_info": MCPToolInfo }`
- `MCP_TOOL_DISABLED`: `{ "tool_name": str, "tool_info": MCPToolInfo }`

#### Tool Execution and Chaining Events

- `MCP_TOOL_CALL_DISPATCHED`: `{ "tool_call_id": str, "function_name": str, "arguments": dict }`
- `MCP_TOOL_CALL_RESULT`: `{ "tool_call_id": str, "function_name": str, "arguments": dict, "result": any, "error": None }`
- `MCP_TOOL_CALL_ERROR`: `{ "tool_call_id": str, "function_name": str, "arguments": dict, "result": any, "error": str }`
- `TOOL_CHAIN_START`: `{ "tool_chain_id": str, "initial_query": str, ... }`
- `TOOL_CHAIN_ITERATION_START`: `{ "tool_chain_id": str, "iteration": int, ... }`
- `TOOL_CHAIN_ITERATION_END`: `{ "tool_chain_id": str, "success": bool, ... }`
- `TOOL_CHAIN_END`: `{ "success": bool, "total_iterations": int }`
- `TOOL_CHAIN_LIMIT_REACHED`: `{ "tool_chain_id": str, "limit_type": str, ... }`
- `TOOL_CHAIN_ERROR`: `{ "tool_chain_id": str, "error": str, "iteration": int }`

## Event Flow: A Real Chat Session

The following describes the event flow in a typical chat session, referencing `chat_session.py`:

1. **Session Initialization**: Subscribers (tool call, tool chaining, message history) are registered to all LLM provider publishers and tool execution publishers.
2. **User Sends Message**: The message is added to history; the provider is selected.
3. **Provider Streams Response**: As the LLM streams content, the provider publishes `CONTENT`, `ROLE`, and `FINISH` events. If a tool call is requested, it publishes `LLM_TOOL_CALL_REQUEST`.
4. **Tool Call Handling**: The tool call subscriber receives the event, dispatches the tool call, and publishes `MCP_TOOL_CALL_DISPATCHED` and `MCP_TOOL_CALL_RESULT` (or `MCP_TOOL_CALL_ERROR`).
5. **Tool Chaining**: The tool chaining subscriber coordinates further tool calls and publishes chaining events.
6. **Message History**: The message history subscriber updates the chat log in response to all relevant events.
7. **UI/Other Subscribers**: Any registered UI or monitoring subscribers receive and process events as needed.

## Deploying Publishers and Subscribers

### Publisher Setup

Each LLM provider and tool execution manager instantiates an `EventPublisher`. Subscribers are registered using:

```python
publisher.subscribe(subscriber)
publisher.unsubscribe(subscriber)
publisher.clear_subscribers()
```

To publish an event:

```python
publisher.publish(EventType.CONTENT, {"content": "Hello world!"})
```

### Subscriber Implementation

Subscribers must implement the `EventSubscriber` interface:

```python
class MySubscriber(EventSubscriber):
    def get_subscribed_events(self) -> List[EventType]:
        return [EventType.CONTENT, EventType.ERROR]
    def on_event(self, event: Event) -> None:
        print(f"Received event: {event.type} -> {event.data}")
```

Example: Registering a subscriber in a chat session:

```python
session = ChatSession()
session.register_subscriber(MySubscriber())
```

## Example Subscribers

- **ContentPrinterSubscriber**: Prints streamed content to the console as it arrives.
- **ContentAccumulatorSubscriber**: Collects content for returning complete responses.
- **UsageStatsSubscriber**: Tracks and reports token usage statistics.
- **ErrorHandlerSubscriber**: Handles and reports errors.

See `event_subscribers_examples.py` for more details.

## Best Practices and Troubleshooting

- Always register subscribers before streaming begins to avoid missing events.
- Use clear event type filtering in subscribers to avoid unnecessary processing.
- Validate payload formats for each event type to ensure compatibility.
- For complex workflows (e.g., tool chaining), use dedicated subscribers to manage state and coordination.
- Use logging in subscribers and publishers to aid debugging and monitoring.

## References

- `event_data.py`: Complete event type definitions and payload standards
- `event_publisher.py`: Publisher implementation and API
- `event_subscriber.py`: Subscriber interface and patterns
- `event_subscribers_examples.py`: Reference implementations
- `chat_session.py`: Real-world deployment and integration patterns
