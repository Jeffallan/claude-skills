# Quick Start Guide

Get up and running with the Fullstack Dev Skills Plugin.

## Installation (Choose One)

### Marketplace (Recommended)
```bash
# Add the marketplace
/plugin marketplace add jeffallan/claude-skills

# Install the plugin
/plugin install fullstack-dev-skills@jeffallan

# Restart Claude Code when prompted
```

### Install from GitHub
```bash
claude plugin install https://github.com/jeffallan/claude-skills
```

### Install via skills.sh
```bash
npx skills add jeffallan/claude-skills
```

> **Note:** This method installs skills only. Slash commands (`/common-ground`, `/project:*`) are not included.

### Local Development
```bash
cp -r ./skills/* ~/.claude/skills/
```
Restart Claude Code after copying.

## Test Your Installation

Verify skills are working:

```bash
# Test NestJS Expert
"Help me implement JWT authentication in NestJS"

# Test React Expert
"Create a custom React hook for form validation"

# Test Debugging Wizard
"Debug this memory leak in my Node.js application"

# Test Security Reviewer
"Review this code for security vulnerabilities"
```

## First Steps

### 1. What's Included

<!-- SKILL_COUNT -->66<!-- /SKILL_COUNT --> skills covering:
- 12 Language Experts (Python, TypeScript, Go, Rust, C++, Swift, Kotlin, C#, PHP, Java, SQL, JavaScript)
- 7 Backend Framework Experts (NestJS, Django, FastAPI, Spring Boot, Laravel, Rails, .NET Core)
- 7 Frontend & Mobile Experts (React, Next.js, Vue, Angular, React Native, Flutter)
- <!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> Project Workflow Commands (discovery, planning, execution, retrospectives)
- Plus: Infrastructure, DevOps, Security, Architecture, Testing, and more

### 2. First Prompt

Specify the tech stack and Claude activates the appropriate skills:

```
"I need to implement a user profile feature in my NestJS API with authentication"
→ Activates NestJS Expert + Secure Code Guardian
```

```
"My React app has a memory leak, help me debug it"
→ Activates Debugging Wizard + React Expert
```

### 3. Learn More

See [Skills Guide](SKILLS_GUIDE.md) for decision trees, skill combinations, and detailed examples for every category.

## Effective Usage

### 1. Provide Context
Include relevant information:
- Framework/language you're using
- What you're trying to accomplish
- Any constraints or requirements
- Error messages (if debugging)

### 2. Ask for Multiple Perspectives
```
"Review this authentication code for both security and performance issues"
[Activates: Security Reviewer + Code Reviewer]
```

### 3. Reference the Guides
- [README](README.md) - Overview and architecture
- [Skills Guide](SKILLS_GUIDE.md) - Detailed skill reference with decision trees
- [Common Ground](docs/COMMON_GROUND.md) - Context engineering guide
- [Workflow Commands](docs/WORKFLOW_COMMANDS.md) - Workflow commands reference
- [Contributing](CONTRIBUTING.md) - How to customize/extend

## Troubleshooting

### Skills Not Activating
1. Restart Claude Code after installation
2. Check skill files exist: `ls ~/.claude/skills/`
3. Be more specific with framework/technology names
4. Try explicitly mentioning the skill name: "Use the NestJS Expert to help me..."

### Skills Not Loading After Install
1. Verify the plugin is installed: `/plugin list`
2. Check for conflicting skill names in `~/.claude/skills/`
3. Try reinstalling: `/plugin uninstall fullstack-dev-skills@jeffallan` then reinstall

### How to Update
```bash
# Marketplace installs update automatically
# For manual installs, pull latest and re-copy:
cd claude-skills && git pull
cp -r ./skills/* ~/.claude/skills/
```

### Need Help
- Check [Skills Guide](SKILLS_GUIDE.md) for skill-specific guidance
- Review individual `skills/*/SKILL.md` files
- Open an [issue on GitHub](https://github.com/jeffallan/claude-skills/issues)

## Next Steps

### Explore Skills
Browse the `skills/` directory for available skills.

### Customize
Edit any `SKILL.md` to match team conventions.

### Contribute
Add new skills. See `CONTRIBUTING.md`.

## Support

- Documentation: Check [README](README.md) and [Skills Guide](SKILLS_GUIDE.md)
- Issues: [GitHub Issues](https://github.com/jeffallan/claude-skills/issues)
- Discussions: [GitHub Discussions](https://github.com/jeffallan/claude-skills/discussions)
