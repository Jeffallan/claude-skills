# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.3.0]: https://github.com/jeffallan/claude-skills/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jeffallan/claude-skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jeffallan/claude-skills/compare/v0.0.4...v0.1.0
[0.0.4]: https://github.com/jeffallan/claude-skills/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/jeffallan/claude-skills/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/jeffallan/claude-skills/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/jeffallan/claude-skills/releases/tag/v0.0.1
