# GitHub Projects Adapter

**Status:** docs-verified on 2026-11-09; to be marked live-tested after the pilot on a private GitHub repo.

GitHub Projects (v2) adds a board on top of GitHub Issues. Tickets and groups are GitHub issues, so every operation is the one in `references/adapters/github-issues.md`, plus one step: each issue `spec:triage` groups is also added to the configured Project. Triage never creates a Project, and stays single-repo: it adds only issues from this repo, even when the Project spans several.

## Config

```json
{
  "tracker": "github-projects",
  "github": { "repo": "owner/repo", "project": "https://github.com/orgs/owner/projects/7" }
}
```

`github.project` names the Project by owner and project number (`owner/7`) or by its URL, never by title. Titles aren't unique, and the title lookup (`projectsV2(query:)`) is a search.

## Token scope

Adding items needs a token with the `project` scope, which the default `gh` login does not grant. Check with `gh auth status`; when the scope is missing, run:

```bash
gh auth refresh -s project
```

The `project` scope reaches every Project the account can write to. Prefer a fine-grained token limited to the one organization or user where you can.

## Operations

| Operation | Call | Notes |
|-----------|------|-------|
| Create | GitHub Issues Create, then add the issue to the Project | |
| Read | GitHub Issues Read | |
| List spec tickets | GitHub Issues List spec tickets | |
| Link | GitHub Issues Link, then add the ticket to the Project | |
| Unlink | GitHub Issues Unlink | The item stays in the Project |
| Update | GitHub Issues Update | Project fields (status, iteration) are never set; the workflow moves no status |
| Comment | GitHub Issues Comment | |
| Close | GitHub Issues Close | The Project's own automation may move the item; the workflow never sets a Project field |
| Reopen | GitHub Issues Reopen | |
| Ensure group | GitHub Issues Ensure group, then add the spec issue to the Project | |
| Link groups | GitHub Issues Link groups | |
| List ungrouped | GitHub Issues List ungrouped with `project:<owner>/<number>` added to the search | `project:` takes the number, never a title |

### Add an issue to the Project

```bash
# Project node ID: organization, or user(login:) for a user-owned Project
gh api graphql -f query='query($o:String!,$n:Int!){organization(login:$o){projectV2(number:$n){id}}}' -F o=<owner> -F n=<number> --jq .data.organization.projectV2.id
# Issue node ID
gh issue view <n> --repo <repo> --json id --jq .id
# Add. An issue already in the Project fails with UNPROCESSABLE "Content already exists in this project" and a null item: treat that as success
gh api graphql -f query='mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}' -F p=<project-id> -F c=<issue-node-id>
```

Add the spec issue and each sub-issue one by one; adding a parent is not known to add its sub-issues.

## Open items

- Whether adding a parent issue adds its sub-issues automatically. The adapter adds each one either way.
- Whether the Project's built-in workflows (item closed, PR merged) move items in ways `spec:complete` should expect. Seen in the pilot.
