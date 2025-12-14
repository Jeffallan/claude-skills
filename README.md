# Fullstack Dev Skills Plugin

[![Version](https://img.shields.io/badge/version-0.0.4-blue.svg)](https://github.com/jeffallan/claude-skills)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-purple.svg)](https://github.com/jeffallan/claude-skills)

> A comprehensive Claude Code plugin with 19 specialized skills for full-stack developers. Now with selective disclosure architecture for 50% faster skill loading.

Transform Claude Code into your expert pair programmer across the entire development stack - from React frontends to FastAPI backends, from debugging to deployment, from code review to security analysis.

## Why This Plugin?

Traditional monolithic skills load thousands of tokens upfront. This plugin uses **selective disclosure** - each skill starts lean (~80-100 lines) with a routing table, then loads detailed knowledge only when needed from 91 specialized reference files.

**The Result:** 50% token reduction on initial skill load, faster responses, and surgical precision when you need deep expertise.

## Quick Start

### Install from Marketplace

```bash
# Add the marketplace
/plugin marketplace add jeffallan/claude-skills

# Install the plugin
/plugin install fullstack-dev-skills@jeffallan

# Restart Claude Code when prompted
```

### Try It Out

```bash
# "Help me build a NestJS API with authentication"
# → Activates NestJS Expert, loads auth patterns

# "Debug this React performance issue"
# → Activates React Expert + Debugging Wizard, loads performance reference

# "Review this code for security vulnerabilities"
# → Activates Security Reviewer, loads OWASP patterns
```

## Architecture

### Selective Disclosure Pattern

Each skill follows this structure:

```
skills/react-expert/
├── SKILL.md                    # Lean core (80 lines)
│   ├── Role definition
│   ├── When to use
│   ├── Core workflow
│   └── Routing table          # Points to references
└── references/                 # Loaded on-demand
    ├── server-components.md    # RSC patterns
    ├── react-19-features.md    # use() hook, actions
    ├── state-management.md     # Context, Zustand, Redux
    ├── hooks-patterns.md       # Custom hooks, optimization
    ├── performance.md          # memo, lazy, virtualization
    └── testing-react.md        # Testing Library patterns
```

**How It Works:**
1. Skill loads with minimal context (~80 lines)
2. Claude reads the routing table
3. Loads specific references only when context requires
4. 50% faster initial responses, surgical precision when needed

### Project Structure

```
claude-skills/
├── .claude-plugin/
│   ├── plugin.json           # Plugin metadata
│   └── marketplace.json      # Marketplace configuration
├── skills/                   # 19 specialized skills
│   ├── react-expert/
│   │   ├── SKILL.md
│   │   └── references/       # 6 reference files
│   ├── nestjs-expert/
│   │   ├── SKILL.md
│   │   └── references/       # 5 reference files
│   ├── fastapi-expert/
│   │   ├── SKILL.md
│   │   └── references/       # 4 reference files
│   └── ... (16 more skills)
├── README.md
├── SKILLS_GUIDE.md          # Quick reference guide
└── CONTRIBUTING.md          # Contribution guidelines
```

**Stats:**
- 19 skills
- 91 reference files
- ~50% token reduction
- Covers 10+ frameworks

## Skills Overview

### Backend Frameworks

| Skill | Description | Reference Files |
|-------|-------------|-----------------|
| **NestJS Expert** | TypeScript backend with dependency injection, guards, pipes | 5 files: modules, decorators, database, testing, websockets |
| **Django Expert** | Python web framework with Django/DRF | 4 files: ORM, DRF, auth, async |
| **FastAPI Expert** | Async Python APIs with Pydantic validation | 4 files: Pydantic v2, async SQLAlchemy, auth, testing |

### Frontend & Mobile

| Skill | Description | Reference Files |
|-------|-------------|-----------------|
| **React Expert** | React 19, Server Components, hooks, performance | 6 files: RSC, React 19, state, hooks, performance, testing |
| **React Native Expert** | Cross-platform mobile with Expo & native modules | 5 files: navigation, native modules, performance, storage, gestures |
| **Flutter Expert** | Cross-platform apps with Dart, Material Design | 5 files: state, navigation, async, native, testing |

### Testing & Quality

| Skill | Description | Reference Files |
|-------|-------------|-----------------|
| **Test Master** | Comprehensive testing strategy (unit, integration, E2E, performance) | 6 files: strategy, unit, integration, E2E, performance, security |
| **Playwright Expert** | E2E browser testing and automation | 4 files: selectors, fixtures, visual testing, CI |
| **Code Reviewer** | Thorough code review with best practices | 5 files: checklist, patterns, performance, security, refactoring |
| **Code Documenter** | Inline docs and OpenAPI specifications | 4 files: JSDoc, Python docs, OpenAPI, technical writing |

### DevOps & Operations

| Skill | Description | Reference Files |
|-------|-------------|-----------------|
| **DevOps Engineer** | CI/CD, Docker, Kubernetes, infrastructure | 6 files: Docker, K8s, CI/CD, IaC, monitoring, security |
| **Monitoring Expert** | Observability, logging, metrics, alerting | 5 files: metrics, logging, tracing, alerting, dashboards |

### Architecture & Design

| Skill | Description | Reference Files |
|-------|-------------|-----------------|
| **Architecture Designer** | System design, microservices, ADRs | 6 files: patterns, microservices, event-driven, database, caching, ADRs |
| **Feature Forge** | Requirements gathering and specification | 4 files: requirements, user stories, specs, validation |
| **Spec Miner** | Code analysis and reverse engineering (read-only) | 4 files: static analysis, patterns, documentation, metrics |

### Security

| Skill | Description | Reference Files |
|-------|-------------|-----------------|
| **Secure Code Guardian** | Writing secure code, preventing vulnerabilities | 6 files: OWASP Top 10, input validation, auth, crypto, API security |
| **Security Reviewer** | Security code review and SAST analysis | 5 files: SAST, vulnerability patterns, secrets, dependencies, threat modeling |

### Workflow Skills

| Skill | Description | Reference Files |
|-------|-------------|-----------------|
| **Debugging Wizard** | Systematic debugging across all languages | 5 files: methodology, tools, common issues, performance, concurrency |
| **Fullstack Guardian** | Full-stack feature implementation | 5 files: API design, frontend integration, database, deployment, testing |

## Usage Patterns

### Context-Aware Activation

Skills activate automatically based on your request:

```bash
# Backend Development
"Implement JWT authentication in my NestJS API"
→ Activates: NestJS Expert
→ Loads: references/authentication.md

# Frontend Development
"Build a React component with Server Components"
→ Activates: React Expert
→ Loads: references/server-components.md

# Performance Optimization
"My React app is slow, help me optimize"
→ Activates: React Expert + Debugging Wizard
→ Loads: references/performance.md, references/profiling.md

# Security Review
"Review this authentication code for security issues"
→ Activates: Security Reviewer + Secure Code Guardian
→ Loads: references/auth-patterns.md, references/owasp-top-10.md
```

### Multi-Skill Workflows

Complex tasks combine multiple skills:

**Full Feature Development:**
```
Feature Forge → Architecture Designer → Fullstack Guardian → Test Master → Security Reviewer → DevOps Engineer
```

**Bug Investigation:**
```
Debugging Wizard → Framework Expert → Test Master → Code Reviewer
```

**Security Hardening:**
```
Secure Code Guardian → Security Reviewer → Test Master
```

## Tech Stack Coverage

### Languages
- TypeScript / JavaScript
- Python
- Dart
- Go

### Backend
- NestJS (TypeScript)
- Django / Django REST Framework (Python)
- FastAPI (Python)
- Express (TypeScript)

### Frontend
- React 19 (Server Components, use() hook)
- React Native (Expo, bare workflow)
- Flutter (Material Design, Cupertino)

### Testing
- Jest / Vitest
- Playwright
- React Testing Library
- Pytest

### Databases
- PostgreSQL (TypeORM, Prisma, SQLAlchemy)
- MongoDB (Mongoose, Motor)
- MySQL / MariaDB

### DevOps
- Docker & Docker Compose
- Kubernetes
- GitHub Actions / GitLab CI
- Terraform / Pulumi

### Monitoring
- Prometheus / Grafana
- ELK Stack
- DataDog
- Sentry

## Installation Options

### Option 1: Marketplace (Recommended)

```bash
/plugin marketplace add jeffallan/claude-skills
/plugin install fullstack-dev-skills@jeffallan
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/jeffallan/claude-skills.git
cd claude-skills

# Add as local marketplace
/plugin marketplace add /absolute/path/to/claude-skills

# Install from local
/plugin install fullstack-dev-skills@local
```

### Option 3: Direct Installation

```bash
# Copy skills directly to Claude Code
cp -r ./skills/* ~/.claude/skills/
```

**Note:** Direct installation bypasses plugin management but works for quick testing.

## Documentation

- **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** - Quick reference for when to use each skill
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guidelines for contributing
- **skills/*/SKILL.md** - Individual skill documentation
- **skills/*/references/** - Deep-dive reference materials

## Performance Benefits

### Before (Monolithic Skills)
```
Skill load: 2,000-3,000 tokens
Response time: Slower initial analysis
Precision: Generic responses
```

### After (Selective Disclosure)
```
Skill load: ~80-100 tokens
Reference load: 200-400 tokens (only when needed)
Response time: 50% faster initial responses
Precision: Surgical, context-specific guidance
```

### Example Token Savings

**Scenario:** "Help me build a React component"

**Old approach:**
- Load entire React skill: 2,500 tokens
- Most content unused

**New approach:**
- Load React Expert core: 80 tokens
- User mentions "performance issue"
- Load performance.md: 350 tokens
- **Total:** 430 tokens (83% reduction)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Adding a New Skill

1. Create skill directory:
   ```bash
   mkdir -p skills/my-skill/references
   ```

2. Create lean SKILL.md with routing table:
   ```markdown
   ---
   name: My Skill
   description: Brief description with trigger keywords
   triggers:
     - keyword1
     - keyword2
   ---

   # My Skill

   ## Reference Guide
   | Topic | Reference | Load When |
   |-------|-----------|-----------|
   | Topic 1 | `references/topic1.md` | Context |
   ```

3. Create reference files (4-6 recommended)

4. Update plugin.json

5. Test locally and submit PR

### Adding Reference Files

Keep references focused (200-400 lines each):
- Single topic per file
- Code examples included
- Clear when-to-use guidance
- Cross-references where helpful

## Version History

### v0.0.4 (Current)
- Selective disclosure architecture
- 91 reference files across 19 skills
- 50% token reduction
- Improved routing tables

### v0.0.3
- Added 3 new skills (Flutter, Monitoring, Security Reviewer)
- Updated framework versions
- Enhanced documentation

### v0.0.2
- Initial skill collection
- 16 skills covering full-stack development

## Roadmap

- [ ] Add GraphQL Expert skill
- [ ] Expand Go backend coverage
- [ ] Add Kubernetes advanced patterns
- [ ] Create migration guides between frameworks
- [ ] Add video tutorials for common workflows

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/jeffallan/claude-skills/issues)
- **Discussions:** [GitHub Discussions](https://github.com/jeffallan/claude-skills/discussions)
- **Repository:** [github.com/jeffallan/claude-skills](https://github.com/jeffallan/claude-skills)

## Author

Created by [jeffallan](https://github.com/jeffallan) for full-stack engineers working across modern development stacks.

---

**Built for Claude Code** | **Powered by Selective Disclosure** | **91 Reference Files** | **19 Skills** | **50% Faster**
