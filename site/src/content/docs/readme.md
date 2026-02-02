---
title: README
description: Project overview, architecture, and usage patterns
---

---

## Quick Start

```bash
/plugin marketplace add jeffallan/claude-skills
```
then
```bash
/plugin install fullstack-dev-skills@jeffallan
```

For all installation methods and first steps, see the **[Quick Start Guide](/getting-started/)**.

> **New:** Use `/common-ground` to surface and validate Claude's assumptions about your project before starting work.

## Architecture

### Progressive Disclosure Pattern

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
├── skills/                   # 65 specialized skills
│   ├── react-expert/
│   │   ├── SKILL.md
│   │   └── references/       # 6 reference files
│   ├── nestjs-expert/
│   │   ├── SKILL.md
│   │   └── references/       # 5 reference files
│   ├── python-pro/
│   │   ├── SKILL.md
│   │   └── references/       # Language-specific patterns
│   └── ... (62 more skills)
├── commands/
│   ├── common-ground/        # Context engineering command
│   │   ├── COMMAND.md
│   │   └── references/
│   └── project/              # Project workflow commands
│       ├── discovery/        # Research & validation
│       ├── planning/         # Epic & implementation planning
│       ├── execution/        # Ticket implementation
│       └── retrospectives/   # Reports & completion
├── docs/
│   ├── COMMON_GROUND.md      # Context engineering guide
│   ├── WORKFLOW_COMMANDS.md  # Workflow documentation
│   └── ATLASSIAN_MCP_SETUP.md # MCP server setup guide
├── README.md
├── SKILLS_GUIDE.md          # Quick reference guide
└── CONTRIBUTING.md          # Contribution guidelines
```

**Stats:**
- 65 skills
- 357 reference files
- ~50% token reduction
- Covers 30+ frameworks

## Skills

65 specialized skills across 12 categories covering languages, backend/frontend frameworks, infrastructure, APIs, testing, DevOps, security, data/ML, and platform specialists.

See **[SKILLS_GUIDE.md](/skills-guide/)** for the full list, decision trees, and workflow combinations.

## Usage Patterns

### Context-Aware Activation

Skills activate automatically based on your request:

```bash
"Implement JWT authentication in my NestJS API"
→ Activates: NestJS Expert → Loads: references/authentication.md

# Frontend Development
"Build a React component with Server Components"
→ Activates: React Expert → Loads: references/server-components.md
```

### Multi-Skill Workflows

Complex tasks combine multiple skills:

```
Feature Development: Feature Forge → Architecture Designer → Fullstack Guardian → Test Master → DevOps Engineer
Bug Investigation:   Debugging Wizard → Framework Expert → Test Master → Code Reviewer
Security Hardening:  Secure Code Guardian → Security Reviewer → Test Master
```

## Context Engineering

Surface and validate Claude's hidden assumptions about your project with `/common-ground`. See the **[Common Ground Guide](/guides/common-ground/)** for full documentation.

## Project Workflow

9 workflow commands manage epics from discovery through retrospectives, integrating with Jira and Confluence. See **[Workflow Commands Reference](/guides/workflow-commands/)** for the full command reference and lifecycle diagrams.

> **Setup:** Workflow commands require an Atlassian MCP server. See the **[Atlassian MCP Setup Guide](/guides/atlassian-mcp-setup/)**.

## Documentation

- **[Quick Start Guide](/getting-started/)** - Installation and first steps
- **[SKILLS_GUIDE.md](/skills-guide/)** - Skill reference and decision trees
- **[docs/COMMON_GROUND.md](/guides/common-ground/)** - Context engineering with `/common-ground`
- **[docs/WORKFLOW_COMMANDS.md](/guides/workflow-commands/)** - Project workflow commands guide
- **[docs/ATLASSIAN_MCP_SETUP.md](/guides/atlassian-mcp-setup/)** - Atlassian MCP server setup
- **[docs/local_skill_development.md](/guides/local-development/)** - Local skill development
- **[CONTRIBUTING.md](/contributing/)** - Contribution guidelines
- **skills/\*/SKILL.md** - Individual skill documentation
- **skills/\*/references/** - Deep-dive reference materials

## Contributing

We welcome contributions! See **[CONTRIBUTING.md](/contributing/)** for guidelines on adding skills, writing references, and submitting pull requests.

## Changelog

See [CHANGELOG.md](/changelog/) for full version history and release notes.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/jeffallan/claude-skills/issues)
- **Discussions:** [GitHub Discussions](https://github.com/jeffallan/claude-skills/discussions)
- **Repository:** [github.com/jeffallan/claude-skills](https://github.com/jeffallan/claude-skills)

## Author

Built by **[jeffallan](https://jeffallan.github.io)** [<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" width="16" height="16" alt="LinkedIn"/>](https://www.linkedin.com/in/jeff-smolinski/)

**Principal Consultant** at **[Synergetic Solutions](https://synergetic.solutions)** [<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" width="16" height="16" alt="LinkedIn"/>](https://www.linkedin.com/company/synergetic-holdings)

Fullstack engineering, security compliance, and technical due diligence for teams leveraging AI.

**Need help operationalizing AI workflows?** [Let's talk](https://synergetic.solutions/#contact)

## :clap: Thanks For Your support

[![Stargazers repo roster for @Jeffallan/claude-skills](https://reporoster.com/stars/Jeffallan/claude-skills)](https://github.com/Jeffallan/claude-skills/stargazers)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Jeffallan/claude-skills&type=date&legend=top-left)](https://www.star-history.com/#Jeffallan/claude-skills&type=date&legend=top-left)

---

**Built for Claude Code** | **9 Workflows** | **357 Reference Files** | **65 Skills**
