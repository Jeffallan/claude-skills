# Claude Skills Project Configuration

> This file governs Claude's behavior when working on the claude-skills repository.

---

## Skill Authorship Standards

Skills follow the [Agent Skills specification](https://agentskills.io/specification). This section covers project-specific conventions that go beyond the base spec.

### The Description Trap

**Critical:** Never put process steps or workflow sequences in descriptions. When descriptions contain step-by-step instructions, agents follow the brief description instead of reading the full skill content. This defeats the purpose of detailed skills.

Brief capability statements (what it does) and trigger conditions (when to use it) are both appropriate. Process steps (how it works) are not.

**BAD - Process steps in description:**
```yaml
description: Use for debugging. First investigate root cause, then analyze
patterns, test hypotheses, and implement fixes with tests.
```

**GOOD - Capability + trigger:**
```yaml
description: Diagnoses bugs through root cause analysis and pattern matching.
Use when encountering errors or unexpected behavior requiring investigation.
```

**Format:** `[Brief capability statement]. Use when [triggering conditions].`

Descriptions tell WHAT the skill does and WHEN to use it. The SKILL.md body tells HOW.

---

### Frontmatter Requirements

Per the [Agent Skills specification](https://agentskills.io/specification), only `name` and `description` are top-level required fields. Custom fields go under `metadata`.

```yaml
---
name: skill-name-with-hyphens
description: [Brief capability statement]. Use when [triggering conditions] - max 1024 chars
license: MIT
metadata:
  author: https://github.com/Jeffallan
  company: https://synergetic.solutions
  version: "1.0.0"
  domain: frontend
  triggers: keyword1, keyword2, keyword3
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian, test-master, devops-engineer
---
```

**Top-level fields (spec-defined):**
- `name`: Letters, numbers, and hyphens only (no parentheses or special characters)
- `description`: Maximum 1024 characters. Capability statement + trigger conditions. No process steps.
- `license`: Always `MIT` for this project
- `allowed-tools`: Space-delimited tool list (only on skills that restrict tools)

**Metadata fields (project-specific):**
- `author`: GitHub profile URL of the skill author
- `company`: Optional. URL of the author's company (`https://synergetic.solutions` on skills authored by @jeffallan); omit for contributed skills unless the contributor supplies one
- `version`: Semantic version string (quoted, e.g., `"1.0.0"`)
- `domain`: Category from the domain list below
- `triggers`: Comma-separated searchable keywords
- `role`: `specialist` | `expert` | `architect` | `engineer`
- `scope`: `implementation` | `review` | `design` | `system-design` | `testing` | `analysis` | `infrastructure` | `optimization` | `architecture`
- `output-format`: `code` | `document` | `report` | `architecture` | `specification` | `schema` | `manifests` | `analysis` | `analysis-and-code`
- `related-skills`: Comma-separated skill directory names (e.g., `fullstack-guardian, test-master`). Must resolve to existing skill directories.

**Domain values:**
`language` · `backend` · `frontend` · `infrastructure` · `api-architecture` · `quality` · `devops` · `security` · `data-ml` · `platform` · `specialized` · `workflow`

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

### Framework Idiom Principle

Reference files for framework-specific skills must reflect the idiomatic best practices of that framework, not generic patterns applied uniformly across all skills. If a framework provides a built-in mechanism (e.g., global error handling, middleware, dependency injection), reference examples should use it rather than duplicating that behavior manually. Each framework's conventions for error handling, architecture, and code organization take precedence over cross-project consistency.

---

### Documentation Backlink

Every `SKILL.md` MUST end with a single canonical Documentation link pointing back to the docs site:

```
[Documentation](https://jeffallan.github.io/claude-skills/skills/{domain}/{skill-name}/)
```

- `{domain}` is `metadata.domain` from the frontmatter and must be one of the `domains` in `pyproject.toml` (`[tool.skill-linter]`); the docs site build fails on any other value.
- `{skill-name}` is the skill's directory name.
- Format is exactly markdown link syntax (`[text](url)`), not a bare URL. Strict CommonMark renderers do not auto-link bare URLs, and the line's purpose is to render as a real `<a href>` on aggregators (skills.sh, etc.) for SEO backlinks.

**Why two surfaces, two behaviors:**

- Aggregators consume raw `SKILL.md` from GitHub and render the line as a hyperlink. This is the SEO point.
- The docs site itself would render this line as a self-link, which is redundant. The site's content sync (`site/src/components/site-sync/`, configured by `site/scripts/sync-content.mjs`) strips the line, and the credit line above it, at build time so the docs site, public markdown mirrors, `llms.txt`, and `llms-full.txt` never show it.

**When adding or renaming a skill:** update both the directory name (which becomes `{skill-name}`) and the `metadata.domain` consistently with this URL formula, otherwise the backlink will 404.

### Maintainer Credit

Skills authored by @jeffallan (those with `metadata.company: https://synergetic.solutions`) carry one more line, directly above the Documentation backlink, separated by a blank line. It matches the docs site footer credit:

```
Maintained by [@jeffallan](https://github.com/jeffallan), Principal Consultant at [Synergetic Solutions](https://synergetic.solutions)

[Documentation](https://jeffallan.github.io/claude-skills/skills/{domain}/{skill-name}/)
```

- The Documentation backlink stays the last line
- Contributed skills do not get this line unless their `metadata.company` is set to the same URL
- `syncSkillPages` strips it at build time alongside the Documentation backlink, so the docs site, markdown mirrors, and `llms` files never show it (the site footer shows the same credit once per page)

---

### Progressive Disclosure Architecture

**Tier 1 - SKILL.md (~80-100 lines)**
- Role definition and expertise level
- When-to-use guidance (triggers)
- Core workflow (5 steps)
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
2. Write SKILL.md with capability + trigger description (no process steps)
3. Create reference files for deep content (100+ lines)
4. Add routing table linking topics to references
5. Append the canonical Documentation backlink as the last line (see Documentation Backlink above)
6. Test skill triggers with realistic prompts
7. Add the skill to SKILLS_GUIDE.md in its category

### When Modifying Skills

1. Read the full current skill before editing
2. Maintain capability + trigger description format (no process steps)
3. Preserve progressive disclosure structure
4. Update related cross-references
5. Verify routing table accuracy

### When Accepting Contributions

Every external contribution (issue or PR) gets the `gratitude` label, whatever its outcome.

For each PR:

1. Discuss fit with project goals before any merge decision (scope, overlap with existing skills, promotional content), then verify the content
2. Squash-merge with subject `type(scope): title (#N)`
   - Conflicted fork PRs: squash locally (`git merge --squash`), add `Co-authored-by:` with the contributor's commit email, then close the PR with a comment pointing at the commit
3. Record it in a separate commit, `docs(changelog): record #N <summary> under Unreleased`, adding an entry under `[Unreleased]` → Added/Changed/Fixed that ends with `(#N)` (append `closing #ISSUE` when it resolves one)
4. If skill or reference counts changed, run `uvx skill-linter@0.2.0 stamp` in the same push, otherwise `stamp --check` fails CI on main
5. Post-merge corrections go in their own commit with their own `### Changed` entry

At release time, credit contributors (including issue reporters) in a `### Contributors` section of the version entry:

```markdown
### Contributors
- @handle: What they contributed (#N)
```

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
2. Stamp the counts and version:

```bash
uvx skill-linter@0.2.0 stamp
```

This computes the counts from the filesystem (skills, per-domain skills, references, workflows), writes them to `version.json`, and stamps the version and counts into the files listed under `[[tool.skill-linter.stamp.files]]` in `pyproject.toml` (README.md, QUICKSTART.md, plugin.json, marketplace.json, the docs site and others).

`uvx skill-linter@0.2.0 stamp --check` reports stale files without writing (CI runs it).

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
- Run `uvx skill-linter@0.2.0 stamp` to update counts

**For new commands:**
- Add to `docs/WORKFLOW_COMMANDS.md`
- Run `uvx skill-linter@0.2.0 stamp` to update counts

**For modified skills/commands:**
- Update any cross-references
- Update SKILLS_GUIDE.md if triggers changed

### 4. Generate Social Preview (conditional)

The social preview embeds skill, workflow, and reference counts but **not** the version. Only regenerate when at least one of `skillCount`, `workflowCount`, or `referenceFileCount` in `version.json` changed in this release — patch releases that only fix docs or a single skill normally do not need it.

When regeneration is needed:

```bash
npx -y -p puppeteer node ./assets/capture-screenshot.js
```

This creates `assets/social-preview.png` from `assets/social-preview.html`.

### 5. Validate

**Critical:** Run validation before release to prevent broken skills from being published.

```bash
make validate
```

This runs [skill-linter](https://pypi.org/project/skill-linter/), configured in `pyproject.toml` (`[tool.skill-linter]`), and is the same check CI runs:

- `skill-linter release` checks the shipped plugin tree (manifest, commands map, marketplace entry), then runs every other rule: frontmatter, names and descriptions, sections and references, Markdown syntax (unclosed fences, table separators, comments and column counts), commands, the changelog and stamped counts
- `skill-linter stamp --check` fails when a stamped count or version is stale

**Options:**
```bash
uvx skill-linter@0.2.0 check --skill react-expert   # One skill's rules only
uvx skill-linter@0.2.0 check --only markdown        # One rule group
uvx skill-linter@0.2.0 check --format json          # JSON output
uvx skill-linter@0.2.0 rules                        # Every rule, its group and severity
```

**Exit codes:** 0 = no errors (warnings OK), 1 = errors found

### 6. Final Verification

After running validation, manually verify:

```bash
# Check no old version references remain (except historical changelog)
grep -r "OLD_VERSION" --include="*.md" --include="*.json" --include="*.html"
```

### 7. Plugin Branch

The plugin ships from the `plugin` branch, not from `main`. Pushing the `vX.Y.Z` tag runs `.github/workflows/publish-plugin.yml`, which rebuilds that branch from `scripts/build-plugin-dist.sh` (only `.claude-plugin/plugin.json`, `skills/`, `commands/`, `references/`, `README.md`, `LICENSE`). Both the marketplace entry and the Claude plugin directory read from it.

- Never edit the `plugin` branch by hand; the next publish overwrites it
- After the tag push, confirm the workflow succeeded and the branch's latest commit names the new tag
- A file the plugin needs at runtime must live under one of the shipped paths, or it will be missing from installs

---

## Attribution

Behavioral patterns and process discipline adapted from:
- **[obra/superpowers](https://github.com/obra/superpowers)** by Jesse Vincent (@obra)
- License: MIT

Research documented in: `research/superpowers.md`
