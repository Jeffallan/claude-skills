# Feature: v0.5.0 Roadmap Consolidation & Workflow Definition Schema

## Overview

Reconcile the divergent sources of truth for the claude-skills project (four local v0.5.0 docs, stale ROADMAP.md, misaligned GitHub milestones) into a single consistent system. Introduce machine-readable YAML workflow definitions per command with a DAG mapping file, consolidate the v0.5.0 plan, re-triage all open GitHub issues into appropriate milestones, and update the roadmap. This establishes a local-first project tracking workflow that dogfoods the v0.5.0 backend adapter concept.

## Functional Requirements

### FR-001: Per-Command YAML Workflow Definition

When a workflow command exists, the system shall have a corresponding YAML definition file co-located with the command at `commands/{phase}/{command-name}.yaml` containing:

```yaml
command: "discovery:create"
phase: discovery
path: commands/discovery/create.md
description: docs/workflow/discovery-create.md   # link to long-form markdown
inputs:
  - name: topic
    type: string
    required: true
    description: "Value proposition, feature area, or research question"
  - name: sources
    type: file[]
    required: false
    description: "Markdown files, PDFs, URLs, meeting notes, feature-forge specs"
outputs:
  - name: discovery-workspace
    type: directory
    path: "docs/discovery/{topic}/"
requires:
  - documentation   # declares which backend capabilities this command needs
```

### FR-002: DAG Mapping File

The system shall have a single `commands/workflow-manifest.yaml` file that defines:
- Phase-level DAG (which phases depend on which)
- Per-phase command ordering (sequential vs parallel within a phase)

```yaml
phases:
  intake:
    description: docs/workflow/intake-phase.md
    depends_on: []
    commands:
      - command: intake:document-codebase
        order: 1
      - command: intake:capture-behavior
        order: 2
      - command: intake:create-system-description
        order: 3

  discovery:
    description: docs/workflow/discovery-phase.md
    depends_on:
      - intake: recommended    # not strictly required
    parallel_with:
      - product-discovery      # human-driven, runs alongside
    commands:
      - command: discovery:create
        order: 1
      - command: discovery:synthesize
        order: 2
      - command: discovery:approve
        order: 3

  planning:
    description: docs/workflow/planning-phase.md
    depends_on:
      - discovery: required
    commands:
      - command: planning:epic-plan
        order: 1
      - command: planning:impl-plan
        order: 2

  execution:
    description: docs/workflow/execution-phase.md
    depends_on:
      - planning: required
    commands:
      - command: execution:execute-ticket
        order: 1
        repeat: true
      - command: execution:complete-ticket
        order: 2
        repeat: true

  retrospective:
    description: docs/workflow/retrospective-phase.md
    depends_on:
      - execution: required
    commands:
      - command: retrospectives:complete-epic
        order: 1
```

### FR-003: Consolidated v0.5.0 Plan Document

When the consolidation is complete, the system shall have a single `docs/v0.5.0-plan.md` that merges content from `v0.5.0-ideas.md`, `v0.5.0-ideas-2.md`, and `v0.5.0-implementation.md` into one authoritative document containing:
- Scope summary (what's in v0.5.0, what's deferred)
- Architecture decisions (backend adapter pattern, namespace changes)
- Implementation chunks with dependency graph
- File manifest (new, modified, deleted)
- Links to corresponding GitHub issues

### FR-004: Restructured Narrative Document

The narrative (`docs/v0.5.0-narrative.md`) shall be restructured to follow a per-command format:
- Each workflow command gets a section with: overview, inputs (what it receives), process (what it does), outputs (what it produces), next steps
- References the YAML definitions for machine-readable metadata
- Remains human-readable prose, not YAML

### FR-005: GitHub Issue Re-Triage

When re-triage is complete:

**Milestone structure:**
- **v0.5.0** — Workflow overhaul: backend adapters, intake commands, discovery rework, feature-forge integration, namespace/directory restructure, YAML workflow definitions
- **v0.6.0** — Global-to-local config migration: per-project skill activation, meta-skill/project analyzer, `.claude/skills/` local install strategy (see Discussion #112). #50-55 (context persistence, state validation, error recovery, shared templates, testing infra) move here as they depend on local config
- **v0.7.0+** — Enhanced skill routing (#64-72, pending feasibility evaluation: which are achievable as skills vs. need third-party tooling), common-ground improvements (#108-111, also depend on local config migration and need optimal invocation points defined within the new workflow)

**Issue movements:**
- #50-55 shall be moved from v0.5.0 to v0.6.0 (depend on local config migration)
- #65, #66, #69 shall be moved from v0.5.0 to v0.7.0 (skill content work)
- #68 shall be moved from v0.5.0 to v0.7.0 (deferred quick win)
- #67 shall be closed (deep linking → #69, context sharing → deferred to v0.6.0)
- #64 shall be updated as consolidated issue (absorbs #70, #71, #72 scope), converted to GitHub Discussion, labeled 'needs-third-party'
- #70, #71, #72 shall be closed as duplicates referencing the #64 Discussion
- #62 stays in v0.5.0 (core workflow generalization)
- #103 (epic creation) shall be assigned to v0.5.0 (addressed by discovery rework)
- #109 (common-ground local storage) shall be assigned to v0.6.0 (part of local config migration)
- #108, #110, #111 (common-ground enhancements) shall be assigned to v0.7.0+ (depend on v0.6.0 local config + new workflow being established)
- #106 (GitHub Pages docs), #107 (CI/CD) stay unmilestoned (infrastructure work, not tied to a specific release)
- #98 (example workflow docs), #100 (cross-reference validation) stay unmilestoned as good-first-issues
- New GitHub issues shall be created for v0.5.0 work described in the docs but lacking issues (intake commands, backend adapters, feature-forge integration, directory restructure, YAML schema, narrative restructure)

### FR-006: Roadmap Update

The `ROADMAP.md` shall be updated to:
- Mark v0.3.0 and v0.4.0 as completed (with actual release dates)
- Rewrite v0.5.0 to reflect the workflow overhaul scope from the consolidated plan
- Add v0.6.0 section: global-to-local config migration (Discussion #112), per-project skill activation, #50-55 workflow infra
- Add v0.7.0 section: enhanced skill routing (#64-72, with note on feasibility evaluation needed), common-ground improvements (#108-111), optimal common-ground invocation points within new workflow
- Rewrite v0.8.0+ / v1.0.0 sections to reflect updated understanding
- Link to GitHub issues and the consolidated plan doc
- Update version/count references to current (v0.4.2)

### FR-007: Cleanup of Superseded Documents

When consolidation is complete:
- `docs/v0.5.0-ideas.md` shall be deleted (superseded by consolidated plan)
- `docs/v0.5.0-ideas-2.md` shall be deleted (merged into consolidated plan)
- `docs/v0.5.0-implementation.md` shall be deleted (merged into consolidated plan)
- `docs/v0.5.0-narrative.md` shall be rewritten in place (restructured format)

## Non-Functional Requirements

### Consistency
- Every open GitHub issue shall belong to exactly one milestone
- Every v0.5.0 implementation chunk shall have at least one corresponding GitHub issue
- ROADMAP.md milestone descriptions shall match GitHub milestone descriptions
- YAML definitions shall cover all 11 workflow commands from the v0.5.0 plan

### Maintainability
- YAML schema shall be documented with a JSON Schema or inline comments
- Workflow manifest shall be validatable by `scripts/validate-skills.py` (extended)
- Adding a new command requires: 1 YAML file, 1 command .md, 1 entry in manifest, 1 overview .md

### Compatibility
- YAML definitions shall not break existing command .md files
- Existing command frontmatter format shall be preserved (YAML definitions are additive)
- `scripts/update-docs.py` shall exclude `.yaml` files from workflow count

## Acceptance Criteria

### AC-001: YAML definitions exist for all workflow commands
Given the v0.5.0 plan defines 11 workflow commands
When all YAML files are created
Then `ls commands/*/*.yaml | wc -l` returns 11
And each YAML file parses without error
And each `path` field points to an existing command .md file

### AC-002: DAG manifest is valid and complete
Given the workflow-manifest.yaml exists
When parsed
Then all phase `depends_on` references resolve to defined phases
And all `command` references in phase ordering match existing YAML definition files
And the DAG has no cycles

### AC-003: Consolidated plan replaces all v0.5.0 docs
Given the consolidated `docs/v0.5.0-plan.md` exists
When the three superseded docs are deleted
Then no information is lost (all decisions, file manifests, dependency graphs are present in the new doc)
And the narrative doc is restructured with per-command input/output format

### AC-004: GitHub milestones are consistent
Given all open issues have been triaged
When viewing GitHub milestones
Then v0.5.0 contains only workflow-overhaul-related issues
And v0.6.0+ milestones exist for deferred features
And every v0.5.0 implementation chunk has at least one GitHub issue
And no issue is unmilestoned (except `good first issue` items if intentional)

### AC-005: Roadmap reflects reality
Given ROADMAP.md is updated
When comparing to GitHub milestones
Then completed versions (v0.3.0, v0.4.0, v0.4.x) are marked as released
And v0.5.0 scope matches the consolidated plan doc
And v0.6.0+ sections exist for deferred work
And all issue links resolve to existing GitHub issues

## Error Handling

| Condition | Response |
|-----------|----------|
| YAML parse error in command definition | `validate-skills.py` reports file and line number |
| DAG cycle detected in manifest | Validation script reports the cycle path |
| Orphaned command (YAML exists, no .md) | Validation warning |
| Orphaned .md (command exists, no YAML) | Validation warning (graceful — YAML is additive) |
| GitHub issue referenced in plan but closed/deleted | Roadmap update flags broken links |

## Implementation TODO

### Phase 1: YAML Schema & Definitions
- [ ] Define YAML schema for per-command workflow definitions (document in `commands/references/workflow-definition-schema.md`)
- [ ] Create `.yaml` files for all 11 commands (3 intake, 3 discovery, 2 planning, 2 execution, 1 retrospective)
- [ ] Create `commands/workflow-manifest.yaml` with phase DAG and per-phase ordering
- [ ] Create `docs/workflow/` directory with per-phase and per-command overview markdown files

### Phase 2: Document Consolidation
- [ ] Merge `v0.5.0-ideas.md`, `v0.5.0-ideas-2.md`, `v0.5.0-implementation.md` into `docs/v0.5.0-plan.md`
- [ ] Restructure `docs/v0.5.0-narrative.md` with per-command input/output format
- [ ] Delete superseded docs
- [ ] Cross-link plan doc ↔ GitHub issues ↔ YAML definitions

### Phase 3: GitHub Issue Re-Triage
- [ ] Create milestone: v0.6.0 (global-to-local config migration)
- [ ] Create milestone: v0.7.0 (enhanced skill routing + common-ground)

**v0.5.0 assignments:**
- [ ] Keep #62 in v0.5.0 (core workflow generalization)
- [ ] Assign #103 to v0.5.0 (discovery rework covers this)

**v0.6.0 assignments:**
- [ ] Move #50-55 from v0.5.0 to v0.6.0 (depend on local config)
- [ ] Assign #109 to v0.6.0 (local config migration)

**v0.7.0 assignments:**
- [ ] Move #65, #66, #69 from v0.5.0 to v0.7.0 (skill content work)
- [ ] Move #68 from v0.5.0 to v0.7.0 (deferred diagram generation)
- [ ] Assign #108, #110, #111 to v0.7.0 (common-ground enhancements)

**Closures:**
- [ ] Close #67 (deep linking → #69, context sharing → deferred to v0.6.0)
- [ ] Close #70, #71, #72 as duplicates (merged into #64)
- [ ] Update #64 body to consolidate scope from #70, #71, #72
- [ ] Convert #64 to GitHub Discussion, label 'needs-third-party'

**No milestone:**
- [ ] Leave #98, #100 unmilestoned (good-first-issues)
- [ ] Leave #106, #107 unmilestoned (infrastructure, not release-tied)

**New issues to create for v0.5.0:**
- [ ] Backend adapter reference files (Phase 1 of v0.5.0 plan)
- [ ] Intake commands (document-codebase, capture-behavior, create-system-description)
- [ ] Discovery command rework (topic-based, local-first)
- [ ] Feature-forge integration (system description context, discovery recommendation)
- [ ] Namespace change + directory restructure
- [ ] YAML workflow definition schema + DAG manifest
- [ ] Narrative document restructure
- [ ] CI portability check (`npx skills` detection in GitHub Actions)

**Verification:**
- [ ] Every open issue has a milestone (except #98, #100, #106, #107)
- [ ] No issue is assigned to multiple milestones

### Phase 4: Roadmap Update
- [ ] Mark v0.3.0 as completed (note actual release info)
- [ ] Mark v0.4.0, v0.4.1, v0.4.2 as completed
- [ ] Rewrite v0.5.0 section: workflow overhaul (backend adapters, intake, discovery rework, feature-forge integration, namespace/directory restructure, YAML workflow definitions)
- [ ] Add v0.6.0 section: global-to-local config migration (Discussion #112, meta-skill/project analyzer, per-project `.claude/skills/`, #50-55 workflow infra)
- [ ] Add v0.7.0 section: enhanced skill routing (#64-72 with feasibility notes), common-ground improvements (#108-111), common-ground invocation points in new workflow
- [ ] Update v0.8.0+ / v1.0.0 sections to reflect updated roadmap
- [ ] Update development timeline ASCII diagram
- [ ] Run `python scripts/update-docs.py` to sync counts

### Phase 5: Validation Script Extension
- [ ] Extend `scripts/validate-skills.py` to validate `.yaml` workflow definitions
- [ ] Add DAG cycle detection for `workflow-manifest.yaml`
- [ ] Add orphan detection (YAML without .md, .md without YAML)
- [ ] Ensure `scripts/update-docs.py` excludes `.yaml` from workflow count

### Phase 6: CI Portability Check
- [ ] Add GitHub Action that runs `npx skills add . --non-interactive --list` on PRs
- [ ] Assert detected skill count matches expected count from `version.json`
- [ ] Catches portability regressions that `validate-skills.py` (project-specific) would miss
- [ ] Validates skills remain discoverable by the standard ecosystem tooling (`add-skill`/`skills` CLI, VS Code Copilot, OpenCode, etc.)

## Out of Scope

- **Actually implementing the v0.5.0 backend adapters** — this spec only consolidates the plan and tracking; the adapter code is separate work
- **Docusaurus setup** — noted as a future CI concern in the v0.5.0 plan; not part of this consolidation
- **Automated DAG visualization** — generating mermaid/graphviz from the YAML manifest is a follow-up
- **Migrating existing non-standard frontmatter fields** — `triggers`, `role`, `scope`, `output-format` are tolerated by ecosystem tooling (confirmed: `npx skills` detects all 65 skills). Migration to `metadata.*` is tech debt, not blocking. Tracked separately if needed.

## Resolved Decisions

- **#50-55 → v0.6.0.** These depend on the global-to-local config migration (Discussion #112). Context persistence, state validation, error recovery, shared templates, and testing infra are all easier to implement with per-project config.
- **#98, #100 stay unmilestoned.** Good-first-issues, no milestone needed.
- **v0.6.0 = global-to-local config migration.** The meta-skill/project analyzer from Discussion #112, per-project `.claude/skills/`, selective skill activation. This is the prerequisite for both workflow infra (#50-55) and enhanced routing.
- **v0.7.0 = enhanced skill routing + common-ground.** #64-72 require feasibility triage (some may need third-party tooling rather than pure skill implementations). #108-111 (common-ground) also land here, dependent on v0.6.0 local config being in place. Additionally, optimal common-ground invocation points within the new v0.5.0 workflow need to be identified.
- **Epic terminology retained.** Per v0.5.0-ideas-2.md resolved decisions.
- **Discovery trigger via feature-forge.** "Needs additional discovery" as standing interview option, per v0.5.0-ideas-2.md.
- **Non-standard frontmatter fields are tolerated.** Confirmed via `npx skills add . --list`: all 65 skills detected despite non-standard top-level fields (`triggers`, `role`, `scope`, `output-format`). These fields are not part of the Agent Skills spec but don't break ecosystem tooling. Migration to `metadata.*` is optional tech debt.
- **#69 metadata enhancement must use `metadata` field.** Any NEW metadata (relationship data, domain tags, etc.) must go under the spec's `metadata` key — not as new top-level frontmatter fields. This maintains spec compliance and ecosystem portability. Existing non-standard top-level fields are grandfathered for now.
- **CI portability check via `npx skills`.** Added as a GitHub Action to catch regressions in ecosystem detection. Asserts skill count matches `version.json`.

## #64-72 Feasibility Triage Results

### Achievable as skill work (keep in v0.7.0)
- **#69 — Metadata Enhancement.** Schema/content work using `metadata.*` field. Prerequisite for #65.
- **#65 — Cross-Domain Recommendations.** Enhance Related Skills sections across all skills. Content work. Depends on #69.
- **#66 — Enhanced Routing Logic.** Better descriptions/triggers (content work). Partially addressed by v0.6.0 local config (fewer skills = fewer false positives). Consider merging with #69.

### Needs splitting (decompose into skill work + deferred)
- **#67 — Related Skills Integration.** → Close. Deep linking merges into #69 (metadata enhancement). Context sharing deferred to v0.6.0 — Common Ground local config migration provides a natural foundation for shared skill state. No new issue needed; revisit during v0.6.0 planning.
- **#68 — Skill Dependency Mapping.** → Defer (keep open). Static mermaid diagram generation is a quick win for later. Interactive web visualization is out of scope.

### Needs third-party tooling — consolidated into Discussion
- **#64 — Smart Skill Discovery.** Consolidates #70, #71, #72. Updated to reflect the full scope: semantic search/ranking (vector embeddings + MCP tool), context analysis, description indexing, usage-history-based routing. Converted to GitHub Discussion since the work is exploratory/needs-third-party. Close #70, #71, #72 as duplicates referencing the Discussion.
- **#70 — Context Analysis Algorithms.** → Close. Merged into #64 Discussion.
- **#71 — Description Indexing.** → Close. Keyword optimization merged into #69. Semantic search merged into #64 Discussion.
- **#72 — Routing Table Intelligence.** → Close. Static routing merged into #66. Dynamic/history-based routing merged into #64 Discussion.

## Remaining Open Questions

All questions resolved.

- [x] ~~Should #106 and #107 be milestoned?~~ **No.** Leave unmilestoned.
- [x] ~~For #64-72 feasibility triage: what's the process?~~ **Batch evaluation.** Results documented above.
- [x] ~~For #64, #70, #71, #72?~~ **Consolidate into #64, convert to Discussion.** Close #70, #71, #72 as duplicates.
- [x] ~~For #67 context sharing?~~ **Defer to v0.6.0.** Close #67; deep linking → #69, context sharing → revisit during Common Ground migration.
- [x] ~~For #68 static diagram?~~ **Defer.** Keep open in v0.7.0.
