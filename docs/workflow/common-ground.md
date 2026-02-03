# common-ground

Surface and validate Claude's hidden assumptions about the project for user confirmation. Invocable on-demand at any point in the workflow.

---

## Overview

Claude often operates on assumptions about project context, technology choices, coding standards, and user preferences. This utility command surfaces those assumptions for explicit validation. It scans configuration files, reviews conversation context, classifies assumptions by type and confidence tier (OPEN, WORKING, ESTABLISHED), and presents them for user review via an interactive two-phase flow. Assumptions are persisted to a ground file for future reference. Optional modes include read-only listing (`--list`), quick validation (`--check`), and reasoning graph generation (`--graph`).

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `list` | flag | no | Read-only view of all tracked assumptions |
| `check` | flag | no | Quick validation of current assumptions |
| `graph` | flag | no | Generate mermaid diagram of reasoning structure |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `ground-file` | file | `~/.claude/common-ground/{project-id}/COMMON-GROUND.md` | Human-readable assumptions organized by confidence tier |
| `ground-index` | file | `~/.claude/common-ground/{project-id}/ground.index.json` | Machine-readable assumption index |

## Prerequisites

- Access to the project codebase (for configuration scanning)
- No external tooling required

## Usage

Can be invoked at any point during the workflow — during intake, before planning, mid-execution, or whenever assumptions are building up. There is no prescribed moment; use judgment.
