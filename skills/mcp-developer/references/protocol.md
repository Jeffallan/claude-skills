# MCP Protocol Specification

> Reference for: MCP Developer
> Load when: Protocol compliance, message types, lifecycle management

## Protocol Overview

MCP is built on JSON-RPC 2.0 and enables bidirectional communication between clients (like Claude Desktop) and servers that provide resources, tools, and prompts.

## Message Types

### Request/Response

```typescript
// Request format
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}

// Success response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "description": "Get weather for a location",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": { "type": "string" }
          },
          "required": ["location"]
        }
      }
    ]
  }
}

// Error response
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": { "details": "location is required" }
  }
}
```

### Notifications

```typescript
// Server sends notification (no response expected)
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "file:///project/data.json"
  }
}
```

## Connection Lifecycle

```
1. Client initiates connection (stdio/HTTP/SSE)
2. Client sends initialize request
   → Server responds with capabilities
3. Client sends initialized notification
4. Normal operation (requests/notifications)
5. Client/server can ping for keepalive
6. Client sends shutdown request
7. Connection closes
```

### Initialize Handshake

```typescript
// Client initialize request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": { "listChanged": true },
      "sampling": {}
    },
    "clientInfo": {
      "name": "claude-desktop",
      "version": "1.0.0"
    }
  }
}

// Server response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "resources": { "subscribe": true, "listChanged": true },
      "tools": { "listChanged": true },
      "prompts": { "listChanged": true }
    },
    "serverInfo": {
      "name": "my-mcp-server",
      "version": "1.0.0"
    }
  }
}

// Client sends initialized notification
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

## Core Methods

### Resources

```typescript
// List available resources
resources/list → { resources: Resource[] }

// Read resource content
resources/read { uri: string } → { contents: ResourceContent[] }

// Subscribe to resource updates (if supported)
resources/subscribe { uri: string } → {}

// Unsubscribe
resources/unsubscribe { uri: string } → {}

// Server notifies of changes
notifications/resources/list_changed → {}
notifications/resources/updated { uri: string } → {}
```

### Tools

```typescript
// List available tools
tools/list → { tools: Tool[] }

// Execute tool
tools/call {
  name: string,
  arguments: object
} → { content: ToolResponse[] }

// Server notifies of tool changes
notifications/tools/list_changed → {}
```

### Prompts

```typescript
// List available prompts
prompts/list → { prompts: Prompt[] }

// Get prompt with arguments
prompts/get {
  name: string,
  arguments?: object
} → { messages: PromptMessage[] }

// Server notifies of prompt changes
notifications/prompts/list_changed → {}
```

## Error Codes

Standard JSON-RPC 2.0 codes plus MCP-specific:

```typescript
const ERROR_CODES = {
  // JSON-RPC 2.0 standard
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,

  // MCP-specific (implementation defined)
  RESOURCE_NOT_FOUND: -32001,
  TOOL_EXECUTION_ERROR: -32002,
  UNAUTHORIZED: -32003,
  RATE_LIMIT_EXCEEDED: -32004
};
```

## Transport Mechanisms

### stdio (Standard Input/Output)

```typescript
// Server reads from stdin, writes to stdout
// Each message is newline-delimited JSON
// Used for local integration (Claude Desktop default)
```

### HTTP with SSE (Server-Sent Events)

```typescript
// Client POSTs JSON-RPC requests to endpoint
// Server streams responses and notifications via SSE
// Used for remote servers

POST /mcp HTTP/1.1
Content-Type: application/json

{"jsonrpc":"2.0","id":1,"method":"tools/list"}

// SSE response
GET /mcp/sse HTTP/1.1

event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}
```

## Protocol Versions

Current version: `2024-11-05`

Servers must declare supported version in initialize response. Clients should verify compatibility.

## Best Practices

1. **Validation**: Always validate params with JSON Schema
2. **Error handling**: Return structured errors with helpful messages
3. **Versioning**: Check protocol version in initialize
4. **Timeouts**: Implement request timeouts (30s recommended)
5. **Logging**: Log all protocol messages for debugging
6. **Stateless**: Design tools/resources to be stateless
7. **Idempotency**: Make tool calls idempotent when possible
8. **Notifications**: Use notifications for real-time updates
