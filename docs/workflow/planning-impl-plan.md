# planning:impl-plan

Convert the overview document into an executable implementation plan with topologically sorted execution order, parallel waves, and self-contained ticket descriptions.

---

## Overview

The agent reads the overview document, fetches all Jira tickets, and performs ticket refinement — creating new tickets for gaps, splitting large tickets (>8 story points), adding story points, and linking dependencies. It then generates a lightweight coordination plan in Confluence with execution order, parallel execution waves, and agent recommendations. Each Jira ticket is updated with self-contained implementation details: step-by-step instructions with file paths, code snippets, complete test code, files to modify, and acceptance criteria checklists. This makes each ticket independently executable without needing external document fetches.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `overview-doc-url` | url | yes | Confluence URL of the overview document produced by `planning:epic-plan` |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `implementation-plan` | url | Confluence page with summary metrics, completion status table, topologically sorted execution order, parallel wave strategy, and agent recommendations |
| `updated-tickets` | tickets | Jira tickets updated with self-contained implementation details, file paths, test code, and acceptance criteria |

## Prerequisites

- Overview document published via `planning:epic-plan`
- Jira and Confluence access configured

## Next Steps

After the implementation plan is published, begin executing tickets with `execution:execute-ticket`. Parallel waves defined in the plan indicate which tickets can be worked simultaneously.
