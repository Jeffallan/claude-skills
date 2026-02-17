# Contributing to Fullstack Dev Skills Plugin

Guidelines for contributing to this project.

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

### Adding Supported Agents
To add a new agent that implements the Agent Skills specification, see the [Supported Agents guide](docs/SUPPORTED_AGENTS.md#submit-a-new-agent) for submission instructions and PR template.

### Submitting Changes

#### 1. Fork and Clone
```bash
# Fork on GitHub, then:
git clone https://github.com/jeffallan/claude-skills.git
cd claude-skills
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

# Create SKILL.md following the structure below
```

#### 4. Test Your Changes
```bash
# Copy skills to test location
cp -r skills/* ~/.claude/skills/

# Restart Claude Code and test
# Verify your skill activates correctly
# Test all examples in the SKILL.md
```

#### 4.5. Validate Your Skill

Run the validation script to catch issues before CI:

```bash
python scripts/validate-skills.py --skill your-skill-name
```

#### 5. Commit Your Changes
```bash
git add .
git commit -m "Add: My New Skill for XYZ framework"
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

## Skill Writing Guidelines

### Frontmatter Schema

```yaml
---
name: my-skill-name
description: Use when [triggering conditions]. Invoke for [specific keywords].
license: MIT
metadata:
  author: https://github.com/YourGitHub
  version: "1.0.0"
  triggers: keyword1, keyword2, phrase1
  role: specialist
  scope: implementation
  output-format: code
  domain: frontend
  related-skills: react-expert, typescript-pro, nextjs-developer
---
```

**Description Formula:**
```
Use when [triggering conditions]. Invoke for [specific keywords].
```

**Example:**
```yaml
description: Use when building React 18+ applications requiring component architecture, hooks patterns, or state management. Invoke for Server Components, performance optimization, Suspense boundaries, React 19 features.
```

### Required Sections (In Order)

```markdown
# [Skill Name]

[One-sentence role definition]

## Role Definition

[2-3 sentences defining expert persona with years of experience and specializations]

## When to Use This Skill

- [Bullet list of specific scenarios]
- [When this skill should be triggered]

## Core Workflow

1. **Step** - Brief description
2. **Step** - Brief description
3. **Step** - Brief description

## Technical Guidelines

[Framework-specific patterns, code examples, tables]

### Subsection Title

| Column | Column |
|--------|--------|
| Data   | Data   |

```language
// Code examples with comments
```

## Constraints

### MUST DO
- [Required practices - strong directive language]
- [Use imperative form]

### MUST NOT DO
- [Things to avoid - strong directive language]
- [Use imperative form]

## Output Templates

When implementing [X], provide:
1. [Expected output format]
2. [Additional deliverables]

## Knowledge Reference

[Comma-separated keywords only - no sentences]

```

### Progressive Disclosure Pattern

For skills with extensive reference material, use the progressive disclosure pattern to reduce initial token load:

**Structure:**
```text
skills/my-skill/
├── SKILL.md           # Lean main file (~80-100 lines)
└── references/        # Domain-specific reference files
    ├── topic-a.md     # Loaded when topic A is relevant
    ├── topic-b.md     # Loaded when topic B is relevant
    └── topic-c.md     # Loaded when topic C is relevant
```

**Main SKILL.md includes a routing table:**
```markdown
## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| State Management | `references/state-management.md` | Using Redux, Zustand, Context |
| Server Components | `references/server-components.md` | Next.js App Router, RSC |
| Testing | `references/testing.md` | Writing tests, jest, RTL |
```

**Reference File Format:**
```markdown
# Topic Title

> Reference for: Skill Name
> Load when: Specific trigger conditions

## Section

[Detailed content, code examples, tables...]

## Quick Reference

| Item | Description |
|------|-------------|
| Key  | Value       |
```

**When to Use Progressive Disclosure:**
- Skill has 5+ distinct topic areas
- Original content exceeds 100 lines
- Topics are contextually independent
- Code examples are extensive

**Benefits:**
- 40-50% reduction in initial token load
- Contextual loading of relevant information
- Easier maintenance of domain-specific content

### Token Efficiency Guidelines

1. **Use Tables** - Convert lists to tables where comparing options
2. **One Example Per Pattern** - One comprehensive example instead of many small ones
3. **Keywords Only** - Knowledge Reference should be comma-separated terms, not sentences
4. **Remove Redundancy** - Don't repeat information across sections
5. **Avoid Obvious Comments** - Code should be self-explanatory where possible
6. **Link Don't Reproduce** - Reference external docs instead of copying content
7. **Use Progressive Disclosure** - Split large skills into main file + references/

### Code Examples Best Practices

```typescript
// ❌ Bad: Unclear or anti-pattern
function badExample() {
  // Why this is bad
}

// ✅ Good: Clear, follows best practices
function goodExample() {
  // Why this is good
}
```

**Guidelines:**
- Include both bad and good examples for common mistakes
- Use language tags on all code blocks
- Keep examples practical and real-world
- Remove unnecessary comments that state the obvious

### Framework Version Requirements

Keep examples current with latest stable versions:
- **React**: 19+ (Server Components, use() hook, form actions)
- **Python**: 3.11+ (X | None syntax, match/case)
- **FastAPI/Pydantic**: V2 (field_validator, Annotated pattern)
- **Django**: 5.0+ (async views, async ORM)
- **TypeScript**: 5.x (satisfies operator, const type parameters)
- **Node.js**: 20+ LTS

### Testing Your Skill

Before submitting:
1. **Trigger Test**: Does it activate with appropriate prompts?
2. **Code Test**: Do all code examples compile/run?
3. **Completeness**: Does it cover main use cases?
4. **Accuracy**: Is information correct and up-to-date?
5. **Token Efficiency**: Is content concise without redundancy?
6. **Integration**: Does it reference related skills?

## Code of Conduct

This project follows the [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

### Our Pledge

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, caste, color, religion, or sexual identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming, diverse, inclusive, and healthy community.

### Our Standards

Examples of behavior that contributes to a positive environment:

- Demonstrating empathy and kindness toward other people
- Being respectful of differing opinions, viewpoints, and experiences
- Giving and gracefully accepting constructive feedback
- Accepting responsibility and apologizing to those affected by our mistakes, and learning from the experience
- Focusing on what is best not just for us as individuals, but for the overall community

Examples of unacceptable behavior:

- The use of sexualized language or imagery, and sexual attention or advances of any kind
- Trolling, insulting or derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or email address, without their explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

### Enforcement

Project maintainers are responsible for clarifying and enforcing standards of acceptable behavior and will take appropriate and fair corrective action in response to any behavior that they deem inappropriate, threatening, offensive, or harmful.

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by opening an issue or contacting the maintainers directly. All complaints will be reviewed and investigated promptly and fairly.

## Questions

- Open a [GitHub Discussion](https://github.com/jeffallan/claude-skills/discussions)
- Comment on relevant issues
- Reach out to maintainers

## Recognition

Contributors will be recognized in:
- [GitHub contributors page](https://github.com/Jeffallan/claude-skills/graphs/contributors)
- Release notes for significant contributions
