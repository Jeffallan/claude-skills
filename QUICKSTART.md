# Quick Start Guide

Get up and running with Fullstack Dev Skills Plugin in minutes!

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

### Local Development
```bash
cp -r ./skills/* ~/.claude/skills/
```
Restart Claude Code after copying.

## Test Your Installation

Try these commands to verify skills are working:

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

<!-- SKILL_COUNT -->65<!-- /SKILL_COUNT --> skills covering:
- 12 Language Experts (Python, TypeScript, Go, Rust, C++, Swift, Kotlin, C#, PHP, Java, SQL, JavaScript)
- 7 Backend Framework Experts (NestJS, Django, FastAPI, Spring Boot, Laravel, Rails, .NET Core)
- 7 Frontend & Mobile Experts (React, Next.js, Vue, Angular, React Native, Flutter)
- <!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> Project Workflow Commands (discovery, planning, execution, retrospectives)
- Plus: Infrastructure, DevOps, Security, Architecture, Testing, and more

### 2. Your First Prompt

Be specific about your tech stack and Claude activates the right skills automatically:

```
You: "I need to implement a user profile feature in my NestJS API with authentication"
Claude: [Activates NestJS Expert + Secure Code Guardian]
```

```
You: "My React app has a memory leak, help me debug it"
Claude: [Activates Debugging Wizard + React Expert]
```

### 3. Learn More

See [SKILLS_GUIDE.md](SKILLS_GUIDE.md) for decision trees, skill combinations, and detailed examples for every category.

## Tips for Maximum Effectiveness

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
- [README.md](README.md) - Overview and architecture
- [SKILLS_GUIDE.md](SKILLS_GUIDE.md) - Detailed skill reference with decision trees
- [docs/COMMON_GROUND.md](docs/COMMON_GROUND.md) - Context engineering guide
- [docs/WORKFLOW_COMMANDS.md](docs/WORKFLOW_COMMANDS.md) - Workflow commands reference
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to customize/extend

## Troubleshooting

### Skills Not Activating?
1. Restart Claude Code after installation
2. Check skill files exist: `ls ~/.claude/skills/`
3. Be more specific with framework/technology names
4. Try explicitly mentioning the skill name: "Use the NestJS Expert to help me..."

### Skills Not Loading After Install?
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

### Need Help?
- Check [SKILLS_GUIDE.md](SKILLS_GUIDE.md) for skill-specific guidance
- Review individual `skills/*/SKILL.md` files
- Open an [issue on GitHub](https://github.com/jeffallan/claude-skills/issues)

## What's Next?

### Explore Skills
Browse `skills/` directory to see what each skill offers.

### Customize
Edit any `SKILL.md` to match your team's conventions.

### Contribute
Add your own skills! See `CONTRIBUTING.md`.

### Share
If you find this useful, share with your team:
```bash
# They can install with one command
claude plugin install https://github.com/jeffallan/claude-skills
```

## Quick Reference Card

Print or save this for quick reference:

```
FRAMEWORKS
├─ Backend: NestJS | Django | FastAPI
├─ Frontend: React
└─ Mobile: React Native | Flutter

WORKFLOWS
├─ Requirements: Feature Forge
├─ Implementation: Fullstack Guardian + Framework Expert
├─ Testing: Test Master + Playwright Expert
├─ Review: Code Reviewer + Security Reviewer
├─ Deploy: DevOps Engineer
├─ Monitor: Monitoring Expert
├─ Debug: Debugging Wizard
└─ Design: Architecture Designer

SECURITY
├─ Writing: Secure Code Guardian
└─ Reviewing: Security Reviewer

DOCUMENTATION
└─ Code Documenter (OpenAPI, JSDoc, Docstrings)
```

## Support

- Documentation: Check [README.md](README.md) and [SKILLS_GUIDE.md](SKILLS_GUIDE.md)
- Issues: [GitHub Issues](https://github.com/jeffallan/claude-skills/issues)
- Discussions: [GitHub Discussions](https://github.com/jeffallan/claude-skills/discussions)
- Contributing: See [CONTRIBUTING.md](CONTRIBUTING.md)
