# common-ground

Check the assumptions outstanding specs make against the system's current state, and surface Claude's hidden assumptions about the project for you to confirm. It runs at any point in the workflow.

---

## Overview

Claude often operates on assumptions about project context, technology choices, coding standards, and user preferences. This utility command surfaces those assumptions for explicit validation. It scans configuration files, reviews conversation context, classifies assumptions by type and confidence tier (OPEN, WORKING, ESTABLISHED), and presents them for user review via an interactive two-phase flow. It starts from what is true now: `docs/current-state.json`, which `spec:current` compiles. For each outstanding spec, or the ones you name, it lists the assumptions the spec makes about the current system, the same list `spec:diff` prints, and the `assumption-checker` agent marks each one holds, conflicts or unknown with the source that settles it. A conflict points to `spec:create <spec>`. Confirmed assumptions are kept in a ground file in your repository, next to the system description, and committed. Optional modes include read-only listing (`--list`), quick validation (`--check`), and reasoning graph generation (`--graph`).

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `list` | flag | no | Read-only view of all tracked assumptions |
| `check` | flag | no | Quick validation of current assumptions |
| `graph` | flag | no | Generate mermaid diagram of reasoning structure |
| `specs` | list[string] | no | Outstanding specs whose assumptions to check, in order; every outstanding spec when omitted |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `ground-file` | file | `{docsRoot}/COMMON-GROUND.md` | Human-readable assumptions organized by confidence tier |
| `ground-index` | file | `{docsRoot}/ground.index.json` | Machine-readable assumption index |

## Prerequisites

- Access to the project codebase (for configuration scanning)
- `docs/current-state.json` from `spec:current`, for the spec assumptions check
- No external tooling required

## Usage

Can be invoked at any point during the workflow — during intake, before planning, mid-execution, or whenever assumptions are building up. There is no prescribed moment; use judgment.
