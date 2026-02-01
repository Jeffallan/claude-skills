# execution:execute-ticket

Implement a ticket by following its self-contained implementation details: write code, create tests, verify acceptance criteria.

---

## Overview

Given a ticket key, the agent fetches the ticket's self-contained implementation details, reviews the implementation plan for wave/dependency context, explores the codebase for relevant patterns, and begins coding. It checks for parallel execution opportunities (other tickets in the same wave) and can delegate to specialized agents. The agent follows implementation steps exactly, writes required tests, runs them, and verifies all acceptance criteria. Deviations from the plan require explicit user approval at a checkpoint. The output is a completion summary with suggested commit message.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ticket-key` | string | yes | Jira ticket key to execute (e.g., CC-123) |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `completion-summary` | report | Changes made, files modified/created, tests added, deviations from plan, follow-up tickets, suggested commit message |

## Prerequisites

- Ticket with self-contained implementation details (from `planning:impl-plan`)
- All blocking tickets complete (checked via Jira status)
- Ticketing system access (Jira)

## Next Steps

After execution, review the changes and create a git commit. Then run `execution:complete-ticket` to transition the Jira ticket and update the implementation plan.
