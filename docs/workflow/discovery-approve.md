# discovery:approve

Review synthesis findings, resolve blocking decisions, and create implementation tickets in the ticketing system.

---

## Overview

The agent fetches the synthesis document, extracts the proposed tickets JSON, and walks through any unresolved blocking decisions interactively. After all decisions are resolved, it presents the full ticket list for review and editing (add, remove, modify). Upon approval, it creates tickets in Jira under the target epics with full descriptions, acceptance criteria, and discovery traceability links. The synthesis document is updated with approval status and created ticket keys.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `synthesis-url` | url | yes | Confluence URL of the synthesis document to approve |
| `decisions` | list[string] | no | Pre-resolved blocking decisions (e.g., `--decision=D1:B --decision=D2:Y`) |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `created-tickets` | tickets | Jira tickets created in target implementation epics, linked to discovery epic, with full descriptions and acceptance criteria |

## Prerequisites

- Synthesis document created via `discovery:synthesize`
- Jira and Confluence access configured

## Next Steps

After tickets are created, proceed to `planning:epic-plan` to create the stakeholder-readable overview for the target implementation epic.
