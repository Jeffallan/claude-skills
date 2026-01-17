---
description: Surface and validate Claude's hidden assumptions about the project for user confirmation
argument-hint: [--list] [--check]
---

# Reality Check

**Arguments:** $ARGUMENTS

---

## Purpose

Claude often operates on assumptions about project context, technology choices, coding standards, and user preferences. This command surfaces those assumptions for explicit user validation, preventing misaligned work based on incorrect premises.

---

## Argument Parsing

Parse arguments to determine mode:

| Flag | Mode | Description |
|------|------|-------------|
| (none) | Default | Surface & Adjust two-phase interactive flow |
| `--list` | List | Read-only view of all tracked assumptions |
| `--check` | Check | Quick validation of current assumptions |

---

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Assumption Types & Tiers | `references/assumption-classification.md` | Classifying assumptions, determining type or tier |
| File Management | `references/file-management.md` | Storage operations, project ID, reality file format |

---

## Project Identification

Before any operation, determine the project identity:

1. **Try git remote:**
   ```bash
   git remote get-url origin 2>/dev/null
   ```
   If found, use the URL as project identifier (e.g., `github.com/user/repo`)

2. **Fallback to path:**
   Use the current working directory absolute path

Store this as `{project_id}` for file operations.

---

## Default Mode: Surface & Adjust

When no flags provided, execute the two-phase interactive flow.

### Phase 1: Surface & Select

1. **Analyze current context** to identify assumptions:
   - Scan configuration files (tsconfig.json, package.json, .eslintrc, etc.)
   - Review recent conversation context
   - Check existing reality file for tracked assumptions

2. **Classify each assumption** by type and proposed tier:
   - See `references/assumption-classification.md` for classification rules

3. **Present to user via AskUserQuestion:**

   Present assumptions grouped by category. Use multiSelect to let user choose which to track.

   **Question format:**
   ```
   I've identified assumptions about this project. Which should I track?
   ```

   **Options** (up to 4 categories, user selects via multiSelect):
   - Architecture & Tech Stack assumptions
   - Coding Standards assumptions
   - Testing & Quality assumptions
   - Other/Uncertain items

   User can select multiple categories or use "Other" to specify individual items.

4. **Handle uncertain items:**
   For any `[uncertain]` assumptions, ask direct clarifying questions.

### Phase 2: Adjust Tiers

1. **Show selected assumptions** with proposed tiers

2. **Present tier adjustment options via AskUserQuestion:**

   **Question format:**
   ```
   Review the confidence tiers. Any adjustments needed?
   ```

   **Options:**
   - Accept all proposed tiers
   - Promote some to higher confidence
   - Demote some to lower confidence
   - Add new assumptions

3. **Process adjustments:**
   - Promotions: OPEN -> WORKING -> ESTABLISHED
   - Demotions: ESTABLISHED -> WORKING -> OPEN
   - New additions: User specifies via "Other" with format: `assumption text [tier] [type]`

4. **Write reality file:**
   - Save to `~/.claude/reality-check/{project_id}/reality.md`
   - Update `reality.index.json` for machine-readable access
   - See `references/file-management.md` for file formats

### Output

```
## Reality Check Complete

**Project:** {project_name}
**Tracked Assumptions:** {count}

### Summary
- ESTABLISHED: {count} (high confidence)
- WORKING: {count} (medium confidence)
- OPEN: {count} (needs validation)

**Reality file saved to:** ~/.claude/reality-check/{project_id}/reality.md

Run `/reality-check --list` to view all assumptions.
Run `/reality-check --check` for quick validation.
```

---

## --list Mode

Read-only display of all tracked assumptions.

1. **Load reality file** from `~/.claude/reality-check/{project_id}/reality.md`

2. **Display assumptions** grouped by tier:

```
## Reality Check: All Assumptions

**Project:** {project_name}
**Last Updated:** {timestamp}

### ESTABLISHED ({count})
1. {title} - {assumption} [{type}]
2. ...

### WORKING ({count})
1. {title} - {assumption} [{type}]
2. ...

### OPEN ({count})
1. {title} - {assumption} [{type}]
2. ...

---
(Read-only view. Run `/reality-check` to modify.)
```

3. **Handle missing file:**
   If no reality file exists:
   ```
   No reality file found for this project.
   Run `/reality-check` to surface and track assumptions.
   ```

---

## --check Mode

Quick validation of existing assumptions.

1. **Load reality file** from `~/.claude/reality-check/{project_id}/reality.md`

2. **Present summary via AskUserQuestion:**

   **Question format:**
   ```
   Quick check: Are these assumptions still valid?
   ```

   **Options:**
   - All still valid
   - Some need updates
   - Need full review

3. **Handle responses:**
   - **All valid:** Update `last_validated` timestamp, confirm
   - **Some need updates:** Ask which ones, then enter Phase 2 of default flow
   - **Need full review:** Run full default flow

4. **Handle missing file:**
   If no reality file exists, redirect to default flow:
   ```
   No existing assumptions to check. Starting fresh...
   ```
   Then execute default mode.

---

## Constraints

### MUST DO
- Always identify project before file operations
- Use AskUserQuestion for all interactive selections
- Preserve assumption type (audit trail) - users cannot change type
- Write both human-readable (reality.md) and machine-readable (reality.index.json) files
- Include timestamps for tracking staleness

### MUST NOT DO
- Assume context without surfacing assumptions
- Allow type changes (stated/inferred/assumed/uncertain)
- Proceed without user confirmation on tier changes
- Overwrite reality file without preserving history
