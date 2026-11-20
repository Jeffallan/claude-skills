---
name: create-system-description
description: Write the baseline spec and a living system description from the intake docs, the spec index and every completed spec.
argument-hint: "[--full]"
---

# intake:create-system-description

**Argument:** `$ARGUMENTS`: optional `--full` to rewrite the whole description instead of folding in the specs it hasn't seen.

Write `docs/system-description.md`: one document that tells an auditor, a new senior engineer or an agent what the system is, what it is made of, how data moves, how it is secured and what it depends on. It is built from the intake docs and the completed specs, never from memory. On its first run it also writes the **baseline spec**, so the spec index knows the system that existed before the workflow started. **Describe only what the docs and the code prove; cite the source of each section.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/specs/layout.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit, the goal-run behavior, and the specs root and its index.

## When to use

Run once as the last intake command, after the documentation commands; that first run is a full pass. Rerun later to fold in specs completed since the last run; `spec:complete` proposes the same update for one spec at a time. Use `--full` when the description has drifted far from the code. A project that started from discovery and never ran intake runs it once its first specs are completed; the first pass then works from those specs, the discovery outputs and the code.

## Skills to load

- **`fullstack-dev-skills:architecture-designer`**: the component and data-flow diagrams, and the architecture sections.
- **`fullstack-dev-skills:spec-miner`**: confirm each claim against the code where a doc is missing or thin.
- **`fullstack-dev-skills:security-reviewer`**: the security architecture section.
- **`fullstack-dev-skills:code-documenter`**: structure and format the document.

`guard <command>` below means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`, the ticket guard bundled with this plugin.

## Workflow

### Phase 1: Read the inputs
1. Read `.claude/workflow-config.json` for `specsRoot` (default `docs/specs`). Paths below use the default.
2. Read the intake docs that exist: the docs index (`docs/README.md` or `docs/README-intake.md`), `docs/architecture/*.md`, `docs/domain/*.md`, `docs/security/*.md`, `docs/flows/*.md`, `docs/operations/*.md` and `docs/intake-findings.md`. A missing doc is a gap to fill from the code, and the section says so.
   **No intake docs at all** (the project started from discovery): read the discovery outputs instead, `docs/specs/todo/discovery/*/discovery.md` and `docs/specs/completed/discovery/*/discovery.md` with the feature specs beside them, plus any architecture or flow docs the docs index lists or the owner names. They are plans: a claim taken from them goes into the description only when the code or a completed spec confirms it. Note the topic names for the baseline.
3. Read `docs/specs/INDEX.md`, then each completed spec's `overview.md` under `docs/specs/completed/`, including its `## Completion report`, in the index's order.
4. When `docs/system-description.md` exists, read its `## Change history` table: the specs already folded in.

### Phase 2: The baseline spec (first run only)
When `docs/specs/completed/baseline/overview.md` doesn't exist, write it:

```markdown
# Baseline

**Spec:** baseline
**Discovery:** none
**After:** none
**Feature areas:** <area>, <area>
**Status:** Completed by intake on <YYYY-MM-DD> at <short-sha>

---

## Summary

The system as it stood when intake ran, before any spec in this index. Its documents are the intake docs.

| Area | Document |
|------|----------|
| <area> | <relative link to the intake doc> |

## Completion report

Intake documented the code, characterized its behavior and recorded <n> findings in `docs/intake-findings.md`.
```

On a project with no intake docs, write the same header lines with `**Status:** Completed by intake:create-system-description on <YYYY-MM-DD> at <short-sha>` and replace the Summary and Completion report text: the Summary says the project started from discovery (name the topic or topics) and has no intake docs, and its table links each area to the completed spec that documents it; the Completion report says intake did not run, so there are no intake findings. Keep `**Discovery:** none`, since the baseline came from no topic.

Take the `Feature areas:` values from the documentation phase: the feature groups in `docs/domain/features.md`, as kebab-case names, plus `security`, `data-model` and `integrations` when those docs exist. Without intake docs, take them from the completed specs' `Feature areas:` lines. Write no prose in brackets on a header line; the index splits values on commas. Then run `guard spec-index` so `INDEX.md` lists the baseline. Later specs that change the same areas name them in their own `Feature areas:` line, which is how `spec:create` finds the baseline.

When the baseline exists, leave it alone: it records the system at intake, and later changes belong to later specs. That includes its findings count and list: when a later pass adds, widens or closes a finding, `docs/intake-findings.md` carries the change and the baseline keeps the numbers from the day it was written.

### Phase 3: Plan the pass
- **Full pass**: on the first run (no `docs/system-description.md`), or with `--full`. Every section is written from the intake docs and the completed specs. Without intake docs, every section comes from the completed specs (overview and Completion report, in index order) and the code, with the discovery outputs read as plans to check, never as proof.
- **Incremental pass**: otherwise. Only the completed specs missing from the Change history are folded in, each changing just the sections its feature areas and completion report touch.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the pass type, the inputs found and missing, the baseline spec's feature areas (first run) and the specs to fold in. Do not write until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write or update `docs/system-description.md` with the template below, with `related:` frontmatter naming the intake docs its sections draw on (each of those lists it back). Add `system-description.md` and `specs/INDEX.md` to the docs index (`docs/README.md`, or `docs/README-intake.md` beside an owner README) in the same commit. Each section names its sources. Diagrams are Mermaid. Open findings that affect a section are listed in it by id, never restated as fact or hidden.

### Phase 5: Accuracy audit (required)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-check every component, data store, integration, control and dependency against its source doc and the code. Remove anything not proven. Add a row to the Change history for each spec folded in, then an `## Accuracy audit` section with the date, the commit and what was checked.

## Output template

```markdown
---
command: intake:create-system-description
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# System Description

<2 sentences: what the system does and for whom.>

**Sources:** intake docs under `docs/` (or, without intake, the discovery topics checked against the code), the spec index, completed specs. **Last updated:** <YYYY-MM-DD> at <short-sha>

## 1. Purpose and scope
## 2. Components
<services, apps, workers, data stores, queues and caches, with a Mermaid component diagram>
## 3. Data flow
<Mermaid flowchart of how data enters, moves, is stored and leaves; where personal data lives>
## 4. Security architecture
<authentication, authorization model, secrets handling, encryption, open security findings by id>
## 5. API surface
<public and internal interfaces, with a link to the API reference>
## 6. External dependencies
<third-party services and what breaks without each>
## 7. Infrastructure and operations
<environments, configuration, deployment, monitoring>
## 8. Change management
<how changes reach production: branches, review, CI gates, the spec workflow>

## Change history

| Spec | Folded in | Sections changed |
|------|-----------|------------------|
| baseline | <YYYY-MM-DD> | all |

## Accuracy audit
```

## Failure conditions

- **No intake docs and no completed specs**: state it and stop. Run the documentation commands first.
- **A spec's completion report contradicts the code**: describe the code, flag the discrepancy and add a finding.
- **The spec index is stale** (`guard spec-index --check` fails): regenerate it before reading it.

## Output

`docs/system-description.md`, the baseline spec and refreshed `INDEX.md` on the first run, and a summary: pass type, sections written or changed, specs folded in, gaps and findings raised.
