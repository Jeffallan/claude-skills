# discovery:synthesize

Consolidate a discovery topic's research into findings, blocking decisions and proposed tickets.

---

## Overview

Run it only when `discovery:create` routed items to research. It reads `discovery.md`, the Feature Forge files and `sources/`, answers each open question with cited findings, and proposes the tickets the research supports.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic` | string | yes | Discovery topic name whose research is complete |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `synthesis-document` | file | `{specsRoot}/todo/discovery/{topic}/synthesis.md` | Findings, remaining unknowns, blocking decisions and proposed tickets |

## Next Steps

Run `discovery:approve <topic>`.
