# Quick Start Guide

Get up and running with the Fullstack Dev Skills Plugin.

## Installation (Choose One)

### Marketplace (Recommended)
```bash
# Add the marketplace
/plugin marketplace add jeffallan/claude-skills

# Install the plugin
/plugin install fullstack-dev-skills@fullstack-dev-skills

# Restart Claude Code when prompted
```

### Install from GitHub
```bash
claude plugin install fullstack-dev-skills --marketplace jeffallan/claude-skills
```

### Install via skills.sh
```bash
npx skills add jeffallan/claude-skills
```

> **Note:** This method installs skills only. Slash commands (`/common-ground` and the workflow commands) are not included.

[Supported Agents](docs/SUPPORTED_AGENTS.md#skills-cli) lists the agent ids and flags for Cursor, Codex CLI and other agents.

### Install via Agent Skills CLI
```bash
npx agent-skills-cli@latest add @Jeffallan/claude-skills
```

> **Note:** This method installs skills only. Slash commands (`/common-ground` and the workflow commands) are not included. It installs to 42+ AI agents including Claude, Cursor, Copilot, Windsurf, and more. [Learn more](https://www.agentskills.in)

[Supported Agents](docs/SUPPORTED_AGENTS.md#skills-cli) lists its agent ids and the folders it writes to.

### Local Development
```bash
cp -r ./plugin/skills/* ~/.claude/skills/
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

<!-- SKILL_COUNT -->72<!-- /SKILL_COUNT --> skills covering:
- <!-- SKILL_COUNT:language -->12<!-- /SKILL_COUNT:language --> Language Experts (Python, TypeScript, Go, Rust, C++, Swift, Kotlin, C#, PHP, Java, SQL, JavaScript)
- <!-- SKILL_COUNT:backend -->9<!-- /SKILL_COUNT:backend --> Backend Framework Experts (NestJS, Django, Django Storages S3, FastAPI, Flask, Spring Boot, Laravel, Rails, .NET Core)
- <!-- SKILL_COUNT:frontend -->8<!-- /SKILL_COUNT:frontend --> Frontend & Mobile Experts (React, Next.js, Nuxt, Vue, Vue (JavaScript), Angular, React Native, Flutter)
- <!-- WORKFLOW_COUNT -->13<!-- /WORKFLOW_COUNT --> Project Workflow Commands: `intake`, discovery, spec, ticket and `common-ground`
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

### 4. Your First Spec

The workflow commands need the full plugin install (the skills-only methods above leave them out) and [uv](https://docs.astral.sh/uv/):

1. Run `/fullstack-dev-skills:spec:triage`. With no `.claude/workflow-config.json` yet, it offers a setup wizard that detects your tracker and asks one question at a time.
2. Approve the proposed grouping. Triage creates the spec's group in your tracker and a `spec/<spec-name>` branch.
3. Run `/fullstack-dev-skills:spec:create <spec-name>` and approve the overview. It writes the plan and prints two launch commands: one for the whole spec and one for the next batch.
4. Work the tickets with `ticket:execute` and `ticket:complete`, or start one of the printed goal runs.
5. Finish with `spec:review` and `spec:complete`.

For an existing codebase, start with `/fullstack-dev-skills:intake`. It documents the code, pins its behavior in tests and records its bugs, one checklist item at a time. See [Intake](docs/INTAKE.md).

See [Workflow Commands](docs/WORKFLOW_COMMANDS.md) and [Tracker Setup](docs/TRACKER_SETUP.md).

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
- [Tracker Setup](docs/TRACKER_SETUP.md) - Workflow config and tracker adapters
- [Intake](docs/INTAKE.md) - Adopt an existing codebase
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
3. Try reinstalling: `/plugin uninstall fullstack-dev-skills@fullstack-dev-skills` then reinstall

### How to Update
```bash
# Marketplace installs update automatically
# For manual installs, pull latest and re-copy:
cd claude-skills && git pull
cp -r ./plugin/skills/* ~/.claude/skills/
```

### Need Help
- Check [Skills Guide](SKILLS_GUIDE.md) for skill-specific guidance
- Review individual `plugin/skills/*/SKILL.md` files
- Open an [issue on GitHub](https://github.com/jeffallan/claude-skills/issues)

## Next Steps

### Explore Skills
Browse the `plugin/skills/` directory for available skills.

### Customize
Edit any `SKILL.md` to match team conventions.

### Contribute
Add new skills. See `CONTRIBUTING.md`.

## Support

- Documentation: Check [README](README.md) and [Skills Guide](SKILLS_GUIDE.md)
- Issues: [GitHub Issues](https://github.com/jeffallan/claude-skills/issues)
- Discussions: [GitHub Discussions](https://github.com/jeffallan/claude-skills/discussions)
