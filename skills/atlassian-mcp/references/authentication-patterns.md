# Authentication Patterns

> Reference for: Atlassian MCP Expert
> Load when: OAuth 2.0, API tokens, PAT, permission scopes, credential management

---

## Authentication Methods Overview

| Method | Platform | Use Case | Security Level |
|--------|----------|----------|----------------|
| OAuth 2.1 | Cloud | User-facing apps, integrations | Highest |
| API Token | Cloud | Personal automation, scripts | Medium |
| PAT | Server/DC | Server integrations | Medium |
| Basic Auth | Legacy | Deprecated, avoid | Low |

## OAuth 2.1 (Atlassian Cloud)

### Authorization Code Flow

For applications that act on behalf of users.

**Step 1: Register Your App**

1. Go to [developer.atlassian.com](https://developer.atlassian.com/console/myapps/)
2. Create new app
3. Configure OAuth 2.0 (3LO)
4. Add callback URL
5. Request necessary scopes

**Step 2: Authorization Request**

```typescript
const authUrl = new URL('https://auth.atlassian.com/authorize');
authUrl.searchParams.set('audience', 'api.atlassian.com');
authUrl.searchParams.set('client_id', CLIENT_ID);
authUrl.searchParams.set('scope', 'read:jira-work write:jira-work read:confluence-content.all write:confluence-content');
authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
authUrl.searchParams.set('state', generateState());
authUrl.searchParams.set('response_type', 'code');
authUrl.searchParams.set('prompt', 'consent');

// Redirect user to authUrl.toString()
```

**Step 3: Exchange Code for Token**

```typescript
async function exchangeCodeForToken(code: string): Promise<TokenResponse> {
  const response = await fetch('https://auth.atlassian.com/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      code,
      redirect_uri: REDIRECT_URI,
    }),
  });

  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.statusText}`);
  }

  return response.json();
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  scope: string;
  token_type: 'Bearer';
}
```

**Step 4: Refresh Token**

```typescript
async function refreshAccessToken(refreshToken: string): Promise<TokenResponse> {
  const response = await fetch('https://auth.atlassian.com/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      grant_type: 'refresh_token',
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      refresh_token: refreshToken,
    }),
  });

  return response.json();
}
```

**Step 5: Get Accessible Resources**

```typescript
async function getAccessibleResources(accessToken: string): Promise<Resource[]> {
  const response = await fetch(
    'https://api.atlassian.com/oauth/token/accessible-resources',
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
    }
  );

  return response.json();
}

interface Resource {
  id: string;        // Cloud ID
  name: string;      // Site name
  url: string;       // https://your-site.atlassian.net
  scopes: string[];
  avatarUrl: string;
}
```

### OAuth Scopes Reference

**Jira Scopes:**

| Scope | Description |
|-------|-------------|
| `read:jira-work` | Read issues, projects, boards |
| `write:jira-work` | Create/update issues |
| `manage:jira-project` | Manage project settings |
| `manage:jira-configuration` | Manage global settings |
| `read:jira-user` | Read user profiles |
| `manage:jira-data-provider` | Data provider integrations |

**Confluence Scopes:**

| Scope | Description |
|-------|-------------|
| `read:confluence-content.all` | Read all content |
| `write:confluence-content` | Create/update content |
| `read:confluence-content.summary` | Read content summaries |
| `read:confluence-space.summary` | Read space summaries |
| `write:confluence-space` | Create/manage spaces |
| `read:confluence-user` | Read user profiles |

**Granular Scopes (v2):**

```
read:issue-details:jira
write:issue:jira
read:sprint:jira-software
write:sprint:jira-software
read:page:confluence
write:page:confluence
read:comment:confluence
write:comment:confluence
```

## API Tokens (Atlassian Cloud)

### Creating API Token

1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a descriptive label
4. Copy token immediately (shown only once)

### Using API Token

```typescript
// Basic authentication with API token
const credentials = Buffer.from(`${email}:${apiToken}`).toString('base64');

const response = await fetch('https://your-site.atlassian.net/rest/api/3/myself', {
  headers: {
    Authorization: `Basic ${credentials}`,
    Accept: 'application/json',
  },
});

// For MCP server configuration
const config = {
  JIRA_URL: 'https://your-site.atlassian.net',
  JIRA_USERNAME: 'your-email@company.com',
  JIRA_API_TOKEN: 'your-api-token',
};
```

### Token Security Best Practices

```typescript
// Store tokens securely
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

// Option 1: Environment variables (development only)
const token = process.env.ATLASSIAN_API_TOKEN;

// Option 2: GCP Secret Manager
async function getTokenFromGCP(secretName: string): Promise<string> {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: `projects/my-project/secrets/${secretName}/versions/latest`,
  });
  return version.payload?.data?.toString() || '';
}

// Option 3: AWS Secrets Manager
async function getTokenFromAWS(secretName: string): Promise<string> {
  const client = new SecretsManager({ region: 'us-east-1' });
  const response = await client.getSecretValue({ SecretId: secretName });
  return response.SecretString || '';
}

// Option 4: HashiCorp Vault
async function getTokenFromVault(path: string): Promise<string> {
  const response = await fetch(`${VAULT_ADDR}/v1/${path}`, {
    headers: { 'X-Vault-Token': VAULT_TOKEN },
  });
  const data = await response.json();
  return data.data.data.token;
}
```

## Personal Access Tokens (Server/Data Center)

### Creating PAT

**Jira Server/DC:**
1. Profile > Personal Access Tokens
2. Create token
3. Set expiration date
4. Select permissions

**Confluence Server/DC:**
1. Profile > Settings > Personal Access Tokens
2. Create token
3. Configure permissions

### Using PAT

```typescript
// Bearer token authentication
const response = await fetch('https://jira.internal.company.com/rest/api/2/myself', {
  headers: {
    Authorization: `Bearer ${personalAccessToken}`,
    Accept: 'application/json',
  },
});

// MCP server configuration
const config = {
  JIRA_URL: 'https://jira.internal.company.com',
  JIRA_PERSONAL_TOKEN: 'your-personal-access-token',
};
```

### PAT Permissions

| Permission | Jira | Confluence |
|------------|------|------------|
| Read | Browse projects, view issues | View pages |
| Write | Create/edit issues | Create/edit pages |
| Admin | Project administration | Space administration |

## Token Management

### Token Lifecycle Manager

```typescript
interface TokenInfo {
  accessToken: string;
  refreshToken?: string;
  expiresAt: Date;
  scopes: string[];
}

class TokenManager {
  private tokenInfo: TokenInfo | null = null;
  private refreshThreshold = 5 * 60 * 1000; // 5 minutes

  async getValidToken(): Promise<string> {
    if (!this.tokenInfo) {
      throw new Error('Not authenticated');
    }

    // Check if token needs refresh
    const timeUntilExpiry = this.tokenInfo.expiresAt.getTime() - Date.now();

    if (timeUntilExpiry < this.refreshThreshold) {
      await this.refreshToken();
    }

    return this.tokenInfo.accessToken;
  }

  private async refreshToken(): Promise<void> {
    if (!this.tokenInfo?.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await refreshAccessToken(this.tokenInfo.refreshToken);

    this.tokenInfo = {
      accessToken: response.access_token,
      refreshToken: response.refresh_token || this.tokenInfo.refreshToken,
      expiresAt: new Date(Date.now() + response.expires_in * 1000),
      scopes: response.scope.split(' '),
    };
  }

  isAuthenticated(): boolean {
    return this.tokenInfo !== null && this.tokenInfo.expiresAt > new Date();
  }

  getScopes(): string[] {
    return this.tokenInfo?.scopes || [];
  }

  hasScope(scope: string): boolean {
    return this.getScopes().includes(scope);
  }
}
```

### Token Rotation Strategy

```typescript
class TokenRotationManager {
  private rotationInterval = 30 * 24 * 60 * 60 * 1000; // 30 days

  async checkAndRotate(tokenCreatedAt: Date): Promise<boolean> {
    const age = Date.now() - tokenCreatedAt.getTime();

    if (age > this.rotationInterval) {
      console.warn('API token is due for rotation');
      return true;
    }

    return false;
  }

  async sendRotationReminder(email: string, tokenLabel: string): Promise<void> {
    // Integrate with your notification system
    await sendEmail({
      to: email,
      subject: 'Atlassian API Token Rotation Reminder',
      body: `Your API token "${tokenLabel}" is due for rotation.
             Please create a new token and update your integrations.`,
    });
  }
}
```

## Permission Verification

### Check Current Permissions

```typescript
async function verifyPermissions(
  client: MCPClient,
  requiredOperations: string[]
): Promise<PermissionReport> {
  const report: PermissionReport = {
    hasAllPermissions: true,
    details: [],
  };

  for (const operation of requiredOperations) {
    try {
      switch (operation) {
        case 'read:jira':
          await client.callTool({
            name: 'jira_get_issue',
            arguments: { issue_key: 'TEST-1' },
          });
          break;
        case 'write:jira':
          // Create and immediately delete a test issue
          const created = await client.callTool({
            name: 'jira_create_issue',
            arguments: {
              project_key: 'TEST',
              issue_type: 'Task',
              summary: '[Permission Test] Delete me',
            },
          });
          // Clean up
          await client.callTool({
            name: 'jira_delete_issue',
            arguments: { issue_key: JSON.parse(created.content[0].text).key },
          });
          break;
        case 'read:confluence':
          await client.callTool({
            name: 'confluence_search',
            arguments: { cql: 'type = page', limit: 1 },
          });
          break;
      }

      report.details.push({ operation, status: 'granted' });
    } catch (error: any) {
      report.hasAllPermissions = false;
      report.details.push({
        operation,
        status: 'denied',
        error: error.message,
      });
    }
  }

  return report;
}
```

## Security Checklist

### Do:
- Use OAuth 2.1 for user-facing applications
- Store secrets in dedicated secrets management systems
- Implement token rotation policies
- Use minimal required scopes
- Log authentication events (without secrets)
- Implement rate limiting at application level
- Validate tokens before use

### Don't:
- Hardcode tokens in source code
- Log tokens or secrets
- Share tokens between environments
- Use Basic Auth (deprecated)
- Request more scopes than needed
- Store tokens in browser localStorage
- Commit `.env` files with real credentials

### Environment Configuration Template

```bash
# .env.example (commit this)
ATLASSIAN_SITE_URL=https://your-site.atlassian.net
ATLASSIAN_AUTH_TYPE=oauth  # or 'api_token' or 'pat'

# OAuth settings (if using OAuth)
ATLASSIAN_CLIENT_ID=
ATLASSIAN_CLIENT_SECRET=

# API Token settings (if using API token)
ATLASSIAN_USERNAME=
ATLASSIAN_API_TOKEN=

# PAT settings (if using Server/DC)
ATLASSIAN_PERSONAL_TOKEN=
```

```bash
# .gitignore
.env
.env.local
.env.*.local
credentials.json
**/secrets/**
```

## Troubleshooting

### Common Authentication Errors

**401 Unauthorized:**
- Invalid or expired token
- Wrong authentication method
- Missing Authorization header

**403 Forbidden:**
- Token valid but lacks required scope
- Resource-level permission denied
- IP allowlist blocking request

**Token refresh fails:**
- Refresh token expired (after 90 days of inactivity)
- Client secret changed
- App permissions revoked

### Debug Authentication

```typescript
async function debugAuth(token: string): Promise<void> {
  // Check token validity
  const meResponse = await fetch(
    'https://api.atlassian.com/me',
    { headers: { Authorization: `Bearer ${token}` } }
  );

  console.log('Token status:', meResponse.status);

  if (meResponse.ok) {
    const me = await meResponse.json();
    console.log('Authenticated as:', me.email);
  }

  // Check accessible resources
  const resourcesResponse = await fetch(
    'https://api.atlassian.com/oauth/token/accessible-resources',
    { headers: { Authorization: `Bearer ${token}` } }
  );

  if (resourcesResponse.ok) {
    const resources = await resourcesResponse.json();
    console.log('Accessible sites:', resources.map((r: any) => r.name));
  }
}
```

## Related References

- `mcp-server-setup.md` - Server configuration with credentials
- `jira-queries.md` - Operations that require authentication
- `confluence-operations.md` - Content operations with auth
