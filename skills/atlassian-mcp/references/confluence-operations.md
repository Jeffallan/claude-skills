# Confluence Operations

> Reference for: Atlassian MCP Expert
> Load when: CQL search, page creation, spaces, comments, content management

---

## CQL Fundamentals

### Basic Query Structure

```
field OPERATOR value [AND|OR field OPERATOR value]
```

### Common Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Exact match | `space = "DEV"` |
| `!=` | Not equal | `type != attachment` |
| `~` | Contains | `title ~ "API"` |
| `!~` | Does not contain | `text !~ "deprecated"` |
| `>`, `<`, `>=`, `<=` | Comparison | `lastModified >= "2024-01-01"` |
| `IN` | Multiple values | `space IN ("DEV", "OPS")` |
| `NOT IN` | Exclude | `creator NOT IN ("bot")` |

### Field Reference

**Content Fields:**
```cql
type = page                        -- Pages only
type = blogpost                    -- Blog posts
type = attachment                  -- Attachments
type = comment                     -- Comments
space = "DEVDOCS"                  -- Specific space
space.type = global                -- Global spaces
space.type = personal              -- Personal spaces
```

**Search Fields:**
```cql
title ~ "architecture"             -- Title contains
text ~ "kubernetes"                -- Full text search
content ~ "deployment"             -- Content body
label = "official"                 -- Has label
label IN ("api", "reference")      -- Multiple labels
```

**Date Fields:**
```cql
created >= "2024-01-01"            -- Created after date
lastModified >= now("-30d")        -- Modified in last 30 days
created >= startOfYear()           -- Created this year
lastModified >= startOfMonth()     -- Modified this month
```

**User Fields:**
```cql
creator = currentUser()            -- Created by me
contributor = "john.doe"           -- Edited by user
mention = currentUser()            -- Mentions me
watcher = currentUser()            -- Pages I watch
favourite = currentUser()          -- My favorites
```

## Essential CQL Patterns

### Documentation Search

```cql
-- API documentation in dev space
space = "DEV" AND label = "api-docs" AND type = page

-- Recently updated architecture docs
label = "architecture" AND lastModified >= now("-7d")

-- Search for code examples
text ~ "```" AND label = "tutorial"

-- Find outdated documentation
label = "needs-review" OR lastModified <= now("-180d")

-- Meeting notes from this month
label = "meeting-notes" AND created >= startOfMonth()
```

### Space Management

```cql
-- All pages in multiple spaces
space IN ("DEV", "OPS", "PRODUCT") AND type = page

-- Personal space content
space.type = personal AND creator = currentUser()

-- Archived content
label = "archived" AND space = "LEGACY"

-- Templates
type = page AND label = "template"
```

### Content Discovery

```cql
-- Popular pages (frequently viewed)
type = page AND space = "DOCS" ORDER BY lastModified DESC

-- Draft pages
label = "draft" AND type = page

-- Pages without labels
type = page AND space = "DEV" AND label IS NULL

-- Orphan pages (no parent)
type = page AND ancestor IS NULL AND space = "DOCS"
```

## MCP Tool Calls

### Searching Content

```typescript
// Basic CQL search
const searchResult = await client.callTool({
  name: "confluence_search",
  arguments: {
    cql: 'space = "DEV" AND label = "api-docs"',
    limit: 25,
    expand: ["body.storage", "version", "ancestors"]
  }
});

// Parse results
const results = JSON.parse(searchResult.content[0].text);
for (const page of results.results) {
  console.log(`${page.title} - ${page._links.webui}`);
}

// Search with content preview
const searchWithContent = await client.callTool({
  name: "confluence_search",
  arguments: {
    cql: 'text ~ "deployment" AND space = "OPS"',
    limit: 10,
    excerpt: true
  }
});
```

### Getting Page Content

```typescript
// Get page by ID
const page = await client.callTool({
  name: "confluence_get_page",
  arguments: {
    page_id: "123456",
    expand: ["body.storage", "body.view", "version", "ancestors", "children.page"]
  }
});

// Get page by space and title
const pageByTitle = await client.callTool({
  name: "confluence_get_page_by_title",
  arguments: {
    space_key: "DEV",
    title: "API Reference"
  }
});

// Get page children
const children = await client.callTool({
  name: "confluence_get_children",
  arguments: {
    page_id: "123456",
    expand: ["page"]
  }
});
```

### Creating Pages

```typescript
// Create page with storage format (XHTML)
const newPage = await client.callTool({
  name: "confluence_create_page",
  arguments: {
    space_key: "DEV",
    title: "API Authentication Guide",
    parent_id: "123456",  // Optional parent page
    body: `
      <h2>Overview</h2>
      <p>This guide covers authentication methods for our API.</p>

      <h2>OAuth 2.0</h2>
      <p>We support OAuth 2.0 with the following grant types:</p>
      <ul>
        <li>Authorization Code</li>
        <li>Client Credentials</li>
      </ul>

      <ac:structured-macro ac:name="code">
        <ac:parameter ac:name="language">bash</ac:parameter>
        <ac:plain-text-body><![CDATA[curl -X POST https://api.example.com/oauth/token \\
  -d "grant_type=client_credentials" \\
  -d "client_id=YOUR_CLIENT_ID" \\
  -d "client_secret=YOUR_SECRET"]]></ac:plain-text-body>
      </ac:structured-macro>

      <h2>API Tokens</h2>
      <p>For simple integrations, use API tokens:</p>
      <ac:structured-macro ac:name="info">
        <ac:rich-text-body>
          <p>API tokens are tied to your user account and have the same permissions.</p>
        </ac:rich-text-body>
      </ac:structured-macro>
    `,
    labels: ["api-docs", "authentication", "official"]
  }
});

console.log(`Created page: ${newPage.content[0].text}`);
```

### Updating Pages

```typescript
// Update page content
await client.callTool({
  name: "confluence_update_page",
  arguments: {
    page_id: "123456",
    title: "API Authentication Guide (Updated)",
    body: "<h2>Updated Content</h2><p>New documentation here...</p>",
    version_number: 5,  // Current version + 1
    version_message: "Added OAuth 2.1 section"
  }
});

// Append to existing page
const currentPage = await client.callTool({
  name: "confluence_get_page",
  arguments: {
    page_id: "123456",
    expand: ["body.storage", "version"]
  }
});

const pageData = JSON.parse(currentPage.content[0].text);
const currentBody = pageData.body.storage.value;
const newSection = `
  <h2>New Section</h2>
  <p>Additional content appended to the page.</p>
`;

await client.callTool({
  name: "confluence_update_page",
  arguments: {
    page_id: "123456",
    title: pageData.title,
    body: currentBody + newSection,
    version_number: pageData.version.number + 1
  }
});
```

### Working with Comments

```typescript
// Add comment to page
await client.callTool({
  name: "confluence_add_comment",
  arguments: {
    page_id: "123456",
    body: "<p>This section needs to be updated for v2.0 changes.</p>"
  }
});

// Get page comments
const comments = await client.callTool({
  name: "confluence_get_comments",
  arguments: {
    page_id: "123456",
    expand: ["body.storage", "version"]
  }
});

// Reply to comment
await client.callTool({
  name: "confluence_add_comment",
  arguments: {
    page_id: "123456",
    parent_comment_id: "789012",
    body: "<p>Good catch! I'll update this section.</p>"
  }
});
```

### Managing Labels

```typescript
// Add labels to page
await client.callTool({
  name: "confluence_add_labels",
  arguments: {
    page_id: "123456",
    labels: ["reviewed", "q1-2024", "api-v2"]
  }
});

// Remove label
await client.callTool({
  name: "confluence_remove_label",
  arguments: {
    page_id: "123456",
    label: "draft"
  }
});

// Get page labels
const labels = await client.callTool({
  name: "confluence_get_labels",
  arguments: {
    page_id: "123456"
  }
});
```

### Space Operations

```typescript
// Get space information
const space = await client.callTool({
  name: "confluence_get_space",
  arguments: {
    space_key: "DEV",
    expand: ["description", "homepage"]
  }
});

// List all spaces
const spaces = await client.callTool({
  name: "confluence_list_spaces",
  arguments: {
    type: "global",
    limit: 100
  }
});

// Get space content
const spaceContent = await client.callTool({
  name: "confluence_get_space_content",
  arguments: {
    space_key: "DEV",
    depth: "root",  // or "all"
    expand: ["children.page"]
  }
});
```

## Storage Format Reference

### Common Macros

```xml
<!-- Code block -->
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:parameter ac:name="title">Example</ac:parameter>
  <ac:plain-text-body><![CDATA[print("Hello, World!")]]></ac:plain-text-body>
</ac:structured-macro>

<!-- Info panel -->
<ac:structured-macro ac:name="info">
  <ac:parameter ac:name="title">Note</ac:parameter>
  <ac:rich-text-body>
    <p>Important information here.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<!-- Warning panel -->
<ac:structured-macro ac:name="warning">
  <ac:rich-text-body>
    <p>Be careful with this operation!</p>
  </ac:rich-text-body>
</ac:structured-macro>

<!-- Table of contents -->
<ac:structured-macro ac:name="toc">
  <ac:parameter ac:name="maxLevel">3</ac:parameter>
</ac:structured-macro>

<!-- Jira issue link -->
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="key">PROJ-123</ac:parameter>
</ac:structured-macro>

<!-- Jira issues table -->
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="jqlQuery">project = PROJ AND sprint in openSprints()</ac:parameter>
  <ac:parameter ac:name="columns">key,summary,status,assignee</ac:parameter>
</ac:structured-macro>

<!-- Expand section -->
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Click to expand</ac:parameter>
  <ac:rich-text-body>
    <p>Hidden content here.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<!-- Include page -->
<ac:structured-macro ac:name="include">
  <ac:parameter ac:name=""><ri:page ri:content-title="Shared Footer" /></ac:parameter>
</ac:structured-macro>
```

### Formatting Elements

```xml
<!-- Status badge -->
<ac:structured-macro ac:name="status">
  <ac:parameter ac:name="colour">Green</ac:parameter>
  <ac:parameter ac:name="title">APPROVED</ac:parameter>
</ac:structured-macro>

<!-- User mention -->
<ac:link><ri:user ri:account-id="557058:f3c7..." /></ac:link>

<!-- Page link -->
<ac:link><ri:page ri:content-title="Target Page" ri:space-key="DEV" /></ac:link>

<!-- Attachment -->
<ac:link><ri:attachment ri:filename="diagram.png" /></ac:link>

<!-- Image from attachment -->
<ac:image><ri:attachment ri:filename="screenshot.png" /></ac:image>

<!-- External image -->
<ac:image><ri:url ri:value="https://example.com/image.png" /></ac:image>
```

## Pagination Handling

```typescript
async function getAllPages(cql: string): Promise<Page[]> {
  const allPages: Page[] = [];
  let start = 0;
  const limit = 100;

  while (true) {
    const result = await client.callTool({
      name: "confluence_search",
      arguments: {
        cql,
        start,
        limit,
        expand: ["body.storage"]
      }
    });

    const response = JSON.parse(result.content[0].text);
    allPages.push(...response.results);

    if (response.results.length < limit || !response._links.next) {
      break;
    }

    start += limit;
  }

  return allPages;
}
```

## Error Handling

```typescript
async function safeConfluenceCall<T>(operation: () => Promise<T>): Promise<T> {
  try {
    return await operation();
  } catch (error: any) {
    const status = error.response?.status;

    switch (status) {
      case 404:
        throw new Error(`Page or space not found: ${error.message}`);
      case 403:
        throw new Error(`Permission denied. Check space permissions.`);
      case 409:
        throw new Error(`Version conflict. Page was modified. Refresh and retry.`);
      case 429:
        const retryAfter = error.response?.headers?.['retry-after'] || 60;
        throw new Error(`Rate limited. Retry after ${retryAfter} seconds.`);
      default:
        throw error;
    }
  }
}
```

## Common Anti-Patterns

**Avoid:**
```cql
-- Too broad (slow)
text ~ "the"

-- Missing quotes
space = DEV DOCS  -- WRONG
space = "DEV DOCS"  -- CORRECT

-- Invalid date format
created >= 2024-01-01  -- WRONG
created >= "2024-01-01"  -- CORRECT
```

**Best Practices:**
- Always specify space when possible for faster queries
- Use labels for categorization and filtering
- Combine text search with specific fields
- Cache frequently accessed page content
- Handle version conflicts gracefully

## Related References

- `common-workflows.md` - Documentation sync and automation
- `jira-queries.md` - Linking Confluence pages to Jira issues
- `authentication-patterns.md` - API access configuration
