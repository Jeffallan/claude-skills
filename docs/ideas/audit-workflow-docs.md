# Workflow Documentation Audit Report

> Conducted: 2026-02-02
> Scope: Workflow commands, command docs, guides, YAML definitions, and cross-references
> Method: Full read of all files in scope, cross-referencing YAML definitions against docs

---

## Executive Summary

The workflow documentation is unusually thorough for a project of this size. The `WORKFLOW_COMMANDS.md` file is a well-structured 876-line reference with mermaid diagrams, input/output tables, and checkpoint documentation. The `docs/workflow/` directory provides a clean separation between phase overviews and per-command descriptions, and the YAML definitions are consistent and well-typed.

However, the documentation has grown organically across three layers (README, `WORKFLOW_COMMANDS.md`, and `docs/workflow/`) without clear delineation of audience or purpose. This creates significant redundancy, a confusing entry path for new users, and several structural mismatches between what the YAML definitions declare and what the docs describe.

This report documents all findings, organizes them by area, and proposes a restructuring plan for migration to Astro + Starlight.

---

## 1. Per-Area Findings

### 1.1 `docs/WORKFLOW_COMMANDS.md`

**Strengths:**
- Comprehensive: covers all four phases with mermaid diagrams, command signatures, process steps, output sections, and publish locations.
- The Document Flow Summary table (lines 87-97) is an excellent quick-reference artifact.
- Checkpoint documentation (lines 740-812) is thorough and includes realistic examples with response types.
- Workflow Variations section (lines 816-838) clearly communicates the three main paths through the system.

**Weaknesses:**
- **Drift from YAML manifest.** The document describes four phases (Discovery, Planning, Execution, Retrospectives) and nine commands. The YAML manifest defines five phases (Intake, Discovery, Planning, Execution, Retrospective) and twelve commands plus one utility. The entire Intake phase (3 commands) is absent from `WORKFLOW_COMMANDS.md`.
- **Naming inconsistencies.** The document uses old command names (`create-epic-discovery`, `synthesize-discovery`, `approve-synthesis`, `create-epic-plan`, `create-implementation-plan`) while the YAML manifest uses shorter identifiers (`discovery:create`, `discovery:synthesize`, `discovery:approve`, `planning:epic-plan`, `planning:impl-plan`). A reader switching between the two sources will be confused about which name to use.
- **`complete-sprint` is documented but absent from the manifest.** `WORKFLOW_COMMANDS.md` describes `complete-sprint` as a command (lines 632-673). The manifest's retrospective phase lists only `retrospectives:complete-epic`. There is a `commands/project/retrospectives/complete-sprint.md` implementation file but no `.yaml` definition file for it. This is either a manifest omission or the command was removed without updating the docs.
- **Common Ground absent.** The manifest includes `common-ground` as a utility command. `WORKFLOW_COMMANDS.md` does not mention it at all, despite its relevance to the workflow (it can be invoked at any point).
- **Monolithic structure.** At 876 lines, the file tries to be both a conceptual introduction and a complete reference. The mermaid diagrams and process descriptions serve a "getting started" reader, while the checkpoint tables and integration points serve a "deep reference" reader. These audiences need different documents.

**Recommendations:**
1. Add the Intake phase to `WORKFLOW_COMMANDS.md` or explicitly state it is a pre-workflow phase documented elsewhere.
2. Resolve the command naming inconsistency: pick one canonical form (the YAML `command` identifier) and use it consistently, with aliases noted parenthetically.
3. Either add `complete-sprint` to the manifest YAML (with a `.yaml` definition file) or remove it from `WORKFLOW_COMMANDS.md`.
4. Add a brief mention of `common-ground` as a utility command available during any phase.
5. For the Astro site, split this into a conceptual overview page and individual command reference pages.

---

### 1.2 `docs/workflow/*.md` (Phase Overviews and Command Descriptions)

**Strengths:**
- Clean, consistent structure across all 18 files. Every phase overview has Purpose, Commands table, Outputs, Prerequisites, and Next Steps. Every command description has Overview, Inputs table, Outputs table, Prerequisites, and Next Steps.
- Inputs and outputs match the YAML definitions exactly in all files reviewed. This is strong evidence of either co-generation or disciplined manual maintenance.
- Next Steps sections create a navigable chain: each doc tells you where to go next, forming a complete user journey.
- Status badges (`**Status:** Planned`) on intake commands clearly communicate availability.

**Weaknesses:**
- **No common-ground phase overview.** There is a `docs/workflow/common-ground.md` command description, but no phase overview that contextualizes it. The manifest lists it under `utilities:`, not under a phase. The doc structure treats it as though it belongs to a phase.
- **No `complete-sprint` description.** There is no `docs/workflow/retrospective-complete-sprint.md`. The retrospective phase overview mentions only `complete-epic`. If `complete-sprint` is a valid command, it needs a description doc.
- **Phase names are inconsistent.** The manifest uses `retrospective` (singular). `WORKFLOW_COMMANDS.md` uses `Retrospectives` (plural). The phase overview file is `retrospective-phase.md` (singular). The command prefix in the manifest is `retrospectives:complete-epic` (plural). This inconsistency will cause confusion in code, docs, and URL generation.
- **Relative links may break in a docs site context.** All Next Steps links use relative paths like `[Planning Phase](planning-phase.md)`. These work within the `docs/workflow/` directory but will need transformation for a docs site with different URL structures.

**Recommendations:**
1. Decide whether `complete-sprint` exists in the system. If yes, create `docs/workflow/retrospective-complete-sprint.md` and add it to the manifest. If no, remove all references.
2. Standardize singular vs. plural: the manifest phase name, the YAML command prefix, the docs directory name, and the file naming convention should all agree.
3. Treat `common-ground` as a standalone utility in the docs structure (not shoehorned into a phase pattern).

---

### 1.3 `docs/COMMON_GROUND.md`

**Strengths:**
- Exceptionally well-written conceptual documentation. The Background & Motivation section (lines 16-41) provides genuine insight into the design rationale.
- The two-phase flow diagram (lines 69-88) clearly illustrates the interactive process.
- The confidence tiers (ESTABLISHED, WORKING, OPEN) are well-defined with practical examples and behavior descriptions.
- The use cases section (lines 328-372) maps real scenarios to specific command flags.

**Weaknesses:**
- **Typo on line 176.** "groundin file" should be "grounding file."
- **Overlap with README.** The README (lines 182-227) duplicates the confidence tier explanation and the `--graph` mermaid example. When this content moves to a docs site, the README version should be a brief pointer.
- **No link to the workflow docs.** The Related Documentation section links to `WORKFLOW_COMMANDS.md` and `ATLASSIAN_MCP_SETUP.md`, but does not link to the `docs/workflow/common-ground.md` command description or the YAML definition. A reader in the workflow mindset has no bridge from here to the workflow system.
- **No link FROM workflow docs.** `WORKFLOW_COMMANDS.md` does not mention or link to `COMMON_GROUND.md` at all. The two documentation trees are disconnected.

**Recommendations:**
1. Fix the "groundin file" typo.
2. Add a link to `docs/workflow/common-ground.md` in the Related Documentation section.
3. Add a link to `docs/COMMON_GROUND.md` from within `WORKFLOW_COMMANDS.md` (perhaps in a "Utility Commands" section).
4. For the Astro site, deduplicate the README and `COMMON_GROUND.md` versions of the confidence tier explanation.

---

### 1.4 `docs/ATLASSIAN_MCP_SETUP.md`

**Strengths:**
- Excellent task-oriented structure. A user can follow from top to bottom and end up with a working setup.
- Covers both Cloud and Server/Data Center configurations.
- The Quick Start Checklist (lines 453-461) is a useful verification artifact.
- Security considerations are thorough: credential protection, read-only mode, space/project filtering, audit trail, and token revocation.
- Environment variable reference tables (lines 421-449) serve as a quick lookup.

**Weaknesses:**
- **Only linked from README and COMMON_GROUND.md.** `WORKFLOW_COMMANDS.md` does not link to this guide despite requiring Atlassian integration for all non-intake commands. A user reading the workflow docs and encountering Jira/Confluence references has no pointer to setup instructions.
- **Docker-only approach.** The guide assumes Docker. If a user cannot or does not want to run Docker, there is no alternative path (e.g., `npx` or `pip` installation of the MCP server).
- **No version pinning guidance.** The guide uses `:latest` for the Docker image. For production workflows, this is risky. A note about pinning to a specific version would be prudent.

**Recommendations:**
1. Add a link to `ATLASSIAN_MCP_SETUP.md` from the Integration Points section of `WORKFLOW_COMMANDS.md`.
2. Add a note about version pinning for the Docker image.
3. Mention alternatives to Docker if available, or explicitly state Docker is required.

---

### 1.5 `docs/local_skill_development.md`

**Strengths:**
- Solves a real problem clearly: how to test skill changes without releasing.
- The symlink workflow is well-explained with exact commands.
- Caveats section (lines 96-113) proactively addresses the most likely failure modes.
- Quick Reference section (lines 132-149) provides copy-paste commands.

**Weaknesses:**
- **Orphaned document.** No other document in the project links to this file. It is not referenced from README.md, CONTRIBUTING.md, or any guide. A contributor who needs it will not find it through navigation.
- **No mention of the workflow system.** The guide covers skill development but says nothing about developing or testing workflow commands. Given that commands have a parallel structure (YAML definitions, description docs, implementation `.md` files), a contributor working on workflow commands has no equivalent guide.
- **Placeholder paths.** The guide uses `<plugin>`, `<name>`, `<version>` as placeholders without providing a concrete example of what these look like for the claude-skills project specifically.

**Recommendations:**
1. Link this file from CONTRIBUTING.md and README.md (Documentation section).
2. Add a section or separate document for workflow command development.
3. Include one concrete example with actual claude-skills paths alongside the generic placeholders.

---

### 1.6 `commands/workflow-manifest.yaml`

**Strengths:**
- Clean DAG structure with typed dependency strengths (`required` vs. `recommended`).
- `optional: true` on discovery phase correctly models the skippable nature of that phase.
- `external_skills` reference to `feature-forge` documents the cross-cutting dependency.
- `run_once: true` on intake correctly distinguishes project-level from epic-level phases.

**Weaknesses:**
- **Missing `complete-sprint`.** The retrospective phase lists only `retrospectives:complete-epic`. The `complete-sprint` command exists as an implementation `.md` file but has no YAML definition and no manifest entry. This is the single largest manifest/docs mismatch.
- **No YAML definition files for intake commands exist as `.md` implementation files.** The YAML `path` fields point to `commands/intake/document-codebase.md`, `commands/intake/capture-behavior.md`, and `commands/intake/create-system-description.md`. None of these files exist on disk. The YAML `status: planned` field signals this is expected, but the schema documentation says "`Must resolve to an existing file when status: existing`" -- so the `planned` status makes this valid. However, the schema doc does not explicitly state that `planned` status exempts the path resolution rule.
- **Phase name mismatch.** The manifest uses `retrospective` (singular) but the command identifiers use `retrospectives:` (plural).

**Recommendations:**
1. Resolve the `complete-sprint` question: add it to the manifest or remove the orphaned `.md` file.
2. Make the planned-status path exemption explicit in the schema documentation.
3. Align the phase name and command prefix (both singular or both plural).

---

### 1.7 Command YAML Definitions (Sample of 6)

**Strengths:**
- 100% schema compliance across all 12 files reviewed. Every file has `command`, `phase` (where applicable), `path`, `description`, `inputs`, `outputs`, `requires`, `status`, `argument-hint`, and `repeat`.
- Input/output types are consistent and match the schema's allowed values.
- The `description` field correctly points to the corresponding `docs/workflow/*.md` file in every case.
- `requires` fields accurately distinguish commands needing ticketing/documentation backends from those that do not.

**Weaknesses:**
- **Intake commands point to non-existent implementation files.** `commands/intake/document-codebase.yaml` has `path: commands/intake/document-codebase.md` but this file does not exist. Same for the other two intake commands. The `status: planned` field explains this, but a CI validation step should catch it.
- **`common-ground.yaml` has no `phase` field.** This is correct per the schema (utilities omit `phase`), but is inconsistent with the schema documentation which lists `phase` as required. The schema doc should explicitly state that `phase` is omitted for utility commands.

**Recommendations:**
1. Add a CI validation that verifies `path` files exist when `status: existing`.
2. Clarify in the schema documentation that `phase` is omitted for utility commands.

---

## 2. Workflow Documentation Gap Analysis

### Commands Documented vs. Commands in YAML

| Command | YAML Def | Manifest | `WORKFLOW_COMMANDS.md` | `docs/workflow/` desc | Implementation `.md` |
|---------|----------|----------|------------------------|----------------------|---------------------|
| `intake:document-codebase` | Yes | Yes | **NO** | Yes | **NO** (planned) |
| `intake:capture-behavior` | Yes | Yes | **NO** | Yes | **NO** (planned) |
| `intake:create-system-description` | Yes | Yes | **NO** | Yes | **NO** (planned) |
| `discovery:create` | Yes | Yes | Yes | Yes | Yes |
| `discovery:synthesize` | Yes | Yes | Yes | Yes | Yes |
| `discovery:approve` | Yes | Yes | Yes | Yes | Yes |
| `planning:epic-plan` | Yes | Yes | Yes | Yes | Yes |
| `planning:impl-plan` | Yes | Yes | Yes | Yes | Yes |
| `execution:execute-ticket` | Yes | Yes | Yes | Yes | Yes |
| `execution:complete-ticket` | Yes | Yes | Yes | Yes | Yes |
| `retrospectives:complete-epic` | Yes | Yes | Yes | Yes | Yes |
| `retrospectives:complete-sprint` | **NO** | **NO** | Yes | **NO** | Yes |
| `common-ground` | Yes | Yes (utility) | **NO** | Yes | Yes |

### Phase Overviews

| Phase | Manifest | `WORKFLOW_COMMANDS.md` | `docs/workflow/` overview |
|-------|----------|------------------------|--------------------------|
| Intake | Yes | **NO** | Yes |
| Discovery | Yes | Yes | Yes |
| Planning | Yes | Yes | Yes |
| Execution | Yes | Yes | Yes |
| Retrospective | Yes | Yes | Yes |

### Key Gaps

1. **Intake phase entirely absent from `WORKFLOW_COMMANDS.md`.** Three commands undocumented in the primary reference.
2. **`complete-sprint` exists as implementation and in `WORKFLOW_COMMANDS.md` but has no YAML definition or manifest entry.** This is a ghost command -- documented but not formally defined.
3. **`common-ground` absent from `WORKFLOW_COMMANDS.md`.** Documented in its own guide (`COMMON_GROUND.md`) but invisible in the workflow reference.
4. **README claims 9 workflows.** The manifest defines 12 commands + 1 utility. The README's Project Workflow Commands table lists 9 commands (matching `WORKFLOW_COMMANDS.md`, not the manifest). The count depends on whether intake and common-ground are included.

---

## 3. Proposed Restructuring for Astro + Starlight

### Content Architecture

The existing three-layer documentation (README overview, `WORKFLOW_COMMANDS.md` reference, `docs/workflow/` descriptions) should map to Starlight's built-in structure.

```
Site Structure:
/workflows/                          <- Landing page: DAG diagram, phase cards
/workflows/intake/                   <- Phase overview (from intake-phase.md)
/workflows/intake/document-codebase/ <- Command page (generated from YAML + description .md)
/workflows/intake/capture-behavior/
/workflows/intake/create-system-description/
/workflows/discovery/                <- Phase overview
/workflows/discovery/create/
/workflows/discovery/synthesize/
/workflows/discovery/approve/
/workflows/planning/
/workflows/planning/epic-plan/
/workflows/planning/impl-plan/
/workflows/execution/
/workflows/execution/execute-ticket/
/workflows/execution/complete-ticket/
/workflows/retrospective/
/workflows/retrospective/complete-epic/
/workflows/retrospective/complete-sprint/   <- Only if formalized
/utilities/common-ground/            <- Standalone utility page
/guides/atlassian-setup/             <- Setup guide
/guides/local-development/           <- Development workflow
/guides/getting-started/             <- New: entry point for new users
```

### Page Templates

**Phase Overview Page** (generated from `docs/workflow/{phase}-phase.md` + manifest data):
- Purpose statement
- DAG position indicator (which phases come before/after)
- Command cards with status badges
- Prerequisites
- Next phase link

**Command Reference Page** (generated from YAML definition + `docs/workflow/{command}.md`):
- Command signature with argument hints
- Status badge (existing/planned/deprecated)
- Inputs table (from YAML)
- Outputs table (from YAML)
- Requirements badges (ticketing, documentation)
- Overview narrative (from description `.md`)
- Prerequisites
- Next Steps
- Phase breadcrumb

**Utility Page** (for commands like `common-ground`):
- Same as command reference but without phase context
- Links to the conceptual guide (`COMMON_GROUND.md`)

### What to Retire

- **`WORKFLOW_COMMANDS.md` as a single file.** Its content splits across the phase overview pages and command reference pages. The mermaid diagrams move to the phase overview pages. The checkpoint system documentation becomes a standalone guide at `/guides/checkpoints/`. The integration points section becomes `/guides/atlassian-setup/` (merged with current `ATLASSIAN_MCP_SETUP.md`).
- **Duplicated content in README.** The Project Workflow Commands section in README becomes a brief paragraph pointing to `/workflows/`. The `common-ground` section in README becomes a brief paragraph pointing to `/utilities/common-ground/`.

### What to Create

1. **Getting Started guide.** The biggest gap for new users. Currently, a user must read: README (installation) -> ATLASSIAN_MCP_SETUP.md (MCP config) -> WORKFLOW_COMMANDS.md (understand the system) -> docs/workflow/ files (individual commands). A single "Getting Started with Workflows" guide should walk through: install -> configure Atlassian -> run your first planning cycle.
2. **Checkpoint System guide.** Currently buried in `WORKFLOW_COMMANDS.md`. Deserves its own page since it is a cross-cutting concern.
3. **Workflow FAQ/Troubleshooting.** Common questions like "Can I skip discovery?" or "What if a ticket has no implementation details?" are answered implicitly in the docs but not collected anywhere.

---

## 4. Recommendations for Standalone Pages

Each `docs/workflow/*.md` file is close to being a usable standalone page already. To make them fully independent:

### Required Additions Per Command Page

1. **Command invocation syntax.** Add the actual slash-command syntax at the top. Currently the description docs do not include how to invoke the command (e.g., `/project:discovery:create <epic-key>`). Only `WORKFLOW_COMMANDS.md` has this.
2. **Phase context breadcrumb.** Add a one-line note: "Part of the Discovery phase. Comes after `intake:create-system-description`. Feeds into `discovery:synthesize`."
3. **Requirements callout.** Add a visible callout for external dependencies: "Requires: Jira, Confluence. See [Atlassian Setup Guide](...)."
4. **Status visibility.** The intake commands have a status badge, but the existing commands do not explicitly state they are available. Add a consistent status indicator to all pages.

### Required Additions Per Phase Page

1. **DAG context.** Add which phases depend on this phase and which this phase depends on (pulling from the manifest's `depends_on` field).
2. **Skip conditions.** For optional phases (discovery), state when and how to skip.
3. **External skill dependencies.** The manifest's `external_skills` field (e.g., feature-forge as prerequisite for discovery) should be surfaced in the phase overview.

---

## 5. Priority Ranking

### Critical (Must fix before next release)

1. **Resolve `complete-sprint` status.** Either add YAML definition + manifest entry, or remove from `WORKFLOW_COMMANDS.md` and delete the orphaned implementation file. The current state is contradictory.
2. **Fix phase name inconsistency.** `retrospective` (manifest phase name) vs. `retrospectives` (command prefix). This will cause bugs in any automated tooling that derives one from the other.
3. **Add Intake phase to `WORKFLOW_COMMANDS.md`.** Three commands are invisible to anyone reading the primary workflow reference.

### High (Should fix for docs site launch)

4. **Standardize command naming.** Establish one canonical name per command and document aliases. Current state: `create-epic-discovery` (WORKFLOW_COMMANDS.md) vs. `discovery:create` (manifest) vs. `/project:discovery:create-epic-discovery` (full invocation path).
5. **Cross-link `COMMON_GROUND.md` and `WORKFLOW_COMMANDS.md`.** These are companion documents with zero cross-references.
6. **Cross-link `ATLASSIAN_MCP_SETUP.md` from `WORKFLOW_COMMANDS.md` Integration Points section.** A reader encountering Jira/Confluence requirements needs the setup guide.
7. **Link `local_skill_development.md` from CONTRIBUTING.md and README.** Currently orphaned.
8. **Fix "groundin file" typo in `COMMON_GROUND.md` line 176.**
9. **Add invocation syntax to each `docs/workflow/` command description.** Currently, only `WORKFLOW_COMMANDS.md` shows how to actually invoke commands.

### Medium (Should fix for quality)

10. **Clarify schema documentation for planned-status path exemption.** The schema says `path` must resolve to an existing file but does not mention the `planned` exemption.
11. **Clarify schema documentation for utility command phase omission.** The schema says `phase` is required but utilities omit it.
12. **Create a Getting Started guide.** New users face a fragmented onboarding path across 4+ documents.
13. **Deduplicate README and `COMMON_GROUND.md` confidence tier explanations.** Same content appears in both.
14. **Add CI validation for YAML path resolution.** Catch broken `path` references automatically.
15. **Update README workflow count.** The README claims 9 workflows. The actual count depends on scope definition. Clarify what "workflow" means (commands? phases?) and update.

### Nice-to-Have (Future improvement)

16. **Add a workflow FAQ/troubleshooting page.** Collect implicit answers to common questions.
17. **Add version pinning guidance to `ATLASSIAN_MCP_SETUP.md`.** The `:latest` Docker tag is convenient but risky.
18. **Add a workflow command development guide.** `local_skill_development.md` covers skills but not commands.
19. **Create a checkpoint system standalone guide.** Currently buried in `WORKFLOW_COMMANDS.md` and worth surfacing independently.
20. **Add concrete path examples to `local_skill_development.md`.** Replace generic `<plugin>/<name>/<version>` with actual claude-skills values.

---

## 6. Cross-Reference Matrix

Documents that should link to each other but currently do not:

| From | To | Missing Link |
|------|----|--------------|
| `WORKFLOW_COMMANDS.md` | `COMMON_GROUND.md` | No mention of common-ground utility |
| `WORKFLOW_COMMANDS.md` | `ATLASSIAN_MCP_SETUP.md` | No link in Integration Points section |
| `WORKFLOW_COMMANDS.md` | `docs/workflow/intake-phase.md` | Entire intake phase absent |
| `WORKFLOW_COMMANDS.md` | `docs/workflow/common-ground.md` | No utility commands section |
| `COMMON_GROUND.md` | `docs/workflow/common-ground.md` | No link to the workflow-format description |
| `README.md` | `docs/local_skill_development.md` | Not listed in Documentation section |
| `CONTRIBUTING.md` | `docs/local_skill_development.md` | Not linked for contributors |
| `SKILLS_GUIDE.md` | `WORKFLOW_COMMANDS.md` | No cross-reference to workflows |
| `docs/workflow/retrospective-phase.md` | `complete-sprint` | Phase overview only lists `complete-epic` |

---

## 7. Summary Metrics

| Metric | Count |
|--------|-------|
| Total docs files audited | 26 |
| Total YAML definitions audited | 12 |
| Documentation gaps found | 6 (intake in WORKFLOW_COMMANDS, complete-sprint YAML, common-ground in WORKFLOW_COMMANDS, local dev orphan, cross-links, invocation syntax) |
| Naming inconsistencies found | 3 (command names, phase singular/plural, workflow count) |
| Broken or missing cross-references | 9 (see matrix above) |
| Typos found | 1 |
| Files with no inbound links | 2 (`local_skill_development.md`, `docs/workflow/workflow-definition-schema.md`) |
| Critical priority items | 3 |
| High priority items | 6 |
| Medium priority items | 6 |
| Nice-to-have items | 5 |

