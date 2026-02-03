# Execution Phase

Per-ticket implementation loop where code gets written, tested, and verified against acceptance criteria.

---

## Purpose

Execution is where the implementation plan becomes working code. The phase is split into two commands per ticket: `execute-ticket` for implementation and `complete-ticket` for finalization. This split exists because implementations can be long, conversations may need compacting, and completion tracking was being dropped when bundled with execution.

## Commands

| Order | Command | Repeat | Summary |
|-------|---------|--------|---------|
| 1 | `execution:execute-ticket` | per ticket | Implement the ticket: write code, create tests, verify acceptance criteria |
| 2 | `execution:complete-ticket` | per ticket | Transition Jira status, update implementation plan with completion details |

Steps 1-2 repeat for every ticket in the epic. Parallel execution waves (defined in the implementation plan) allow multiple tickets to be worked simultaneously.

## Outputs

- **Implemented code** — Code changes following the self-contained ticket instructions
- **Tests** — Unit, integration, and E2E tests as specified
- **Completion summary** — Changes made, files modified, tests added, deviations from plan
- **Updated plan** — Implementation plan status tables updated with completion details
- **Transitioned tickets** — Jira tickets moved to "In Review"

## Prerequisites

- Implementation plan with self-contained tickets (from planning phase)
- Ticketing system access (Jira)
- Documentation system access (Confluence) for complete-ticket

## Next Steps

After all tickets in the epic are complete, proceed to the [Retrospective Phase](retrospective-phase.md) to close the epic and generate the completion report.
