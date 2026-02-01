# planning:epic-plan

Analyze an epic's tickets and the codebase to produce a stakeholder-readable overview document with requirements, risk assessment, and testing strategy.

---

## Overview

Given an epic key, the agent fetches all linked tickets and launches parallel codebase exploration agents to discover affected modules, API patterns, component patterns, test conventions, and reference implementations. It synthesizes these into a comprehensive overview document covering purpose, requirements, technical changes with 7-dimension risk scoring, impact analysis, testing strategy, and acceptance criteria. This document is for humans making decisions — tech leads, PMs, architects.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `epic-key` | string | yes | Jira epic key to create a planning document for (e.g., CC-62) |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `overview-document` | url | `/epics/In Progress/{epic-key}/` | Confluence page with epic overview, requirements, risk assessment, impact analysis, testing strategy, codebase analysis, and linked tickets |

## Prerequisites

- Epic with linked tickets in Jira
- Discovery phase completed (if unknowns existed)
- Jira and Confluence access configured

## Next Steps

After the overview document is approved and published, run `planning:impl-plan` with the overview document URL to generate the executable implementation plan.
