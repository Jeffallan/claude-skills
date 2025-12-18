# Claude Skills Project Configuration

> This file governs Claude's behavior when working on the claude-skills repository.

---

## Skill Authorship Standards

### The Description Trap

**Critical:** Skill descriptions must be TRIGGER-ONLY. Never summarize the workflow or process.

When descriptions contain process steps, agents follow the brief description instead of reading the full skill content. This defeats the purpose of detailed skills.

**BAD - Process in description:**
```yaml
description: Use for debugging. First investigate root cause, then analyze
patterns, test hypotheses, and implement fixes with tests.
```

**GOOD - Trigger-only:**
```yaml
description: Use when encountering bugs, errors, or unexpected behavior
requiring investigation.
```

**Format:** `Use when [specific triggering conditions]`

Descriptions tell WHEN to use the skill. The SKILL.md body tells HOW.

---

### Frontmatter Requirements

```yaml
---
name: skill-name-with-hyphens
description: Use when [triggering conditions] - max 1024 chars
triggers: [keyword1, keyword2, keyword3]
role: specialist|expert|architect
scope: implementation|review|design|system-design
output-format: code|document|report|architecture
---
```

**Constraints:**
- `name`: Letters, numbers, and hyphens only (no parentheses or special characters)
- `description`: Maximum 1024 characters, trigger-only format
- `triggers`: Searchable keywords that would appear in user requests

---

### Reference File Standards

**Header format:**
```markdown
# [Reference Title]

> Reference for: [Parent Skill Name]
> Load when: [specific trigger phrases, keywords, scenarios]

---
```

**Guidelines:**
- 100-600 lines per reference file
- Complete, working code examples with TypeScript types
- Cross-reference related skills where relevant
- Include "when to use" and "when not to use" guidance
- Practical patterns over theoretical explanations

---

### Progressive Disclosure Architecture

**Tier 1 - SKILL.md (~80-100 lines)**
- Role definition and expertise level
- When-to-use guidance (triggers)
- Core workflow (5 high-level steps)
- Constraints (MUST DO / MUST NOT DO)
- Routing table to references

**Tier 2 - Reference Files (100-600 lines each)**
- Deep technical content
- Complete code examples
- Edge cases and anti-patterns
- Loaded only when context requires

**Goal:** 50% token reduction through selective loading.

---

## Project Workflow

### When Creating New Skills

1. Check existing skills for overlap
2. Write SKILL.md with trigger-only description
3. Create reference files for deep content (100+ lines)
4. Add routing table linking topics to references
5. Test skill triggers with realistic prompts
6. Update SKILLS_GUIDE.md if adding new domain

### When Modifying Skills

1. Read the full current skill before editing
2. Maintain trigger-only description format
3. Preserve progressive disclosure structure
4. Update related cross-references
5. Verify routing table accuracy

---

## Attribution

Behavioral patterns and process discipline adapted from:
- **[obra/superpowers](https://github.com/obra/superpowers)** by Jesse Vincent (@obra)
- License: MIT

Research documented in: `research/superpowers.md`
