# Retrospective Phase

Epic completion, reporting, and system description update after all tickets are executed.

---

## Purpose

Retrospective closes the loop on an epic. It verifies all work is complete, generates a comprehensive completion report, moves documentation to its final location, closes the epic in the ticketing system, and performs a holistic system description review to capture architectural changes that may have been missed during incremental ticket-by-ticket updates.

## Commands

| Order | Command | Summary |
|-------|---------|---------|
| 1 | `retrospectives:complete-epic` | Verify completion, generate report, close epic, update system description |

## Outputs

- **Completion report** — Deliverables, quality metrics, lessons learned, risk review, recommendations
- **Closed epic** — Epic status set to "Done" in the ticketing system
- **Updated system description** — Holistic post-epic review of `docs/system-description.md`
- **Relocated documentation** — Epic docs moved from "In Progress" to "Complete" folder

## Prerequisites

- All tickets in the epic completed (or explicitly moved to backlog)
- Ticketing system access (Jira)
- Documentation system access (Confluence)

## Next Steps

The updated system description feeds the next cycle. When the next feature is defined via `feature-forge`, it reads the current system description, making each iteration more informed than the last.
