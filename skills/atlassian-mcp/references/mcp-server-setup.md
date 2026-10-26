# MCP Server Setup

---

## Server Options Overview

### Atlassian Rovo MCP Server (official, recommended)

Atlassian hosts the official MCP server. There is nothing to install: clients connect over Streamable HTTP to

```
https://mcp.atlassian.com/v2/mcp
```

**Capabilities:**
- Jira, Confluence, Jira Service Management, Bitbucket Cloud, Compass, Loom, Goals, Projects, Teams, Focus, Talent and the Teamwork Graph
- OAuth 2.1 browser sign-in, or API tokens for headless clients (admin-enabled)
- Acts with the signed-in user's existing Atlassian permissions
- Tools are grouped into permission groups (`read_jira`, `write_jira`, `search_jira`, `read_confluence`, ...) that org admins grant or revoke; `delete_jira` and `manage_jira` are off by default
- Exposes a small set of primary tools and lets the client discover the rest on demand; append `?tools=all` for a flat list (useful behind MCP gateways)
- Atlassian Cloud only

**Endpoint versions:**

| Endpoint | Status |
|----------|--------|
| `https://mcp.atlassian.com/v2/mcp` | Recommended for new setups |
| `https://mcp.atlassian.com/v1/mcp`, `/v1/mcp/authv2` | Still supported; existing v1 connections start exposing v2 tools |
| `https://mcp.atlassian.com/v1/sse` | Legacy SSE endpoint, unsupported after 30 June 2026; move to `/v2/mcp` |

Sources: [atlassian/atlassian-mcp-server](https://github.com/atlassian/atlassian-mcp-server), [Getting started with the Atlassian Rovo MCP Server](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/), [Supported tools](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/).

### Community Servers

Use these only when the official server does not fit, mainly for Jira or Confluence **Server/Data Center**.

**mcp-atlassian (sooperset)** - Python, the most complete community option, and the only one here with Server/DC support. Published on PyPI as `mcp-atlassian` and as a Docker image:
```bash
# Run without installing (recommended)
uvx mcp-atlassian --help

# Or install
uv tool install mcp-atlassian
pip install mcp-atlassian

# Or Docker
docker pull ghcr.io/sooperset/mcp-atlassian:latest
```

**atlassian-mcp (xuanxt)** - TypeScript, Jira and Confluence Cloud only. Published on npm as `@xuandev/atlassian-mcp`:
```bash
npx -y @xuandev/atlassian-mcp
```

### Comparison Matrix

| Feature | Rovo MCP Server | sooperset | xuanxt |
|---------|-----------------|-----------|--------|
| Hosting | Atlassian-hosted | Self-run (stdio, Docker, HTTP) | Self-run |
| Jira / Confluence Cloud | Yes | Yes | Yes |
| Jira / Confluence Server/DC | No | Yes | No |
| Other Atlassian products | JSM, Bitbucket, Compass, Loom, Goals, ... | Jira and Confluence only | Jira and Confluence only |
| OAuth 2.1 | Yes | Yes (bring your own OAuth app) | No |
| API token | Yes, if an admin enables it | Yes | Yes |
| PAT (Server/DC) | No | Yes | No |
| Admin controls | Permission groups, domain and IP allowlists, audit log | Env vars (`READ_ONLY_MODE`, filters) | Env vars |

## Connecting to the Rovo MCP Server

### Claude Code

```bash
claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp
```

Then run `/mcp` in a session and complete the OAuth sign-in in the browser.

### Claude Desktop

Install it from **Settings → Extensions → Browse extensions → Plugins**, then search for **Atlassian**.

### Other Clients

Any client that speaks Streamable HTTP takes the server URL directly. Clients that only run local stdio servers can bridge with the [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) proxy (Node.js 18+):

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v2/mcp"]
    }
  }
}
```

### Headless: API Token Authentication

For automations and other non-interactive clients. An org admin must first enable API token authentication (**Atlassian Administration → Rovo → Rovo MCP server → Authentication**). Jira Service Management tools require it.

| Mechanism | Header |
|-----------|--------|
| Personal API token | `Authorization: Basic <base64(email:api_token)>` |
| Service account API key | `Authorization: Bearer <api_key>` |

```bash
# Build the Basic credential from environment variables; never paste tokens inline
export ATLASSIAN_BASIC_AUTH=$(printf '%s:%s' "$ATLASSIAN_EMAIL" "$ATLASSIAN_API_TOKEN" | base64 -w0)

claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp \
  --header "Authorization: Basic ${ATLASSIAN_BASIC_AUTH}"
```

Create the token with only the scopes the tools need. See [Configuring authentication via API token](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/configuring-authentication-via-api-token/).

### Admin Prerequisites

- **Domain allowlist:** OAuth connections must come from a client domain allowed under Atlassian Administration → Rovo → Rovo MCP server. Atlassian-supported clients are allowed by default.
- **IP allowlist:** if the org uses IP allowlisting, tool calls must come from an allowed IP. Hosted AI clients call from the provider's egress IPs, not the user's VPN.
- **Audit:** every tool call is logged under Insights → Audit log (filter for *Rovo MCP User Actions*).

See [Control Atlassian Rovo MCP Server settings](https://support.atlassian.com/security-and-access-policies/docs/control-atlassian-rovo-mcp-server-settings/).

## Configuring sooperset (Server/DC or Self-Hosted)

**Cloud with API token:**
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your-email@company.com",
        "CONFLUENCE_API_TOKEN": "<confluence-api-token>",
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your-email@company.com",
        "JIRA_API_TOKEN": "<jira-api-token>"
      }
    }
  }
}
```

**Server/Data Center with PAT:**
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://jira.internal.company.com",
        "JIRA_PERSONAL_TOKEN": "<jira-personal-access-token>",
        "CONFLUENCE_URL": "https://confluence.internal.company.com",
        "CONFLUENCE_PERSONAL_TOKEN": "<confluence-personal-access-token>"
      }
    }
  }
}
```

### Environment Variables Reference

From the project's [`.env.example`](https://github.com/sooperset/mcp-atlassian/blob/main/.env.example).

**Jira:**

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_URL` | Base URL of the Jira instance | Yes |
| `JIRA_USERNAME` | Account email (Cloud) | Cloud only |
| `JIRA_API_TOKEN` | API token (Cloud) | Cloud only |
| `JIRA_PERSONAL_TOKEN` | Personal access token (Server/DC) | Server/DC only |
| `JIRA_SSL_VERIFY` | Verify SSL certificates (default: true) | No |

**Confluence:**

| Variable | Description | Required |
|----------|-------------|----------|
| `CONFLUENCE_URL` | Base URL, with `/wiki` for Cloud | Yes |
| `CONFLUENCE_USERNAME` | Account email (Cloud) | Cloud only |
| `CONFLUENCE_API_TOKEN` | API token (Cloud) | Cloud only |
| `CONFLUENCE_PERSONAL_TOKEN` | Personal access token (Server/DC) | Server/DC only |
| `CONFLUENCE_SSL_VERIFY` | Verify SSL certificates (default: true) | No |

**Scope, safety and tuning:**

| Variable | Description | Default |
|----------|-------------|---------|
| `READ_ONLY_MODE` | Disable all create, update and delete tools | false |
| `JIRA_PROJECTS_FILTER` | Comma-separated Jira project keys to limit operations to | All |
| `CONFLUENCE_SPACES_FILTER` | Comma-separated Confluence space keys to limit operations to | All |
| `TOOLSETS` | Tool groups to enable (`default`, `all`, or names such as `jira_agile`) | All |
| `ENABLED_TOOLS` | Comma-separated tool names to enable | All in active toolsets |
| `JIRA_TIMEOUT` / `CONFLUENCE_TIMEOUT` | HTTP timeout in seconds | 75 |
| `ATLASSIAN_RETRY_TOTAL` | Retry attempts for read requests | Off |
| `ATLASSIAN_REQUESTS_PER_SECOND` | Client-side request rate cap | Off |
| `MCP_VERBOSE` / `MCP_VERY_VERBOSE` | INFO / DEBUG logging | WARNING |

## Tool Names Differ by Server

Each server names its tools differently. The examples in `jira-queries.md`, `confluence-operations.md` and `common-workflows.md` use sooperset's names (`jira_search`, `jira_get_issue`, ...). With the Rovo MCP Server, list the tools your client sees (or connect with `?tools=all`) and check [Supported tools](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/) before writing tool calls. Its tools take a `cloudId`; get it from `getAccessibleAtlassianResources`, or pin it in your agent instructions to skip that call.

## Verification and Testing

```bash
# Rovo MCP Server: confirm the connection and auth status
claude mcp list

# sooperset: confirm it starts and sees its environment
uvx mcp-atlassian --help
env | grep -E "^(JIRA|CONFLUENCE)_" | sed 's/=.*/=***/'
```

### Test Connection (sooperset)

```typescript
// test-connection.ts
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function testConnection(): Promise<void> {
  const transport = new StdioClientTransport({
    command: "uvx",
    args: ["mcp-atlassian"],
    env: process.env as Record<string, string>,
  });

  const client = new Client(
    { name: "test-client", version: "1.0.0" },
    { capabilities: {} }
  );

  await client.connect(transport);

  // List available tools
  const tools = await client.listTools();
  console.log("Available tools:", tools.tools.map(t => t.name));

  // Test a simple read operation
  const result = await client.callTool({
    name: "jira_get_issue",
    arguments: { issue_key: "TEST-1" }
  });
  console.log("Test result:", result);

  await client.close();
}

testConnection().catch(console.error);
```

## When to Use Each Server

**Choose the Rovo MCP Server when:**
- Using Atlassian Cloud (the default choice)
- Need products beyond Jira and Confluence
- Want OAuth without running your own OAuth app
- Need admin-managed permissions and audit logging

**Choose sooperset when:**
- Running Jira or Confluence Server/Data Center
- Need PAT authentication
- Must run the server inside your own network
- Want local controls such as `READ_ONLY_MODE` or project and space filters

**Choose xuanxt when:**
- Want a small TypeScript server for Cloud that you can fork and extend

## Troubleshooting

**Rovo MCP Server: sign-in fails after moving from v1 to v2:**
Some clients keep a cached client ID or `.well-known` credentials from v1. Clear them and authenticate again.

**Rovo MCP Server: 403 or "not allowed":**
- The client domain is not on the org's allowlist, or
- IP allowlisting blocks the caller. Hosted clients call from the provider's IPs, so being on the VPN is not enough. Ask an org admin to review both.

**Rovo MCP Server: a tool is missing:**
Its permission group is not granted (`delete_jira` and `manage_jira` are off by default), or it needs the other auth method (JSM tools need an API token, Compass tools need OAuth).

**"Authentication failed" with sooperset:**
```bash
# Verify API token is valid (Cloud)
curl -u "<email>:<api-token>" \
  "https://your-company.atlassian.net/rest/api/3/myself"

# Verify PAT is valid (Server/DC)
curl -H "Authorization: Bearer <personal-access-token>" \
  "https://jira.internal.company.com/rest/api/2/myself"
```

**Rate limited (HTTP 429) with sooperset:**
```json
{
  "mcpServers": {
    "atlassian": {
      "env": {
        "ATLASSIAN_REQUESTS_PER_SECOND": "5",
        "ATLASSIAN_RETRY_TOTAL": "5"
      }
    }
  }
}
```

**Debug logging with sooperset:**
```json
{
  "mcpServers": {
    "atlassian": {
      "env": {
        "MCP_VERY_VERBOSE": "true"
      }
    }
  }
}
```

## Security Best Practices

1. **Prefer OAuth for people, scoped API tokens for automation** - Never share one user's token across a team
2. **Never commit credentials** - Use environment variables or a secrets manager
3. **Rotate API tokens regularly** - Set calendar reminders for 90-day rotation
4. **Grant minimal permission groups** - Leave `delete_jira` and `manage_jira` off unless needed
5. **Review the audit log** - Rovo MCP tool calls are recorded per user
6. **Restrict network access** - Use domain and IP allowlists

## Related References

- `authentication-patterns.md` - OAuth 2.1 and API token setup details
- `jira-queries.md` - JQL syntax after connection is established
- `confluence-operations.md` - CQL and page operations
