---
name: existing-docs
description: Inventory the docs a project already has, map them to the intake doc set and check their claims against the code, so later intake commands link instead of repeating and every wrong claim becomes a finding.
argument-hint: "[directory]"
---

# intake:existing-docs

**Argument:** `$ARGUMENTS`: optional root directory to analyze (defaults to the project root).

Produce `docs/intake-existing-docs.md`: every doc the project had before intake, which intake topics each one covers, and how well its claims hold against the code. Later documentation commands read it to link to an owner doc that already covers their topic and to write only what is missing. **Never edit an owner doc.** A wrong claim in one becomes a finding; the owner fixes it later.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` (especially "Existing docs") and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase.

## When to use

Run once during intake, right after the findings tracker starts and before `intake:document-codebase`, so the docstrings and every later doc can see what the project already says. Run it on a project with no docs too: the inventory then says so, and the checklist item is checked with that note.

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: check each claim against the code that would prove or disprove it.
- **`fullstack-dev-skills:code-documenter`**: structure and validate the inventory.

## Workflow

### Phase 1: Find the docs
List every Markdown or text doc the project tracks: the root `README`, `docs/`, `CONTRIBUTING`, ADRs, design notes, runbooks, and doc folders inside packages. Skip vendored and installed trees, generated API output, the changelog and license files, and intake's own files.

### Phase 2: Map topics
For each doc, list the intake topics it covers (data model, file tree, integrations, API, user model, features, glossary, security, authorization, user flow, configuration, analytics, onboarding) and how much: full, partial or a mention. A topic no doc covers is a coverage gap; the intake command for it writes its doc as usual.

### Phase 3: Check the claims
Read each doc's factual claims (names, paths, commands, settings, endpoints, roles, versions, steps) and check each against the code with `spec-miner`:

- **Holds:** the code bears it out.
- **Wrong:** the code contradicts it. Append a finding (area `docs`) whose Location is the code symbol and whose What quotes the doc's claim and says what the code does.
- **Unverified:** no code can settle it (timings, team process, intent). List it; it is not a finding.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the doc list, the topic map and the wrong claims found. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write `docs/intake-existing-docs.md` from the template below, with `related: []` frontmatter (the intake docs that link to an owner doc add themselves later, both ways).

### Phase 5: Accuracy audit
Give the prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`), then re-check every Wrong row against the code: the finding id exists, the cited symbol resolves, and the quoted claim matches the doc as written. End with `## Accuracy audit`.

## Output template

```markdown
---
related: []
---
# Existing Docs

<1-2 sentences: how many docs the project had, and how intake uses them.>

## Inventory

| Doc | Topics covered | Coverage | Claims checked | Wrong (finding ids) | Unverified |
|-----|----------------|----------|----------------|---------------------|------------|
| `<path>` | <intake topics> | full / partial / mention | <n> | <F-NNN, ...> or none | <n> |

## Coverage gaps

| Intake topic | Covered by | What the intake doc must add |
|--------------|------------|------------------------------|

## Unverified claims

| Doc | Claim | Why no code can settle it |
|-----|-------|---------------------------|

## Accuracy audit
```

## Failure conditions

- **No docs found:** write the inventory with an empty table and "No docs found before intake." Every intake topic is then a gap.
- **An owner doc sits at an intake doc's path:** record it; the intake command writes its doc beside it as `<name>-intake.md`.

## Output

`docs/intake-existing-docs.md`, plus a short summary: docs found, topics fully covered, gaps, and the finding ids raised.
