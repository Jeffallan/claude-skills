---
description: Surface and validate Claude's hidden assumptions about the project for user confirmation
argument-hint: [--list] [--check] [--graph]
---

# Common Ground

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
| `--graph` | Graph | Generate mermaid diagram of reasoning structure |

---

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Assumption Types & Tiers | `references/assumption-classification.md` | Classifying assumptions, determining type or tier |
| File Management | `references/file-management.md` | Storage operations, project ID, ground file format |
| Reasoning Graph | `references/reasoning-graph.md` | Using --graph flag, generating mermaid diagrams |

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
   - Check existing ground file for tracked assumptions

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

4. **Write ground file:**
   - Save to `~/.claude/common-ground/{project_id}/COMMON-GROUND.md`
   - Update `ground.index.json` for machine-readable access
   - See `references/file-management.md` for file formats

### Output

```
## Common Ground Complete

**Project:** {project_name}
**Tracked Assumptions:** {count}

### Summary
- ESTABLISHED: {count} (high confidence)
- WORKING: {count} (medium confidence)
- OPEN: {count} (needs validation)

**Ground file saved to:** ~/.claude/common-ground/{project_id}/COMMON-GROUND.md

Run `/common-ground --list` to view all assumptions.
Run `/common-ground --check` for quick validation.
```

---

## --list Mode

Read-only display of all tracked assumptions.

1. **Load ground file** from `~/.claude/common-ground/{project_id}/COMMON-GROUND.md`

2. **Display assumptions** grouped by tier:

```
## Common Ground: All Assumptions

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
(Read-only view. Run `/common-ground` to modify.)
```

3. **Handle missing file:**
   If no ground file exists:
   ```
   No ground file found for this project.
   Run `/common-ground` to surface and track assumptions.
   ```

---

## --check Mode

Quick validation of existing assumptions.

1. **Load ground file** from `~/.claude/common-ground/{project_id}/COMMON-GROUND.md`

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
   If no ground file exists, redirect to default flow:
   ```
   No existing assumptions to check. Starting fresh...
   ```
   Then execute default mode.

---

## --graph Mode

Generate a mermaid diagram showing Claude's reasoning structure—not just assumptions, but the decision tree that led to the current approach.

### Purpose

Make the shape of Claude's reasoning visible:
- Decision points and branches considered
- Paths taken vs alternatives
- Where uncertainty lives in the reasoning chain

### Flow

1. **Run standard common-ground flow** (if no existing ground file, execute default mode first)

2. **Analyze reasoning structure** behind confirmed assumptions:
   - What decision points led to these assumptions?
   - What alternatives were considered at each branch?
   - What confidence level exists at each node?

3. **Generate mermaid diagram** following conventions in `references/reasoning-graph.md`

4. **Output files:**
   - Update `COMMON-GROUND.md` with embedded `## Reasoning Graph` section
   - Optionally create standalone `REASONING.mermaid` in project root

### Output Format

The reasoning graph is embedded in `COMMON-GROUND.md`:

```markdown
## Reasoning Graph

```mermaid
flowchart TD
    ROOT[Task: {task_description}] --> D1{Decision Point?}
    D1 -->|"weight: 0.8 [inferred]"| P1[Chosen Path]
    D1 -->|"weight: 0.2 [alternative]"| P2[Alternative]
    ...
```
```

### Conversational Interaction

Since mermaid is text-based, graph manipulation happens conversationally:

| User Says | Claude Action |
|-----------|---------------|
| "Expand the {branch} branch" | Regenerate graph with that path elaborated |
| "Why not {alternative}?" | Explain reasoning, potentially adjust weights |
| "I actually want {alternative}" | Update graph with that branch as chosen |
| "What's downstream of {node}?" | Expand that subtree |

After each significant interaction, regenerate the graph showing updated state.

### Example Output

```
## --graph Complete

**Project:** {project_name}
**Reasoning Nodes:** {count}
**Decision Points:** {count}

### Graph Summary
- Root: {task_description}
- Major Decisions: {count}
- Open Questions: {count} nodes with uncertain status

**Graph embedded in:** ~/.claude/common-ground/{project_id}/COMMON-GROUND.md

Run `/common-ground --list` to view assumptions.
Run `/common-ground --graph` to regenerate after changes.
```

See `references/reasoning-graph.md` for detailed mermaid conventions and node styling.

---

## Constraints

### MUST DO
- Always identify project before file operations
- Use AskUserQuestion for all interactive selections
- Preserve assumption type (audit trail) - users cannot change type
- Write both human-readable (COMMON-GROUND.md) and machine-readable (ground.index.json) files
- Include timestamps for tracking staleness
- When using --graph, show decision points that led to assumptions
- Preserve alternative branches in graph (grayed out) for context

### MUST NOT DO
- Assume context without surfacing assumptions
- Allow type changes (stated/inferred/assumed/uncertain)
- Proceed without user confirmation on tier changes
- Overwrite ground file without preserving history
- Generate graphs without first having confirmed assumptions
- Remove alternative branches from graph (preserve for exploration)
