<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,14,25,27&height=200&section=header&text=Claude%20Skills&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=65%20Skills%20%E2%80%A2%209%20Workflows%20%E2%80%A2%20Built%20with%20%E2%9D%A4%EF%B8%8F%20for%20Full-Stack%20Devs&descSize=20&descAlignY=55" width="100%"/>
</p>

<p align="center">
  <a href="https://github.com/jeffallan/claude-skills"><img src="https://img.shields.io/badge/version-0.4.2-blue.svg?style=for-the-badge" alt="Version"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License"/></a>
  <a href="https://github.com/jeffallan/claude-skills"><img src="https://img.shields.io/badge/Claude_Code-Plugin-purple.svg?style=for-the-badge" alt="Claude Code"/></a>
  <a href="https://github.com/jeffallan/claude-skills/stargazers"><img src="https://img.shields.io/github/stars/jeffallan/claude-skills?style=for-the-badge&color=yellow" alt="Stars"/></a>
  <a href="https://github.com/jeffallan/claude-skills/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/jeffallan/claude-skills/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"/></a>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=A855F7&center=true&vCenter=true&multiline=true&repeat=false&width=800&height=80&lines=Transform+Claude+Code+into+your+expert+pair+programmer;across+the+entire+development+stack" alt="Typing SVG" />
</p>

<p align="center">
  <strong><!-- SKILL_COUNT -->65<!-- /SKILL_COUNT --> Skills</strong> | <strong><!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> Workflows</strong> | <strong>Context Engineering</strong> | <strong>Progressive Disclosure</strong>
</p>

<p align="center">
  <a href="https://github.com/Chat2AnyLLM/awesome-claude-skills/blob/main/FULL-SKILLS.md"><img src="https://img.shields.io/github/stars/Chat2AnyLLM/awesome-claude-skills?style=for-the-badge&label=awesome-claude-skills&color=brightgreen&logo=awesomelists&logoColor=white" alt="Awesome Claude Skills"/></a>
  <a href="https://github.com/BehiSecc/awesome-claude-skills"><img src="https://img.shields.io/github/stars/BehiSecc/awesome-claude-skills?style=for-the-badge&label=awesome-claude-skills&color=brightgreen&logo=awesomelists&logoColor=white" alt="Awesome Claude Skills (BehiSecc)"/></a>
</p>

---

## Quick Start

```bash
/plugin marketplace add jeffallan/claude-skills
```
then
```bash
/plugin install fullstack-dev-skills@jeffallan
```

For all installation methods and first steps, see the **[Quick Start Guide](QUICKSTART.md)**.

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
- <!-- SKILL_COUNT -->65<!-- /SKILL_COUNT --> skills
- <!-- REFERENCE_COUNT -->357<!-- /REFERENCE_COUNT --> reference files
- ~50% token reduction
- Covers 30+ frameworks

## Skills

<!-- SKILL_COUNT -->65<!-- /SKILL_COUNT --> specialized skills across 12 categories covering languages, backend/frontend frameworks, infrastructure, APIs, testing, DevOps, security, data/ML, and platform specialists.

See **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** for the full list, decision trees, and workflow combinations.

## Usage Patterns

### Context-Aware Activation

Skills activate automatically based on your request:

```bash
# Backend Development
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

Surface and validate Claude's hidden assumptions about your project with `/common-ground`. See the **[Common Ground Guide](docs/COMMON_GROUND.md)** for full documentation.

## Project Workflow

<!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> workflow commands manage epics from discovery through retrospectives, integrating with Jira and Confluence. See **[Workflow Commands Reference](docs/WORKFLOW_COMMANDS.md)** for the full command reference and lifecycle diagrams.

> **Setup:** Workflow commands require an Atlassian MCP server. See the **[Atlassian MCP Setup Guide](docs/ATLASSIAN_MCP_SETUP.md)**.

## Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Installation and first steps
- **[SKILLS_GUIDE.md](SKILLS_GUIDE.md)** - Skill reference and decision trees
- **[docs/COMMON_GROUND.md](docs/COMMON_GROUND.md)** - Context engineering with `/common-ground`
- **[docs/WORKFLOW_COMMANDS.md](docs/WORKFLOW_COMMANDS.md)** - Project workflow commands guide
- **[docs/ATLASSIAN_MCP_SETUP.md](docs/ATLASSIAN_MCP_SETUP.md)** - Atlassian MCP server setup
- **[docs/local_skill_development.md](docs/local_skill_development.md)** - Local skill development
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **skills/\*/SKILL.md** - Individual skill documentation
- **skills/\*/references/** - Deep-dive reference materials

## Contributing

We welcome contributions! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for guidelines on adding skills, writing references, and submitting pull requests.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history and release notes.

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

**Built for Claude Code** | **<!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> Workflows** | **<!-- REFERENCE_COUNT -->357<!-- /REFERENCE_COUNT --> Reference Files** | **<!-- SKILL_COUNT -->65<!-- /SKILL_COUNT --> Skills**
