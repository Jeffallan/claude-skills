# Implementation Plan Template

`spec:create` writes this file from the approved overview. The ticket commands, `guard block`, `guard gate` and `guard run-batches` parse two of its tables, so keep their headings and columns exactly as shown:

- `## Completion Status`: the first column is the ticket ID, then Status, Completed Date and Notes.
- `## Execution Order`: the second column is the ticket ID.

Only Ready tickets from the overview's Readiness table get rows and sections.

## Template

```markdown
# <Spec title> implementation plan

**Spec:** <spec-name>
**Status:** Draft, waiting for owner approval

## Summary

| Metric | Value |
|--------|-------|
| **Tickets** | <count of Ready tickets> |
| **Branch** | `spec/<spec-name>` |
| **Verification** | `<command>`, `<command>` |

---

## Completion Status

| Ticket | Status | Completed Date | Notes |
|--------|--------|----------------|-------|
| <ID> | Pending | - | - |

`ticket:complete` updates a row and commits it with the ticket, so the table holds no SHAs; `git log --grep "Ticket: <ID>"` finds the commit. Notes carry the evidence summary from `guard summary`. `guard block` writes Blocked rows.

---

## Execution Order

| # | Ticket | Summary | Risk | Dependencies |
|---|--------|---------|------|--------------|
| 1 | <ID> | <one line> | Low / Medium / High | None / <ID> |

---

## Tickets

### <ID>: <title>

**Skill:** <up to two skills by exact name from the plugin's skill list, or none>
**Docs:** <docs under the docs root this ticket must update or check, or none>
**Depends on:** <ID> | none
**Type:** test | stand-in | refactor

<What to build, in plain terms, with the files it touches and the reuse it must follow.>

**RED:** <the failing test to write first and the command that runs it; for a stand-in ticket, the check that fails before the change>

**Acceptance criteria:**
- [ ] <observable result with the command that checks it>

---

## Proposed tracker changes

Changes `spec:create` may not make on its own (create, split, close, transition, membership, labels), new issues a goal run found, and debt follow-ups. Nothing here is written to the tracker until the owner approves it, usually at `spec:complete`.

| # | Change | Plain example | Files | Duplicate check |
|---|--------|---------------|-------|-----------------|

---

## Open questions

Questions a skill or ticket needed answered that no one could answer during the run. Each blocks its ticket as `Blocked: question`.

| # | Ticket | Question | Asked by |
|---|--------|----------|----------|
```

## Rules

- Every ticket has a `Skill:` line naming up to two skills that exist (a stack skill and a project skill, for example), so the goal run loads them instead of guessing.
- Every ticket has a `Docs:` line: the docs `spec:create` found citing what it changes, and their `related:` docs. `ticket:execute` adds any doc `guard docs-affected` finds that the line missed.
- Every ticket names its RED check before any implementation step. Refactor fix tickets name the stand-in instead: suite green before and after, test files unchanged by digest, metrics show the clone or dead code gone.
- Dependencies name ticket IDs only, so `guard block` can mark dependents "depends on <ID>".
- Never delete a Completion Status row. A ticket moved out of the spec gets a Proposed tracker changes entry and stays listed with its reason.
