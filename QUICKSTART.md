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

### 1. Understand What You Have
<!-- SKILL_COUNT -->65<!-- /SKILL_COUNT --> skills covering:
- 12 Language Experts (Python, TypeScript, Go, Rust, C++, Swift, Kotlin, C#, PHP, Java, SQL, JavaScript)
- 10 Backend Framework Experts (NestJS, Django, FastAPI, Spring Boot, Laravel, Rails, .NET Core, etc.)
- 7 Frontend & Mobile Experts (React, Next.js, Vue, Angular, React Native, Flutter)
- <!-- WORKFLOW_COUNT -->9<!-- /WORKFLOW_COUNT --> Project Workflow Commands (discovery, planning, execution, retrospectives)
- Plus: Infrastructure, DevOps, Security, Architecture, Testing, and more

### 2. Common Use Cases

**Starting a New Feature**
```
You: "I need to implement a user profile feature in my NestJS API with authentication"
Claude: [Activates NestJS Expert + Secure Code Guardian]
```

**Debugging an Issue**
```
You: "My React app has a memory leak, help me debug it"
Claude: [Activates Debugging Wizard + React Expert]
```

**Code Review**
```
You: "Review this authentication implementation for security issues"
Claude: [Activates Code Reviewer + Security Reviewer]
```

**Setting Up Infrastructure**
```
You: "Help me set up monitoring for my FastAPI application"
Claude: [Activates Monitoring Expert + FastAPI Expert]
```

### 3. Best Practices

**Be Specific About Tech Stack**
✅ "Help me implement pagination in my FastAPI endpoint"
❌ "Help me implement pagination"

**Mention Security When Relevant**
✅ "Implement user authentication in Django with proper security"
✅ "Review this code for security issues"

**Combine Skills**
✅ "Design the architecture and implement a microservices system"
✅ "Implement this feature and add comprehensive tests"

### 4. Skill Activation Examples

| Your Request | Skills Activated |
|-------------|------------------|
| "Implement GraphQL in NestJS" | NestJS Expert |
| "Debug this async issue" | Debugging Wizard |
| "Review this PR" | Code Reviewer |
| "Set up CI/CD pipeline" | DevOps Engineer |
| "Create E2E tests with Playwright" | Playwright Expert, Test Master |
| "Design a scalable architecture" | Architecture Designer |
| "Implement secure password hashing" | Secure Code Guardian |
| "Scan code for vulnerabilities" | Security Reviewer |

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

### 3. Follow Recommended Workflows

**New Feature: Requirements → Design → Implement → Test → Review → Deploy**
1. Feature Forge (requirements)
2. Architecture Designer (design)
3. Fullstack Guardian + Framework Expert (implement)
4. Test Master + Playwright Expert (test)
5. Code Reviewer + Security Reviewer (review)
6. DevOps Engineer (deploy)
7. Monitoring Expert (observe)

### 4. Reference the Guides
- `README.md` - Overview and installation
- `SKILLS_GUIDE.md` - Detailed skill reference
- `CONTRIBUTING.md` - How to customize/extend

## Troubleshooting

### Skills Not Activating?
1. Restart Claude Code after installation
2. Check skill files exist: `ls ~/.claude/skills/`
3. Be more specific with framework/technology names
4. Try explicitly mentioning the skill name: "Use the NestJS Expert to help me..."

### Need Help?
- Check `SKILLS_GUIDE.md` for skill-specific guidance
- Review individual `skills/*/SKILL.md` files
- Open an issue on GitHub

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

- 📖 Documentation: Check README.md and SKILLS_GUIDE.md
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 🤝 Contributing: See CONTRIBUTING.md

Happy coding! 🚀
