# Connect Jira and Confluence to Claude Code (Atlassian MCP Setup)

An Atlassian MCP (Model Context Protocol) server connects Claude Code to Jira and Confluence, so Claude can search, read and update your issues and pages from the terminal. You can set one up in two ways:

- Atlassian's remote MCP server (the Rovo MCP Server) takes one command and a browser sign-in. It works with Atlassian Cloud only.
- The community `mcp-atlassian` server runs in Docker with API tokens. It also works with Jira and Confluence Server or Data Center, and it can limit Claude to chosen projects and spaces or run read-only.

If the Atlassian connector already works in Claude chat or Cowork and only Claude Code can't see it, go to [Atlassian Connector Works in Claude Chat but Not in Claude Code](#atlassian-connector-works-in-claude-chat-but-not-in-claude-code).

> **Workflow commands:** you need this only when your workflow tracker is Jira. Specs live in your repo, so no workflow command uses Confluence. See [Tracker Setup](TRACKER_SETUP.md#jira).

---

## Table of Contents

- [Atlassian Remote MCP Server Setup (Cloud)](#atlassian-remote-mcp-server-setup-cloud)
- [Atlassian Connector Works in Claude Chat but Not in Claude Code](#atlassian-connector-works-in-claude-chat-but-not-in-claude-code)
- [Prerequisites](#prerequisites)
- [Getting API Tokens](#getting-api-tokens)
- [Environment Setup](#environment-setup)
- [MCP Configuration](#mcp-configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

---

## Atlassian Remote MCP Server Setup (Cloud)

Atlassian hosts an official MCP server at `https://mcp.atlassian.com/v2/mcp`. It needs an Atlassian Cloud site and signs you in with OAuth, so you store no tokens. Add it to Claude Code:

```bash
claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp
```

Start `claude`, run `/mcp`, select `atlassian` and sign in to Atlassian in the browser window that opens. Claude then works with your Jira and Confluence permissions.

The command uses the default `local` scope, which makes the server available to you in the current project only. Add `--scope user` to use it in every project, or `--scope project` to save it in the project's `.mcp.json` for your teammates. Each person still signs in with their own Atlassian account.

```bash
claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v2/mcp
```

Things to know before you rely on it:

- Older guides use `https://mcp.atlassian.com/v1/sse`. Atlassian stopped supporting that endpoint after June 30, 2026, so use the v2 URL.
- If your organization restricts Atlassian Cloud to an IP allowlist, tool calls must come from an allowed address, even after a successful sign-in.
- Tool calls draw on your organization's Rovo credits.
- For Jira or Confluence Server and Data Center, use the Docker setup below.

---

## Atlassian Connector Works in Claude Chat but Not in Claude Code

Claude chat and Cowork use the connectors added at [claude.ai/customize/connectors](https://claude.ai/customize/connectors). Claude Code keeps its own list of MCP servers, and it adds your claude.ai connectors to that list only when you sign in to Claude Code with your claude.ai subscription account. If `/mcp` in Claude Code doesn't show the Atlassian connector:

1. Run `/status` in Claude Code to see which authentication method is active.
2. Claude Code skips claude.ai connectors when it authenticates with `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, an `apiKeyHelper` setting, a cloud provider such as Amazon Bedrock or Google Cloud, or a `claude setup-token` token in `CLAUDE_CODE_OAUTH_TOKEN`. Unset the variable or setting, run `/login` and choose your claude.ai account.
3. Run `/mcp` again. Connectors from claude.ai carry a claude.ai label, and one you have never signed in to sits under **Show unused connectors**.
4. If it is still missing, check that `ENABLE_CLAUDEAI_MCP_SERVERS=false` isn't set in your shell and that no settings file contains `"disableClaudeAiConnectors": true`.

On Team and Enterprise plans, an Owner adds the Atlassian connector for the organization, and each member then connects their own Atlassian account.

To keep signing in to Claude Code with an API key or a cloud provider, add Atlassian's server to Claude Code directly, as shown in [Atlassian Remote MCP Server Setup (Cloud)](#atlassian-remote-mcp-server-setup-cloud). A server you add in Claude Code takes precedence over a claude.ai connector with the same URL, and `/mcp` then lists the connector as hidden.

---

## Prerequisites

The rest of this guide sets up the community `mcp-atlassian` server in Docker. Before you start, make sure you have:

1. **Docker installed and running**
   - Verify with: `docker --version`
   - Docker must be able to pull images from `ghcr.io`

2. **Atlassian account access**
   - For Cloud: Account with access to your organization's Jira and Confluence
   - For Server/Data Center: Administrative access to generate personal access tokens

3. **Claude Code CLI installed**
   - Claude Code starts the MCP server from the configuration below

---

## Getting API Tokens

### Atlassian Cloud (Recommended)

API tokens are the standard authentication method for Atlassian Cloud products.

**Step 1: Navigate to API Token Management**

1. Go to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Sign in with your Atlassian account

**Step 2: Create a New API Token**

1. Click **Create API token**
2. Enter a descriptive label (e.g., "Claude MCP Integration")
3. Choose an expiry date between 1 and 365 days (new tokens default to one year)
4. Click **Create**
5. **Copy the token immediately**, because Atlassian will not show it again

**Step 3: Note Your Credentials**

You will need:
- **Email address**: The email associated with your Atlassian account
- **API token**: The token you just created
- **Instance URL**: Your Atlassian Cloud URL (e.g., `https://yourcompany.atlassian.net`)

One API token works for both Jira and Confluence when they are on the same Atlassian Cloud instance.

---

### Atlassian Server / Data Center

For self-hosted Atlassian products, use Personal Access Tokens (PATs).

**Jira Server/Data Center:**

1. Navigate to your Jira instance
2. Click your profile icon > **Profile**
3. Go to **Personal Access Tokens**
4. Click **Create token**
5. Set token name and expiry
6. Copy the generated token

**Confluence Server/Data Center:**

1. Navigate to your Confluence instance
2. Click your profile icon > **Settings**
3. Go to **Personal Access Tokens**
4. Click **Create token**
5. Set token name and expiry
6. Copy the generated token

---

## Environment Setup

### Step 1: Create Environment File

Create a `.env.local` file in your project root (or the directory where you will run Claude Code):

```bash
touch .env.local
```

### Step 2: Configure Environment Variables

Add the following variables to `.env.local` based on your setup:

**For Atlassian Cloud:**

```bash
# Confluence Cloud Configuration
CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_USERNAME=your.email@company.com
CONFLUENCE_API_TOKEN=your-api-token-here

# Jira Cloud Configuration
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your-api-token-here

# Optional: Limit to specific spaces/projects
# CONFLUENCE_SPACES_FILTER=DOCS,WIKI,ENG
# JIRA_PROJECTS_FILTER=PROJ,DEV,OPS

# Optional: Enable read-only mode (disables all write operations)
# READ_ONLY_MODE=true
```

**For Atlassian Server/Data Center:**

```bash
# Confluence Server Configuration
CONFLUENCE_URL=https://confluence.yourcompany.com
CONFLUENCE_PERSONAL_TOKEN=your-personal-access-token
CONFLUENCE_SSL_VERIFY=true  # Set to "false" for self-signed certificates

# Jira Server Configuration
JIRA_URL=https://jira.yourcompany.com
JIRA_PERSONAL_TOKEN=your-personal-access-token
JIRA_SSL_VERIFY=true  # Set to "false" for self-signed certificates

# Optional: Limit to specific spaces/projects
# CONFLUENCE_SPACES_FILTER=DOCS,WIKI
# JIRA_PROJECTS_FILTER=PROJ,DEV

# Optional: Enable read-only mode
# READ_ONLY_MODE=true
```

### Step 3: Verify .gitignore

Make sure `.env.local` is in your `.gitignore` so git never picks up your credentials:

```bash
# Check if .env.local is ignored
grep -q "\.env\.local" .gitignore || echo ".env.local" >> .gitignore
```

---

## MCP Configuration

### Step 1: Create MCP Configuration File

Create or update `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        ".env.local",
        "ghcr.io/sooperset/mcp-atlassian:latest"
      ]
    }
  }
}
```

### Step 2: Pull the Docker Image

Pull the image before the first run:

```bash
docker pull ghcr.io/sooperset/mcp-atlassian:latest
```

### Configuration Options

**Multiple Environment Files:**

If you have separate environment files for different purposes:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        ".env.atlassian",
        "ghcr.io/sooperset/mcp-atlassian:latest"
      ]
    }
  }
}
```

**Combining with Other MCP Servers:**

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        ".env.local",
        "ghcr.io/sooperset/mcp-atlassian:latest"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    }
  }
}
```

---

## Verification

### Step 1: Test Docker Connectivity

Verify the container can start and read your environment:

```bash
docker run --rm --env-file .env.local ghcr.io/sooperset/mcp-atlassian:latest --help
```

### Step 2: Test with Claude Code

Start Claude Code and verify the MCP server is recognized:

```bash
claude
```

Then ask Claude to list available MCP tools or perform a simple operation:

```
List the Jira projects I have access to.
```

Or:

```
Show me the recent pages in Confluence.
```

### Step 3: Verify Specific Operations

**Test Jira connectivity:**
```
What issues are in project [YOUR_PROJECT_KEY]?
```

**Test Confluence connectivity:**
```
List pages in the [YOUR_SPACE_KEY] Confluence space.
```

### Expected Behavior

When working correctly:
- Claude can list Jira projects and issues
- Claude can read and create Confluence pages
- Claude can search across both platforms
- Claude reports any permission errors clearly

---

## Troubleshooting

### Common Issues

**Issue: "Authentication failed" or "401 Unauthorized"**

Causes and solutions:
1. **Invalid API token**: Regenerate your API token from Atlassian
2. **Wrong username**: For Cloud, use your email address, not username
3. **Token expired**: Cloud API tokens last at most 365 days, and Server/DC tokens can expire too; create a new one
4. **Wrong URL format**:
   - Jira Cloud: `https://yourcompany.atlassian.net`
   - Confluence Cloud: `https://yourcompany.atlassian.net/wiki`

**Issue: "Connection refused" or "Cannot reach host"**

Causes and solutions:
1. **Docker networking**: Ensure Docker can reach external URLs
2. **VPN required**: Connect to VPN if accessing internal Atlassian Server
3. **Firewall blocking**: Check corporate firewall rules
4. **Wrong URL**: Verify the URL is accessible in your browser

**Issue: "SSL certificate verify failed"**

For self-signed certificates on Server/Data Center:
```bash
CONFLUENCE_SSL_VERIFY=false
JIRA_SSL_VERIFY=false
```

**Issue: "Permission denied" when reading/writing**

Causes and solutions:
1. **Insufficient permissions**: Your Atlassian account needs appropriate project/space permissions
2. **Read-only mode enabled**: Check if `READ_ONLY_MODE=true` is set
3. **Space/project restrictions**: Verify you have access to the specific space or project

**Issue: Docker image not found**

```bash
# Pull the latest image
docker pull ghcr.io/sooperset/mcp-atlassian:latest

# Verify it exists
docker images | grep mcp-atlassian
```

**Issue: Environment file not found**

Ensure the path in `.mcp.json` is correct:
- Use relative path from where Claude Code runs
- Or use absolute path: `/Users/yourname/project/.env.local`

### Debug Mode

To see detailed logs, run the container manually:

```bash
docker run -it --rm --env-file .env.local ghcr.io/sooperset/mcp-atlassian:latest
```

### Verifying Environment Variables

Check that your environment file is properly formatted:

```bash
# List all variables (redacted)
grep -E "^[A-Z_]+" .env.local | sed 's/=.*/=***/'
```

Expected output:
```
CONFLUENCE_URL=***
CONFLUENCE_USERNAME=***
CONFLUENCE_API_TOKEN=***
JIRA_URL=***
JIRA_USERNAME=***
JIRA_API_TOKEN=***
```

---

## Security Considerations

### Credential Protection

1. **Never commit credentials**: Ensure `.env.local` is in `.gitignore`
2. **Use environment-specific files**: Keep production and development credentials separate
3. **Rotate tokens regularly**: Set calendar reminders to rotate API tokens
4. **Use minimal permissions**: Only grant the Atlassian account permissions it needs

### Read-Only Mode

For safer exploration or demo environments:

```bash
READ_ONLY_MODE=true
```

This prevents any write operations to Jira or Confluence.

### Space and Project Filtering

Limit Claude's access to specific areas:

```bash
# Only access these Confluence spaces
CONFLUENCE_SPACES_FILTER=DOCS,PUBLIC

# Only access these Jira projects
JIRA_PROJECTS_FILTER=SUPPORT,DOCS
```

### Audit Trail

All operations performed through the MCP server are:
- Logged in Atlassian's audit logs
- Associated with your Atlassian account
- Subject to your organization's compliance policies

### Token Revocation

If you suspect a token has been compromised:

1. Go to [Atlassian API Token Management](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Revoke** next to the compromised token
3. Create a new token
4. Update your `.env.local` file

---

## Environment Variable Reference

### Confluence Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CONFLUENCE_URL` | Yes | Confluence instance URL |
| `CONFLUENCE_USERNAME` | Cloud only | Email address for authentication |
| `CONFLUENCE_API_TOKEN` | Cloud only | API token from Atlassian |
| `CONFLUENCE_PERSONAL_TOKEN` | Server only | Personal access token |
| `CONFLUENCE_SSL_VERIFY` | No | Set to `false` for self-signed certs |
| `CONFLUENCE_SPACES_FILTER` | No | Comma-separated space keys to limit access |

### Jira Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JIRA_URL` | Yes | Jira instance URL |
| `JIRA_USERNAME` | Cloud only | Email address for authentication |
| `JIRA_API_TOKEN` | Cloud only | API token from Atlassian |
| `JIRA_PERSONAL_TOKEN` | Server only | Personal access token |
| `JIRA_SSL_VERIFY` | No | Set to `false` for self-signed certs |
| `JIRA_PROJECTS_FILTER` | No | Comma-separated project keys to limit access |

### Global Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `READ_ONLY_MODE` | No | Set to `true` to disable all write operations |

---

## Quick Start Checklist

- [ ] Docker installed and running
- [ ] API token created at [Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens)
- [ ] `.env.local` created with credentials
- [ ] `.env.local` added to `.gitignore`
- [ ] `.mcp.json` created with Atlassian configuration
- [ ] Docker image pulled: `docker pull ghcr.io/sooperset/mcp-atlassian:latest`
- [ ] Connection tested with Claude Code

---

## Additional Resources

- [Atlassian API Token Documentation](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
- [MCP Atlassian GitHub Repository](https://github.com/sooperset/mcp-atlassian)
- [Atlassian Rovo MCP Server](https://github.com/atlassian/atlassian-mcp-server)
- [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp), including [MCP servers from claude.ai](https://code.claude.com/docs/en/mcp#use-mcp-servers-from-claude-ai)
- [Tracker Setup](./TRACKER_SETUP.md): the Jira adapter the workflow commands use
