# discovery:synthesize

Consolidate research artifacts from multiple sources into actionable findings, recommendations, and proposed tickets.

---

## Overview

The agent fetches all provided source documents (discovery docs, interview summaries, spike reports, competitive analyses), performs cross-source analysis to identify themes and contradictions, generates feature recommendations mapped to target epics, and produces a comprehensive synthesis document. The synthesis includes a machine-readable proposed tickets section (JSON) that the approval command consumes.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source-urls` | list[url] | yes | One or more Confluence document URLs to synthesize |
| `target` | string | no | Target implementation epic key (e.g., `--target=CC-62`). Auto-detected from sources if omitted. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `synthesis-document` | url | `/epics/Discovery/{discovery-epic-key}/Synthesis/` | Confluence page with consolidated findings, validated/invalidated hypotheses, recommendations by epic, blocking decisions, and proposed tickets JSON |

## Prerequisites

- Discovery document created via `discovery:create`
- Human research completed with artifacts accessible via URL
- Jira and Confluence access configured

## Next Steps

Review the synthesis document. When ready, run `discovery:approve` with the synthesis URL to resolve blocking decisions and create tickets in the ticketing system.
