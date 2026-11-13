---
name: status
description: Show where every spec stands and the next command for each, read from the spec branches and their PRs
argument-hint: "[--all]"
---

# Spec Status

Read-only. List every spec with its state, ticket counts, build order, the ticket in progress, its PR and the next command to run. It reads each `spec/<name>` branch with git, so it works from any checkout. For a GitHub project it also asks for each branch's PR (`status.pullRequests` in `.claude/workflow-config.json` turns that off or on).

`guard <command>` below means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`, the ticket guard bundled with this plugin.

## Steps

1. Run `guard spec-status`, adding `--all` when the owner asked for completed specs too. When it warns that a PR lookup failed, the PR column shows `unknown`; pass on the warning and the fix (`gh auth status`).
2. Show the table as it prints. Then, in one or two sentences, name the spec that most needs attention: a PR waiting on review, a spec ready to complete, or a goal run that stopped with Pending tickets.

## States

| State | Meaning |
|-------|---------|
| Triaged | The branch exists; no overview yet |
| Drafting | An overview, no plan yet |
| Planned | A plan, no ticket finished |
| In progress | Some tickets Done or Blocked, some Pending |
| Ready for review | Every ticket Done or Blocked; no review yet |
| In review | The rollup exists and the gate still refuses |
| Ready to complete | The gate passes |
| PR open | The spec PR is open |
| Completed | Merged; hidden unless `--all` |

## Rules

- Write nothing: no files, no commits, no tracker or PR writes.
- Never call `AskUserQuestion`; this command runs the same attended or in a goal.
