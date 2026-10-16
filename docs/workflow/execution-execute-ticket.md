# execution:execute-ticket

Implement a ticket by following its self-contained implementation details: write failing tests, write code until they pass, verify acceptance criteria.

---

## Overview

Given a ticket key, the agent fetches the ticket's self-contained implementation details, reviews the implementation plan for wave/dependency context, explores the codebase for relevant patterns, and checks for parallel execution opportunities (other tickets in the same wave), delegating to specialized agents where that helps. Before touching production code, the agent writes failing tests for the acceptance criteria and records that each one fails for the reason the ticket describes. It then follows the implementation steps until the tests pass, refactors with the tests green, and verifies all acceptance criteria. Tickets with no code use a stand-in check (a validator, a grep, a fixture run) with its own RED result. Deviations from the plan require explicit user approval at a checkpoint. The output is a completion summary with suggested commit message.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ticket-key` | string | yes | Jira ticket key to execute (e.g., CC-123) |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `completion-summary` | report | Changes made, files modified/created, tests added with their RED results, deviations from plan, follow-up tickets, suggested commit message |

## Prerequisites

- Ticket with self-contained implementation details (from `planning:impl-plan`)
- All blocking tickets complete (checked via Jira status)
- Ticketing system access (Jira)

## Next Steps

After execution, review the changes and create a git commit. Then run `execution:complete-ticket` to transition the Jira ticket and update the implementation plan.
