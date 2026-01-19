# Common Workflows

> Reference for: Atlassian MCP Expert
> Load when: Issue triage, documentation sync, sprint automation, end-to-end patterns

---

## Issue Triage Workflow

Automatically categorize, prioritize, and route incoming issues.

### Triage Bot Implementation

```typescript
interface TriageResult {
  issueKey: string;
  category: string;
  priority: string;
  assignee: string | null;
  labels: string[];
  actions: string[];
}

async function triageNewIssue(
  client: MCPClient,
  issueKey: string
): Promise<TriageResult> {
  // Get issue details
  const issueResult = await client.callTool({
    name: "jira_get_issue",
    arguments: {
      issue_key: issueKey,
      expand: ["changelog"]
    }
  });

  const issue = JSON.parse(issueResult.content[0].text);
  const result: TriageResult = {
    issueKey,
    category: "uncategorized",
    priority: issue.fields.priority?.name || "Medium",
    assignee: null,
    labels: [],
    actions: []
  };

  // Categorize based on content
  const summary = issue.fields.summary.toLowerCase();
  const description = (issue.fields.description?.content?.[0]?.content?.[0]?.text || "").toLowerCase();
  const text = `${summary} ${description}`;

  // Category detection
  if (text.match(/\b(crash|down|outage|critical|emergency)\b/)) {
    result.category = "incident";
    result.priority = "Highest";
    result.labels.push("incident", "urgent");
  } else if (text.match(/\b(bug|error|fail|broken|doesn't work)\b/)) {
    result.category = "bug";
    result.labels.push("bug", "needs-investigation");
  } else if (text.match(/\b(feature|enhancement|request|add|improve)\b/)) {
    result.category = "feature";
    result.labels.push("feature-request");
  } else if (text.match(/\b(docs|documentation|readme|guide)\b/)) {
    result.category = "documentation";
    result.labels.push("documentation");
  }

  // Component detection for routing
  const componentMap: Record<string, { component: string; team: string }> = {
    "api|rest|endpoint": { component: "API", team: "backend-team" },
    "ui|button|page|screen|css": { component: "Frontend", team: "frontend-team" },
    "database|sql|query|migration": { component: "Database", team: "data-team" },
    "auth|login|password|sso": { component: "Authentication", team: "security-team" },
    "deploy|ci|cd|pipeline": { component: "DevOps", team: "platform-team" }
  };

  for (const [pattern, { component, team }] of Object.entries(componentMap)) {
    if (text.match(new RegExp(`\\b(${pattern})\\b`))) {
      result.labels.push(component.toLowerCase());
      result.actions.push(`Route to ${team}`);
      break;
    }
  }

  // Apply triage results
  await client.callTool({
    name: "jira_update_issue",
    arguments: {
      issue_key: issueKey,
      fields: {
        priority: { name: result.priority },
        labels: [...new Set([...issue.fields.labels || [], ...result.labels])]
      }
    }
  });

  // Add triage comment
  await client.callTool({
    name: "jira_add_comment",
    arguments: {
      issue_key: issueKey,
      body: `*Automated Triage Results*

Category: ${result.category}
Priority: ${result.priority}
Labels added: ${result.labels.join(", ")}

${result.actions.length > 0 ? `Recommended actions:\n${result.actions.map(a => `- ${a}`).join("\n")}` : ""}`
    }
  });

  return result;
}
```

### Bulk Triage New Issues

```typescript
async function triageBacklog(client: MCPClient, projectKey: string): Promise<void> {
  // Find untriaged issues
  const searchResult = await client.callTool({
    name: "jira_search",
    arguments: {
      jql: `project = ${projectKey} AND labels IS EMPTY AND created >= -7d AND resolution IS EMPTY`,
      max_results: 50,
      fields: ["summary", "description", "priority", "labels"]
    }
  });

  const response = JSON.parse(searchResult.content[0].text);
  console.log(`Found ${response.total} issues to triage`);

  for (const issue of response.issues) {
    const result = await triageNewIssue(client, issue.key);
    console.log(`Triaged ${issue.key}: ${result.category} (${result.priority})`);

    // Rate limiting
    await delay(500);
  }
}
```

## Documentation Sync Workflow

Keep Confluence documentation in sync with Jira issues.

### Generate Release Notes

```typescript
async function generateReleaseNotes(
  client: MCPClient,
  projectKey: string,
  version: string,
  confluenceSpaceKey: string
): Promise<string> {
  // Get all issues in the release
  const searchResult = await client.callTool({
    name: "jira_search",
    arguments: {
      jql: `project = ${projectKey} AND fixVersion = "${version}" AND resolution = Done ORDER BY issuetype, priority DESC`,
      max_results: 200,
      fields: ["summary", "issuetype", "priority", "assignee", "labels"]
    }
  });

  const response = JSON.parse(searchResult.content[0].text);

  // Group by issue type
  const grouped: Record<string, any[]> = {};
  for (const issue of response.issues) {
    const type = issue.fields.issuetype.name;
    if (!grouped[type]) grouped[type] = [];
    grouped[type].push(issue);
  }

  // Build Confluence page content
  let content = `
<h2>Release ${version}</h2>
<p>Released on ${new Date().toISOString().split('T')[0]}</p>

<ac:structured-macro ac:name="toc">
  <ac:parameter ac:name="maxLevel">2</ac:parameter>
</ac:structured-macro>

<h2>Summary</h2>
<p>This release includes ${response.total} changes.</p>
<table>
  <tr><th>Type</th><th>Count</th></tr>
  ${Object.entries(grouped).map(([type, issues]) =>
    `<tr><td>${type}</td><td>${issues.length}</td></tr>`
  ).join('')}
</table>
`;

  // Add sections for each issue type
  const typeOrder = ["New Feature", "Improvement", "Bug", "Task"];
  const orderedTypes = [...new Set([...typeOrder, ...Object.keys(grouped)])];

  for (const type of orderedTypes) {
    if (!grouped[type]) continue;

    content += `
<h2>${type}s</h2>
<table>
  <tr><th>Key</th><th>Summary</th><th>Assignee</th></tr>
  ${grouped[type].map(issue => `
    <tr>
      <td><ac:structured-macro ac:name="jira"><ac:parameter ac:name="key">${issue.key}</ac:parameter></ac:structured-macro></td>
      <td>${escapeHtml(issue.fields.summary)}</td>
      <td>${issue.fields.assignee?.displayName || 'Unassigned'}</td>
    </tr>
  `).join('')}
</table>
`;
  }

  // Create or update Confluence page
  const pageTitle = `Release Notes - ${version}`;

  // Check if page exists
  const existingSearch = await client.callTool({
    name: "confluence_search",
    arguments: {
      cql: `space = "${confluenceSpaceKey}" AND title = "${pageTitle}"`,
      limit: 1
    }
  });

  const existingResults = JSON.parse(existingSearch.content[0].text);

  if (existingResults.results.length > 0) {
    // Update existing page
    const pageId = existingResults.results[0].id;
    const currentVersion = existingResults.results[0].version.number;

    await client.callTool({
      name: "confluence_update_page",
      arguments: {
        page_id: pageId,
        title: pageTitle,
        body: content,
        version_number: currentVersion + 1,
        version_message: `Updated release notes for ${version}`
      }
    });

    return pageId;
  } else {
    // Create new page
    const newPage = await client.callTool({
      name: "confluence_create_page",
      arguments: {
        space_key: confluenceSpaceKey,
        title: pageTitle,
        body: content,
        labels: ["release-notes", `version-${version.replace(/\./g, '-')}`]
      }
    });

    return JSON.parse(newPage.content[0].text).id;
  }
}
```

### Sync Meeting Notes to Jira

```typescript
interface ActionItem {
  description: string;
  assignee: string;
  dueDate?: string;
}

async function syncMeetingNotes(
  client: MCPClient,
  confluencePageId: string,
  jiraProjectKey: string
): Promise<string[]> {
  // Get meeting notes content
  const pageResult = await client.callTool({
    name: "confluence_get_page",
    arguments: {
      page_id: confluencePageId,
      expand: ["body.storage"]
    }
  });

  const page = JSON.parse(pageResult.content[0].text);
  const content = page.body.storage.value;

  // Extract action items (look for checkbox patterns)
  const actionItems = extractActionItems(content);
  const createdIssues: string[] = [];

  for (const item of actionItems) {
    // Create Jira task
    const newIssue = await client.callTool({
      name: "jira_create_issue",
      arguments: {
        project_key: jiraProjectKey,
        issue_type: "Task",
        summary: item.description,
        description: {
          type: "doc",
          version: 1,
          content: [{
            type: "paragraph",
            content: [{
              type: "text",
              text: `Action item from meeting: ${page.title}\n\nSource: ${page._links.webui}`
            }]
          }]
        },
        assignee: item.assignee,
        due_date: item.dueDate,
        labels: ["meeting-action", "auto-created"]
      }
    });

    const issueKey = JSON.parse(newIssue.content[0].text).key;
    createdIssues.push(issueKey);
  }

  // Update Confluence page with Jira links
  if (createdIssues.length > 0) {
    const jiraLinksSection = `
<h2>Linked Jira Issues</h2>
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="jqlQuery">key IN (${createdIssues.join(',')})</ac:parameter>
  <ac:parameter ac:name="columns">key,summary,status,assignee</ac:parameter>
</ac:structured-macro>
`;

    await client.callTool({
      name: "confluence_update_page",
      arguments: {
        page_id: confluencePageId,
        title: page.title,
        body: content + jiraLinksSection,
        version_number: page.version.number + 1
      }
    });
  }

  return createdIssues;
}

function extractActionItems(html: string): ActionItem[] {
  // Parse action items from common patterns
  const items: ActionItem[] = [];

  // Pattern: [x] or [ ] followed by @mention and task description
  const taskPattern = /\[[ x]\]\s*@([a-zA-Z.]+)\s*[-:]\s*(.+?)(?=<|$)/gi;
  let match;

  while ((match = taskPattern.exec(html)) !== null) {
    items.push({
      assignee: match[1],
      description: match[2].trim()
    });
  }

  return items;
}
```

## Sprint Automation Workflow

Automate sprint ceremonies and reporting.

### Sprint Planning Assistant

```typescript
interface SprintPlanningReport {
  totalPoints: number;
  byAssignee: Record<string, number>;
  byComponent: Record<string, number>;
  riskyItems: string[];
  recommendations: string[];
}

async function analyzeSprintPlanning(
  client: MCPClient,
  boardId: number,
  sprintId: number
): Promise<SprintPlanningReport> {
  // Get sprint issues
  const searchResult = await client.callTool({
    name: "jira_search",
    arguments: {
      jql: `sprint = ${sprintId}`,
      max_results: 100,
      fields: ["summary", "assignee", "customfield_10001", "components", "labels", "priority"]
    }
  });

  const response = JSON.parse(searchResult.content[0].text);
  const issues = response.issues;

  const report: SprintPlanningReport = {
    totalPoints: 0,
    byAssignee: {},
    byComponent: {},
    riskyItems: [],
    recommendations: []
  };

  for (const issue of issues) {
    const points = issue.fields.customfield_10001 || 0; // Story points
    const assignee = issue.fields.assignee?.displayName || "Unassigned";
    const components = issue.fields.components?.map((c: any) => c.name) || ["No Component"];

    report.totalPoints += points;
    report.byAssignee[assignee] = (report.byAssignee[assignee] || 0) + points;

    for (const component of components) {
      report.byComponent[component] = (report.byComponent[component] || 0) + points;
    }

    // Identify risks
    if (points === 0) {
      report.riskyItems.push(`${issue.key}: No story points estimated`);
    }
    if (points >= 8) {
      report.riskyItems.push(`${issue.key}: Large story (${points} points) - consider breaking down`);
    }
    if (assignee === "Unassigned") {
      report.riskyItems.push(`${issue.key}: No assignee`);
    }
  }

  // Generate recommendations
  const avgPointsPerPerson = report.totalPoints / Object.keys(report.byAssignee).length;

  for (const [assignee, points] of Object.entries(report.byAssignee)) {
    if (points > avgPointsPerPerson * 1.5) {
      report.recommendations.push(`${assignee} has ${points} points (${Math.round((points / avgPointsPerPerson - 1) * 100)}% above average) - consider rebalancing`);
    }
  }

  return report;
}
```

### Sprint Retrospective Generator

```typescript
async function generateRetroBoard(
  client: MCPClient,
  boardId: number,
  sprintId: number,
  confluenceSpaceKey: string
): Promise<string> {
  // Get completed sprint data
  const sprintResult = await client.callTool({
    name: "jira_get_sprint_report",
    arguments: {
      board_id: boardId,
      sprint_id: sprintId
    }
  });

  const sprintReport = JSON.parse(sprintResult.content[0].text);

  // Get sprint issues with details
  const issuesResult = await client.callTool({
    name: "jira_search",
    arguments: {
      jql: `sprint = ${sprintId}`,
      max_results: 100,
      fields: ["summary", "status", "resolution", "customfield_10001", "assignee"]
    }
  });

  const issues = JSON.parse(issuesResult.content[0].text).issues;

  // Calculate metrics
  const completed = issues.filter((i: any) => i.fields.resolution);
  const incomplete = issues.filter((i: any) => !i.fields.resolution);
  const completedPoints = completed.reduce((sum: number, i: any) => sum + (i.fields.customfield_10001 || 0), 0);
  const plannedPoints = issues.reduce((sum: number, i: any) => sum + (i.fields.customfield_10001 || 0), 0);

  // Create retrospective page
  const content = `
<h2>Sprint Retrospective: ${sprintReport.sprint.name}</h2>
<p><em>Generated on ${new Date().toISOString().split('T')[0]}</em></p>

<h3>Sprint Metrics</h3>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Start Date</td><td>${sprintReport.sprint.startDate}</td></tr>
  <tr><td>End Date</td><td>${sprintReport.sprint.endDate}</td></tr>
  <tr><td>Issues Planned</td><td>${issues.length}</td></tr>
  <tr><td>Issues Completed</td><td>${completed.length}</td></tr>
  <tr><td>Completion Rate</td><td>${Math.round(completed.length / issues.length * 100)}%</td></tr>
  <tr><td>Points Planned</td><td>${plannedPoints}</td></tr>
  <tr><td>Points Completed</td><td>${completedPoints}</td></tr>
  <tr><td>Velocity</td><td>${completedPoints} points</td></tr>
</table>

<h3>Completed Items</h3>
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="jqlQuery">sprint = ${sprintId} AND resolution IS NOT EMPTY</ac:parameter>
  <ac:parameter ac:name="columns">key,summary,assignee</ac:parameter>
</ac:structured-macro>

${incomplete.length > 0 ? `
<h3>Incomplete Items (Spillover)</h3>
<ac:structured-macro ac:name="warning">
  <ac:rich-text-body>
    <p>${incomplete.length} items were not completed and will spill over to the next sprint.</p>
  </ac:rich-text-body>
</ac:structured-macro>
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="jqlQuery">sprint = ${sprintId} AND resolution IS EMPTY</ac:parameter>
  <ac:parameter ac:name="columns">key,summary,assignee,status</ac:parameter>
</ac:structured-macro>
` : ''}

<h3>Discussion Points</h3>
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">What went well?</ac:parameter>
  <ac:rich-text-body>
    <ul>
      <li><em>Add team input here...</em></li>
    </ul>
  </ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">What could be improved?</ac:parameter>
  <ac:rich-text-body>
    <ul>
      <li><em>Add team input here...</em></li>
    </ul>
  </ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Action Items</ac:parameter>
  <ac:rich-text-body>
    <ac:task-list>
      <ac:task><ac:task-body><em>Add action items here...</em></ac:task-body></ac:task>
    </ac:task-list>
  </ac:rich-text-body>
</ac:structured-macro>
`;

  const newPage = await client.callTool({
    name: "confluence_create_page",
    arguments: {
      space_key: confluenceSpaceKey,
      title: `Sprint Retro - ${sprintReport.sprint.name}`,
      body: content,
      labels: ["sprint-retro", "team-meeting"]
    }
  });

  return JSON.parse(newPage.content[0].text).id;
}
```

## Issue-Documentation Link Workflow

Bidirectional linking between code changes and documentation.

### Link PR to Documentation

```typescript
async function linkPRToDocumentation(
  client: MCPClient,
  issueKey: string,
  docPageId: string
): Promise<void> {
  // Add remote link to Jira issue
  await client.callTool({
    name: "jira_add_remote_link",
    arguments: {
      issue_key: issueKey,
      url: `https://your-site.atlassian.net/wiki/spaces/DEV/pages/${docPageId}`,
      title: "Related Documentation",
      icon_url: "https://your-site.atlassian.net/wiki/favicon.ico"
    }
  });

  // Add Jira macro to Confluence page
  const pageResult = await client.callTool({
    name: "confluence_get_page",
    arguments: {
      page_id: docPageId,
      expand: ["body.storage", "version"]
    }
  });

  const page = JSON.parse(pageResult.content[0].text);

  // Check if link already exists
  if (page.body.storage.value.includes(issueKey)) {
    return; // Already linked
  }

  const jiraLink = `
<ac:structured-macro ac:name="info">
  <ac:parameter ac:name="title">Related Issue</ac:parameter>
  <ac:rich-text-body>
    <p><ac:structured-macro ac:name="jira"><ac:parameter ac:name="key">${issueKey}</ac:parameter></ac:structured-macro></p>
  </ac:rich-text-body>
</ac:structured-macro>
`;

  await client.callTool({
    name: "confluence_update_page",
    arguments: {
      page_id: docPageId,
      title: page.title,
      body: jiraLink + page.body.storage.value,
      version_number: page.version.number + 1
    }
  });
}
```

## Utility Functions

```typescript
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === maxRetries) throw error;

      const delay = baseDelay * Math.pow(2, attempt - 1);
      console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Related References

- `jira-queries.md` - JQL syntax for workflow queries
- `confluence-operations.md` - Page creation and formatting
- `authentication-patterns.md` - Secure API access for automated workflows
