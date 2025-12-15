<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,14,25,27&height=200&section=header&text=Claude%20Skills&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=54%20Specialized%20Skills%20for%20Full-Stack%20Developers&descSize=20&descAlignY=55" width="100%"/>
</p>

<p align="center">
  <a href="https://github.com/jeffallan/claude-skills"><img src="https://img.shields.io/badge/version-0.2.0-blue.svg?style=for-the-badge" alt="Version"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License"/></a>
  <a href="https://github.com/jeffallan/claude-skills"><img src="https://img.shields.io/badge/Claude_Code-Plugin-purple.svg?style=for-the-badge" alt="Claude Code"/></a>
  <a href="https://github.com/jeffallan/claude-skills/stargazers"><img src="https://img.shields.io/github/stars/jeffallan/claude-skills?style=for-the-badge&color=yellow" alt="Stars"/></a>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=A855F7&center=true&vCenter=true&multiline=true&repeat=false&width=800&height=80&lines=Transform+Claude+Code+into+your+expert+pair+programmer;across+the+entire+development+stack" alt="Typing SVG" />
</p>

<p align="center">
  <strong>🚀 50% Faster Loading</strong> • <strong>📚 284 Reference Files</strong> • <strong>🎯 25+ Frameworks</strong> • <strong>🔒 Selective Disclosure</strong>
</p>

---


## Quick Start

Get started in minutes with our **[Quick Start Guide](QUICKSTART.md)**.

**TL;DR:**
```bash
/plugin marketplace add jeffallan/claude-skills
```
then
```bash
/plugin install fullstack-dev-skills@jeffallan
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
├── skills/                   # 54 specialized skills
│   ├── react-expert/
│   │   ├── SKILL.md
│   │   └── references/       # 6 reference files
│   ├── nestjs-expert/
│   │   ├── SKILL.md
│   │   └── references/       # 5 reference files
│   ├── python-pro/
│   │   ├── SKILL.md
│   │   └── references/       # Language-specific patterns
│   └── ... (51 more skills)
├── README.md
├── SKILLS_GUIDE.md          # Quick reference guide
└── CONTRIBUTING.md          # Contribution guidelines
```

**Stats:**
- 54 skills
- 284 reference files
- ~50% token reduction
- Covers 25+ frameworks

## Skills Overview

**54 specialized skills** across 10 categories:

- **Languages (12)**: Python Pro, TypeScript Pro, JavaScript Pro, Go Pro, Rust Engineer, SQL Pro, C++ Pro, Swift Expert, Kotlin Specialist, C# Developer, PHP Pro, Java Architect
- **Backend Frameworks (10)**: NestJS Expert, Django Expert, FastAPI Expert, Spring Boot Engineer, Laravel Specialist, Rails Expert, .NET Core Expert
- **Frontend & Mobile (6)**: React Expert, Next.js Developer, Vue Expert, Angular Architect, React Native Expert, Flutter Expert
- **Infrastructure (5)**: Kubernetes Specialist, Terraform Engineer, Postgres Pro, Cloud Architect, Database Optimizer
- **API & Architecture (9)**: GraphQL Architect, API Designer, WebSocket Engineer, Microservices Architect, MCP Developer, Architecture Designer, Feature Forge, Spec Miner
- **Testing & Quality (4)**: Test Master, Playwright Expert, Code Reviewer, Code Documenter
- **DevOps & Operations (5)**: DevOps Engineer, Monitoring Expert, SRE Engineer, Chaos Engineer, CLI Developer
- **Security (2)**: Secure Code Guardian, Security Reviewer
- **Specialized (3)**: Legacy Modernizer, Embedded Systems, Game Developer
- **Workflow (2)**: Debugging Wizard, Fullstack Guardian

See **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** for when to use each skill, workflows, and examples.

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
- Go
- Rust
- C++
- Swift
- Kotlin
- C#
- PHP
- Ruby
- Java
- SQL
- Dart

### Backend
- NestJS (TypeScript)
- Django / Django REST Framework (Python)
- FastAPI (Python)
- Express (TypeScript)
- Spring Boot (Java)
- Laravel (PHP)
- Ruby on Rails (Ruby)
- .NET Core (C#)
- GraphQL APIs

### Frontend
- React 19 (Server Components, use() hook)
- Next.js (App Router, Server Actions)
- Vue 3 (Composition API, Pinia)
- Angular (Standalone Components, Signals)
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

### Infrastructure & DevOps
- Docker & Docker Compose
- Kubernetes (K8s, Helm)
- Terraform
- AWS / Azure / GCP
- PostgreSQL / MySQL / MongoDB
- CI/CD (GitHub Actions, GitLab CI)

### Monitoring
- Prometheus / Grafana
- ELK Stack
- DataDog
- Sentry

## Installation Options

### Option 1: Marketplace (Recommended)

```bash
/plugin marketplace add jeffallan/claude-skills
```
then
```bash
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

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history and release notes.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/jeffallan/claude-skills/issues)
- **Discussions:** [GitHub Discussions](https://github.com/jeffallan/claude-skills/discussions)
- **Repository:** [github.com/jeffallan/claude-skills](https://github.com/jeffallan/claude-skills)

## Author

Created by [jeffallan](https://github.com/jeffallan) for full-stack engineers working across modern development stacks.

## :clap: Thanks For Your support 

[![Stargazers repo roster for @Jeffallan/claude-skills](https://reporoster.com/stars/Jeffallan/claude-skills)](https://github.com/Jeffallan/claude-skills/stargazers)

---

**Built for Claude Code** | **Powered by Selective Disclosure** | **284 Reference Files** | **54 Skills** | **50% Faster**
