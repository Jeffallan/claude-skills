# v0.5.0 Plan: Workflow Overhaul

## Scope

Decouple workflow commands from Jira/Confluence, add per-project backend configuration, create a project intake phase, rework discovery for product-centric workflows, integrate feature-forge into the pipeline, and fix the epic creation gap.

**What's in v0.5.0:**
- Backend adapter pattern — per-project config for ticketing (local/Jira/GitHub Issues) and documentation (local/Confluence/GitHub Wiki)
- Namespace change — `project:phase:action` becomes `phase:action`
- 11 commands (3 new intake, 7 reworked, 1 removed)
- Discovery rework — topic-based, local-first, produces epics AND tickets (#103 fix)
- Feature-forge integration — system description context, discovery recommendation, skill-aware tickets
- Intake commands — document-codebase, capture-behavior, create-system-description
- Directory restructure — `commands/project/` flattened to `commands/`
- YAML workflow definitions and DAG manifest (Phase 1 — completed)

**What's deferred:**
- v0.6.0: Global-to-local config migration (Discussion #112), per-project skill activation, #50-55 (context persistence, state validation, error recovery, shared templates, testing infra)
- v0.7.0+: Enhanced skill routing (#64-72, feasibility evaluation pending), common-ground improvements (#108-111), optimal common-ground invocation points within new workflow
- #65/#66/#69/#68 moved to v0.7.0 (skill content work, dependency mapping)

**Links:**
- Narrative walkthrough: [`docs/v0.5.0-narrative.md`](v0.5.0-narrative.md)
- YAML schema: [`docs/workflow/workflow-definition-schema.md`](workflow/workflow-definition-schema.md)
- Workflow manifest: [`commands/workflow-manifest.yaml`](../commands/workflow-manifest.yaml)

---

## Architecture Decisions

### Backend Adapter Pattern

Every command gains a Phase 0 config resolution step that loads backend-specific reference files:

```
.claude/workflow-config.json (in consumer project)
    ├── ticketing: "local" | "jira" | "github-issues"
    └── documentation: "local" | "confluence" | "github-wiki"

Command Phase 0:
  1. Read .claude/workflow-config.json (default: local/local)
  2. Load references/ticketing-{backend}.md
  3. Load references/docs-{backend}.md
  4. Proceed with abstract operations
```

All commands replace hardcoded Jira/Confluence operations with abstract verbs ("create ticket", "publish document") and a routing table to backend-specific reference files.

### Namespace Change

Drop the `project:` prefix. Use `phase:action` format:

| Old | New |
|-----|-----|
| `project:discovery:create-epic-discovery` | `discovery:create` |
| `project:discovery:synthesize-discovery` | `discovery:synthesize` |
| `project:discovery:approve-synthesis` | `discovery:approve` |
| `project:planning:create-epic-plan` | `planning:epic-plan` |
| `project:planning:create-implementation-plan` | `planning:impl-plan` |
| `project:execution:execute-ticket` | `execution:execute-ticket` |
| `project:execution:complete-ticket` | `execution:complete-ticket` |
| `project:retrospectives:complete-epic` | `retrospectives:complete-epic` |
| `project:retrospectives:complete-sprint` | **REMOVED** |
| *(new)* | `intake:document-codebase` |
| *(new)* | `intake:capture-behavior` |
| *(new)* | `intake:create-system-description` |

### Command Count: 11

- 3 new (intake)
- 1 removed (complete-sprint — retros at epic level only)
- 7 existing (reworked)

### Discovery Rework: Topic-Based, Not Jira-Epic-Based

Discovery starts from a **topic** (value proposition, feature area, research question), not a pre-existing Jira epic. It PRODUCES epics and tickets, fixing the epic creation gap (#103). Local-first input: markdown files, PDFs, URLs, meeting notes, feature-forge specs.

### Feature-Forge Discovery Integration

During the structured interview, every `AskUserQuestions` prompt includes a standing option: **"Needs additional discovery."** Flagged unknowns are collected and surfaced as a discovery recommendation at interview end, with options to run discovery, skip to planning, or handle research separately.

### Skill-Aware Ticket Generation

Both planning commands (`planning:epic-plan` and `planning:impl-plan`) read installed skills from the consumer project (`.claude-plugin/plugin.json` or local skill manifests) and use prompt engineering techniques to craft ticket descriptions that explicitly instruct agents to invoke the correct skill per implementation step. Example: a React component ticket embeds "Invoke `react-expert` for component implementation" in its description. This leverages the per-repo skill installation model — planning has full visibility into what skills are available and generates tickets that are skill-aware from the start.

---

## Workflow DAG

Different people may own different phases. The workflow is a DAG, not a strict sequence.

```
INTAKE (one-time)                      PRODUCT DISCOVERY (human-driven)
├─ intake:document-codebase            ├─ Value Propositions
├─ intake:capture-behavior             ├─ Customer Segments
└─ intake:create-system-description    ├─ Domain Research
         │                             └─ Feature Identification
         │                                    │
         │                            FEATURE DEFINITION (per feature)
         │                            └─ feature-forge → specs/{name}.spec.md
         │                                    │
         │                            DISCOVERY (when research needed, optional)
         │                            ├─ discovery:create (from topic, NOT from Jira epic)
         │                            ├─ [HUMAN RESEARCH]
         │                            ├─ discovery:synthesize (local docs, notes, artifacts)
         │                            └─ discovery:approve → creates EPICS + tickets
         │                                    │
         └───────────────┬────────────────────┘
                         │
                     PLANNING
                     ├─ planning:epic-plan (stakeholder-readable overview)
                     └─ planning:impl-plan (execution plan + skill-aware tickets)
                         │
                     EXECUTION
                     ├─ execution:execute-ticket × N
                     └─ execution:complete-ticket × N (incremental sys desc updates)
                         │
                     RETROSPECTIVE
                     └─ retrospectives:complete-epic (retro report + sys desc update)
```

**Key relationships:**
- Intake and Product Discovery run in **parallel** (independent)
- Feature-forge specs features BEFORE discovery commands run
- Discovery is **optional** — skip if feature spec is sufficient, use when unknowns need human research
- Discovery creates epics (not consumes them) — this is the #103 fix
- Common-ground runs **on demand** (future hooks per #111)

---

## Implementation Chunks

### Pre: YAML Workflow Definitions (COMPLETED)

**Phase:** 0 | **Status:** Done

YAML schema, per-command definition files, DAG manifest, and phase documentation created as part of the v0.5.0 roadmap consolidation spec.

**Deliverables:**
- [`docs/workflow/workflow-definition-schema.md`](workflow/workflow-definition-schema.md) — YAML schema documentation
- [`commands/workflow-manifest.yaml`](../commands/workflow-manifest.yaml) — Phase DAG and per-phase ordering
- 12 per-command YAML definitions (see [YAML Definitions](#yaml-definitions) below)
- 18 phase/command overview docs under `docs/workflow/`

**GitHub Issues:** Part of roadmap consolidation spec

---

### Chunk 1: Backend Adapter Foundation

**Phase:** 1 | **Depends on:** Nothing | **GitHub Issues:** #62 (core workflow generalization)

| What | Detail |
|------|--------|
| Create | 9 reference files at `commands/references/` (final path) |
| Fix | `scripts/update-docs.py` — exclude `references/` from workflow count |
| Scope | ~1,370 lines new + small script edit |

#### Files to Create

| File | Purpose | ~Lines |
|------|---------|--------|
| `commands/references/workflow-config-schema.md` | JSON schema for `.claude/workflow-config.json` with examples for each backend combo | 200 |
| `commands/references/config-resolution.md` | How commands resolve config: find file → validate → load backends → fallback to local | 120 |
| `commands/references/ticketing-local.md` | Local markdown tickets: YAML frontmatter + body in `docs/epics/{phase}/{epic}/tickets/` | 150 |
| `commands/references/ticketing-jira.md` | Jira operations via Atlassian MCP; cross-refs `atlassian-mcp` skill | 150 |
| `commands/references/ticketing-github-issues.md` | GitHub Issues via `gh` CLI; labels as status, milestones as epics | 150 |
| `commands/references/docs-local.md` | Local markdown docs in structured `docs/` folder mirroring Confluence paths | 150 |
| `commands/references/docs-confluence.md` | Confluence operations via Atlassian MCP; cross-refs `atlassian-mcp` skill | 150 |
| `commands/references/docs-github-wiki.md` | GitHub Wiki pages via `gh` CLI | 100 |
| `commands/references/local-docs-structure.md` | Full local directory structure with Docusaurus setup guidance | 200 |

#### Script Fix

**File:** `scripts/update-docs.py` (line 84-89)

`count_workflows()` uses `rglob("*.md")` which would count reference files. Fix to exclude `references/` subdirectories:

```python
def count_workflows(base_path: Path) -> int:
    """Count workflow command markdown files."""
    commands_dir = base_path / COMMANDS_DIR
    if not commands_dir.exists():
        return 0
    return sum(1 for f in commands_dir.rglob("*.md") if "references" not in f.parts)
```

#### Verification

```bash
python scripts/update-docs.py --check
# Should still report 9 workflows (refs not counted)
```

---

### Chunk 2: Decouple Non-Discovery Commands

**Phase:** 2 (partial) | **Depends on:** Chunk 1 | **GitHub Issues:** #62

| What | Detail |
|------|--------|
| Rewrite in place | 5 existing commands — abstract Jira/Confluence operations |
| Skip | `complete-sprint.md` — being deleted, no point decoupling |
| Per-file changes | Add Phase 0 config resolution, abstract all hardcoded operations, add routing table |
| Scope | 5 files, ~57 references abstracted |

#### Commands to Decouple

| Command File | Refs to Abstract | Key Changes | YAML Definition |
|-------------|-----------------|-------------|-----------------|
| `commands/project/planning/create-epic-plan.md` | 16 | JQL queries → "query child tickets"; 5 agent refs stay | [`epic-plan.yaml`](../commands/project/planning/epic-plan.yaml) |
| `commands/project/planning/create-implementation-plan.md` | 9 | Update Jira tickets → "update tickets"; Confluence plan → "publish plan" | [`impl-plan.yaml`](../commands/project/planning/impl-plan.yaml) |
| `commands/project/execution/execute-ticket.md` | 9 | Fetch Jira ticket → "fetch ticket"; status transitions abstracted | [`execute-ticket.yaml`](../commands/project/execution/execute-ticket.yaml) |
| `commands/project/execution/complete-ticket.md` | 12 | Transition Jira → "transition status"; Update Confluence → "update plan" | [`complete-ticket.yaml`](../commands/project/execution/complete-ticket.yaml) |
| `commands/project/retrospectives/complete-epic.md` | 11 | Close Jira → "close epic"; move Confluence pages → "move documents" | [`complete-epic.yaml`](../commands/project/retrospectives/complete-epic.yaml) |

Each command gets:
1. **Phase 0** — Config resolution step (load backend refs)
2. **Abstract operations** — All Jira/Confluence verbs replaced with generic verbs
3. **Routing table** — Footer section pointing to backend-specific reference files

#### Verification

```bash
# No hardcoded Jira/Confluence refs outside routing tables
grep -r "Jira\|Confluence\|JQL" commands/project/planning/ commands/project/execution/ commands/project/retrospectives/
# Should only appear in routing table comments, not in operational steps
```

---

### Chunk 3: Discovery Rework

**Phase:** 2+3 (merged) | **Depends on:** Chunk 1 | **GitHub Issues:** #62, #103

| What | Detail |
|------|--------|
| Full rewrite | 3 discovery commands in place |
| Key changes | Topic-based input (not Jira epic key), local-first sources, produces epics AND tickets, Phase 1.5 epic creation (#103 fix) |
| Scope | 3 files, full rewrites (~750 lines total) |

Merges Phase 2 decoupling with Phase 3 rework — no point abstracting refs in files getting fully rewritten.

#### 3.1 `create-epic-discovery.md` → topic-based discovery

**YAML Definition:** [`commands/project/discovery/create.yaml`](../commands/project/discovery/create.yaml)

**Current:** Takes a Jira epic key, fetches epic details, creates Confluence discovery page.

**New:** Takes a **topic** (value proposition, feature area, research question). Accepts local sources: markdown files, PDFs, URLs, meeting notes, feature-forge specs. Creates a structured discovery workspace (local or in doc system) with research questions, hypotheses, unknowns, domain context, stakeholder inputs. Does NOT require pre-existing ticketing artifacts.

#### 3.2 `synthesize-discovery.md` → local-first synthesis

**YAML Definition:** [`commands/project/discovery/synthesize.yaml`](../commands/project/discovery/synthesize.yaml)

**Current:** Takes Confluence URLs as input, publishes synthesis to Confluence.

**New:** Takes discovery workspace refs, local docs, research artifacts (not just Confluence URLs). Consolidates findings into actionable recommendations. Proposes **epics AND tickets** (not just tickets) with metadata. Output includes proposed epic structure aligned with value propositions.

#### 3.3 `approve-synthesis.md` → epic creation fix (#103)

**YAML Definition:** [`commands/project/discovery/approve.yaml`](../commands/project/discovery/approve.yaml)

**Current:** Assumes target epics exist in Jira. Creates tickets linked to existing epics.

**New:** Creates EPICS first, then tickets linked to epics. Adds Phase 1.5: Epic Verification & Creation:
- **A) Auto-create** — present epic details for approval, create in batch, record ID mappings
- **B) Map to existing** — query candidates, let user map proposed → existing epics
- **C) Skip** — proceed without epic links (warning)
- **D) Cancel** — abort for manual fix

Error handling with rollback on batch failure. Works with any configured ticketing backend.

#### Verification

```bash
# No hardcoded Jira/Confluence refs outside routing tables
grep -r "Jira\|Confluence\|JQL" commands/project/discovery/
# approve-synthesis.md contains Phase 1.5 epic creation flow
grep -c "Epic Verification" commands/project/discovery/approve-synthesis.md
```

---

### Chunk 4: Intake Commands

**Phase:** 4 | **Depends on:** Chunk 1 | **GitHub Issues:** New issue required (intake commands)

| What | Detail |
|------|--------|
| Create at final paths | 3 new commands under `commands/intake/` |
| Create refs | 2 reference files under `commands/intake/references/` |
| Scope | 5 new files (~1,300 lines) |

Independent of Chunks 2 and 3 — only needs Chunk 1.

#### 4.1 `commands/intake/document-codebase.md` (~250 lines)

**YAML Definition:** [`commands/intake/document-codebase.yaml`](../commands/intake/document-codebase.yaml)

```yaml
description: Use when onboarding a new project to add documentation to existing code
argument-hint: [--scope=<path>] [--format=<jsdoc|docstring|xml>]
```

**Workflow:** Scan codebase → identify undocumented functions/classes/modules → prioritize (public APIs first) → checkpoint approval → generate docstrings → output summary → pointer to `capture-behavior`

#### 4.2 `commands/intake/capture-behavior.md` (~250 lines)

**YAML Definition:** [`commands/intake/capture-behavior.yaml`](../commands/intake/capture-behavior.yaml)

```yaml
description: Use when capturing existing system behavior through tests for an undocumented codebase
argument-hint: [--scope=<path>] [--type=<unit|integration|both>]
```

**Workflow:** Scan code → identify untested behavior → analyze coverage gaps → checkpoint test plan → generate characterization tests (assert CURRENT behavior) → run tests → output summary → pointer to `create-system-description`

#### 4.3 `commands/intake/create-system-description.md` (~300 lines)

**YAML Definition:** [`commands/intake/create-system-description.yaml`](../commands/intake/create-system-description.yaml)

```yaml
description: Use when creating a living system description document for a project
argument-hint: [--output=<path>]
```

**Workflow:** Parallel agent analysis (architecture, security, API, data) → generate SOC2-style document:
- System Purpose & Scope
- System Components (services, databases, queues, caches)
- Data Flow Diagram (mermaid)
- Security Architecture
- API Surface Area
- External Dependencies
- Infrastructure Overview
- Change Management Process

**Output:** `docs/system-description.md` (configurable path)

#### 4.4 Reference Files

| File | Purpose | ~Lines |
|------|---------|--------|
| `commands/intake/references/characterization-tests.md` | Patterns for behavior-capturing tests across languages | 200 |
| `commands/intake/references/system-description-template.md` | Full SOC2-style template with examples for web apps, APIs, microservices | 300 |

#### Verification

```bash
# All files have valid frontmatter
head -5 commands/intake/*.md
# Reference files within 100-600 line range
wc -l commands/intake/references/*.md
```

---

### Chunk 5: Feature-Forge Integration

**Phase:** 5 | **Depends on:** Chunks 2, 3, and 4 | **GitHub Issues:** New issue required (feature-forge integration)

| What | Detail |
|------|--------|
| Update | `skills/feature-forge/SKILL.md` — system description context + discovery integration |
| Update | `skills/feature-forge/references/specification-template.md` — workflow integration + optional EARS |
| Create | `skills/feature-forge/references/system-context-integration.md` (~150 lines) |
| Update | Planning commands — read feature specs, skill-aware ticket descriptions |
| Update | `complete-ticket.md` — incremental system description updates |
| Update | `complete-epic.md` — holistic system description review |
| Scope | 1 new file + 6 files updated |

#### 5.1 Feature-Forge: System Description Context

**File:** `skills/feature-forge/SKILL.md`

Add Step 0 to Core Workflow:
> 0. **Context** — Check for `docs/system-description.md` (or path from config). If found, load as background context. Reference existing components/APIs during interviews. Skip questions the system description already answers.

#### 5.2 Feature-Forge: Output Boundaries

**File:** `skills/feature-forge/references/specification-template.md`

- Add `## Workflow Integration` section with epic target field
- Explicit note: "High-level TODOs only. Detailed implementation steps generated by `/planning:impl-plan`."
- Make EARS format **optional** — offer for complex features, simpler format for straightforward ones

#### 5.3 Feature-Forge: Discovery Integration

**File:** `skills/feature-forge/SKILL.md`

During the structured interview, every `AskUserQuestions` prompt about proposed functionality includes a standing option: **"Needs additional discovery."** When selected, feature-forge records the question topic as a flagged unknown and moves to the next question without blocking.

At interview end, if any unknowns were flagged:
1. Adds `## Discovery Recommendation` section to spec listing unknowns with original question context
2. Presents `AskUserQuestions` prompt:
   - **A) Run discovery (Recommended)** — create discovery workspace for flagged unknowns
   - **B) Skip to planning** — proceed with unknowns flagged as risks
   - **C) Handle research separately** — run `discovery:create` later

If no unknowns flagged, no recommendation shown.

#### 5.4 System Context Reference

**New file:** `skills/feature-forge/references/system-context-integration.md` (~150 lines)
- How to use system description sections during requirements gathering
- Which sections inform which interview questions
- How specs should reference system components
- How flagged unknowns map to discovery workspace research questions

#### 5.5 Planning Commands: Read Feature Specs + Skill-Aware Ticket Creation

**File:** `commands/project/planning/create-epic-plan.md`
**YAML Definition:** [`commands/project/planning/epic-plan.yaml`](../commands/project/planning/epic-plan.yaml)

Add to Phase 0:
> Check for `specs/{feature_name}.spec.md` related to this epic. If found, use requirements, acceptance criteria, and NFRs as input. Do not re-derive what the spec already defines.

**File:** `commands/project/planning/create-implementation-plan.md`
**YAML Definition:** [`commands/project/planning/impl-plan.yaml`](../commands/project/planning/impl-plan.yaml)

When generating self-contained ticket descriptions, read available skills at the project level (`.claude-plugin/plugin.json` or installed skill manifests) and craft prompts that invoke the correct skill per implementation step.

Example ticket description:
> **Suggested skill:** `react-expert` for component implementation, `test-master` for test suite

This is core to the v0.5.0 vision: planning has full visibility into what skills are available in the consumer project and generates tickets that are skill-aware from the start. Each ticket becomes self-contained with the right skill invocation embedded in its description.

#### 5.6 System Description Updates on Completion

**File:** `commands/project/execution/complete-ticket.md` — Add Step 4c:
**YAML Definition:** [`commands/project/execution/complete-ticket.yaml`](../commands/project/execution/complete-ticket.yaml)
> If changes affect APIs, external deps, security, or data models → propose targeted updates to `docs/system-description.md` → checkpoint approval → apply.

**File:** `commands/project/retrospectives/complete-epic.md` — Add to Phase 5:
**YAML Definition:** [`commands/project/retrospectives/complete-epic.yaml`](../commands/project/retrospectives/complete-epic.yaml)
> Review all changes across the epic. Update system description holistically. Update mermaid diagrams if architecture changed. Checkpoint approval.

#### Verification

```bash
python scripts/validate-skills.py --skill feature-forge
# Verify discovery integration
grep -c "additional discovery" skills/feature-forge/SKILL.md
# Verify spec reading in planning
grep -c "spec.md" commands/project/planning/create-epic-plan.md
```

---

### Chunk 6: Directory Restructure + Cleanup

**Phase:** 6 | **Depends on:** Chunks 1-5 (all content finalized) | **GitHub Issues:** New issue required (namespace change + directory restructure)

| What | Detail |
|------|--------|
| Move | 4 directories from `commands/project/` to `commands/` |
| Rename | 5 files to shorter names |
| Delete | `complete-sprint.md` |
| Update | `scripts/update-docs.py` — `COMMANDS_DIR` path + exclusions |
| Update | `.claude-plugin/plugin.json` — command paths and registered names |
| Scope | Mechanical moves/renames + 2 config updates |

#### Directory Moves

| Old Path | New Path |
|----------|----------|
| `commands/project/discovery/` | `commands/discovery/` |
| `commands/project/planning/` | `commands/planning/` |
| `commands/project/execution/` | `commands/execution/` |
| `commands/project/retrospectives/` | `commands/retrospectives/` |

#### File Renames

| Old Filename | New Filename |
|-------------|-------------|
| `create-epic-discovery.md` | `create.md` |
| `synthesize-discovery.md` | `synthesize.md` |
| `approve-synthesis.md` | `approve.md` |
| `create-epic-plan.md` | `epic-plan.md` |
| `create-implementation-plan.md` | `impl-plan.md` |

#### Deletions

| File | Reason |
|------|--------|
| `commands/project/retrospectives/complete-sprint.md` | Sprint retrospectives removed; retros at epic level only |

#### Script Update

**File:** `scripts/update-docs.py`

```python
COMMANDS_DIR = "commands"  # was "commands/project"

def count_workflows(base_path: Path) -> int:
    """Count workflow command markdown files."""
    commands_dir = base_path / COMMANDS_DIR
    if not commands_dir.exists():
        return 0
    return sum(
        1 for f in commands_dir.rglob("*.md")
        if "references" not in f.parts and "common-ground" not in f.parts
    )
```

#### Verification

```bash
# Old directory should be empty/gone
ls commands/project/ 2>&1
# Should show: No such file or directory

# Workflow count should be 11
python scripts/update-docs.py --dry-run

# No dangling references to old paths
grep -r "commands/project" commands/ scripts/ .claude-plugin/

# No references to complete-sprint
grep -r "complete-sprint" commands/ docs/ README.md
```

---

### Chunk 7: Documentation + Validation

**Phase:** 7+8 | **Depends on:** Chunk 6 | **GitHub Issues:** New issue required (narrative document restructure)

| What | Detail |
|------|--------|
| Major rewrite | `docs/WORKFLOW_COMMANDS.md` |
| Update | `README.md`, `SKILLS_GUIDE.md`, `ROADMAP.md`, `CHANGELOG.md`, `docs/ATLASSIAN_MCP_SETUP.md` |
| Bump | `version.json` → `0.5.0` |
| Propagate | `python scripts/update-docs.py` |
| Validate | Full validation suite |
| Regenerate | Social preview image |

#### Documentation Updates

| File | Changes |
|------|---------|
| `docs/WORKFLOW_COMMANDS.md` | Major rewrite: new namespace (`phase:action`), DAG lifecycle diagram, Configuration section, Intake Phase, discovery rework (topic-based), all backends, feature-forge integration, skill-aware tickets, command table (11 commands) |
| `SKILLS_GUIDE.md` | Add feature-forge workflow integration notes (system description context, discovery recommendation, output boundaries) |
| `README.md` | Update workflow section; note Atlassian MCP is now optional; add `.claude/workflow-config.json` reference; update directory structure |
| `ROADMAP.md` | Update #62, #103 status to completed; add intake phase items; update v0.5.0 section |
| `CHANGELOG.md` | Add v0.5.0 entry (Added: intake commands, backend adapters, discovery rework, feature-forge integration; Changed: namespace, directory structure; Removed: complete-sprint; Fixed: #103 epic creation) |
| `docs/ATLASSIAN_MCP_SETUP.md` | Add note: only needed when config specifies jira/confluence backends |
| `version.json` | Bump to `0.5.0` |
| `.claude-plugin/plugin.json` | Update keywords (add "local-first", "github-issues", "workflow-config") |

#### Validation Suite

```bash
# 1. Skill validation
python scripts/validate-skills.py

# 2. Doc counts in sync (should show 11 workflows)
python scripts/update-docs.py --check

# 3. No hardcoded Jira/Confluence refs in command files
grep -r "Jira\|Confluence\|JQL\|Atlassian" \
  commands/discovery/ commands/planning/ commands/execution/ \
  commands/retrospectives/ commands/intake/
# Should return nothing (only allowed in commands/references/)

# 4. All new files have valid frontmatter
python scripts/validate-skills.py

# 5. Reference files within 100-600 line range
find commands/ -path "*/references/*.md" -exec wc -l {} \;

# 6. No dangling references to deleted file
grep -r "complete-sprint" commands/ docs/ README.md SKILLS_GUIDE.md

# 7. Propagate final counts
python scripts/update-docs.py

# 8. Regenerate social preview
node ./assets/capture-screenshot.js
```

---

## File Manifest

### New Files (15 files, ~2,970 lines)

| Phase | File | ~Lines |
|-------|------|--------|
| 1 | `commands/references/workflow-config-schema.md` | 200 |
| 1 | `commands/references/config-resolution.md` | 120 |
| 1 | `commands/references/ticketing-local.md` | 150 |
| 1 | `commands/references/ticketing-jira.md` | 150 |
| 1 | `commands/references/ticketing-github-issues.md` | 150 |
| 1 | `commands/references/docs-local.md` | 150 |
| 1 | `commands/references/docs-confluence.md` | 150 |
| 1 | `commands/references/docs-github-wiki.md` | 100 |
| 1 | `commands/references/local-docs-structure.md` | 200 |
| 4 | `commands/intake/document-codebase.md` | 250 |
| 4 | `commands/intake/capture-behavior.md` | 250 |
| 4 | `commands/intake/create-system-description.md` | 300 |
| 4 | `commands/intake/references/characterization-tests.md` | 200 |
| 4 | `commands/intake/references/system-description-template.md` | 300 |
| 5 | `skills/feature-forge/references/system-context-integration.md` | 150 |

### Renamed/Moved Files (Phase 6 restructure)

| Old Path | New Path |
|----------|----------|
| `commands/project/discovery/create-epic-discovery.md` | `commands/discovery/create.md` |
| `commands/project/discovery/synthesize-discovery.md` | `commands/discovery/synthesize.md` |
| `commands/project/discovery/approve-synthesis.md` | `commands/discovery/approve.md` |
| `commands/project/planning/create-epic-plan.md` | `commands/planning/epic-plan.md` |
| `commands/project/planning/create-implementation-plan.md` | `commands/planning/impl-plan.md` |
| `commands/project/execution/execute-ticket.md` | `commands/execution/execute-ticket.md` |
| `commands/project/execution/complete-ticket.md` | `commands/execution/complete-ticket.md` |
| `commands/project/retrospectives/complete-epic.md` | `commands/retrospectives/complete-epic.md` |

### Deleted Files

| File | Reason |
|------|--------|
| `commands/project/retrospectives/complete-sprint.md` | Sprint retrospectives removed; retros at epic level only |

### Modified Files (updated to reflect Phase 1 completion)

| Phase | File | Change Scope |
|-------|------|-------------|
| 1+6 | `scripts/update-docs.py` | Fix `count_workflows()`, update `COMMANDS_DIR` |
| 2+3 | `commands/discovery/create.md` | Full rewrite: topic-based, not Jira-epic-based |
| 2+3 | `commands/discovery/synthesize.md` | Rewrite: local-first input, proposes epics + tickets |
| 2+3 | `commands/discovery/approve.md` | Rewrite: creates epics + tickets, Phase 1.5 epic creation |
| 2+5 | `commands/planning/epic-plan.md` | Abstract refs + read feature specs + skill-aware ticket descriptions |
| 2+5 | `commands/planning/impl-plan.md` | Abstract refs + skill-aware ticket creation |
| 2 | `commands/execution/execute-ticket.md` | Abstract 9 refs |
| 2+5 | `commands/execution/complete-ticket.md` | Abstract 12 refs + system desc update |
| 2+5 | `commands/retrospectives/complete-epic.md` | Abstract 11 refs + system desc update |
| 5 | `skills/feature-forge/SKILL.md` | Add system description context step + discovery integration |
| 5 | `skills/feature-forge/references/specification-template.md` | Workflow integration + optional EARS |
| 7 | `docs/WORKFLOW_COMMANDS.md` | Major rewrite |
| 7 | `SKILLS_GUIDE.md` | Feature-forge integration notes |
| 7 | `README.md` | Update workflow section + directory structure |
| 7 | `ROADMAP.md` | Update issue statuses |
| 7 | `CHANGELOG.md` | Add v0.5.0 entry |
| 7 | `docs/ATLASSIAN_MCP_SETUP.md` | Mark as optional |
| 7 | `version.json` | Bump to 0.5.0 |
| 7 | `.claude-plugin/plugin.json` | Update paths, names, keywords |

---

## YAML Definitions

All 12 per-command YAML definition files created in Phase 1 (completed):

| Command | YAML Definition | Phase Doc |
|---------|----------------|-----------|
| `intake:document-codebase` | [`commands/intake/document-codebase.yaml`](../commands/intake/document-codebase.yaml) | [`docs/workflow/intake-document-codebase.md`](workflow/intake-document-codebase.md) |
| `intake:capture-behavior` | [`commands/intake/capture-behavior.yaml`](../commands/intake/capture-behavior.yaml) | [`docs/workflow/intake-capture-behavior.md`](workflow/intake-capture-behavior.md) |
| `intake:create-system-description` | [`commands/intake/create-system-description.yaml`](../commands/intake/create-system-description.yaml) | [`docs/workflow/intake-create-system-description.md`](workflow/intake-create-system-description.md) |
| `discovery:create` | [`commands/project/discovery/create.yaml`](../commands/project/discovery/create.yaml) | [`docs/workflow/discovery-create.md`](workflow/discovery-create.md) |
| `discovery:synthesize` | [`commands/project/discovery/synthesize.yaml`](../commands/project/discovery/synthesize.yaml) | [`docs/workflow/discovery-synthesize.md`](workflow/discovery-synthesize.md) |
| `discovery:approve` | [`commands/project/discovery/approve.yaml`](../commands/project/discovery/approve.yaml) | [`docs/workflow/discovery-approve.md`](workflow/discovery-approve.md) |
| `planning:epic-plan` | [`commands/project/planning/epic-plan.yaml`](../commands/project/planning/epic-plan.yaml) | [`docs/workflow/planning-epic-plan.md`](workflow/planning-epic-plan.md) |
| `planning:impl-plan` | [`commands/project/planning/impl-plan.yaml`](../commands/project/planning/impl-plan.yaml) | [`docs/workflow/planning-impl-plan.md`](workflow/planning-impl-plan.md) |
| `execution:execute-ticket` | [`commands/project/execution/execute-ticket.yaml`](../commands/project/execution/execute-ticket.yaml) | [`docs/workflow/execution-execute-ticket.md`](workflow/execution-execute-ticket.md) |
| `execution:complete-ticket` | [`commands/project/execution/complete-ticket.yaml`](../commands/project/execution/complete-ticket.yaml) | [`docs/workflow/execution-complete-ticket.md`](workflow/execution-complete-ticket.md) |
| `retrospectives:complete-epic` | [`commands/project/retrospectives/complete-epic.yaml`](../commands/project/retrospectives/complete-epic.yaml) | [`docs/workflow/retrospective-complete-epic.md`](workflow/retrospective-complete-epic.md) |
| `common-ground` | [`commands/common-ground/common-ground.yaml`](../commands/common-ground/common-ground.yaml) | [`docs/workflow/common-ground.md`](workflow/common-ground.md) |

---

## GitHub Issues

### v0.5.0 (Workflow Overhaul)

| Issue | Description | Chunk(s) | Status |
|-------|-------------|----------|--------|
| #62 | Core workflow generalization | 1, 2, 3 | Open |
| #103 | Epic creation gap | 3 | Open |
| New | Backend adapter reference files | 1 | To create |
| New | Intake commands | 4 | To create |
| New | Discovery command rework | 3 | To create |
| New | Feature-forge integration | 5 | To create |
| New | Namespace change + directory restructure | 6 | To create |
| New | YAML workflow definition schema + DAG manifest | Pre | To create |
| New | Narrative document restructure | 7 | To create |
| New | CI portability check | — | To create |

### Deferred to v0.6.0 (Global-to-Local Config Migration)

| Issue | Description |
|-------|-------------|
| #50-55 | Context persistence, state validation, error recovery, shared templates, testing infra |
| #109 | Common-ground local storage |

### Deferred to v0.7.0+ (Enhanced Skill Routing + Common-Ground)

| Issue | Description |
|-------|-------------|
| #65 | Cross-domain recommendations |
| #66 | Enhanced routing logic |
| #68 | Skill dependency mapping |
| #69 | Metadata enhancement |
| #108, #110, #111 | Common-ground enhancements |

---

## Resolved Decisions

- **Epic terminology** — Evaluated alternatives (initiative, feature, workstream, deliverable, milestone). Decision: **keep "epic."** It's the least ambiguous term across all three backends (Jira uses it natively, GitHub Issues maps milestones to it, local markdown uses folder labels). The adapter layer abstracts backend-specific mapping.
- **Discovery trigger** — Feature-forge embeds "Needs additional discovery" as a standing option during its structured interview. Flagged unknowns are collected and surfaced as a discovery recommendation at interview end, with options to run discovery, skip to planning, or handle research separately.
- **EARS format optional** — Made optional in feature-forge; offer EARS for complex features with conditional/state-dependent behavior; simpler formats for straightforward features.
- **Non-standard frontmatter fields tolerated** — Confirmed via `npx skills add . --list`: all 65 skills detected despite non-standard top-level fields (`triggers`, `role`, `scope`, `output-format`). Migration to `metadata.*` is optional tech debt.
- **#50-55 → v0.6.0** — These depend on global-to-local config migration (Discussion #112). Context persistence, state validation, error recovery, shared templates, and testing infra are all easier to implement with per-project config.
- **#69 metadata enhancement must use `metadata` field** — Any NEW metadata must go under the spec's `metadata` key, not as new top-level frontmatter fields. Existing non-standard fields are grandfathered.
- **CI portability check via `npx skills`** — GitHub Action to catch regressions in ecosystem detection. Asserts skill count matches `version.json`.

---

## Open Questions

- **Common-ground hooks** (#111, #107) — on-demand for now; hook-based injection in future
- **Docusaurus setup** — per-project CI/CD concern; add setup instructions in `local-docs-structure.md` but don't implement deployment in this version
- **EARS format monitoring** — made optional in feature-forge; monitor whether structured vs. simple format affects agent execution quality
- **Tiki integration** — potential future adapter for the ticketing backend (Go CLI for local task management)

---

## Implementation Summary

| Chunk | Phase | New Files | Modified Files | Lines (est.) | Status |
|-------|-------|-----------|---------------|-------------|--------|
| Pre. YAML definitions | 0 | 31 | 0 | ~2,000 | **Completed** |
| 1. Backend adapters | 1 | 9 | 1 | ~1,400 | Pending |
| 2. Decouple commands | 2 | 0 | 5 | ~500 | Pending |
| 3. Discovery rework | 2+3 | 0 | 3 | ~750 | Pending |
| 4. Intake commands | 4 | 5 | 0 | ~1,300 | Pending |
| 5. Feature-forge | 5 | 1 | 6 | ~600 | Pending |
| 6. Restructure | 6 | 0 | 2 + moves | ~100 | Pending |
| 7. Docs + validation | 7+8 | 0 | 8 | ~1,500 | Pending |

### Dependency Graph

```
Chunk Pre (YAML definitions) ✓
    │
Chunk 1 (foundation)
├──→ Chunk 2 (decouple non-discovery)──┐
├──→ Chunk 3 (discovery rework)────────┼──→ Chunk 5 (feature-forge)──→ Chunk 6 (restructure)──→ Chunk 7 (docs)
└──→ Chunk 4 (intake)──────────────────┘
```

Chunks 2, 3, and 4 are independent of each other — only Chunk 1 gates them. They can run in parallel if desired.
