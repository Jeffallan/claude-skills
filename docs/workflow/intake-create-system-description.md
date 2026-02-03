# intake:create-system-description

Launch parallel analysis threads to produce a SOC2-style living document covering architecture, API surface, security patterns, and external dependencies.

**Status:** Planned

---

## Overview

The agent runs parallel analysis: one thread maps the architecture (services, databases, queues), another catalogs the API surface area, another traces security patterns (auth, encryption, access controls), and another maps external dependencies. The output is `docs/system-description.md` — a system overview suitable for an auditor or a new senior engineer. This document becomes the shared context for all subsequent workflow phases, and is incrementally updated during execution and holistically reviewed during retrospective.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `system-description` | file | `docs/system-description.md` | Living document: architecture, API surface, security, deployments, third-party dependencies |

## Prerequisites

- Documented codebase (from `intake:document-codebase`)
- Characterization tests (from `intake:capture-behavior`)

## Next Steps

The system description is complete. Feature-forge reads it during feature definition. If discovery is needed, proceed to `discovery:create`. Otherwise, proceed directly to `planning:epic-plan`.
