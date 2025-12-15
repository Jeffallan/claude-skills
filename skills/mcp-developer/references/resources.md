# MCP Resources Reference

> Reference for: MCP Developer
> Load when: Implementing resource providers, URI schemes, content types

## Resource Basics

Resources represent data or content that can be read by AI assistants. They use URI schemes to identify content.

```typescript
{
  "uri": "file:///path/to/resource",
  "name": "Human-readable name",
  "description": "What this resource contains",
  "mimeType": "application/json"
}
```

## Common URI Schemes

### File URIs

```typescript
{
  "uri": "file:///config/settings.json",
  "name": "Application Settings",
  "mimeType": "application/json"
}

{
  "uri": "file:///docs/README.md",
  "name": "README Documentation",
  "mimeType": "text/markdown"
}
```

### Custom Schemes

```typescript
// Database resources
{
  "uri": "db://users/schema",
  "name": "Users Table Schema",
  "mimeType": "text/plain"
}

// API resources
{
  "uri": "api://v1/status",
  "name": "API Status",
  "mimeType": "application/json"
}

// Git resources
{
  "uri": "git://main/commits",
  "name": "Recent Commits",
  "mimeType": "text/plain"
}
```

## Resource Templates

Templates allow dynamic URIs with parameters.

```typescript
// TypeScript
server.setRequestHandler(ListResourceTemplatesRequestSchema, async () => {
  return {
    resourceTemplates: [
      {
        uriTemplate: "user://{user_id}/profile",
        name: "User Profile",
        description: "Get user profile by ID",
        mimeType: "application/json",
      },
      {
        uriTemplate: "repo://{owner}/{repo}/issues",
        name: "GitHub Issues",
        description: "List issues for a repository",
        mimeType: "application/json",
      },
    ],
  };
});

// Handle templated URIs in read_resource
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  // Parse user profile URI
  const userMatch = uri.match(/^user:\/\/([^/]+)\/profile$/);
  if (userMatch) {
    const userId = userMatch[1];
    const profile = await getUserProfile(userId);
    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(profile, null, 2),
        },
      ],
    };
  }

  // Parse GitHub issues URI
  const repoMatch = uri.match(/^repo:\/\/([^/]+)\/([^/]+)\/issues$/);
  if (repoMatch) {
    const [, owner, repo] = repoMatch;
    const issues = await fetchGitHubIssues(owner, repo);
    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(issues, null, 2),
        },
      ],
    };
  }

  throw new Error(`Unknown resource: ${uri}`);
});
```

```python
# Python
@app.list_resource_templates()
async def list_resource_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate="user://{user_id}/profile",
            name="User Profile",
            description="Get user profile by ID",
            mimeType="application/json",
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    # Parse template URI
    import re

    match = re.match(r'^user://([^/]+)/profile$', uri)
    if match:
        user_id = match.group(1)
        profile = await get_user_profile(user_id)
        return json.dumps(profile, indent=2)

    raise ValueError(f"Unknown resource: {uri}")
```

## Content Types

### Text Content

```typescript
{
  "uri": "file:///data.txt",
  "mimeType": "text/plain",
  "text": "The content of the file"
}
```

### JSON Content

```typescript
{
  "uri": "api://status",
  "mimeType": "application/json",
  "text": JSON.stringify({
    "status": "ok",
    "uptime": 12345
  }, null, 2)
}
```

### Binary Content (Base64)

```typescript
{
  "uri": "file:///image.png",
  "mimeType": "image/png",
  "blob": "base64-encoded-data-here"
}
```

### Markdown Content

```typescript
{
  "uri": "docs://api-reference",
  "mimeType": "text/markdown",
  "text": "# API Reference\n\n## Endpoints\n..."
}
```

## Implementation Patterns

### File System Resources

```typescript
import * as fs from "fs/promises";
import * as path from "path";

const ALLOWED_DIR = "/path/to/allowed/directory";

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  const files = await fs.readdir(ALLOWED_DIR);

  return {
    resources: files.map((file) => ({
      uri: `file:///${file}`,
      name: file,
      description: `File: ${file}`,
      mimeType: getMimeType(file),
    })),
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  if (uri.startsWith("file:///")) {
    const filename = uri.slice(8); // Remove "file:///"
    const safePath = path.resolve(ALLOWED_DIR, filename);

    // Security: ensure path is within allowed directory
    if (!safePath.startsWith(ALLOWED_DIR)) {
      throw new McpError(ErrorCode.InvalidParams, "Access denied");
    }

    const content = await fs.readFile(safePath, "utf-8");

    return {
      contents: [
        {
          uri,
          mimeType: getMimeType(filename),
          text: content,
        },
      ],
    };
  }

  throw new Error(`Unknown resource: ${uri}`);
});
```

### Database Resources

```python
@app.list_resources()
async def list_resources() -> list[Resource]:
    tables = await db.get_tables()

    return [
        Resource(
            uri=f"db://{table}/schema",
            name=f"{table} Schema",
            description=f"Schema for {table} table",
            mimeType="text/plain",
        )
        for table in tables
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri.startswith("db://"):
        parts = uri[5:].split("/")
        table = parts[0]
        resource_type = parts[1] if len(parts) > 1 else "data"

        if resource_type == "schema":
            schema = await db.get_schema(table)
            return schema

        if resource_type == "data":
            rows = await db.query(f"SELECT * FROM {table} LIMIT 100")
            return json.dumps(rows, indent=2)

    raise ValueError(f"Unknown resource: {uri}")
```

### API Resources

```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "api://v1/status",
        name: "API Status",
        mimeType: "application/json",
      },
      {
        uri: "api://v1/metrics",
        name: "API Metrics",
        mimeType: "application/json",
      },
    ],
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  if (uri === "api://v1/status") {
    const status = await checkApiStatus();
    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(status, null, 2),
        },
      ],
    };
  }

  if (uri === "api://v1/metrics") {
    const metrics = await collectMetrics();
    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(metrics, null, 2),
        },
      ],
    };
  }

  throw new Error(`Unknown resource: ${uri}`);
});
```

### Git Repository Resources

```python
import git

@app.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="git://log",
            name="Git Log",
            description="Recent commits",
            mimeType="text/plain",
        ),
        Resource(
            uri="git://status",
            name="Git Status",
            description="Working tree status",
            mimeType="text/plain",
        ),
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    repo = git.Repo(".")

    if uri == "git://log":
        log = repo.git.log("--oneline", "-n", "10")
        return log

    if uri == "git://status":
        status = repo.git.status()
        return status

    raise ValueError(f"Unknown resource: {uri}")
```

## Resource Subscriptions

Allow clients to subscribe to resource updates.

```typescript
// Declare subscription capability
const server = new Server(
  { name: "example", version: "1.0.0" },
  {
    capabilities: {
      resources: {
        subscribe: true,
        listChanged: true,
      },
    },
  }
);

// Track subscriptions
const subscriptions = new Set<string>();

server.setRequestHandler(SubscribeRequestSchema, async (request) => {
  subscriptions.add(request.params.uri);
  return {};
});

server.setRequestHandler(UnsubscribeRequestSchema, async (request) => {
  subscriptions.delete(request.params.uri);
  return {};
});

// Notify subscribers when resource changes
async function notifyResourceUpdate(uri: string) {
  if (subscriptions.has(uri)) {
    await server.notification({
      method: "notifications/resources/updated",
      params: { uri },
    });
  }
}

// Example: file watcher
const watcher = fs.watch(WATCHED_DIR, async (event, filename) => {
  if (event === "change") {
    const uri = `file:///${filename}`;
    await notifyResourceUpdate(uri);
  }
});
```

## Best Practices

### 1. URI Design

```typescript
// Good: Hierarchical and descriptive
"db://users/schema"
"db://users/data"
"api://v1/endpoints/users"
"file:///config/app.json"

// Bad: Flat and ambiguous
"db1"
"data"
"config"
```

### 2. MIME Types

```typescript
function getMimeType(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase();

  const mimeTypes: Record<string, string> = {
    json: "application/json",
    txt: "text/plain",
    md: "text/markdown",
    html: "text/html",
    xml: "application/xml",
    csv: "text/csv",
    png: "image/png",
    jpg: "image/jpeg",
    pdf: "application/pdf",
  };

  return mimeTypes[ext || ""] || "application/octet-stream";
}
```

### 3. Security

```python
def is_safe_path(base_dir: str, path: str) -> bool:
    """Ensure path doesn't escape base directory"""
    base = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base_dir, path))
    return target.startswith(base)

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri.startswith("file:///"):
        path = uri[8:]
        if not is_safe_path(ALLOWED_DIR, path):
            raise ValueError("Access denied")

        full_path = os.path.join(ALLOWED_DIR, path)
        with open(full_path) as f:
            return f.read()
```

### 4. Caching

```typescript
const resourceCache = new Map<string, { content: string; timestamp: number }>();
const CACHE_TTL = 60000; // 1 minute

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;
  const now = Date.now();

  // Check cache
  const cached = resourceCache.get(uri);
  if (cached && now - cached.timestamp < CACHE_TTL) {
    return {
      contents: [{ uri, mimeType: "application/json", text: cached.content }],
    };
  }

  // Fetch and cache
  const content = await fetchResource(uri);
  resourceCache.set(uri, { content, timestamp: now });

  return {
    contents: [{ uri, mimeType: "application/json", text: content }],
  };
});
```

### 5. Large Resources

```python
@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "db://logs/recent":
        # For large datasets, limit size
        logs = await db.query(
            "SELECT * FROM logs ORDER BY timestamp DESC LIMIT 1000"
        )
        return json.dumps(logs, indent=2)

    if uri == "file:///large.txt":
        # Read first 100KB only
        with open("/path/to/large.txt") as f:
            content = f.read(100 * 1024)
            if f.read(1):  # Check if there's more
                content += "\n\n[Content truncated...]"
            return content
```

### 6. Error Handling

```typescript
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  try {
    const content = await fetchResource(request.params.uri);
    return {
      contents: [
        {
          uri: request.params.uri,
          mimeType: "application/json",
          text: content,
        },
      ],
    };
  } catch (error) {
    if (error instanceof NotFoundError) {
      throw new McpError(ErrorCode.InvalidParams, `Resource not found: ${request.params.uri}`);
    }
    throw new McpError(ErrorCode.InternalError, `Failed to read resource: ${error.message}`);
  }
});
```
