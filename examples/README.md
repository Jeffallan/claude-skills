# Multi-Skill Workflow Examples

> Real-world examples showing how multiple Claude Skills chain together to complete complex tasks.

## Why Multi-Skill Workflows?

Individual skills are powerful, but real development tasks rarely fit into a single skill's domain. These examples demonstrate how skills hand off context to each other, building on previous outputs to deliver complete solutions.

## Examples

| Example | Skills Used | Language | Difficulty |
|---------|-------------|----------|------------|
| [Full-Stack Feature Development](FULLSTACK_FEATURE_TYPESCRIPT.md) | feature-forge, architecture-designer, nextjs-developer, nestjs-expert, test-master, playwright-expert, devops-engineer | TypeScript | Advanced |
| [Django API Debugging](DEBUGGING_DJANGO.md) | debugging-wizard, django-expert, test-master, code-reviewer | Python | Intermediate |
| [Legacy Java Modernization](LEGACY_MODERNIZATION_JAVA.md) | spec-miner, legacy-modernizer, architecture-designer, spring-boot-engineer, test-master, security-reviewer | Java | Advanced |

## How to Read These Examples

Each example follows the same structure:

1. **Overview** — The scenario and why multiple skills are needed
2. **Step N — [Stage] with [skill-name]** — Each skill invocation with:
   - The prompt used to trigger the skill
   - The skill's output (captured from actual execution)
   - What the skill contributed to the workflow
3. **Key Takeaways** — Patterns and lessons learned

## Skill Workflow Patterns

These examples map to workflows defined in [SKILLS_GUIDE.md](../SKILLS_GUIDE.md#skill-workflows):

- **Example 1** → [New Feature Development](../SKILLS_GUIDE.md#new-feature-development) + [Full Feature Development](../SKILLS_GUIDE.md#full-feature-development) + [Modern Web App](../SKILLS_GUIDE.md#modern-web-app)
- **Example 2** → [Bug Fixing](../SKILLS_GUIDE.md#bug-fixing)
- **Example 3** → [Legacy Migration](../SKILLS_GUIDE.md#legacy-migration) + [Enterprise Java](../SKILLS_GUIDE.md#enterprise-java)

## Contributing

Have a multi-skill workflow you'd like to share? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. Workflow examples should:

- Use **3 or more skills** in sequence
- Include **actual skill outputs** captured from Claude Code
- Cover a **realistic development scenario**
- Reference **exact skill names** from the `skills/` directory
