# Spec Phase

Groups tickets into specs, plans each spec as three local files, reviews the finished branch and merges it through one PR.

---

## Purpose

A spec is a group of tickets built on one branch and merged in one PR. Its files live next to the code under `docs/specs/todo/<spec-name>/` and move to `docs/specs/completed/` when the spec finishes. Tickets stay in the configured tracker (Jira, GitHub Issues, GitHub Projects, Linear or text files in the repo).

## Commands

| Order | Command | Summary |
|-------|---------|---------|
| 1 | `spec:triage` | Group open tickets into specs, then create each spec's tracker group and branch after approval |
| 2 | `spec:create` | Write `overview.md`, `implementation-plan.md` and `goal-prompt.md`, and print the goal launch commands |
| 3 | `spec:review` | Run adversarial reviewers and blind verifiers over the branch diff |
| 4 | `spec:complete` | Run the gate, open the PR, turn review feedback into fix tickets, merge on approval and close the tickets |

## Prerequisites

- `.claude/workflow-config.json` (the commands offer a setup wizard when it is missing)
- `uv` installed, to run the ticket guard bundled with the plugin

## Next Steps

Between `spec:create` and `spec:review`, the [Ticket Phase](ticket-phase.md) runs each ticket, usually in one goal run.
