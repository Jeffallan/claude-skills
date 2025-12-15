# MCP Tools Reference

> Reference for: MCP Developer
> Load when: Implementing tool functions, defining schemas, handling execution

## Tool Definition

Tools are functions that AI assistants can invoke to perform actions or retrieve data.

```typescript
{
  "name": "tool_name",
  "description": "Clear description of what the tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "What this parameter is for"
      }
    },
    "required": ["param1"]
  }
}
```

## Input Schema Patterns

### Simple String Parameter

```typescript
{
  "name": "search_docs",
  "description": "Search documentation for a query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query",
        "minLength": 1
      }
    },
    "required": ["query"]
  }
}
```

### Enum Values

```typescript
{
  "name": "get_weather",
  "description": "Get weather information",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": { "type": "string" },
      "units": {
        "type": "string",
        "enum": ["celsius", "fahrenheit"],
        "default": "celsius",
        "description": "Temperature units"
      }
    },
    "required": ["location"]
  }
}
```

### Nested Objects

```typescript
{
  "name": "create_task",
  "description": "Create a new task",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": { "type": "string", "minLength": 1 },
      "metadata": {
        "type": "object",
        "properties": {
          "priority": { "type": "string", "enum": ["low", "medium", "high"] },
          "tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "required": ["title"]
  }
}
```

### Array Parameters

```typescript
{
  "name": "batch_process",
  "description": "Process multiple items",
  "inputSchema": {
    "type": "object",
    "properties": {
      "items": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": { "type": "string" },
            "action": { "type": "string", "enum": ["update", "delete"] }
          },
          "required": ["id", "action"]
        },
        "minItems": 1,
        "maxItems": 100
      }
    },
    "required": ["items"]
  }
}
```

### Union Types (anyOf)

```typescript
{
  "name": "search",
  "description": "Search by ID or query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "search": {
        "anyOf": [
          { "type": "string", "description": "Search query" },
          { "type": "number", "description": "Item ID" }
        ]
      }
    },
    "required": ["search"]
  }
}
```

## Tool Response Formats

### Text Response

```typescript
{
  "content": [
    {
      "type": "text",
      "text": "Operation completed successfully"
    }
  ]
}
```

### Multiple Content Blocks

```typescript
{
  "content": [
    {
      "type": "text",
      "text": "Found 3 results:"
    },
    {
      "type": "text",
      "text": "1. First result\n2. Second result\n3. Third result"
    }
  ]
}
```

### Image Content

```typescript
{
  "content": [
    {
      "type": "image",
      "data": "base64-encoded-image-data",
      "mimeType": "image/png"
    }
  ]
}
```

### Resource Reference

```typescript
{
  "content": [
    {
      "type": "resource",
      "resource": {
        "uri": "file:///data/results.json",
        "mimeType": "application/json",
        "text": "{\"results\": [...]}"
      }
    }
  ]
}
```

## Tool Implementation Patterns

### Database Query Tool

```typescript
// TypeScript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "query_database") {
    const { table, filter, limit } = request.params.arguments as {
      table: string;
      filter?: Record<string, any>;
      limit?: number;
    };

    // Validate table name (prevent SQL injection)
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(table)) {
      throw new McpError(ErrorCode.InvalidParams, "Invalid table name");
    }

    const results = await db.query(table, filter, limit || 10);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(results, null, 2),
        },
      ],
    };
  }
});
```

```python
# Python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_database":
        args = QueryArgs(**arguments)  # Pydantic validation

        # Validate table name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', args.table):
            raise ValueError("Invalid table name")

        results = await db.query(args.table, args.filter, args.limit)

        return [
            TextContent(type="text", text=json.dumps(results, indent=2))
        ]
```

### File System Tool

```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "read_file") {
    const { path } = request.params.arguments as { path: string };

    // Security: validate path is within allowed directory
    const safePath = resolvePath(ALLOWED_DIR, path);
    if (!safePath.startsWith(ALLOWED_DIR)) {
      throw new McpError(ErrorCode.InvalidParams, "Access denied");
    }

    const content = await fs.readFile(safePath, "utf-8");

    return {
      content: [{ type: "text", text: content }],
    };
  }
});
```

### HTTP API Tool

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "fetch_api":
        args = FetchArgs(**arguments)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    args.url,
                    timeout=30.0,
                    headers={"User-Agent": "MCP Server"}
                )
                response.raise_for_status()

                return [
                    TextContent(
                        type="text",
                        text=response.text
                    )
                ]
            except httpx.HTTPError as e:
                raise McpError(INTERNAL_ERROR, f"HTTP request failed: {e}")
```

### Async Background Task

```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "start_job") {
    const { jobType, params } = request.params.arguments as {
      jobType: string;
      params: Record<string, any>;
    };

    // Start job asynchronously
    const jobId = await jobQueue.enqueue(jobType, params);

    return {
      content: [
        {
          type: "text",
          text: `Job started with ID: ${jobId}`,
        },
      ],
    };
  }

  if (request.params.name === "check_job") {
    const { jobId } = request.params.arguments as { jobId: string };

    const status = await jobQueue.getStatus(jobId);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(status, null, 2),
        },
      ],
    };
  }
});
```

## Best Practices

### 1. Descriptive Names and Descriptions

```typescript
// Good
{
  "name": "search_knowledge_base",
  "description": "Search the knowledge base using semantic search. Returns top 5 relevant documents with excerpts.",
  "inputSchema": { ... }
}

// Bad
{
  "name": "search",
  "description": "Search",
  "inputSchema": { ... }
}
```

### 2. Input Validation

```python
class SearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=5, ge=1, le=50)
    filters: dict[str, str] = Field(default_factory=dict)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        # Sanitize query
        return v.strip()
```

### 3. Error Handling

```typescript
try {
  const result = await executeOperation(params);
  return { content: [{ type: "text", text: result }] };
} catch (error) {
  if (error instanceof ValidationError) {
    throw new McpError(ErrorCode.InvalidParams, error.message);
  }
  if (error instanceof NotFoundError) {
    return {
      content: [{ type: "text", text: "Resource not found" }],
      isError: true,
    };
  }
  throw new McpError(ErrorCode.InternalError, `Operation failed: ${error.message}`);
}
```

### 4. Rate Limiting

```python
from asyncio import Lock
from datetime import datetime, timedelta

rate_limiter = {}
rate_limit_lock = Lock()

async def check_rate_limit(tool_name: str, limit: int = 10) -> None:
    async with rate_limit_lock:
        now = datetime.now()
        if tool_name not in rate_limiter:
            rate_limiter[tool_name] = []

        # Remove old entries
        rate_limiter[tool_name] = [
            t for t in rate_limiter[tool_name]
            if now - t < timedelta(minutes=1)
        ]

        if len(rate_limiter[tool_name]) >= limit:
            raise McpError(-32004, "Rate limit exceeded")

        rate_limiter[tool_name].append(now)
```

### 5. Idempotency

```typescript
// For operations that should be idempotent, use unique IDs
{
  "name": "create_record",
  "inputSchema": {
    "type": "object",
    "properties": {
      "idempotency_key": {
        "type": "string",
        "description": "Unique key to prevent duplicate operations"
      },
      "data": { "type": "object" }
    },
    "required": ["idempotency_key", "data"]
  }
}
```

### 6. Timeouts

```python
import asyncio

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "long_operation":
        try:
            result = await asyncio.wait_for(
                execute_operation(arguments),
                timeout=30.0  # 30 second timeout
            )
            return [TextContent(type="text", text=str(result))]
        except asyncio.TimeoutError:
            raise McpError(INTERNAL_ERROR, "Operation timed out")
```

### 7. Logging

```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const startTime = Date.now();
  console.error(`[${new Date().toISOString()}] Tool call: ${request.params.name}`);

  try {
    const result = await executeTool(request.params.name, request.params.arguments);
    const duration = Date.now() - startTime;
    console.error(`[${new Date().toISOString()}] Tool completed in ${duration}ms`);
    return result;
  } catch (error) {
    console.error(`[${new Date().toISOString()}] Tool failed:`, error);
    throw error;
  }
});
```
