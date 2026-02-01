# execution:complete-ticket

Finalize a ticket after execution by transitioning Jira to "In Review" and updating the implementation plan with completion details.

---

## Overview

The agent identifies the completed ticket (from argument or conversation context), gathers completion details from the execution summary, confirms the finalization plan with the user, then transitions the Jira ticket to "In Review" and updates the implementation plan's completion status, execution order, and parallel wave tables. It also records detailed completion notes including changes made, tests added, deviations, and follow-up tickets. Can be used standalone if the user provides completion details manually.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ticket-key` | string | no | Jira ticket key to complete. Optional if context is available from a prior `execute-ticket` invocation. |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `transitioned-ticket` | tickets | Jira ticket moved to "In Review" status |
| `updated-plan` | url | Implementation plan updated with completion details and status tracking |

## Prerequisites

- Ticket executed via `execution:execute-ticket` (or manual completion details provided)
- Implementation plan URL available (from ticket description or user)
- Jira and Confluence access configured

## Next Steps

Repeat `execute-ticket` + `complete-ticket` for the next ticket. After all tickets in the epic are complete, run `retrospectives:complete-epic`.
