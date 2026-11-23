# Ticket Phase

Runs each ticket of a spec test-first, with one commit per ticket, attended or inside a goal run.

---

## Purpose

`ticket:execute` writes the failing test, then the code, and records RED and GREEN evidence. `ticket:complete` checks that evidence, updates the plan's Completion Status table and commits. Neither command writes to the tracker.

## Commands

| Order | Command | Summary |
|-------|---------|---------|
| 1 | `ticket:execute` | Implement one ticket test-first from the spec's implementation plan |
| 2 | `ticket:complete` | Check the evidence, update the Completion Status table and commit |

## Prerequisites

- A spec created by `spec:create`, with the spec branch checked out
- A clean working tree

## Next Steps

When every ticket is Done or Blocked, run `spec:review`.
