# Jira Queries and Operations

> Reference for: Atlassian MCP Expert
> Load when: JQL syntax, issue CRUD, sprints, boards, backlog management

---

## JQL Fundamentals

### Basic Query Structure

```
field OPERATOR value [AND|OR field OPERATOR value]
```

### Common Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Exact match | `project = "PROJ"` |
| `!=` | Not equal | `status != Done` |
| `~` | Contains (text search) | `summary ~ "login bug"` |
| `!~` | Does not contain | `description !~ "test"` |
| `>`, `<`, `>=`, `<=` | Comparison | `created >= -7d` |
| `IN` | Multiple values | `status IN (Open, "In Progress")` |
| `NOT IN` | Exclude values | `assignee NOT IN (john, jane)` |
| `IS` | Null check | `assignee IS EMPTY` |
| `IS NOT` | Not null | `resolution IS NOT EMPTY` |
| `WAS` | Historical state | `status WAS "In Progress"` |
| `CHANGED` | Field changed | `status CHANGED FROM Open` |

### Field Reference

**Standard Fields:**
```jql
project = PROJ
issuetype = Bug
status = "In Progress"
priority = High
assignee = currentUser()
reporter = "john.doe"
resolution = Unresolved
labels = backend
component = "API"
fixVersion = "2.0"
affectsVersion = "1.5"
```

**Date Fields:**
```jql
created >= -30d                    -- Last 30 days
updated >= "2024-01-01"           -- Since specific date
due <= endOfWeek()                 -- Due this week
resolved >= startOfMonth()         -- Resolved this month
```

**Text Search:**
```jql
summary ~ "authentication"         -- Summary contains
description ~ "error AND login"    -- Description search
text ~ "payment failed"            -- All text fields
comment ~ "blocked"                -- Comment contains
```

## Essential JQL Patterns

### Sprint and Backlog Queries

```jql
-- Current sprint issues
sprint in openSprints() AND project = PROJ

-- Backlog items
sprint IS EMPTY AND resolution IS EMPTY AND project = PROJ

-- Sprint completion
sprint = "Sprint 23" AND status = Done

-- Spillover from last sprint
sprint in closedSprints() AND resolution IS EMPTY

-- Ready for sprint planning
status = "Ready for Dev" AND sprint IS EMPTY
```

### Bug Tracking

```jql
-- Open bugs by priority
issuetype = Bug AND resolution IS EMPTY ORDER BY priority DESC

-- Critical production bugs
issuetype = Bug AND priority IN (Highest, High)
  AND labels = production AND resolution IS EMPTY

-- Bugs created this week
issuetype = Bug AND created >= startOfWeek()

-- Bugs without reproduction steps
issuetype = Bug AND "Reproduction Steps" IS EMPTY
  AND resolution IS EMPTY

-- Regression bugs
issuetype = Bug AND labels = regression AND fixVersion = "2.0"
```

### Team Workload

```jql
-- My open issues
assignee = currentUser() AND resolution IS EMPTY

-- Unassigned high priority
assignee IS EMPTY AND priority IN (Highest, High)
  AND resolution IS EMPTY

-- Team member workload
assignee = "jane.smith" AND sprint in openSprints()

-- Blocked issues
status = Blocked OR labels = blocked

-- Stale issues (no update in 14 days)
updated <= -14d AND resolution IS EMPTY
```

### Release Management

```jql
-- Release candidates
fixVersion = "2.0" AND status = "Ready for Release"

-- Missing fix version
resolution = Done AND fixVersion IS EMPTY AND updated >= -30d

-- Release blockers
fixVersion = "2.0" AND priority = Blocker AND resolution IS EMPTY

-- Changelog items
fixVersion = "2.0" AND resolution = Done ORDER BY issuetype
```

## MCP Tool Calls

### Searching Issues

```typescript
// Basic JQL search
const searchResult = await client.callTool({
  name: "jira_search",
  arguments: {
    jql: "project = PROJ AND sprint in openSprints()",
    max_results: 50,
    fields: ["summary", "status", "assignee", "priority"]
  }
});

// Parse response
const issues = JSON.parse(searchResult.content[0].text);
for (const issue of issues.issues) {
  console.log(`${issue.key}: ${issue.fields.summary}`);
}
```

### Getting Issue Details

```typescript
// Get single issue with all fields
const issue = await client.callTool({
  name: "jira_get_issue",
  arguments: {
    issue_key: "PROJ-123",
    expand: ["changelog", "comments", "transitions"]
  }
});

// Get issue with specific fields
const issuePartial = await client.callTool({
  name: "jira_get_issue",
  arguments: {
    issue_key: "PROJ-123",
    fields: ["summary", "description", "customfield_10001"]
  }
});
```

### Creating Issues

```typescript
// Create a bug
const newBug = await client.callTool({
  name: "jira_create_issue",
  arguments: {
    project_key: "PROJ",
    issue_type: "Bug",
    summary: "Login fails with SSO enabled",
    description: {
      type: "doc",
      version: 1,
      content: [
        {
          type: "paragraph",
          content: [{ type: "text", text: "Users cannot log in when SSO is enabled." }]
        },
        {
          type: "heading",
          attrs: { level: 3 },
          content: [{ type: "text", text: "Steps to Reproduce" }]
        },
        {
          type: "orderedList",
          content: [
            { type: "listItem", content: [{ type: "paragraph", content: [{ type: "text", text: "Enable SSO in settings" }] }] },
            { type: "listItem", content: [{ type: "paragraph", content: [{ type: "text", text: "Log out" }] }] },
            { type: "listItem", content: [{ type: "paragraph", content: [{ type: "text", text: "Attempt to log in via SSO" }] }] }
          ]
        }
      ]
    },
    priority: "High",
    labels: ["sso", "authentication", "production"],
    components: ["Authentication"],
    assignee: "jane.smith"
  }
});

console.log(`Created: ${newBug.content[0].text}`); // PROJ-456
```

### Updating Issues

```typescript
// Update issue fields
await client.callTool({
  name: "jira_update_issue",
  arguments: {
    issue_key: "PROJ-123",
    fields: {
      summary: "Updated summary",
      priority: { name: "Highest" },
      labels: ["urgent", "production"]
    }
  }
});

// Add comment
await client.callTool({
  name: "jira_add_comment",
  arguments: {
    issue_key: "PROJ-123",
    body: "Investigating this issue. Initial analysis suggests a race condition."
  }
});

// Transition issue
await client.callTool({
  name: "jira_transition_issue",
  arguments: {
    issue_key: "PROJ-123",
    transition: "In Progress"
  }
});
```

### Sprint Operations

```typescript
// Get active sprints
const sprints = await client.callTool({
  name: "jira_get_sprints",
  arguments: {
    board_id: 42,
    state: "active"
  }
});

// Move issue to sprint
await client.callTool({
  name: "jira_move_to_sprint",
  arguments: {
    sprint_id: 123,
    issue_keys: ["PROJ-100", "PROJ-101", "PROJ-102"]
  }
});

// Get sprint report
const report = await client.callTool({
  name: "jira_get_sprint_report",
  arguments: {
    board_id: 42,
    sprint_id: 123
  }
});
```

## Pagination Handling

```typescript
async function getAllIssues(jql: string): Promise<Issue[]> {
  const allIssues: Issue[] = [];
  let startAt = 0;
  const maxResults = 100;

  while (true) {
    const result = await client.callTool({
      name: "jira_search",
      arguments: {
        jql,
        start_at: startAt,
        max_results: maxResults,
        fields: ["summary", "status", "assignee"]
      }
    });

    const response = JSON.parse(result.content[0].text);
    allIssues.push(...response.issues);

    if (startAt + response.issues.length >= response.total) {
      break;
    }

    startAt += maxResults;
  }

  return allIssues;
}
```

## Bulk Operations

```typescript
// Bulk update with JQL
async function bulkUpdateLabels(jql: string, addLabels: string[]) {
  const issues = await getAllIssues(jql);

  for (const issue of issues) {
    const existingLabels = issue.fields.labels || [];
    await client.callTool({
      name: "jira_update_issue",
      arguments: {
        issue_key: issue.key,
        fields: {
          labels: [...new Set([...existingLabels, ...addLabels])]
        }
      }
    });

    // Respect rate limits
    await delay(100);
  }
}

// Usage
await bulkUpdateLabels(
  'project = PROJ AND sprint in openSprints() AND labels = backend',
  ['q4-priority', 'needs-review']
);
```

## Error Handling

```typescript
async function safeJiraCall<T>(
  operation: () => Promise<T>,
  retries = 3
): Promise<T> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const status = error.response?.status;

      // Don't retry client errors (except rate limits)
      if (status >= 400 && status < 500 && status !== 429) {
        throw error;
      }

      // Rate limited - wait and retry
      if (status === 429) {
        const retryAfter = parseInt(error.response?.headers?.['retry-after'] || '60');
        console.log(`Rate limited. Waiting ${retryAfter}s...`);
        await delay(retryAfter * 1000);
        continue;
      }

      // Server error - exponential backoff
      if (attempt < retries) {
        const backoff = Math.pow(2, attempt) * 1000;
        console.log(`Attempt ${attempt} failed. Retrying in ${backoff}ms...`);
        await delay(backoff);
      } else {
        throw error;
      }
    }
  }
  throw new Error('Unexpected end of retry loop');
}
```

## Common Anti-Patterns

**Avoid:**
```jql
-- Too broad (slow, may timeout)
project IS NOT EMPTY

-- Missing quotes for multi-word values
status = In Progress  -- WRONG
status = "In Progress"  -- CORRECT

-- Case sensitivity issues
assignee = John  -- May fail
assignee = "john.doe@company.com"  -- CORRECT

-- Inefficient ordering
ORDER BY created  -- Missing direction
ORDER BY created DESC  -- CORRECT
```

## Related References

- `common-workflows.md` - End-to-end workflow patterns
- `authentication-patterns.md` - Credential setup for API calls
- `confluence-operations.md` - Linking Jira issues to Confluence pages
