# Claude Skills Roadmap

## Current Status

**Version:** v<!-- VERSION -->0.4.9<!-- /VERSION --> (Released January 2026)

- **<!-- SKILL_COUNT -->66<!-- /SKILL_COUNT --> Skills** across 12 domains
- **<!-- REFERENCE_COUNT -->365<!-- /REFERENCE_COUNT --> Reference Files** with progressive disclosure architecture
- **30+ Frameworks** and technologies covered
- **<!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> Project Workflow Commands** for epic planning, discovery, execution, and retrospectives
- **50% Token Reduction** through selective disclosure architecture
- Skills organized by domain: Backend, Frontend, DevOps, Mobile, Data, Security, Product, and Business

---

## Development Timeline

```
v0.4.2 ──────> v0.5.0 ──────> v0.6.0 ──────> v0.7.0 ──────> v1.0.0
(Current)      Workflow       Local-First    Skill          Stable
               Overhaul       Config         Routing        Release
```

---

## v0.3.0 - Domain Expansion & Stabilization (Released)

**Released:** December 26, 2025 | Patches: v0.3.1 (2025-12-26), v0.3.2 (2026-01-17)

Added 9 skills across Data Science (pandas-pro, spark-engineer, ml-pipeline), AI/LLM (prompt-engineer, rag-architect, fine-tuning-expert), and Platform (salesforce-developer, shopify-expert, wordpress-pro) domains. Completed skill trigger validation, routing table accuracy audit, and reference documentation for test-master, debugging-wizard, and code-reviewer enhancements.

---

## v0.4.0 - Project Workflow Commands & Cross-Referencing (Released)

**Released:** January 18, 2026 | Patches: v0.4.1 (2026-01-19), v0.4.2 (2026-01-29)

Introduced 9 project workflow commands spanning discovery, planning, execution, and retrospective phases. Added Atlassian MCP integration for Jira/Confluence operations, epic-driven development lifecycle, and Common Ground assumption-surfacing skill. Established the progressive disclosure architecture with tiered reference loading.

---

## v0.5.0 - Workflow Overhaul

**Scope:** Decouple workflow commands from Jira/Confluence, add per-project backend configuration, create a project intake phase, rework discovery for product-centric workflows, integrate feature-forge into the pipeline.

See [`docs/v0.5.0-plan.md`](docs/v0.5.0-plan.md) for the consolidated implementation plan.

### Backend Adapter Pattern
- [#62](https://github.com/Jeffallan/claude-skills/issues/62): Generalize workflow commands for multiple ticketing and documentation systems
- [#119](https://github.com/Jeffallan/claude-skills/issues/119): Backend adapter reference files (9 reference files for local, Jira, GitHub Issues, Confluence, GitHub Wiki backends)
- Per-project config via `.claude/workflow-config.json` — ticketing (`local` | `jira` | `github-issues`) and documentation (`local` | `confluence` | `github-wiki`)

### Intake Commands (New Phase)
- [#120](https://github.com/Jeffallan/claude-skills/issues/120): Three new commands — `intake:document-codebase`, `intake:capture-behavior`, `intake:create-system-description`
- Generates living system documentation, characterization tests, and SOC2-style system description

### Discovery Rework
- [#121](https://github.com/Jeffallan/claude-skills/issues/121): Full rewrite — topic-based input (not Jira epic key), local-first sources, produces epics AND tickets
- [#103](https://github.com/Jeffallan/claude-skills/issues/103): Epic creation gap fix — discovery now creates epics, not just tickets

### Feature-Forge Integration
- [#122](https://github.com/Jeffallan/claude-skills/issues/122): System description context (Step 0), discovery recommendation ("Needs additional discovery" standing option), output boundaries (optional EARS), skill-aware ticket generation

### Namespace & Directory Restructure
- [#123](https://github.com/Jeffallan/claude-skills/issues/123): Drop `project:` prefix — `project:phase:action` becomes `phase:action`; flatten `commands/project/` to `commands/`; remove `complete-sprint` command

### Already Completed (Phase 1-2)
- [#124](https://github.com/Jeffallan/claude-skills/issues/124): YAML workflow definition schema + DAG manifest
- [#125](https://github.com/Jeffallan/claude-skills/issues/125): Narrative document restructure with per-command metadata

### Infrastructure
- [#126](https://github.com/Jeffallan/claude-skills/issues/126): CI portability check — GitHub Action asserting `npx skills` detection matches `version.json`

### Command Count: 11
- 3 new (intake), 7 reworked (backend-agnostic), 1 removed (complete-sprint)

---

## v0.6.0 - Local-First Configuration

**Scope:** Global-to-local config migration, per-project skill activation, workflow infrastructure hardening.

This release moves configuration from global to per-project, enabling teams to customize skill sets and workflow behavior per repository. Builds on the backend adapter pattern from v0.5.0.

### Configuration Migration
- [Discussion #112](https://github.com/Jeffallan/claude-skills/discussions/112): Global-to-local config migration — `.claude/skills/` local install strategy, meta-skill/project analyzer
- Per-project skill activation — select which skills are active for a given repository

### Workflow Infrastructure
- [#50](https://github.com/Jeffallan/claude-skills/issues/50): Context Persistence — auto-store epic workflow state
- [#51](https://github.com/Jeffallan/claude-skills/issues/51): State Validation — prevent commands from running out of order
- [#52](https://github.com/Jeffallan/claude-skills/issues/52): Error Recovery — resume/rollback/retry mechanisms
- [#53](https://github.com/Jeffallan/claude-skills/issues/53): Extract Shared Templates — centralize checkpoint patterns
- [#54](https://github.com/Jeffallan/claude-skills/issues/54): Regression Test Suite — automated execution testing
- [#55](https://github.com/Jeffallan/claude-skills/issues/55): Performance & Security Testing — systematic integration

### Common Ground
- [#109](https://github.com/Jeffallan/claude-skills/issues/109): Common-ground local storage — persist assumptions per project

---

## v0.7.0 - Enhanced Skill Routing

**Scope:** Improved skill discovery and routing, common-ground workflow integration. Depends on v0.6.0 local config.

### Skill Routing Improvements
- [#65](https://github.com/Jeffallan/claude-skills/issues/65): Cross-Domain Recommendations — suggest complementary skills from different domains
- [#66](https://github.com/Jeffallan/claude-skills/issues/66): Enhanced Routing Logic — context-aware skill selection
- [#68](https://github.com/Jeffallan/claude-skills/issues/68): Skill Dependency Mapping — represent skill relationships
- [#69](https://github.com/Jeffallan/claude-skills/issues/69): Skill metadata enhancement — structured `metadata` field for richer skill descriptors

### Common Ground Enhancements
- [#108](https://github.com/Jeffallan/claude-skills/issues/108): Common-ground SessionStart hook — automatic assumption surfacing on session start
- [#110](https://github.com/Jeffallan/claude-skills/issues/110): Common-ground progressive disclosure — phased assumption surfacing
- [#111](https://github.com/Jeffallan/claude-skills/issues/111): Common-ground UserPromptSubmit hook — contextual assumption checks

### Feasibility Evaluation
- [#64](https://github.com/Jeffallan/claude-skills/issues/64): Smart Skill Discovery — consolidates #70, #71, #72; requires third-party tooling evaluation (vector embeddings, semantic search). Tracked separately pending feasibility assessment.

---

## v1.0.0 - Stable Release

**Scope:** Production-ready platform with comprehensive testing and documentation.

### Production Readiness
- Comprehensive test coverage
- Performance benchmarks established
- Security audit completed
- Documentation complete for all commands, skills, and configuration
- Migration guides for all versions

### Stable Guarantees
- Semantic versioning commitment
- Backward compatibility within major version
- Long-term support model

---

## Beyond v1.0.0 - Future Considerations

- Marketplace for community-created skills
- Plugin architecture for custom integrations
- Team collaboration features
- IDE integrations
- CI/CD pipeline connectors

---

## Contributing to the Roadmap

We welcome community input on the roadmap direction. Here's how you can contribute:

### Suggest Features
- Open a GitHub issue with the `enhancement` label
- Use the feature request template
- Explain the use case and expected benefits

### Vote on Priorities
- React to existing feature requests
- Comment with your use cases
- Help refine feature specifications

### Contribute Skills
- Follow the skill creation guide
- Submit pull requests for new skills
- Improve existing skill documentation

### Share Feedback
- Report bugs and issues promptly
- Suggest improvements to existing skills
- Participate in community discussions

---

## Versioning Philosophy

**Semantic Versioning:** We follow semver (MAJOR.MINOR.PATCH)
- **MAJOR:** Breaking changes, major architecture shifts
- **MINOR:** New features, new skills, backward-compatible additions
- **PATCH:** Bug fixes, documentation updates, minor improvements

**Release Cadence:**
- Minor versions: Quarterly
- Patch versions: As needed
- Major versions: When significant architecture changes occur

**Backward Compatibility:**
- Skills maintain compatibility within major versions
- Deprecation notices provided one minor version in advance
- Migration guides for breaking changes
- Support for previous minor version maintained

---

## Stay Updated

- **GitHub:** Watch the repository for updates
- **Releases:** Follow the releases page for version announcements
- **Discussions:** Participate in roadmap discussions
- **Issues:** Track progress on specific features

---

*This roadmap is a living document and subject to change based on community feedback, technical constraints, and emerging priorities. Last updated: February 2026 (v0.4.9)*
