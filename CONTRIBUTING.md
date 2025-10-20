# Contributing to Fullstack Dev Skills Plugin

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or suggest features
- Check existing issues before creating a new one
- Provide detailed information:
  - Steps to reproduce (for bugs)
  - Expected vs actual behavior
  - Claude Code version
  - Relevant error messages or logs

### Suggesting New Skills
When suggesting a new skill:
1. Explain the use case and target audience
2. Describe what the skill should do
3. List relevant technologies/frameworks
4. Provide examples of when it would be triggered

### Submitting Changes

#### 1. Fork and Clone
```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR-USERNAME/fullstack-dev-skills-plugin.git
cd fullstack-dev-skills-plugin
```

#### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

#### 3. Make Your Changes

**For New Skills:**
```bash
# Create skill directory
mkdir -p skills/my-new-skill

# Create SKILL.md with proper frontmatter
cat > skills/my-new-skill/SKILL.md << 'SKILLEOF'
---
name: My New Skill
description: Clear description with trigger keywords. Use when working with X, Y, Z technologies or when user mentions A, B, C concepts.
---

# My New Skill

## Instructions

### Core Workflow

1. **Step 1**
2. **Step 2**

[Include comprehensive examples, best practices, and patterns]

## Critical Rules

### Always Do
- ...

### Never Do
- ...

## Knowledge Base
- ...

## Integration with Other Skills
- ...

## Best Practices Summary
1. ...
SKILLEOF

# Add to package.json
# Edit package.json and add "my-new-skill" to claudeCode.skills array
```

**For Skill Improvements:**
- Update the relevant SKILL.md file
- Ensure examples are correct and tested
- Update documentation if needed

#### 4. Test Your Changes
```bash
# Copy skills to test location
cp -r skills/* ~/.claude/skills/

# Restart Claude Code and test
# Verify your skill activates correctly
# Test all examples in the SKILL.md
```

#### 5. Commit Your Changes
```bash
git add .
git commit -m "Add: My New Skill for XYZ framework"
# or
git commit -m "Fix: Corrected example in React Expert skill"
# or
git commit -m "Update: Improved NestJS authentication examples"
```

**Commit Message Format:**
- `Add:` for new features/skills
- `Fix:` for bug fixes
- `Update:` for improvements to existing content
- `Docs:` for documentation changes
- `Refactor:` for code restructuring

#### 6. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Description of what changed and why
- Any relevant issue numbers (e.g., "Fixes #123")
- Screenshots/examples if applicable

## Skill Writing Guidelines

### Frontmatter Requirements
```yaml
---
name: Skill Name  # Clear, descriptive name
description: Comprehensive description with keywords. Use when [specific scenarios]. # Be specific about triggers
allowed-tools: Read, Write, Edit  # Optional: restrict tools (e.g., Code Reviewer should be read-only)
---
```

### Content Structure
Each skill should include:

1. **Title and Introduction**
   - Brief overview of the skill's purpose

2. **Instructions Section**
   - **Core Workflow**: Step-by-step approach
   - Clear, actionable steps

3. **Code Examples**
   - Practical, real-world examples
   - Both ❌ bad and ✅ good examples where applicable
   - Properly formatted code blocks with language tags

4. **Best Practices**
   - Framework/technology-specific best practices
   - Common patterns and anti-patterns

5. **Critical Rules**
   - **Always Do**: Required practices
   - **Never Do**: Things to avoid

6. **Knowledge Base**
   - Technologies covered
   - Related tools and frameworks

7. **Integration with Other Skills**
   - How this skill works with others
   - Common combinations

8. **Best Practices Summary**
   - Numbered list of 8-10 key practices

### Writing Style
- **Clear and Concise**: Get to the point quickly
- **Actionable**: Provide specific guidance, not general advice
- **Examples-Heavy**: Show, don't just tell
- **Comprehensive**: Cover common scenarios and edge cases
- **Professional**: Technical but accessible tone

### Code Examples Best Practices
```typescript
// ❌ Bad: Unclear, unsafe, or anti-pattern
function badExample() {
  // Why this is bad
}

// ✅ Good: Clear, safe, follows best practices
function goodExample() {
  // Why this is good
}
```

### Testing Your Skill
Before submitting:
1. **Trigger Test**: Does it activate with appropriate prompts?
2. **Code Test**: Do all code examples work?
3. **Completeness**: Does it cover the main use cases?
4. **Accuracy**: Is all information correct and up-to-date?
5. **Integration**: Does it mention related skills?

## Code of Conduct

### Be Respectful
- Be welcoming and inclusive
- Respect differing viewpoints
- Give and receive constructive feedback gracefully
- Focus on what's best for the community

### Be Collaborative
- Help others learn and grow
- Share knowledge generously
- Acknowledge contributions
- Be patient with newcomers

### Be Professional
- Stay on topic
- Avoid inflammatory language
- Assume good intent
- Keep discussions productive

## Questions?

- Open a [GitHub Discussion](https://github.com/YOUR-USERNAME/fullstack-dev-skills-plugin/discussions)
- Comment on relevant issues
- Reach out to maintainers

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- GitHub contributors page

Thank you for helping make this plugin better! 🚀
