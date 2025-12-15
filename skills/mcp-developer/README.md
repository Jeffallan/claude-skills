# MCP Developer Skill

Model Context Protocol specialist for building servers and clients that connect AI systems with external tools and data sources.

## Overview

This skill provides comprehensive guidance for implementing MCP (Model Context Protocol) servers and clients using TypeScript or Python SDKs. It covers protocol compliance, security, performance optimization, and production deployment.

## Structure

```
mcp-developer/
├── SKILL.md                       # Main skill definition (94 lines)
├── README.md                      # This file
└── references/
    ├── protocol.md                # MCP protocol spec, JSON-RPC 2.0, lifecycle (247 lines)
    ├── typescript-sdk.md          # TypeScript/Node.js implementation (353 lines)
    ├── python-sdk.md              # Python implementation (370 lines)
    ├── tools.md                   # Tool definitions, schemas, execution (483 lines)
    └── resources.md               # Resource providers, URIs, content types (557 lines)
```

## When to Use

Invoke this skill for:
- Building MCP servers for data source integration
- Implementing tool functions for AI assistants
- Creating resource providers with URI schemes
- Setting up MCP clients for Claude integration
- Debugging protocol compliance issues
- Optimizing MCP performance and security

## Key Topics Covered

### Protocol (protocol.md)
- JSON-RPC 2.0 message format
- Connection lifecycle (initialize, shutdown)
- Request/response patterns
- Notifications and subscriptions
- Error codes and handling
- Transport mechanisms (stdio, HTTP/SSE)

### TypeScript SDK (typescript-sdk.md)
- Server setup with `@modelcontextprotocol/sdk`
- Resource providers
- Tool implementations
- Prompt templates
- Input validation with Zod
- Error handling
- Client integration

### Python SDK (python-sdk.md)
- Server setup with `mcp` package
- Resource providers
- Tool implementations
- Prompt templates
- Input validation with Pydantic
- Error handling
- Client integration

### Tools (tools.md)
- Tool definition patterns
- Input schema design (enums, arrays, nested objects)
- Response formats (text, images, resources)
- Implementation patterns (database, file system, HTTP)
- Best practices (validation, rate limiting, timeouts)
- Idempotency and error handling

### Resources (resources.md)
- URI scheme design (file://, custom schemes)
- Resource templates with parameters
- Content types (text, JSON, binary, markdown)
- Implementation patterns (file system, database, API)
- Subscriptions and notifications
- Caching and security

## Example Usage

### Building a TypeScript MCP Server

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server(
  { name: "my-server", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {} } }
);

// Implement tools and resources
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [/* ... */]
}));

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Building a Python MCP Server

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("my-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="example", description="...", inputSchema={...})]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Implementation
    pass

# Run server
async with stdio_server() as (read, write):
    await app.run(read, write, app.create_initialization_options())
```

## Integration Points

This skill works well with:
- **FastAPI Expert** - For HTTP transport servers
- **TypeScript Pro** - For advanced TypeScript patterns
- **Python Pro** - For Python best practices
- **Security Reviewer** - For security audits
- **DevOps Engineer** - For deployment and monitoring
- **Test Master** - For comprehensive testing strategies

## Reference Loading Strategy

The skill uses selective disclosure to minimize token load:

1. Start with SKILL.md (94 lines) for overview and routing
2. Load specific reference files based on context:
   - `protocol.md` when working with protocol compliance
   - `typescript-sdk.md` for Node.js implementations
   - `python-sdk.md` for Python implementations
   - `tools.md` for tool function development
   - `resources.md` for resource provider development

## Standards and Compliance

- **Protocol**: JSON-RPC 2.0 compliant
- **Version**: MCP protocol version 2024-11-05
- **Security**: Input validation, authentication, authorization
- **Performance**: Caching, rate limiting, timeouts
- **Testing**: Unit tests, integration tests, protocol compliance tests

## Resources

- MCP Specification: https://modelcontextprotocol.io
- TypeScript SDK: https://github.com/modelcontextprotocol/typescript-sdk
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Claude Desktop Integration: https://claude.ai/desktop

## License

Part of the claude-skills collection.
