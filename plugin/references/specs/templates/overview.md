# Overview Template

`spec:create` fills this template first and shows it to the owner. The plan and the goal prompt are built from the approved overview, so anything they need must be here. Replace every `<placeholder>`; delete a section's guidance line once it is filled. Keep the four header lines above the first `##` heading: `guard spec-index` reads them (see `references/specs/layout.md`).

## Template

```markdown
# <Spec title>

**Spec:** <spec-name>
**Discovery:** <topic>, <topic> | none
**After:** <spec-name> | none
**Feature areas:** <area>, <area>
**Status:** Draft, waiting for owner approval
**Branch:** spec/<spec-name>, base <default-branch> at <short-sha>
**Created:** <YYYY-MM-DD>

---

## Readiness

Every ticket the tracker groups under this spec, checked against the code before planning.

| Ticket | Readiness | Evidence or question |
|--------|-----------|----------------------|
| <ID> | Ready | <one line: why it can be planned now> |
| <ID> | Blocked: question | <the exact question, and who can answer it> |
| <ID> | Blocked: decision | <the decision needed and its options> |
| <ID> | Blocked: needs-spec | <what is missing from the ticket> |
| <ID> | Already done | <commit SHA and the check that proves it: `git log --grep`, `git grep`, `git merge-base --is-ancestor`> |

Only Ready tickets enter the plan and the goal prompt. Already done tickets are closed by `spec:complete`.

## 1. Purpose

<Two or three sentences: what changes for the user or the codebase, and why now.>

## 2. Scope

**In:**
- <one line per Ready ticket's outcome>

**Out:**
- <what a reader might assume is included but isn't>

## 3. Success criteria

- <an observable end state with the command that checks it>

## 4. Design

<Decisions that shape the tickets, as a table of area and decision. Cite the subagent findings that drove each one.>

| Area | Decision |
|------|----------|
| <area> | <decision> |

## 5. Reuse

<Existing helpers, components, patterns and tests the tickets must use instead of writing new code, each with its path.>

## 6. Debt in scope

<Debt this spec touches and pays down, with the ticket that pays it. Debt it only notices goes to the plan's Proposed tracker changes.>

## 7. Risks

<Each risk with its likelihood, its impact and the ticket or check that covers it.>

## 8. Linked tickets

<The tracker group and each ticket by ID. Names, never paths.>
```

## Rules

- The Readiness table is the first table in the file. `guard gate` lists its Blocked rows for the owner at `spec:complete`.
- Every Already done row carries commit evidence from a code check, never memory or the ticket's status.
- A Blocked row states the exact question or decision, so the owner can answer it without reading the ticket.
- `spec:complete` appends a `## Completion report` section (what happened, deviations, debt, follow-ups). `spec:create` never writes one.
