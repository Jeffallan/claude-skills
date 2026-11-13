# Linear Adapter

**Status:** docs-verified, not live-tested. Calls were checked against the Linear SDK GraphQL schema (last changed 2026-11-04) and the Linear docs on 2026-11-09. No call has run against a live workspace; see Open items.

Maps every operation in `references/adapters/operations.md` to the Linear GraphQL API (`https://api.linear.app/graphql`). Use the Linear MCP server's tools when one is connected and offers the call; otherwise send the GraphQL below with the owner's API key from the environment. Never write a key into a file.

## Config

```json
{ "tracker": "linear", "linear": { "team": "ENG", "repoScope": { "label": "web-app" } } }
```

`repoScope` holds a label, or `{}` when the team holds only this repo's tickets. Every query that lists tickets adds `labels: {name: {eq: "<label>"}}` to its filter. Below, `<scope>` stands for that clause.

## Grouping

A spec's group is a Linear project named with the spec name, owned by the configured team. An issue belongs to at most one project.

## Operations

| Operation | Call | Notes |
|-----------|------|-------|
| Create | `issueCreate(input: {teamId, title, description, projectId})` | `teamId` is required; `description` is Markdown. Add the scope label through `labelIds` |
| Read | `issue(id: "<id or ENG-123>")` with `title description state{name type} labels{nodes{name}} project{id name} updatedAt` | The `ENG-123` identifier form is common but not stated in the schema text |
| List spec tickets | `issues(filter: {project: {id: {eq: "<projectId>"}}})` | Paginated connection |
| Link | `issueUpdate(id: "<id>", input: {projectId: "<projectId>"})` | |
| Unlink | `issueUpdate(id: "<id>", input: {projectId: null})` | |
| Update | Append: read `description`, then `issueUpdate(id:, input: {description: "<old>\n\n<new>"})`. Field: `issueUpdate` with `estimate` for points | Skip points when the team has estimates off |
| Comment | `commentCreate(input: {issueId, body})` | |
| Close | Find the team's `workflowStates` with `type: "completed"`, then `issueUpdate(id:, input: {stateId})` | There is no close mutation |
| Reopen | The same, with a state of type `unstarted` or `started` | Optional; `spec:complete` only reopens text tickets |
| Ensure group | Find: `projects(filter: {name: {eq: "<spec-name>"}, accessibleTeams: {some: {id: {eq: "<teamId>"}}}})`, keeping exact name matches. Create when none match: `projectCreate(input: {name: "<spec-name>", teamIds: ["<teamId>"]})`. Close the group: `projectUpdate(id:, input: {statusId})` with a `projectStatuses` entry of type `completed` | Project names are not unique. When two projects share the name, refuse and name both |
| Link groups | `projectRelationCreate(input: {projectId: "<blocking>", relatedProjectId: "<blocked>", type: "blocks", anchorType, relatedAnchorType})` | Best effort. Anchor values are undocumented and the direction is untested (Open items); only end-to-start dependencies exist. When the call fails, report it and keep the `After:` line as the record |
| List ungrouped | `issues(filter: {team: {id: {eq: "<teamId>"}}, project: {null: true}, state: {type: {nin: ["completed", "canceled", "duplicate"]}}, <scope>})` | |

Rate limits: 2,500 requests and 3,000,000 complexity points per hour per user with an API key.

## Automation to know about

Linear's GitHub integration acts on its own, per team, by default:

- A branch name, commit or PR that mentions an issue ID links it. Opening a linked PR moves the issue to In Progress; merging it moves the issue to Done.
- Magic words (`closes`, `fixes`, `resolves`, `completes`, `implements` and their forms) before an ID close the issue when the PR merges into **any** branch, not only the default one.

The workflow avoids both: branches are `spec/<spec-name>`, commits carry the neutral `Ticket: <id>` trailer, and the spec PR body lists Linear tickets as a neutral list with no magic words. Tell the owner they can also scope the team's PR automations in Linear's GitHub settings. `spec:complete` closes Linear tickets after the merge.

## Open items

- Valid `anchorType` and `relatedAnchorType` values, which project blocks the other for `type: "blocks"`, and which plans include project dependencies.
- Whether `IssueUpdateInput.projectId` is the right field (not re-read in the schema).
- Whether a PR that lists Linear IDs without magic words still links them and fires the In Progress move. If it does, the tickets are still open at that point, and the post-merge close settles their final state.
- Whether the Linear MCP server's tools cover every operation, or some need GraphQL.
