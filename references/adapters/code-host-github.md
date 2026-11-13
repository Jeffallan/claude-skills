# GitHub Code-Host Adapter

**Status:** docs-verified; to be marked live-tested after the pilot on a private GitHub repo.

Maps the code-host operations in `references/adapters/operations.md` to GitHub through `gh`. Only `spec:complete` uses them, attended, and every write raises the shared "ask" permission prompt. Goal runs deny all of them.

## Config

```json
{ "codeHost": { "type": "github" } }
```

The repo comes from `github.repo`, else the `origin` remote. With `codeHost.type` set to `none`, `spec:complete` prints the manual steps instead (see the end of this file).

## Operations

| Operation | Call | Notes |
|-----------|------|-------|
| Push branch | `git push -u origin spec/<spec-name>` | Shared "ask" rule |
| Open or reuse PR | Reuse: `gh pr list --head spec/<spec-name> --state open --json number,url`. Open: `gh pr create --base <default-branch> --head spec/<spec-name> --title "<title>" --body-file <file>` | Reuse an open PR for the branch; never open a second |
| Read PR feedback | Reviews: `gh pr view <n> --json reviews,reviewRequests,author`. Threads: `gh api graphql` on `pullRequest(number:){reviewThreads(first:100){nodes{id isResolved comments(first:20){nodes{author{login} body url}}}}}`. Write access per author: `gh api repos/{owner}/{repo}/collaborators/{login}/permission --jq .permission` | Only authors with `write`, `maintain` or `admin`, or requested reviewers, become findings; show the rest and never ticket them |
| Reply and resolve | Reply: `gh api graphql` `addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId, body})`. Resolve: `resolveReviewThread(input:{threadId})` | Only replies the owner approved |
| Check PR | `gh pr view <n> --json statusCheckRollup,reviewDecision,mergeable` plus the unresolved-thread count from Read PR feedback | Clear means: every check passed, `reviewDecision` is `APPROVED`, no change requests, no unresolved threads. A solo owner can't approve their own PR: when `gh api repos/{owner}/{repo}/collaborators --jq '[.[] \| select(.permissions.push)] \| length'` is 1, an empty `reviewDecision` counts as clear and the merge question is the approval |
| Merge PR | `gh pr merge <n> --merge` (or the repo's required method) | Only after the owner answers yes to "Merge PR #N now?" |

## PR body

The body is the record of what the merge closes:

- `Closes #N` for each Done and Already done GitHub ticket.
- A neutral list (`- ENG-123: <title>`) for Jira, Linear and text tickets, with no closing words.
- Blocked tickets listed under "Still open", so the merge never closes them.
- PR-feedback fix tickets listed by local ID (`<spec-name>-fb<round>-<n>`), never as closing.

## Manual steps for other hosts

When `codeHost.type` is `none`, `spec:complete` prints:

1. `git push -u origin spec/<spec-name>`
2. Open a PR from `spec/<spec-name>` into the default branch with the generated body (printed in full).
3. When reviewers leave feedback, paste each comment and its author's role into `spec:complete`; it treats them as findings.
4. Merge, then rerun `spec:complete <spec-name>`; it closes the tickets and the group.
