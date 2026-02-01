# retrospectives:complete-epic

Verify all tickets are complete, generate a comprehensive completion report, close the epic in Jira, and perform a holistic system description review.

---

## Overview

The agent fetches the epic, verifies all linked tickets are in "Done" status (blocking if any are incomplete), then generates a 12-section completion report covering objectives vs. outcomes, ticket breakdown, technical deliverables, architecture decisions, quality metrics, technical debt, testing effectiveness, documentation, lessons learned, risk review, and recommendations. It moves documentation from "In Progress" to "Complete" in Confluence, closes the epic in Jira, and performs a full system description review — not just incremental updates, but a holistic check ensuring architecture diagrams, API surfaces, and dependency maps reflect the post-epic state.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `epic-key` | string | yes | Jira epic key to complete (e.g., CC-62) |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `completion-report` | report | 12-section report: summary, objectives, tickets, deliverables, architecture, quality, debt, testing, docs, lessons, risks, recommendations |
| `closed-epic` | tickets | Epic closed in Jira with "Done" status and "Completed" resolution |
| `updated-system-description` | file | `docs/system-description.md` updated with holistic post-epic review |

## Prerequisites

- All tickets in the epic completed (or explicitly moved to backlog with user override)
- Overview document and implementation plan accessible in Confluence
- Jira and Confluence access configured

## Next Steps

The system description is now current. The next `feature-forge` invocation reads the updated system description, and the workflow cycle begins again. The sprint folder location is available for `complete-sprint` if a sprint retrospective is needed.
