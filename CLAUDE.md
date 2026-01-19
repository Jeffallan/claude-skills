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

## Release Checklist

When releasing a new version, update all version numbers and counts consistently.

### 1. Update Version Numbers

| File | Location |
|------|----------|
| `.claude-plugin/plugin.json` | `"version": "X.Y.Z"` |
| `.claude-plugin/marketplace.json` | `"version": "X.Y.Z"` (appears twice: metadata and plugins) |
| `README.md` | Badge URL: `version-X.Y.Z-blue.svg` |
| `ROADMAP.md` | Current status section: `**Version:** vX.Y.Z` |
| `ROADMAP.md` | Last updated footer |

### 2. Update Counts

Verify actual counts match documentation:

```bash
# Count skills (subtract 1 for parent directory)
find skills/ -maxdepth 1 -type d | wc -l

# Count reference files
find skills/ -path "*/references/*.md" | wc -l

# Count project workflow commands
find commands/project -name "*.md" | wc -l
```

**Files to update with new counts:**

| File | What to Update |
|------|----------------|
| `.claude-plugin/plugin.json` | Description: "X specialized skills" |
| `.claude-plugin/marketplace.json` | Description: "X specialized skills", "Y commands" |
| `README.md` | Header image (skills/workflows), badge stats, project structure comments, stats section, footer |
| `ROADMAP.md` | Current status: skills, reference files, frameworks, commands |
| `QUICKSTART.md` | "X skills covering" section |
| `assets/social-preview.html` | Subtitle, stats spans (skills, workflows, reference files) |

### 3. Update CHANGELOG.md

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

### 4. Update Documentation for New/Modified Content

**For new skills:**
- Add to `SKILLS_GUIDE.md` in appropriate category
- Add to decision trees if applicable
- Verify skill count in all locations above

**For new commands:**
- Add to `docs/WORKFLOW_COMMANDS.md`
- Add to `README.md` Project Workflow Commands table
- Update command count in all locations above

**For modified skills/commands:**
- Update any cross-references
- Update SKILLS_GUIDE.md if triggers changed

### 5. Generate Social Preview

After all updates, regenerate the social preview image:

```bash
node ./assets/capture-screenshot.js
```

This creates `assets/social-preview.png` from `assets/social-preview.html`.

### 6. Validate Skills Integrity

**Critical:** Run these checks to prevent broken skills from being released.

```bash
# Validate YAML frontmatter in all SKILL.md files
python3 -c "
import yaml, os
errors = []
for skill in sorted(os.listdir('skills')):
    path = f'skills/{skill}/SKILL.md'
    if os.path.isfile(path):
        with open(path) as f:
            content = f.read()
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    yaml.safe_load(parts[1])
                except yaml.YAMLError as e:
                    errors.append(f'{skill}: {e}')
if errors:
    print('YAML ERRORS:')
    for e in errors: print(f'  - {e}')
    exit(1)
print('All YAML valid')
"

# Verify all skills have references directory
for skill in skills/*/; do
  if [ ! -d "${skill}references" ]; then
    echo "ERROR: Missing references directory: $skill"
    exit 1
  fi
done && echo "All skills have references directories"

# Count reference files per skill (should be 5 each)
for skill in skills/*/; do
  count=$(ls "${skill}references/"*.md 2>/dev/null | wc -l)
  if [ "$count" -lt 1 ]; then
    echo "WARNING: $skill has no reference files"
  fi
done
```

**Common YAML issues to avoid:**
- Unquoted colons in description (e.g., `Keywords:` causes parsing errors)
- Special characters that need escaping
- Missing required frontmatter fields

### 7. Final Verification

Run parallel searches to verify consistency:

```bash
# Check no old version references remain (except historical changelog)
grep -r "OLD_VERSION" --include="*.md" --include="*.json" --include="*.html"

# Verify counts match
grep -r "XX skills" --include="*.md" --include="*.json" --include="*.html"
```

---

## Attribution

Behavioral patterns and process discipline adapted from:
- **[obra/superpowers](https://github.com/obra/superpowers)** by Jesse Vincent (@obra)
- License: MIT

Research documented in: `research/superpowers.md`
