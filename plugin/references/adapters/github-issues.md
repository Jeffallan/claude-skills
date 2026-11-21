# GitHub Issues Adapter

**Status:** docs-verified on 2026-11-09; to be marked live-tested after the pilot on a private GitHub repo.

Maps every operation in `references/adapters/operations.md` to GitHub Issues through the `gh` CLI. `gh issue` covers the plain calls; `gh api` covers sub-issues and dependencies. Run `gh auth status` first; every call uses that login.

## Config

```json
{ "tracker": "github-issues", "github": { "repo": "owner/repo" } }
```

`github.repo` defaults to the `origin` remote. GitHub scopes tickets by repo already, so there is no `repoScope`.

## Grouping

A spec's group is a parent issue titled with the spec name, labelled `spec`. Tickets are its sub-issues. Milestones stay free for versions: an issue holds one milestone and milestones don't nest.

Sub-issue calls take the issue **id**, not its number. Get it with `gh api repos/{owner}/{repo}/issues/{n} --jq .id`. Sub-issues must share the parent's repository owner; a parent holds at most 100.

## Operations

| Operation | Call | Notes |
|-----------|------|-------|
| Create | `gh issue create --repo <repo> --title "<title>" --body-file <file>`; then Link when a group is given | Or GraphQL `createIssue` with `parentIssueId` to create and attach in one call |
| Read | `gh issue view <n> --repo <repo> --json number,title,body,state,labels,updatedAt,url`; parent: `gh api repos/{owner}/{repo}/issues/{n}/parent` | |
| List spec tickets | `gh api repos/{owner}/{repo}/issues/{parent}/sub_issues --paginate --jq '.[] \| {number, state, title}'` | 100 per page; one page covers a full spec |
| Link | `gh api -X POST repos/{owner}/{repo}/issues/{parent}/sub_issues -F sub_issue_id=<id>` | A ticket that already has a parent is refused unless the owner approves `replace_parent`; then add `-F replace_parent=true`. Show the current parent when asking |
| Unlink | `gh api -X DELETE repos/{owner}/{repo}/issues/{parent}/sub_issue -F sub_issue_id=<id>` | `sub_issue` is singular here |
| Update | Append: read the body, write body plus the new text to a file, `gh issue edit <n> --repo <repo> --body-file <file>`. Field: `gh issue edit` flags (`--add-label`, `--milestone`) | GitHub Issues has no points field; skip points |
| Comment | `gh issue comment <n> --repo <repo> --body-file <file>` | |
| Close | `gh issue close <n> --repo <repo> --reason completed` | |
| Reopen | `gh issue reopen <n> --repo <repo>` | Optional; `spec:complete` only reopens text tickets |
| Ensure group | Find: `gh issue list --repo <repo> --label spec --state all --search '"<spec-name>" in:title' --json number,title,id`, then keep titles equal to the spec name exactly. Create when none match: `gh issue create --title "<spec-name>" --label spec --body "Spec: <spec-name>"` | Search is fuzzy and eventually consistent, so the exact filter runs client-side and a group created in this run is kept by the ID from the create call. When two issues share the name, refuse and name both. Create the `spec` label first if it is missing |
| Link groups | `gh api -X POST repos/{owner}/{repo}/issues/{blocked}/dependencies/blocked_by -F issue_id=<blocking id>` | Native since 2025-08-21; 50 links per relationship type; needs triage permission |
| List ungrouped | `gh issue list --repo <repo> --state open --search "no:parent-issue -has:sub-issue -label:spec" --json number,title,updatedAt` | When the qualifiers are rejected, list open issues and drop those with a parent or sub-issues |

## Closing at merge

The spec PR body says `Closes #N` for each Done and Already done ticket, so GitHub closes them when the PR merges into the default branch. `spec:complete` then closes any still open and the spec issue last. Closing the parent closes no sub-issue.

## Open items

- Whether `gh issue list --search` (REST search) accepts `no:parent-issue` and `has:sub-issue`, or needs `advanced_search=true`.
- Whether a blocked-by dependency can span two repositories. Triage is single-repo, so the adapter never needs it.
