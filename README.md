<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,14,25,27&height=200&section=header&text=Claude%20Skills&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=66%20Skills%20%E2%80%A2%209%20Workflows%20%E2%80%A2%20Built%20for%20Full-Stack%20Devs&descSize=20&descAlignY=55" width="100%"/>
</p>

<p align="center">
<a href="https://trendshift.io/repositories/20667" target="_blank"><img src="https://trendshift.io/api/badge/repositories/20667" alt="Jeffallan%2Fclaude-skills | Trendshift" style="width: 200px; height: 44px;" width="200" height="44"/></a>
<a href="https://github.com/hesreallyhim/awesome-claude-code"><img src="https://awesome.re/mentioned-badge.svg" alt="Mentioned in Awesome Claude Code"/></a>
</p>

<p align="center">
  <a href="https://github.com/jeffallan/claude-skills"><img src="https://img.shields.io/badge/version-0.4.8-blue.svg?style=for-the-badge" alt="Version"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License"/></a>
  <a href="https://github.com/jeffallan/claude-skills"><img src="https://img.shields.io/badge/Claude_Code-Plugin-purple.svg?style=for-the-badge" alt="Claude Code"/></a>
  <a href="https://github.com/jeffallan/claude-skills/stargazers"><img src="https://img.shields.io/github/stars/jeffallan/claude-skills?style=for-the-badge&color=yellow" alt="Stars"/></a>
  <a href="https://github.com/jeffallan/claude-skills/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/jeffallan/claude-skills/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"/></a>
</p>

---

## Quick Start

```bash
# Add the marketplace
/plugin marketplace add jeffallan/claude-skills

# Install the plugin
/plugin install fullstack-dev-skills@jeffallan

# Restart Claude Code when prompted
```

For all installation methods and first steps, see the [**Quick Start Guide**](QUICKSTART.md).

**Full documentation:** [jeffallan.github.io/claude-skills](https://jeffallan.github.io/claude-skills)

## Skills

<!-- SKILL_COUNT -->66<!-- /SKILL_COUNT --> specialized skills across 12 categories covering languages, backend/frontend frameworks, infrastructure, APIs, testing, DevOps, security, data/ML, and platform specialists.

See [**Skills Guide**](SKILLS_GUIDE.md) for the full list, decision trees, and workflow combinations.

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

Surface and validate Claude's hidden assumptions about your project with `/common-ground`. See the [**Common Ground Guide**](docs/COMMON_GROUND.md) for full documentation.

## Project Workflow

<!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> workflow commands manage epics from discovery through retrospectives, integrating with Jira and Confluence. See <a href="docs/WORKFLOW_COMMANDS.md"><strong>Workflow Commands Reference</strong></a> for the full command reference and lifecycle diagrams.
&nbsp;

> [!TIP]
> **Setup:** Workflow commands require an Atlassian MCP server. See the [**Atlassian MCP Setup Guide**](docs/ATLASSIAN_MCP_SETUP.md).

## Documentation

- [**Quick Start Guide**](QUICKSTART.md) - Installation and first steps
- [**Skills Guide**](SKILLS_GUIDE.md) - Skill reference and decision trees
- [**Common Ground**](docs/COMMON_GROUND.md) - Context engineering with `/common-ground`
- [**Workflow Commands**](docs/WORKFLOW_COMMANDS.md) - Project workflow commands guide
- [**Atlassian MCP Setup**](docs/ATLASSIAN_MCP_SETUP.md) - Atlassian MCP server setup
- [**Local Development**](docs/local_skill_development.md) - Local skill development
- [**Contributing**](CONTRIBUTING.md) - Contribution guidelines
- **skills/\*/SKILL.md** - Individual skill documentation
- **skills/\*/references/** - Deep-dive reference materials

## Contributing

See [**Contributing**](CONTRIBUTING.md) for guidelines on adding skills, writing references, and submitting pull requests.

## Changelog

See [Changelog](CHANGELOG.md) for full version history and release notes.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/jeffallan/claude-skills/issues)
- **Discussions:** [GitHub Discussions](https://github.com/jeffallan/claude-skills/discussions)
- **Repository:** [github.com/jeffallan/claude-skills](https://github.com/jeffallan/claude-skills)

## Author

Built by [**jeffallan**](https://jeffallan.github.io) [<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" width="16" height="16" alt="LinkedIn"/>](https://www.linkedin.com/in/jeff-smolinski/)

**Principal Consultant** at [**Synergetic Solutions**](https://synergetic.solutions) [<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" width="16" height="16" alt="LinkedIn"/>](https://www.linkedin.com/company/synergetic-holdings)

Fullstack engineering, security engineering, compliance, and technical due diligence.

## Community

[![Stargazers repo roster for @Jeffallan/claude-skills](https://reporoster.com/stars/Jeffallan/claude-skills)](https://github.com/Jeffallan/claude-skills/stargazers)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Jeffallan/claude-skills&type=date&legend=top-left)](https://www.star-history.com/#Jeffallan/claude-skills&type=date&legend=top-left)

---

**Built for Claude Code** | **<!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> Workflows** | **<!-- REFERENCE_COUNT -->365<!-- /REFERENCE_COUNT --> Reference Files** | **<!-- SKILL_COUNT -->66<!-- /SKILL_COUNT --> Skills**
