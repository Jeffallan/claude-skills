# Jira Adapter

**Status:** docs-verified, not live-tested. Endpoints were checked against the Jira Cloud platform and Jira Software OpenAPI documents on 2026-11-09. No call has run against a live site; see Open items.

Maps every operation in `references/adapters/operations.md` to Jira Cloud REST v3. Use the Atlassian MCP server's tools when one is connected and offers the call; otherwise call the endpoints below with the owner's API token from the environment. Never write a token into a file.

## Config

```json
{
  "tracker": "jira",
  "jira": { "site": "example.atlassian.net", "project": "KEY", "repoScope": { "component": "web-app" } }
}
```

`repoScope` holds a component or a label. Every query that lists tickets adds the matching clause: `component = "<name>"` or `labels = "<name>"`. Below, `<scope>` stands for that clause.

## Grouping

A spec's group is an Epic whose summary is the spec name. Tickets join it through the `parent` field. The Epic Link custom field and Parent Link are deprecated; never use them. The Agile endpoint `POST /rest/agile/1.0/epic/{epic}/issue` fails in team-managed projects, so the adapter uses `parent` everywhere.

## Operations

| Operation | Call | Notes |
|-----------|------|-------|
| Create | `POST /rest/api/3/issue` with `fields.project.key`, `fields.issuetype`, `fields.summary`, `fields.description`, optional `fields.parent: {"key": "<EPIC>"}` | The description must be Atlassian Document Format, not Markdown. Allowed fields come from `GET /rest/api/3/issue/createmeta` |
| Read | `GET /rest/api/3/issue/{key}` | Returns the current key when the issue moved |
| List spec tickets | `POST /rest/api/3/search/jql` with `jql: "parent = <EPIC> AND <scope>"`, `fields: ["key","summary","status","updated"]` | Page with `nextPageToken`; there is no `total`. Search is eventually consistent: pass tickets created in this run in `reconcileIssues` (max 50). The legacy `/rest/api/3/search` is being removed |
| Link | `PUT /rest/api/3/issue/{key}` with `{"fields": {"parent": {"key": "<EPIC>"}}}` | In team-managed projects the ticket and the Epic must be in the same project |
| Unlink | `PUT /rest/api/3/issue/{key}` with `{"fields": {"parent": null}}` | |
| Update | Append: `GET` the issue, add the new paragraphs to the end of the ADF `description`, then `PUT /rest/api/3/issue/{key}` with the whole description. Field: `PUT` with `{"fields": {"<field-id>": <value>}}` | Find the story points field ID in `GET /rest/api/3/field`; skip points when the field doesn't exist |
| Comment | `POST /rest/api/3/issue/{key}/comment` with an ADF `body` | |
| Close | `GET /rest/api/3/issue/{key}/transitions`, pick the transition whose target status is in the Done category, then `POST /rest/api/3/issue/{key}/transitions` with `{"transition": {"id": "<id>"}}` | There is no generic close. Transition IDs differ per workflow. When the transition screen has required fields the call fails; report it and let the owner close by hand |
| Reopen | The same two calls, picking a transition into a To Do or In Progress category status | Optional for Jira; `spec:complete` only reopens text tickets |
| Ensure group | Find: `POST /rest/api/3/search/jql` with `project = <KEY> AND issuetype = Epic AND summary ~ "\"<spec-name>\""`. Keep only results whose summary equals the spec name exactly. Create when none match: `POST /rest/api/3/issue` with `issuetype: {"name": "Epic"}` and the spec name as summary | `~` is a text search, so the exact filter runs client-side. When two Epics share the name, refuse and name both |
| Link groups | `POST /rest/api/3/issueLink` with `{"type": {"name": "Blocks"}, "outwardIssue": {"key": "<blocking EPIC>"}, "inwardIssue": {"key": "<blocked EPIC>"}}` | Best effort. Needs issue linking on and the Link issues permission. Link type names are site-configurable; direction is unconfirmed (Open items) |
| List ungrouped | `POST /rest/api/3/search/jql` with `project = <KEY> AND <scope> AND parent is EMPTY AND issuetype not in (Epic, subTaskIssueTypes()) AND statusCategory != Done` | `parent is EMPTY` replaces the deprecated "issues without epic" endpoint |

## Automation to know about

Jira has no closing keywords. Smart Commits (`KEY-1 #done` in a commit message, with the GitHub for Jira app installed) transition issues from commits. The workflow never writes ticket keys with `#` tokens into commits; it uses the `Ticket: <id>` trailer, so Smart Commits stay idle. `spec:complete` closes Jira tickets after the merge.

## Open items

- Which side of a "Blocks" link is the blocker when sent as `outwardIssue` and `inwardIssue`. The table assumes outward blocks inward; one test link on a scratch site settles it.
- Whether company-managed sites still require an Epic Name field when creating an Epic through the API.
- The `to.statusCategory` field shape in the transitions response was not re-read; confirm before relying on it.
- Whether the Atlassian MCP server's tools cover every operation, or some need the REST call.
- The JQL clauses beyond `parent is EMPTY` in List ungrouped were not re-read against the JQL reference.
