# Skill SKILL.md Consistency Audit Report

> Audit date: 2026-02-02
> Audited by: Claude Opus 4.5
> Sample size: 10 skills out of 65 total
> Reference standard: CLAUDE.md project instructions (Skill Authorship Standards)

---

## 1. Consistency Matrix

The table below tracks whether each sampled skill conforms to the documented standard for each dimension.

| Dimension | react-expert | nestjs-expert | python-pro | code-reviewer | architecture-designer | feature-forge | debugging-wizard | terraform-engineer | security-reviewer | pandas-pro |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Frontmatter: required fields** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Description starts "Use when"** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Description trigger-only (no process)** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Description has "Invoke for" clause** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Role: valid enum value** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Scope: valid enum value** | PASS | PASS | PASS | PASS | PASS | PASS | WARN | PASS | PASS | PASS |
| **Output-format: valid enum value** | PASS | PASS | PASS | PASS | PASS | PASS | WARN | PASS | PASS | PASS |
| **H1 title present** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Role Definition section** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **When to Use section (bullet list)** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS |
| **Core Workflow (5 steps)** | PASS | PASS | PASS | PASS | PASS | PASS | FAIL (6) | PASS | FAIL (6) | PASS |
| **Reference Guide table** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Constraints: MUST DO** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Constraints: MUST NOT DO** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Output Templates section** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Knowledge Reference section** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Related Skills section** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Related Skills all valid** | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | FAIL | FAIL | FAIL |
| **No extra non-standard sections** | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS |
| **Line count 80-100** | 78 (low) | 74 (low) | 72 (low) | 72 (low) | 69 (low) | 75 (low) | 73 (low) | 77 (low) | 74 (low) | 76 (low) |
| **`allowed-tools` field** | -- | -- | -- | PASS | -- | -- | -- | -- | PASS | -- |

**Legend:** PASS = conforms, FAIL = deviates, WARN = uses value outside documented enum but value is reasonable, -- = not applicable

---

## 2. Common Quality Issues Across Skills

### 2.1 Phantom Related Skills References (CRITICAL)

The most significant cross-cutting issue. Multiple skills reference Related Skills that **do not exist** in the repository. Across the 10 sampled skills, 4 contain broken references. A broader search reveals this is a systemic problem across the full skill set (30+ phantom references found).

**Phantom names found in sampled skills:**
| Phantom Reference | Found In | Closest Actual Skill |
|---|---|---|
| "Data Science Pro" | python-pro | `pandas-pro` |
| "Cloud Architect" | terraform-engineer | `cloud-architect` (this one actually exists) |
| "Security Engineer" | terraform-engineer | `security-reviewer` or `secure-code-guardian` |
| "Secure Code Guardian" (display name) | architecture-designer, security-reviewer | `secure-code-guardian` (exists, but display name differs from H1 title) |
| "Data Scientist" | pandas-pro | No equivalent skill |

**Broader systemic phantoms found across all skills (not just sample):**
- "Backend Developer" (referenced by 6 skills) -- does not exist
- "Performance Engineer" (referenced by 8 skills) -- does not exist
- "Data Engineer" (referenced by 3 skills) -- does not exist
- "TypeScript Expert" (referenced in javascript-pro) -- actual name is `typescript-pro`
- "React Developer" (referenced in javascript-pro, typescript-pro) -- actual name is `react-expert`
- "Azure Specialist" (referenced in csharp-developer) -- does not exist
- "IoT Engineer" (referenced in embedded-systems) -- does not exist
- "Cloud Architect" (referenced by 7 skills) -- actually exists as `cloud-architect`
- "Security Engineer" (referenced by 2 skills) -- does not exist

**Root cause:** Related Skills use human-readable display names (e.g., "Backend Developer") that are not validated against the actual skill inventory. Some are aspirational references to skills that were never created. Others use slightly different display names than the actual skill's H1 title.

### 2.2 All Skills Fall Below Target Line Count

CLAUDE.md specifies Tier 1 SKILL.md files should be "~80-100 lines." Every sampled skill falls below the target range:

| Skill | Lines (non-blank) | Total Lines |
|---|---|---|
| react-expert | 78 | ~99 |
| nestjs-expert | 74 | ~95 |
| python-pro | 72 | ~93 |
| code-reviewer | 72 | ~93 |
| architecture-designer | 69 | ~90 |
| feature-forge | 75 | ~100 |
| debugging-wizard | 73 | ~94 |
| terraform-engineer | 77 | ~98 |
| security-reviewer | 74 | ~95 |
| pandas-pro | 76 | ~97 |

When blank lines are included, most files are close to the lower end of the 80-100 range. This is acceptable but means there is no headroom -- no skill invests its "line budget" on skill-specific nuances that would differentiate it from a template fill.

### 2.3 Core Workflow Step Count Inconsistency

CLAUDE.md specifies "Core workflow (5 high-level steps)." Two sampled skills use 6 steps:

- **debugging-wizard**: 6 steps (Reproduce, Isolate, Hypothesize, Test, Fix, Prevent)
- **security-reviewer**: 6 steps (Scope, Automated scan, Manual review, Active testing, Categorize, Report)

Both 6-step workflows are domain-justified and arguably better for it. This suggests the "5 steps" guidance may be too rigid, or these skills should be brought into compliance.

### 2.4 Frontmatter Enum Drift

The CLAUDE.md documents these enums:
- `scope`: `implementation | review | design | system-design`
- `output-format`: `code | document | report | architecture`

**Actual values found across the full 65-skill set that fall outside these enums:**

| Field | Non-standard Value | Skill(s) |
|---|---|---|
| `scope` | `analysis` | debugging-wizard |
| `scope` | `testing` | playwright-expert, test-master |
| `scope` | `infrastructure` | kubernetes-specialist, cloud-architect |
| `scope` | `optimization` | database-optimizer |
| `scope` | `architecture` | legacy-modernizer |
| `output-format` | `analysis` | debugging-wizard |
| `output-format` | `manifests` | kubernetes-specialist |
| `output-format` | `specification` | api-designer |
| `output-format` | `schema` | graphql-architect |
| `output-format` | `analysis-and-code` | database-optimizer |
| `output-format` | `code+analysis` | legacy-modernizer |

These are all reasonable values. The issue is that CLAUDE.md's enum list is incomplete, not that the skills are wrong. The documented enums need to be expanded, or a note added that custom values are permitted.

### 2.5 Non-Standard Frontmatter Fields

Two fields appear in some skills but are not documented in CLAUDE.md's Frontmatter Requirements:

- `allowed-tools`: Used by `code-reviewer`, `spec-miner`, `security-reviewer` (3 skills)

This field is meaningful (restricts which tools the skill can use) but is undocumented. It should either be added to the frontmatter spec or removed from the skills.

### 2.6 "When to Use" Format Inconsistency

9 of 10 sampled skills use a **bullet list** under "When to Use This Skill." The exception is **security-reviewer**, which uses a comma-separated prose paragraph:

```
Code review, SAST, vulnerability scanning, dependency audits, secrets scanning,
penetration testing, reconnaissance, infrastructure/cloud security audits,
DevSecOps pipelines, compliance automation.
```

This is the only format deviation in the sample but should be standardized for docs site generation.

### 2.7 Output Templates Format Inconsistency

Most skills use a numbered list under "Output Templates." Two deviate:

- **security-reviewer**: Uses inline prose with numbered parentheticals: `"Provide: (1) Executive summary... (2) Findings table..."`
- **debugging-wizard**: Uses bold labels in a numbered list (a richer format than others)

Neither is wrong, but for docs site rendering consistency, a single format should be chosen.

### 2.8 Attribution Comments in Routing Tables

Three skills contain HTML comments for attribution in their Reference Guide tables:

- `code-reviewer`: `<!-- Rows below adapted from obra/superpowers by Jesse Vincent (@obra), MIT License -->`
- `debugging-wizard`: Same pattern
- `test-master`: Same pattern

These are invisible in rendered markdown but would appear in raw source. For a docs site generator that processes SKILL.md files, these should either be preserved (if attribution is required) or moved to a separate attribution section.

---

## 3. Section Order Analysis

The expected section order (derived from CLAUDE.md's Progressive Disclosure Architecture and the majority pattern) is:

```
1. YAML Frontmatter
2. # Title
3. One-line subtitle/description
4. ## Role Definition
5. ## When to Use This Skill
6. ## Core Workflow
7. ## Reference Guide (table)
8. ## Constraints (### MUST DO, ### MUST NOT DO)
9. ## Output Templates
10. ## Knowledge Reference
11. ## Related Skills
```

**All 10 sampled skills follow this exact order**, with one exception:

- **feature-forge** adds a non-standard `## Pre-Discovery with Subagents` section between "Core Workflow" and "Reference Guide." This is the only skill in the sample with an extra section.

This is a strong positive finding: section order is highly consistent.

---

## 4. Per-Skill Deviations (Only Where Notable)

### 4.1 feature-forge

- **Extra section:** `## Pre-Discovery with Subagents` is a non-standard section not found in other skills. It describes a multi-agent workflow pattern.
- **Tool-specific constraints:** References `AskUserQuestions` tool explicitly in both Core Workflow and Constraints. This is unique among sampled skills and raises a question: should skills reference specific tools by name, or keep tool usage implicit?
- **File output path:** Specifies `Save as: specs/{feature_name}.spec.md` in Output Templates -- the only skill to prescribe a file path.

### 4.2 security-reviewer

- **"When to Use" is prose, not bullets** (see section 2.6 above).
- **Core Workflow has 6 steps** instead of 5.
- **Output Templates is prose** instead of numbered list.
- **Has `allowed-tools` field** not in the documented frontmatter spec.
- Overall, this skill deviates more from the template than any other in the sample.

### 4.3 debugging-wizard

- **Core Workflow has 6 steps** instead of 5.
- **`scope: analysis`** and **`output-format: analysis`** are outside documented enums.
- **Output Templates uses bold labels** (e.g., `**Root Cause**:`, `**Evidence**:`) -- richer format than others.

### 4.4 code-reviewer

- **Has `allowed-tools` field** (undocumented in spec).
- **Attribution HTML comment** in Reference Guide table.

### 4.5 python-pro

- **Phantom Related Skill:** References "Data Science Pro" which does not exist.

### 4.6 terraform-engineer

- **Phantom Related Skill:** References "Security Engineer" which does not exist.
- References "Cloud Architect" which does exist.

### 4.7 pandas-pro

- **Phantom Related Skill:** References "Data Scientist" which does not exist.
- Only 2 Related Skills listed (fewest in sample; others have 3-4).

### 4.8 architecture-designer

- **Lowest line count** in sample (69 non-blank lines).
- Related Skills reference names ("Secure Code Guardian") that use different casing/display than the H1 title in the actual skill.

### 4.9 react-expert, nestjs-expert

No notable deviations. These are the most template-conformant skills in the sample.

---

## 5. Docs Site Readiness Assessment

### What Works Well for Standalone Pages

1. **Consistent section structure** -- The 11-section order is machine-parseable and could directly map to page sections.
2. **YAML frontmatter** -- Provides structured metadata for page generation (title, category via scope, output type).
3. **Reference Guide table** -- Could generate "See Also" or "Deep Dive" link sections.
4. **Constraints** -- MUST DO / MUST NOT DO sections are visually distinctive and could be rendered as callout boxes.
5. **Related Skills** -- Natural cross-linking between pages (once phantom references are fixed).

### What Is Missing for Standalone Pages

| Gap | Impact | Effort |
|---|---|---|
| **No skill category/domain field** in frontmatter | Cannot auto-generate category pages (Frontend, Backend, etc.) | Low -- add `category` field |
| **No version/last-updated field** in frontmatter | Cannot show freshness on docs site | Low -- add `version` or `last-updated` field |
| **No short summary** separate from description | Description is trigger-focused; pages need a human-readable 1-2 sentence summary | Medium -- add `summary` field or derive from subtitle |
| **Related Skills use display names, not slugs** | Cannot auto-link without a name-to-slug mapping | Medium -- switch to slugs or add mapping |
| **Reference Guide paths are relative** | Docs site needs resolvable links | Low -- establish URL convention |
| **No difficulty/complexity indicator** | Users cannot self-select skills by experience level | Low -- add to frontmatter |
| **One-line subtitle has no consistent format** | Some are "Senior X specializing in Y", some are "Expert X developer..." | Low -- standardize template |
| **Knowledge Reference is a comma-separated string** | Not parseable for tag generation | Medium -- convert to YAML list or use triggers for this |

---

## 6. Template Recommendation

Based on this audit, the ideal SKILL.md structure for docs site generation would be:

```yaml
---
name: skill-name-with-hyphens
description: Use when [triggering conditions]. Invoke for [specific keywords].
summary: One-sentence human-readable summary for docs site cards.
category: frontend|backend|language|quality|architecture|design|workflow|infrastructure|security|data|devops|testing
triggers: [keyword1, keyword2, keyword3]
role: specialist|expert|architect
scope: implementation|review|design|system-design|analysis|testing|infrastructure|optimization
output-format: code|document|report|architecture|analysis|specification
version: "1.0"
---

# Skill Display Name

One-line role statement: "Senior [role] specializing in [domain]."

## Role Definition

2-3 sentences establishing persona, years of experience, and specializations.

## When to Use This Skill

- Bullet list only (no prose paragraphs)
- 5-7 specific triggering scenarios
- Each bullet starts with a gerund (Building, Implementing, etc.)

## Core Workflow

1. **Verb** - Brief description (5 steps, no more, no fewer)
2. **Verb** - Brief description
3. **Verb** - Brief description
4. **Verb** - Brief description
5. **Verb** - Brief description

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Topic Name | `references/filename.md` | Specific triggering condition |

## Constraints

### MUST DO
- Specific, domain-relevant imperatives (not generic platitudes)
- 6-8 items

### MUST NOT DO
- Specific, domain-relevant prohibitions
- 6-8 items

## Output Templates

When implementing [domain] solutions, provide:
1. Numbered list format only
2. 3-5 deliverables
3. Each item is a concrete artifact

## Knowledge Reference

Comma-separated list of technologies, standards, and tools.

## Related Skills

- **Actual Skill Display Name** - Relationship context (use exact H1 title from target skill)
- 3-4 related skills minimum
```

---

## 7. Priority-Ranked Recommendations

### Critical (Must fix before docs site generation)

1. **Fix all phantom Related Skills references.** Audit every skill's Related Skills against the actual inventory of 65 skills. Either correct the display name to match an existing skill's H1 title, or remove the reference. Estimated: 30+ broken references across the full set.

2. **Standardize Related Skills to use resolvable identifiers.** Currently these use human-friendly display names that cannot be auto-linked. Options:
   - (a) Use the frontmatter `name` (slug) as a machine-readable identifier alongside the display name
   - (b) Build a display-name-to-slug mapping table
   - (c) Add a `display-name` field to frontmatter so the mapping is self-contained

3. **Expand the documented frontmatter enums** in CLAUDE.md to match actual usage. Add `analysis`, `testing`, `infrastructure`, `optimization`, `architecture` to `scope`. Add `analysis`, `manifests`, `specification`, `schema` to `output-format`.

### High (Should fix for quality)

4. **Standardize the "When to Use" section** to always use bullet lists, not prose. Fix security-reviewer.

5. **Standardize the "Output Templates" section** to always use numbered lists, not inline prose. Fix security-reviewer.

6. **Enforce the 5-step Core Workflow rule** or explicitly amend CLAUDE.md to allow 5-6 steps. Two skills (debugging-wizard, security-reviewer) have 6 steps that are domain-justified.

7. **Document the `allowed-tools` frontmatter field** in CLAUDE.md, or decide it belongs in a separate mechanism.

8. **Remove or relocate non-standard sections** (feature-forge's "Pre-Discovery with Subagents") into a reference file to maintain the standard section order.

### Medium (Should fix for docs site polish)

9. **Add a `category` frontmatter field** for docs site navigation. Values like `frontend`, `backend`, `language`, `quality`, `architecture`, `design`, `workflow`, `infrastructure`, `security`, `data`, `devops`, `testing` would enable auto-generated category index pages.

10. **Add a `summary` frontmatter field** (or standardize the subtitle line) for docs site cards and search results. The current `description` is trigger-focused and reads awkwardly as a page summary.

11. **Standardize the subtitle line format** after the H1. Propose template: `"Senior [role] specializing in [1-2 domains] with expertise in [signature capability]."`

12. **Convert Reference Guide relative paths** to a docs-site-resolvable format, or establish a URL convention that a build step can apply.

### Low (Nice to have)

13. **Consider converting Knowledge Reference** from comma-separated prose to a YAML list in frontmatter (or a bullet list in the body) for tag generation on the docs site.

14. **Add `version` or `last-updated` metadata** to frontmatter for docs site freshness indicators.

15. **Standardize Related Skills count** to 3-4 per skill. pandas-pro has only 2; some non-sampled skills have 4-5.

16. **Handle attribution HTML comments** in routing tables. Decide whether to preserve as-is, move to a footer, or add an `attribution` frontmatter field.

17. **Consider adding a `difficulty` or `experience-level` field** to help users self-select appropriate skills.

---

## 8. Validation Script Gaps

The existing `scripts/validate-skills.py` checks YAML parsing, required fields, name format, description prefix, references directory, and count consistency. Based on this audit, the following checks should be added:

1. **Related Skills existence check** -- Verify each bold name in Related Skills maps to an actual skill's H1 title or frontmatter name.
2. **Core Workflow step count** -- Warn if not exactly 5 (or 5-6 if the standard is amended).
3. **"When to Use" format check** -- Ensure section uses bullet list format, not prose.
4. **Frontmatter enum validation** -- Check `scope` and `output-format` against the expanded (documented) enum list.
5. **Section order check** -- Verify sections appear in the canonical order.
6. **Line count check** -- Warn if below 80 or above 100 non-blank lines.

---

## 9. Summary

The skill set shows strong structural consistency. The 11-section template is followed by all 10 sampled skills, with section order preserved perfectly in 9 of 10 cases. Frontmatter fields are present and well-formed. Descriptions consistently follow the "Use when... Invoke for..." pattern.

The critical gap is **phantom Related Skills references** -- a systemic issue affecting approximately half the skill set and blocking reliable cross-linking on a docs site. The secondary gap is **enum drift** in frontmatter values, where actual usage has outgrown the documented specification.

Addressing the Critical and High priority items (8 items) would make the skill set docs-site-ready. The Medium and Low items (9 items) would polish the experience but are not blockers.
