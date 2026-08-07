# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- README banner (capsule-render URL) still displayed 66 skills after the v0.4.16 release; the counts are URL-encoded inside the image URL where no `<!-- SKILL_COUNT -->` marker can live, so `update-docs.py` never touched them. The script now rewrites the banner's `desc=` parameter from computed counts

## [0.4.16] - 2026-08-07

### Added
- New skill: `django-storages-s3` — production AWS S3 file storage for Django with `django-storages` and `boto3`. Covers the Django 4.2+ `STORAGES` dict, public/private custom backends, presigned GET/POST URLs, CloudFront integration, a least-privilege IAM policy, and S3 mocking (`InMemoryStorage`/`moto`). Cross-referenced with `django-expert` (#218)
- `ReferencePathChecker` in `scripts/validate-skills.py`: validates that file paths cited in skill markdown (backtick paths and markdown links) resolve relative to the containing file or the skill root. Broken paths previously failed silently when an agent tried to load deferred reference content; this class of bug has now recurred across several releases and is guarded automatically in CI and `make validate`
- `devops-engineer`: new `references/gitlab-ci.md` covering GitLab CI/CD best practices (pipeline dedup via `workflow:rules`, `needs:` DAG, cache vs artifacts, CI/CD components, environments, OIDC secrets, runner isolation, MR-widget reporting) plus a routing-table row; the GitLab counterpart to the existing GitHub Actions reference (#219)

### Changed
- `devops-engineer/references/gitlab-ci.md`: post-merge patch replacing the kaniko build example with BuildKit rootless (`moby/buildkit:rootless` + `buildctl-daemonless.sh` with registry cache) and noting kaniko's archived status in the core principles; kaniko is unmaintained and should not be the recommended build path

### Fixed
- `vue-expert-js/SKILL.md`: three shared-Vue reference paths pointed at `vue-expert/references/*.md`, which does not resolve from the skill directory; corrected to `../vue-expert/references/*.md` (#225)
- `react-expert/references/migration-class-to-modern.md`: self-referencing path `react-expert/references/server-components.md` corrected to `references/server-components.md` (#225)
- `fastapi-expert/references/migration-from-django.md`: cross-reference to legacy-modernizer used an absolute-style path (`/skills/legacy-modernizer/...`) that resolves nowhere; corrected to `../legacy-modernizer/references/migration-strategies.md`. Found by the new `ReferencePathChecker` audit
- `nestjs-expert/references/migration-from-express.md`: cross-reference to legacy-modernizer's strangler-fig reference was a hardcoded contributor-machine absolute path (`/Users/.../claude-skills/skills/...`); corrected to `../legacy-modernizer/references/strangler-fig-pattern.md`. Caught by `ReferencePathChecker` on CI's clean runner; the checker now rejects absolute paths unconditionally so a stale local clone can never mask one
- `site/package-lock.json`: applied `npm audit fix` to clear docs-site dependency vulnerabilities (14 findings down to 9; the remainder stem from advisories published after the fix was cut). Verified via clean `npm ci`, `npm audit`, and a successful 98-page site build before merge (#220)
- `site/package-lock.json`: follow-up fresh `npm audit fix` clearing post-July advisories (9 findings down to 5). The remaining 5 require a semver-major Astro 7 upgrade (cascading @astrojs/starlight and @astrojs/mdx majors) and are dev-server/SSR-context advisories with low exposure for a statically built site; tracked as separate upgrade work
- `rag-architect/SKILL.md`: reranking example instantiated the Cohere client with a hard-coded `"YOUR_API_KEY"` placeholder; now reads `COHERE_API_KEY` from the environment with a note on secrets handling, closing #210 (#216)
- `terraform-engineer/SKILL.md`: core workflow allowed proceeding from `terraform plan` straight to `terraform apply`; now requires presenting a plan summary (highlighting destructive actions) and receiving explicit user approval before apply, refusing when approval is withheld, closing #211 (#213)
- `devops-engineer/SKILL.md`: the "never deploy to production without explicit approval" constraint was not operationalized in the core workflow; the deploy step now determines the target environment and, for production or customer-facing targets, presents the deployment summary and rollback plan and requires explicit user approval before running deployment commands, closing #196 and #212

### Contributors
- @vasugarg09 — Fixed broken relative reference paths in `vue-expert-js` and `react-expert` (#225)
- @chgreer1070 — Patched docs-site dependency vulnerabilities via `npm audit fix` (#220)
- @kasymovpost — GitLab CI/CD best-practices reference for devops-engineer (#219)
- @awais786 — New `django-storages-s3` skill: production S3 file storage for Django (#218)
- @snvtac — Replaced hard-coded Cohere API key placeholder in `rag-architect` with environment lookup (#216)
- @SergiuLupaiescu — Added user-approval gate between `terraform plan` and `apply` in `terraform-engineer` (#213)
- @specterslient95-lgtm — Reported the missing plan/apply approval gate (#211) and the non-operationalized production-deploy constraint (#196, #212)

## [0.4.15] - 2026-05-20

### Fixed
- `commands/project/execution/complete-ticket.md`: corrected YAML frontmatter that failed strict parsing in oh-my-pi and the GitHub renderer. Two issues: unquoted double quotes around `"In Review"` were interpreted as a quoted-string opener with trailing junk, and `argument-hint: [ticket-key] (optional...)` led with `[` which opens a flow-style sequence and then failed on the prose tail. Wrapped both values in matching outer quotes (#193)

### Added
- `CommandFrontmatterChecker` in `scripts/validate-skills.py`: strict-parses YAML frontmatter on every `commands/**/*.md` with PyYAML (no fallback to the lenient simple parser, which had been masking these bugs). Runs as part of the workflow validation pass.

### Contributors
- @rlex — Reported broken YAML frontmatter in `complete-ticket.md` after the `0.4.14` release surfaced the parse error in oh-my-pi (#193)

## [0.4.14] - 2026-05-01

### Fixed
- `postgres-pro` reference docs: corrected invalid column references in `pg_stat_user_tables` and `pg_stat_user_indexes` query examples (`tablename` → `relname`, `indexname` → `indexrelname`) so the snippets actually run. Hardened identifier assembly with `format('%I.%I', schemaname, relname)` for safety against quoted/case-sensitive identifiers. Clarified the `VACUUM FREEZE` comment to note it operates on the current database, not the entire cluster (#191)

### Contributors
- @sobstel — Fix invalid `pg_stat_*` column references and `VACUUM FREEZE` scope comment in `postgres-pro` references (#191)

## [0.4.13] - 2026-04-28

### Added
- Canonical Documentation backlink at the bottom of every `SKILL.md` linking to the docs site (`[Documentation](https://jeffallan.github.io/claude-skills/skills/{domain}/{skill-name}/)`), so skill aggregators (skills.sh, etc.) that consume raw source markdown render a real `<a href>` backlink to the docs site for SEO. The docs build pipeline (`syncSkillPages` in `site/scripts/sync-content.mjs`) strips this line at build time, so the docs site, public markdown mirrors, `llms.txt`, and `llms-full.txt` render cleanly without self-references. Documented the convention in CLAUDE.md.

## [0.4.12] - 2026-04-21

### Added
- Curated cross-references for 7 hub skills: 22 back-references added for agent routing quality (closes #68)
  - `devops-engineer`: terraform-engineer, kubernetes-specialist, sre-engineer, monitoring-expert, security-reviewer
  - `fullstack-guardian`: secure-code-guardian, architecture-designer, react-expert, typescript-pro
  - `test-master`: debugging-wizard, code-reviewer, feature-forge
  - `database-optimizer`: postgres-pro, graphql-architect
  - `security-reviewer`: api-designer, mcp-developer
  - `architecture-designer`: microservices-architect, code-reviewer
  - `kubernetes-specialist`: terraform-engineer, security-reviewer, chaos-engineer

### Changed
- Bumped 7 hub skills from v1.1.0 → v1.1.1 (cross-reference updates)
- Added Prettier markdown formatting to pre-commit hooks, CI, and Makefile — covers `skills/`, `docs/`, and root `.md` files; excludes `commands/` (prompt templates) (#158)
- Documented linting and formatting conventions in CONTRIBUTING.md with Make targets (#158)
- Added explicit `name:` frontmatter to 9 workflow commands across `retrospectives/`, `discovery/`, `planning/`, and `execution/` directories — documents intent and protects against filename renames (filename-derived fallback was already working correctly) (#182, #183, #184, #185)

### Fixed
- README: restored the broken link to the Workflow Commands Reference docs. The paragraph began with `<!-- WORKFLOW_COUNT -->`, which CommonMark parses as an HTML block and disables inline markdown, causing the embedded link to render as literal text (#180)
- `commands/common-ground/COMMAND.md`: added explicit `name: common-ground` so the slash command registers as `/common-ground`. Without it, Claude Code derived the name from the filename (`COMMAND.md`) and registered it as `/COMMAND` (#186)

### Contributors
- @modir — Fix broken Workflow Commands docs link in README (#180)
- @xiaolai — Add missing `name:` frontmatter fields across workflow commands (#182, #183, #184, #185, #186)

## [0.4.11] - 2026-03-23

### Added
- Context management reference (`prompt-engineer/references/context-management.md`) covering attention budgets, lost-in-the-middle mitigation, four-bucket context tiering, KV-cache optimization, observation masking, and degradation metrics (#168)

### Changed
- Updated `prompt-engineer` skill (v1.1.0 → v1.2.0): added context management routing, expanded triggers, added `rag-architect` and `debugging-wizard` to related skills
- Total reference files: 365 → 366

### Contributors
- @Genius-apple — Context management content adapted from the context-engineer skill submission (#168)

## [0.4.10] - 2026-03-06

### Changed
- Improved skill quality across 65 skills via Tessl review optimization (#172)
  - Expanded descriptions with capability verbs (what it does + when to use it)
  - Removed redundant "Role Definition" and "When to Use This Skill" sections
  - Added structured workflow validation checkpoints with failure recovery loops
  - Added inline code examples demonstrating key patterns per technology
  - Tightened MUST DO / MUST NOT DO constraints with rationale
  - Removed "Knowledge Reference" keyword lists (absorbed into descriptions and triggers)
- Narrowed Description Trap from "trigger-only" to "no process steps" — capability verbs now permitted in descriptions per AgentSkills.io spec
- Updated description format to `[Brief capability statement]. Use when [triggering conditions].`
- Validator now checks `"Use when" in description` instead of `startswith("Use when")`
- Standardized README links from HTML to Markdown, improved Quick Start readability (#166)

### Fixed
- Fixed stale counts on docs site landing page (65 → 66 skills, 357 → 365 references)
- Added Astro site files to `update-docs.py` release automation so counts stay in sync

### Contributors
- @popey — Improve skill quality across 65 skills via Tessl review (#172)
- @hasan613 — Standardize README links and improve Quick Start section (#166)

## [0.4.9] - 2026-02-24

### Added
- Issue linking documentation in `atlassian-mcp/references/jira-queries.md` with parameter semantics, code examples, and anti-patterns (#163)

### Changed
- Updated `php-pro` Symfony console command example to use framework's built-in exception handling (#164)
- Added Framework Idiom Principle to CLAUDE.md reference file standards
- Added inline `jira_create_issue_link` parameter hints to `approve-synthesis` and `create-implementation-plan` commands (#163)

### Fixed
- Fixed reversed Jira "Blocks" link parameters — `inward_issue_key` is the blocker, `outward_issue_key` is the blocked issue (#163)
- Fixed nested code block rendering in `prompt-engineer` skill's CoT example (#160)

### Contributors
- @wiretail — Report and document reversed Jira issue link semantics (#163)
- @Big-Shark — Update console example in symfony-patterns (#164)
- @fiberproduct — Fix nested code block formatting in prompt-patterns.md (#160)

## [0.4.8] - 2026-02-17

### Added
- 🎉 **Milestone:** Appeared on [GitHub Weekly Trending](https://github.com/Jeffallan/claude-skills/discussions/148) repos (#8 overall)

### Changed
- Added Agent Skills CLI as alternative installation method in QUICKSTART.md (#151)
- Upgraded GitHub Actions for Node 24 compatibility (#146)
  - `actions/checkout` v4 → v6
  - `actions/setup-node` v4 → v6
  - `actions/setup-python` v5 → v6
- Upgraded `actions/upload-pages-artifact` v3 → v4 (#147)

### Fixed
- Removed incorrect Python/Pydantic V1 reference from `php-pro` skill MUST NOT DO section (#154)

### Contributors
- @salmanmkc — Upgrade GitHub Actions for Node 24 compatibility (#146)
- @salmanmkc — Upgrade GitHub Actions to latest versions (#147)
- @Karanjot786 — Add Agent Skills CLI installation method (#151)
- @Aivanaso — Remove copy-paste error from php-pro skill (#154)

## [0.4.7] - 2026-02-08

### Added
- Bidirectional cross-reference validation in `validate-skills.py` (closes #100)
  - `CrossRefChecker` class: warns when skill A references B but B doesn't reference A
  - Orphan detection: warns about skills with no incoming or outgoing references
  - New `--check crossrefs` CLI option for isolated cross-reference validation
  - All issues are WARNING severity (advisory, won't fail CI)

### Changed
- Upgraded Code of Conduct to Contributor Covenant v2.1 (closes #131)
- Refactored `CrossRefChecker._build_graph()` to reuse `BaseChecker._extract_frontmatter()`

## [0.4.6] - 2026-02-08

### Added
- `the-fool` — domain-agnostic critical reasoning skill with 5 modes (Socratic questioning, dialectic synthesis, pre-mortem, red team, evidence audit)
  - Two-step `AskUserQuestion` mode selection for 5 modes within 4-option constraint
  - 6 reference files: mode-selection-guide, socratic-questioning, dialectic-synthesis, pre-mortem-analysis, red-team-adversarial, evidence-audit
  - Added to Workflow category in SKILLS_GUIDE.md
  - Added Critical Thinking decision tree and Decision Validation workflow

### Fixed
- Fixed `sync-content.mjs` regex in `stripHtmlCommentTags` not stripping version markers (dots in `0.4.x` didn't match `\w+`)
- Fixed social preview generation command in CLAUDE.md release checklist (added `npm install --no-save puppeteer`)

## [0.4.5] - 2026-02-05

### Added
- Added "Mentioned in Awesome Claude Code" badge to README (closes #138)
- Added Awesome Claude Code stat to social preview
- Added `scripts/validate-markdown.py` for detecting markdown parsing errors
  - Checks for HTML comments breaking tables, unclosed code blocks, missing table separators, column count mismatches
  - Integrated into CI workflow and release checklist

### Fixed
- Fixed markdown bold formatting rendering as raw `**` in README.md (#139)
- Fixed minor syntax error in skill YAML frontmatter (#137)
- Fixed incorrect JQL syntax in epic planning workflows (`Parent =` → `"Epic Link" =`)
  - Affected: `create-epic-plan`, `create-epic-discovery`, `WORKFLOW_COMMANDS.md`
- Fixed markdown parsing errors across skill files:
  - Moved HTML comments above tables in `code-reviewer` and `debugging-wizard` skills
  - Added missing closing code fences in `incident-chaos`, `mysql-tuning`, `postgresql-tuning`
  - Escaped pipe character in `php-pro/modern-php-features.md` table

### Contributors
- @hesreallyhim — Featured in Awesome Claude Code (#138)
- @hesreallyhim — Fix formatting and links in README.md (#139)
- @hesreallyhim — fix: minor syntax error in .md yaml frontmatter (#137)

## [0.4.4] - 2026-02-03

### Fixed
- Replaced CONTRIBUTORS.md reference with GitHub contributors link in CONTRIBUTING.md (closes #130)

### Changed
- Refactored `validate-skills.py` with Python 3.11+ best practices (closes #133)
  - Extracted `FrontmatterResult` dataclass and `_extract_frontmatter()` helper to eliminate duplicate parsing
  - Created `MetadataEnumChecker` generic base class for enum field validators
  - Compiled regex patterns at module level for performance
  - Modernized type hints (`X | None` syntax) and added `DFSColor` IntEnum
- `update-docs.py` now auto-bumps version in ROADMAP "Last updated" line
- Added `__pycache__/` to `.gitignore`
- Added AdaL CLI (SylphAI) to supported agents table (#135)

### Contributors
- @liyin2015 — docs: add AdaL CLI to supported agents (#135)

## [0.4.3] - 2026-02-03

### Added
- Documentation site built with Astro Starlight (`site/`) (closes #106)
  - Custom GitHub stars component with live API fetch
  - View as Markdown toggle for skill pages
  - SEO metadata improvements
- Automated release workflow `.github/workflows/release.yml` (closes #107)
  - Triggers on version tag push (`v*`)
  - Validates using reusable workflow
  - Extracts release notes from CHANGELOG.md
  - Builds and deploys docs site to GitHub Pages
  - Creates GitHub Release with extracted notes
- YAML workflow definitions and DAG manifest for project commands (`commands/`) (closes #124)
- `related-skills` field in skill frontmatter metadata (closes #69)
- `scripts/migrate-frontmatter.py` for bulk skill metadata updates
- Local skill development guide (`docs/local_skill_development.md`)

### Changed
- Restructured primary docs, workflow docs, and skill files
- Rewrote ROADMAP.md with re-triaged GitHub issues
- Extended `validate-skills.py` with related-skills validation
- Documentation tone consistency improvements (closes #132)
- Fixed broken links and missing references in cloud-architect skill
- Added links in SKILLS_GUIDE.md

## [0.4.2] - 2026-01-29

### Added
- 4 new reference files for vue-expert-js skill (closes #97):
  - composables-patterns.md: Custom composables, ref/reactive patterns, lifecycle hooks
  - component-architecture.md: Props, emits, slots, provide/inject, dynamic components
  - state-management.md: Pinia setup, store patterns, reactive state
  - testing-patterns.md: Vitest/Vue Test Utils, component mounting, mocking
- `version.json` for centralized version and count management
- `scripts/update-docs.py` for automated documentation updates with marker-based replacement
- `scripts/validate-skills.py` for skill YAML and reference file validation
- HTML comment markers in documentation files for explicit count replacement (fixes #99)
- `AskUserQuestions` tool integration in feature-forge skill for structured elicitation during discovery, interview, and validation phases (closes #102)
- Multi-agent pre-discovery pattern in feature-forge for launching parallel Task subagents with domain-specific skills before the specification workshop (closes #102)
- `discovery-for-feature-forge.md` example prompt for multi-agent discovery workflow
- Reusable GitHub Actions validation workflow `.github/workflows/validate.yml` (closes #105)
- CI workflow `.github/workflows/ci.yml` triggering on PRs and pushes to main (closes #105)
- CI status badge in README
- Bloc state management reference for flutter-expert skill (#117)

### Changed
- Total reference files: 351 → 356
- Clarified `npx add-skill` installation and slash command limitations in README (#96)
- `update-docs.py` now uses `<!-- MARKER -->...<!-- /MARKER -->` tags instead of broad regex patterns
- Documentation files (README.md, QUICKSTART.md, ROADMAP.md, social-preview.html) updated with markers
- feature-forge interview flow rewritten to alternate between structured `AskUserQuestions` and open-ended elicitation
- feature-forge constraints updated to require `AskUserQuestions` for structured choices
- Minor README tidying
- Non-standard headers (`Reference for:`, `Load when:`) removed from 337 reference files (closes #104)
- `non-standard-headers` validation promoted from warning to error in `validate-skills.py`

### Fixed
- Pattern matching in `update-docs.py` no longer incorrectly matches inline comments like `# 6 reference files` in project structure trees (fixes #99)
- Missing version comparison link for v0.4.1 in CHANGELOG (#116)

### Contributors
- @thomassamoul — feat: add bloc state management to flutter expert (#117)
- @Coopyrightdmin — fix: add missing version link for v0.4.1 (#116)
- @Chidwan3578 — docs: clarify npx add-skill installation (#96)

## [0.4.1] - 2026-01-19

### Added
- 50 new reference files for 10 skills:
  - atlassian-mcp (5 files): MCP server setup, Jira queries, Confluence operations, authentication, workflows
  - fine-tuning-expert (5 files): LoRA/PEFT, dataset preparation, hyperparameters, evaluation, deployment
  - ml-pipeline (5 files): Feature engineering, training pipelines, experiment tracking, orchestration, validation
  - pandas-pro (5 files): DataFrame operations, data cleaning, aggregation, merging, performance
  - prompt-engineer (5 files): Prompt patterns, optimization, evaluation frameworks, structured outputs, system prompts
  - rag-architect (5 files): Vector databases, embedding models, chunking strategies, retrieval optimization, evaluation
  - salesforce-developer (5 files): Apex development, LWC, SOQL/SOSL, integrations, deployment
  - shopify-expert (5 files): Liquid templating, Storefront API, app development, checkout, performance
  - spark-engineer (5 files): Spark SQL/DataFrames, RDD operations, partitioning, performance tuning, streaming
  - wordpress-pro (5 files): Theme development, plugin architecture, Gutenberg blocks, hooks/filters, security
- Release checklist validation step in CLAUDE.md for YAML and reference integrity checks

### Fixed
- YAML parsing errors in 53 skills caused by unescaped `Keywords:` pattern in descriptions (fixes #93)
- Missing reference files for 10 skills that had routing tables but no actual reference files (fixes #92)

### Changed
- Total reference files: 304 → 351
- Skill descriptions now follow trigger-only format consistently

## [0.4.0] - 2026-01-18

### Added
- New `--graph` flag for `/common-ground` command
  - Generates mermaid flowchart diagrams visualizing Claude's reasoning structure
  - Decision points, chosen paths, alternatives, and uncertainties displayed visually
  - Node colors indicate confidence: green (chosen), yellow (decision point), orange (uncertain), gray (alternative)
- New `references/reasoning-graph.md` reference file (280 lines)
  - Mermaid diagram generation patterns and templates
  - Node types, styling rules, and edge label conventions
  - Complete examples with auth system reasoning tree
- README "Context Engineering" section featuring `/common-ground` command
- README Quick Start callout for `--graph` flag

### Changed
- Updated README header stats to include "Context Engineering"
- Enhanced README Author section with LinkedIn profile links
- Updated project structure documentation to show `commands/common-ground/`
- Total reference files: 301 → 304

## [0.3.2] - 2026-01-16

### Added
- New `/common-ground` command for surfacing Claude's hidden assumptions (#88)
  - Two-phase interactive flow (Surface & Select, Adjust Tiers)
  - Assumption classification by Type (stated/inferred/assumed/uncertain)
  - Confidence tiers (ESTABLISHED/WORKING/OPEN)
  - `--list` and `--check` flags for quick access
  - Ground file storage in ~/.claude/common-ground/
  - Introduced hybrid command pattern (COMMAND.md + references/) for complex commands
- New `/approve-synthesis` command for reviewing and approving synthesis documents (#87)
  - Reviews proposed tickets from synthesis
  - Resolves blocking decisions before ticket creation
  - Allows add/remove/modify of tickets before Jira creation
  - Creates approved tickets in Jira
- New `vue-expert-js` skill for JavaScript-only Vue development (#86)
  - JSDoc typing patterns for Vue components
  - Runtime prop validation

### Changed
- Split `/synthesize-discovery` workflow into two commands (#87)
  - `/synthesize-discovery` now creates synthesis document with proposed tickets
  - `/approve-synthesis` handles decision resolution and Jira ticket creation
- Enhanced `vue-expert` skill with mobile and build tooling (#86)
  - Quasar framework patterns for mobile-first development
  - Capacitor native plugin integration
  - PWA service workers and offline strategies
  - Vite build configuration and optimization
  - Updated Nuxt reference with Custom SSR + Fastify patterns
- Total skills: 64 → 65
- Total reference files: 298 → 301
- Total project commands: 8 → 9

## [0.3.1] - 2025-12-26

### Changed
- Moved legacy workflow commands from `.claude/commands/` to `.claude/old-commands/legacy/` to avoid polluting the user's command namespace when installing the plugin
- Workflow commands remain available via the plugin's `commands/project/` directory structure for programmatic use

## [0.3.0] - 2025-12-26

### Added
- **8 project workflow commands** organized into 4 phases:
  - **Discovery:** `create-epic-discovery`, `synthesize-discovery` - Research and validate requirements
  - **Planning:** `create-epic-plan`, `create-implementation-plan` - Analyze codebase and create execution plans
  - **Execution:** `execute-ticket`, `complete-ticket` - Implement and complete individual tickets
  - **Retrospectives:** `complete-epic`, `complete-sprint` - Generate reports and close work items
- New `commands/project/` directory structure with organized subfolders
- Comprehensive workflow documentation (`docs/WORKFLOW_COMMANDS.md`) with mermaid diagrams
- Atlassian MCP server setup guide (`docs/ATLASSIAN_MCP_SETUP.md`)
- Jira integration for ticket management (read tickets, update status, transitions)
- Confluence integration for document publishing across all workflow phases
- Mandatory checkpoint system with user approval gates at each phase
- 10 new skills bringing total to 64:
  - salesforce-developer, shopify-expert, wordpress-pro, atlassian-mcp
  - pandas-pro, spark-engineer, ml-pipeline, prompt-engineer, rag-architect, fine-tuning-expert

### Changed
- Updated `plugin.json` and `marketplace.json` with `commands` field
- Added project management keywords (jira, confluence, epic-planning, sprint, discovery, retrospectives)
- Updated README with project workflow commands section and updated project structure
- Total skills: 54 → 64 (19% increase)
- Total reference files: 284 → 298

## [0.2.0] - 2025-12-14

### Added
- **35 new skills** converted from agents:
  - **Languages (12):** python-pro, typescript-pro, javascript-pro, golang-pro, rust-engineer, sql-pro, cpp-pro, swift-expert, kotlin-specialist, csharp-developer, php-pro, java-architect
  - **Frameworks (7):** nextjs-developer, vue-expert, angular-architect, spring-boot-engineer, laravel-specialist, rails-expert, dotnet-core-expert
  - **Infrastructure (5):** kubernetes-specialist, terraform-engineer, postgres-pro, cloud-architect, database-optimizer
  - **API/Architecture (5):** graphql-architect, api-designer, websocket-engineer, microservices-architect, mcp-developer
  - **Operations (3):** sre-engineer, chaos-engineer, cli-developer
  - **Specialized (3):** legacy-modernizer, embedded-systems, game-developer
- **193 new reference files** across all new skills
- Comprehensive language-specific patterns for 12 programming languages
- Framework-specific best practices for 7 additional frameworks
- Infrastructure-as-code and cloud architecture patterns
- Modern API design and microservices architecture patterns

### Enhanced
- **test-master:** Added QA methodology, automation frameworks, performance testing, security testing
- **code-documenter:** Added documentation systems, API documentation patterns, technical writing standards
- **devops-engineer:** Added platform engineering, deployment strategies, incident response procedures
- **monitoring-expert:** Added performance testing, profiling techniques, capacity planning
- **security-reviewer:** Added penetration testing, infrastructure security, compliance scanning
- **fullstack-guardian:** Added API design standards, architecture decision records, comprehensive deliverables checklist

### Changed
- Total skills: 19 → 54 (184% increase)
- Total reference files: 91 → 284 (212% increase)
- Expanded tech stack coverage to 25+ frameworks
- Added 12 programming languages with deep expertise
- Enhanced decision trees and skill routing

## [0.1.0] - 2025-12-14

### Added
- Progressive disclosure architecture for all 19 skills
- 91 reference files across all skills for contextual loading
- Routing tables in each SKILL.md pointing to domain-specific references

### Changed
- Refactored all SKILL.md files to lean format (~80-100 lines each)
- 50% token reduction on initial skill load
- Updated CONTRIBUTING.md with progressive disclosure guidelines
- Rewrote README.md with architecture documentation and improved structure

## [0.0.4] - 2025-12-14

### Changed
- Optimized all 19 skills with modern patterns
- Framework version updates (React 19, Pydantic V2, Django 5.0, Flutter 3+)
- ~42% token efficiency improvements across all skills
- Standardized frontmatter schema (triggers, role, scope, output-format)

## [0.0.3] - 2025-10-20

### Changed
- Updated plugin.json marketplace schema
- Set release version for plugin distribution

## [0.0.2] - 2025-10-20

### Fixed
- Restructured to correct Claude Code plugin format
- Fixed plugin directory structure

## [0.0.1] - 2025-10-20

### Added
- Initial release with 19 comprehensive skills
- **Original Development Skills** (6): DevOps Engineer, Feature Forge, Fullstack Guardian, Spec Miner, Test Master, Code Documenter
- **Testing & E2E** (1): Playwright Expert
- **Backend Framework Skills** (3): NestJS Expert, Django Expert, FastAPI Expert
- **Frontend & Mobile Skills** (3): React Expert, React Native Expert, Flutter Expert
- **Workflow Skills** (4): Debugging Wizard, Monitoring Expert, Architecture Designer, Code Reviewer
- **Security Skills** (2): Secure Code Guardian, Security Reviewer
- Comprehensive documentation (README, SKILLS_GUIDE, CONTRIBUTING)
- MIT License

### Tech Stack Coverage
- Languages: TypeScript, JavaScript, Python, Dart, Go
- Backend: NestJS, Django, FastAPI, Express
- Frontend: React, React Native, Flutter
- Testing: Jest, Playwright, Pytest, React Testing Library
- DevOps: Docker, Kubernetes, CI/CD
- Monitoring: Prometheus, Grafana, ELK, DataDog
- Security: OWASP Top 10, SAST tools

[0.4.16]: https://github.com/jeffallan/claude-skills/compare/v0.4.15...v0.4.16
[0.4.15]: https://github.com/jeffallan/claude-skills/compare/v0.4.14...v0.4.15
[0.4.14]: https://github.com/jeffallan/claude-skills/compare/v0.4.13...v0.4.14
[0.4.13]: https://github.com/jeffallan/claude-skills/compare/v0.4.12...v0.4.13
[0.4.12]: https://github.com/jeffallan/claude-skills/compare/v0.4.11...v0.4.12
[0.4.11]: https://github.com/jeffallan/claude-skills/compare/v0.4.10...v0.4.11
[0.4.10]: https://github.com/jeffallan/claude-skills/compare/v0.4.9...v0.4.10
[0.4.9]: https://github.com/jeffallan/claude-skills/compare/v0.4.8...v0.4.9
[0.4.8]: https://github.com/jeffallan/claude-skills/compare/v0.4.7...v0.4.8
[0.4.7]: https://github.com/jeffallan/claude-skills/compare/v0.4.6...v0.4.7
[0.4.6]: https://github.com/jeffallan/claude-skills/compare/v0.4.5...v0.4.6
[0.4.5]: https://github.com/jeffallan/claude-skills/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/jeffallan/claude-skills/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/jeffallan/claude-skills/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/jeffallan/claude-skills/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/jeffallan/claude-skills/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/jeffallan/claude-skills/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/jeffallan/claude-skills/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/jeffallan/claude-skills/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/jeffallan/claude-skills/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jeffallan/claude-skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jeffallan/claude-skills/compare/v0.0.4...v0.1.0
[0.0.4]: https://github.com/jeffallan/claude-skills/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/jeffallan/claude-skills/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/jeffallan/claude-skills/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/jeffallan/claude-skills/releases/tag/v0.0.1
