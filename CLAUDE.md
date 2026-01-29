# Claude Skills Project Configuration

> This file governs Claude's behavior when working on the claude-skills repository.

---

## Skill Authorship Standards

Skills follow the [Agent Skills specification](https://agentskills.io/specification). This section covers project-specific conventions that go beyond the base spec.

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

Reference files follow the [Agent Skills specification](https://agentskills.io/specification). No specific headers are required.

**Guidelines:**
- 100-600 lines per reference file
- Keep files focused on a single topic
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

## Release Checklist

When releasing a new version, follow these steps.

### 1. Update Version and Counts

Version and counts are managed through `version.json`:

```json
{
  "version": "0.4.2",
  "skillCount": 65,
  "workflowCount": 9,
  "referenceFileCount": 355
}
```

**To release a new version:**

1. Update the `version` field in `version.json`
2. Run the update script:

```bash
python scripts/update-docs.py
```

The script will:
- Compute counts from the filesystem (skills, references, workflows)
- Update `version.json` with computed counts
- Update all documentation files (README.md, plugin.json, etc.)

**Options:**
```bash
python scripts/update-docs.py --check    # Verify files are in sync (CI use)
python scripts/update-docs.py --dry-run  # Preview changes without writing
```

### 2. Update CHANGELOG.md

Add new version entry at the top following Keep a Changelog format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features, skills, commands

### Changed
- Modified functionality, updated skills

### Fixed
- Bug fixes
```

Add version comparison link at bottom:
```markdown
[X.Y.Z]: https://github.com/jeffallan/claude-skills/compare/vPREVIOUS...vX.Y.Z
```

### 3. Update Documentation for New/Modified Content

**For new skills:**
- Add to `SKILLS_GUIDE.md` in appropriate category
- Add to decision trees if applicable
- Run `python scripts/update-docs.py` to update counts

**For new commands:**
- Add to `docs/WORKFLOW_COMMANDS.md`
- Add to `README.md` Project Workflow Commands table
- Run `python scripts/update-docs.py` to update counts

**For modified skills/commands:**
- Update any cross-references
- Update SKILLS_GUIDE.md if triggers changed

### 4. Generate Social Preview

After all updates, regenerate the social preview image:

```bash
node ./assets/capture-screenshot.js
```

This creates `assets/social-preview.png` from `assets/social-preview.html`.

### 5. Validate Skills Integrity

**Critical:** Run validation before release to prevent broken skills from being published.

```bash
python scripts/validate-skills.py
```

The script validates:
- **YAML frontmatter** - Parsing, required fields (name, description, triggers), format
- **Name format** - Letters, numbers, hyphens only
- **Description** - Max 1024 chars, starts with "Use when"
- **References** - Directory exists, has files, proper headers
- **Count consistency** - Skills/reference counts match across documentation

**Options:**
```bash
python scripts/validate-skills.py --check yaml       # YAML checks only
python scripts/validate-skills.py --check references # Reference checks only
python scripts/validate-skills.py --skill react-expert  # Single skill
python scripts/validate-skills.py --format json      # JSON output for CI
python scripts/validate-skills.py --help             # Full usage
```

**Exit codes:** 0 = success (warnings OK), 1 = errors found

### 6. Final Verification

After running validation, manually verify:

```bash
# Check no old version references remain (except historical changelog)
grep -r "OLD_VERSION" --include="*.md" --include="*.json" --include="*.html"
```

---

## Attribution

Behavioral patterns and process discipline adapted from:
- **[obra/superpowers](https://github.com/obra/superpowers)** by Jesse Vincent (@obra)
- License: MIT

Research documented in: `research/superpowers.md`
