# discovery:create

Create a structured discovery workspace with research questions, hypotheses, and a research plan for a given topic.

---

## Overview

Given an epic key, the agent fetches the epic and its linked tickets, extracts explicit and implicit questions, categorizes them by theme (customer discovery, technical feasibility, business viability, scope boundaries), and identifies appropriate research methods. The output is a published Confluence discovery document that structures the human research phase.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `epic-key` | string | yes | Jira epic key for the discovery epic (e.g., CC-60) |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `discovery-document` | url | `/epics/Discovery/{epic-key}/` | Confluence page with hypothesis map, research questions matrix, dependencies, research plan, decision framework, and risk register |

## Prerequisites

- Epic exists in Jira with linked tickets
- Jira and Confluence access configured

## Next Steps

After the discovery document is created, humans conduct research (interviews, spikes, competitive analysis). When research is complete, run `discovery:synthesize` with the discovery document URL and any additional research artifact URLs.
