# Documentation Audit: Primary User-Facing Files

> Audit date: 2026-02-02
> Auditor: Technical writing agent (Claude Opus 4.5)
> Scope: README.md, SKILLS_GUIDE.md, QUICKSTART.md, CONTRIBUTING.md
> Supporting context: docs/COMMON_GROUND.md, docs/WORKFLOW_COMMANDS.md, CHANGELOG.md, docs/ideas/documentation-site.md

---

## Executive Summary

The four primary documents serve different audiences but suffer from significant content overlap, inconsistent naming conventions, and a structural problem: README.md tries to be both a landing page and a comprehensive reference. SKILLS_GUIDE.md is the strongest standalone document. QUICKSTART.md and CONTRIBUTING.md both contain stale installation instructions that diverge from the README. The biggest single improvement would be thinning the README to a focused landing page and letting specialized documents own their respective topics.

---

## Per-File Findings

### 1. README.md

**Purpose:** Project landing page and primary discovery surface (GitHub, search engines, LLM retrieval).

**Strengths:**
- Strong visual presentation with badges, animated header, star history
- Clear "Quick Start" section at the top with copy-paste install command
- Well-structured project tree showing directory layout
- Good use of the Documentation section as a hub linking to specialized docs
- Tech Stack Coverage section serves as an effective keyword surface for search/discovery

**Weaknesses:**

1. **Tries to be everything.** At 438 lines, the README functions as landing page, architecture guide, skills catalog, installation manual, usage tutorial, contributing guide, and marketing page. No single audience can scan it efficiently. A first-time visitor looking for "how do I install this" must scroll past architecture diagrams and 65-skill category lists.

2. **Duplicate installation instructions.** Three installation options appear in the "Quick Start" section at the top AND again in "Installation Options" at line 305. These two sections use different option numbering (the Installation Options section has two entries both labeled "Option 2"), different ordering, and different levels of detail.

3. **Skills Overview duplicates SKILLS_GUIDE.md.** Lines 116-133 reproduce a condensed version of the skill catalog that also lives in SKILLS_GUIDE.md. When skills are added or recategorized, both must be updated. Neither is clearly the source of truth.

4. **Context Engineering section duplicates docs/COMMON_GROUND.md.** Lines 182-227 reproduce the overview, command examples, confidence tiers, and mermaid graph that all exist in greater detail in docs/COMMON_GROUND.md. This section is 45 lines of content that could be 5 lines and a link.

5. **Project Workflow Commands section duplicates docs/WORKFLOW_COMMANDS.md.** Lines 229-242 duplicate the phase table from the workflow docs. The README should link, not reproduce.

6. **Contributing section duplicates CONTRIBUTING.md.** Lines 362-401 contain a condensed "Adding a New Skill" guide that partially overlaps with CONTRIBUTING.md but uses different line-count guidance (200-400 lines per reference here vs. no specific range in CONTRIBUTING.md). The frontmatter example in the README uses `name: My Skill` (with spaces), while CONTRIBUTING.md uses a different description formula. CLAUDE.md says names must be "letters, numbers, and hyphens only."

7. **Stale option numbering.** Under "Installation Options," there are two sections both labeled "Option 2" (npx add-skill and Local Development). Option 3 (Direct Installation) should logically be Option 4, or the npx method should be Option 2 and Local Development should be Option 3.

8. **Tech Stack Coverage is a wall of text.** Lines 244-297 list every supported technology in a flat bullet list. This is useful for SEO keyword density on GitHub but provides no navigational value. A reader cannot determine which skill covers which technology from this list alone.

**Recommendations:**
- Thin the README to under 200 lines: hero, one-line description, single install command, 3-sentence "what is this," link hub to specialized docs, contributing CTA, license/support
- Move architecture details to a dedicated `docs/ARCHITECTURE.md` or let the future docs site own it
- Remove the inline skills catalog; replace with a single sentence and link to SKILLS_GUIDE.md
- Remove the inline Context Engineering section; replace with a 2-line summary and link to docs/COMMON_GROUND.md
- Remove the inline Workflow Commands section; link to docs/WORKFLOW_COMMANDS.md
- Remove the inline Contributing guide; link to CONTRIBUTING.md
- Fix the duplicate "Option 2" numbering immediately (this is a bug regardless of restructuring)
- Consider moving Tech Stack Coverage to SKILLS_GUIDE.md where it provides navigational context

---

### 2. SKILLS_GUIDE.md

**Purpose:** Quick reference for which skill to use when.

**Strengths:**
- Clear, scannable structure with consistent formatting throughout
- Decision trees are genuinely useful -- they answer the question "I have X problem, which skill do I use?"
- Skill Combinations section provides practical multi-skill workflow patterns
- Examples section with "Good Prompts" gives concrete, actionable guidance
- No unnecessary preamble; gets straight to content
- The flattest, most reference-like document in the set -- appropriate for its purpose

**Weaknesses:**

1. **No introduction or context.** The document opens with `## When to Use Each Skill` with no preamble explaining what this document is, who it is for, or how it relates to the rest of the project. A single paragraph at the top would help.

2. **Category counts diverge from README.** The README lists 12 categories; SKILLS_GUIDE.md lists 12 categories but with different groupings. For example, README has "Workflow (2): Debugging Wizard, Fullstack Guardian" as a category, while SKILLS_GUIDE.md has the same skills under a "Workflow" heading. This is consistent, but the README's parenthetical counts (e.g., "Languages (12)") are not replicated here, making cross-reference verification manual.

3. **Examples section is excessively long.** Lines 257-322 contain 50+ example prompts across 7 subsections. This is valuable content, but the sheer volume makes it hard to scan. The most common use cases (top 10) should be separated from the exhaustive list.

4. **No link back to README or installation.** A reader who lands here directly (via search, deep link, or LLM referral) has no way to learn how to install the plugin. A single line at the top with a link to the README or QUICKSTART.md would solve this.

5. **"Tips for Effective Use" is generic.** The 5 tips at line 249-255 are so general ("Be Specific," "Context Matters") that they add little value. They duplicate the more concrete best practices in QUICKSTART.md.

6. **Missing: which skills are new or recently updated.** For returning users, a "What's New" callout at the top referencing the latest release would help.

**Recommendations:**
- Add a 2-3 line introduction with a link to README.md and QUICKSTART.md
- Trim the Examples section: keep the top 16 "Good Prompts" and move the framework-specific, language-specific, and platform-specific examples into a collapsible section or separate file
- Remove or merge "Tips for Effective Use" into QUICKSTART.md where it belongs
- Consider adding a "Last updated: vX.Y.Z" line at the top so readers know if content is current

---

### 3. QUICKSTART.md

**Purpose:** Get a new user from zero to working installation in minutes.

**Strengths:**
- Starts with installation immediately -- no preamble
- Three installation methods presented concisely
- "Test Your Installation" section is a strong inclusion -- gives the user a way to verify success
- "Quick Reference Card" at the bottom is a genuinely useful cheat sheet
- Reasonable length (208 lines)

**Weaknesses:**

1. **Installation instructions diverge from README.** QUICKSTART.md offers three methods: Marketplace, Install from GitHub (`claude plugin install https://...`), and Local Development (`cp -r`). README.md offers four methods: Marketplace, npx add-skill, Local Development, and Direct Installation. The "Install from GitHub" method in QUICKSTART.md (`claude plugin install https://...`) does not appear in the README at all. The npx method in the README does not appear in QUICKSTART.md. This is confusing and suggests neither document is the source of truth.

2. **Skill counts may go stale.** Lines 50-54 contain hardcoded counts ("12 Language Experts," "10 Backend Framework Experts," "7 Frontend & Mobile Experts"). These are not wrapped in `<!-- SKILL_COUNT -->` markers and will not be updated by `scripts/update-docs.py`. The "10 Backend Framework Experts" claim conflicts with the README, which lists 7 in the "Backend Frameworks" category.

3. **"First Steps" section mixes audiences.** Subsections 1-4 cover what the plugin contains (reference), common use cases (tutorial), best practices (guidance), and skill activation examples (reference). This interleaving makes it hard to follow a linear getting-started path.

4. **"Follow Recommended Workflows" duplicates SKILLS_GUIDE.md.** The 7-step new feature workflow at lines 127-134 is identical to the "New Feature Development" workflow in SKILLS_GUIDE.md lines 96-104. One should link to the other.

5. **References section at line 136-139 is incomplete.** It lists README.md, SKILLS_GUIDE.md, and CONTRIBUTING.md, but omits docs/COMMON_GROUND.md and docs/WORKFLOW_COMMANDS.md.

6. **Troubleshooting is thin.** Only two scenarios are covered (skills not activating, need help). Common issues like "I installed but Claude does not seem to use the skills" or "how do I update to the latest version" are not addressed.

7. **Closing tone is informal.** "Happy coding!" with a rocket emoji is not consistent with the professional tone of the rest of the documentation set.

**Recommendations:**
- Consolidate installation instructions with the README. One document should be the canonical source; the other should link to it. Recommendation: QUICKSTART.md owns the detailed install instructions; README.md has a one-liner and a link.
- Fix the stale "10 Backend Framework Experts" count (should be 7 per README categories, or 8 if counting Express separately)
- Restructure "First Steps" into a linear flow: Install -> Verify -> Try your first prompt -> Learn more
- Remove the duplicated workflow; link to SKILLS_GUIDE.md
- Expand the Troubleshooting section with 2-3 more common scenarios
- Add "How to update" instructions
- Remove the closing emoji; end with the Support section

---

### 4. CONTRIBUTING.md

**Purpose:** Guide contributors through the process of adding or modifying skills.

**Strengths:**
- Clear step-by-step contribution workflow (fork, branch, change, test, commit, PR)
- Commit message format is well-defined
- Progressive Disclosure Pattern section is thorough and well-explained
- Token Efficiency Guidelines are specific and actionable
- Code Examples Best Practices section sets a clear standard
- Framework Version Requirements table pins versions -- good for consistency

**Weaknesses:**

1. **Frontmatter schema conflicts with CLAUDE.md.** CONTRIBUTING.md line 88 shows `name: Skill Name` (with a space), but CLAUDE.md explicitly states: "name: Letters, numbers, and hyphens only (no parentheses or special characters)." The description formula on line 103 (`[Role] for [Domain]. Invoke for [triggers]. Keywords: [terms].`) conflicts with CLAUDE.md's mandate: "descriptions must be TRIGGER-ONLY" and "Format: `Use when [specific triggering conditions]`." These are not minor style differences; they will produce skills that fail validation.

2. **Missing validation step.** The contribution workflow (steps 1-6) does not mention running `python scripts/validate-skills.py` before submitting a PR. Given that CI runs this check, contributors will hit failures they could have caught locally. This should be step 4.5.

3. **Reference file guidance is vague.** The README says "200-400 lines each" for references. CLAUDE.md says "100-600 lines per reference file." CONTRIBUTING.md's Progressive Disclosure section says "200 lines" as a threshold for when to split, but does not state a target range. Three different documents give three different numbers.

4. **Testing instructions are impractical.** Step 4 says to `cp -r skills/* ~/.claude/skills/` and restart Claude Code. For marketplace-installed plugins, this method may not work or may conflict with the installed version. No guidance is given for testing with the marketplace/local plugin workflow.

5. **No mention of the `commands/` directory.** The guide covers skill creation in detail but says nothing about creating or modifying workflow commands. A contributor looking to add a command has no guidance.

6. **Code of Conduct is minimal.** Three short subsections (Be Respectful, Be Collaborative, Be Professional) with two bullet points each. This is fine for a small project but may need expansion as community grows. Consider linking to a standard CoC (e.g., Contributor Covenant) instead of maintaining a custom one.

7. **"Recognition" section references a CONTRIBUTORS.md file.** This file does not appear in the project structure shown in README.md. If it exists, it should be linked. If it does not exist, this is a broken promise.

**Recommendations:**
- Align the frontmatter schema with CLAUDE.md immediately. The description formula must say "Use when [triggering conditions]," not the `[Role] for [Domain]` pattern. The name field must show a hyphenated example.
- Add `python scripts/validate-skills.py --skill my-new-skill` as an explicit step before submitting a PR
- Standardize reference file line guidance across all documents (CLAUDE.md's 100-600 range is the most permissive; pick one range and use it everywhere)
- Add a section on contributing workflow commands
- Link or create the CONTRIBUTORS.md file
- Add a note about testing with the marketplace install method

---

## Cross-File Redundancy Map

The following content appears in multiple documents. For each topic, one document should be the **single source of truth (SSoT)**; all others should link to it.

| Topic | README | QUICKSTART | SKILLS_GUIDE | CONTRIBUTING | Recommended SSoT |
|-------|--------|------------|--------------|--------------|-------------------|
| Installation methods | 4 methods (lines 306-347) | 3 methods (lines 8-27) | -- | 1 method (line 51) | QUICKSTART.md |
| Skill category list | Lines 120-132 | Lines 50-55 | Lines 5-93 | -- | SKILLS_GUIDE.md |
| New feature workflow | Lines 167-169 | Lines 127-134 | Lines 96-104 | -- | SKILLS_GUIDE.md |
| Bug fixing workflow | Lines 172-174 | -- | Lines 107-111 | -- | SKILLS_GUIDE.md |
| Context Engineering overview | Lines 182-227 | -- | -- | -- | docs/COMMON_GROUND.md |
| Workflow Commands table | Lines 233-238 | -- | -- | -- | docs/WORKFLOW_COMMANDS.md |
| Skill activation examples | Lines 139-161 | Lines 99-108 | Lines 259-322 | -- | SKILLS_GUIDE.md |
| Best practices / tips | Lines 136-161 | Lines 85-95, 110-134 | Lines 249-255 | -- | QUICKSTART.md |
| Progressive disclosure explanation | Lines 46-73 | -- | -- | Lines 172-226 | CONTRIBUTING.md |
| Contributing quick guide | Lines 362-401 | -- | -- | Full document | CONTRIBUTING.md |
| Frontmatter schema | Lines 373-387 | -- | -- | Lines 84-98 | CONTRIBUTING.md |
| Tech stack coverage | Lines 244-297 | Lines 176-198 (condensed) | Implicit in categories | -- | SKILLS_GUIDE.md (integrated into categories) |
| Support links | Lines 413-415 | Lines 200-205 | -- | Lines 296-298 | README.md |
| Project structure tree | Lines 74-108 | -- | -- | Lines 177-184 (partial) | README.md |

**Key finding:** 14 topics are duplicated across 2 or more files. Installation instructions appear in 3 files with different content in each. The skill activation examples appear in 3 files with varying levels of detail.

---

## Proposed Restructuring for a Docs Site

This mapping assumes the docs site structure proposed in `docs/ideas/documentation-site.md` and assigns each piece of current content to its future home.

### README.md (Thin Landing Page)

Retain only:
- Hero banner and badges
- 3-sentence project description
- Single install command with link to full QUICKSTART.md
- Link hub: Quick Start, Skills Guide, Common Ground, Workflow Commands, Contributing
- License, Support, Author
- Star history / social proof

Everything else moves to dedicated pages.

### /getting-started/ (from QUICKSTART.md)

- All installation methods (single source of truth)
- Verification steps
- First prompt walkthrough
- Troubleshooting
- How to update

### /skills/ (from SKILLS_GUIDE.md)

- Skill index (filterable)
- Decision trees
- Skill combinations
- Example prompts (condensed)
- Tech stack coverage (integrated into skill cards)

### /architecture/ (from README.md sections)

- Progressive disclosure pattern explanation
- Project structure tree
- How skills activate (context-aware activation)

### /workflows/ (from docs/WORKFLOW_COMMANDS.md)

- Phase overview with DAG diagram
- Command reference table
- Per-command detail pages

### /common-ground/ (from docs/COMMON_GROUND.md)

- Existing content, mostly unchanged
- Remove background/origin story from main flow; move to a "Design Philosophy" subpage

### /contributing/ (from CONTRIBUTING.md)

- Fork/branch/test/PR workflow
- Skill writing guidelines (single source of truth for frontmatter schema)
- Reference file standards
- Validation and testing
- Add: command writing guidelines

---

## Priority Ranking of Improvements

### Critical (Fix Now)

1. **Fix duplicate "Option 2" numbering in README.md Installation Options.** This is a visible bug.

2. **Align CONTRIBUTING.md frontmatter schema with CLAUDE.md.** The description formula and name format directly conflict with the project's own CLAUDE.md. Contributors following CONTRIBUTING.md will produce skills that fail validation. Change the description formula to `Use when [triggering conditions]` and the name example to `my-skill-name` (hyphenated).

3. **Fix stale count "10 Backend Framework Experts" in QUICKSTART.md.** This contradicts the README (which says 7). Either wrap these counts in update markers or replace with a general statement.

### High Priority (Next Release)

4. **Consolidate installation instructions.** Designate QUICKSTART.md as the single source of truth. README.md gets a one-liner and a link. CONTRIBUTING.md links to QUICKSTART.md for testing setup. Remove the `claude plugin install https://...` method from QUICKSTART.md if it is not a supported path, or add it to the README if it is.

5. **Remove duplicated sections from README.md.** Replace inline Context Engineering, Workflow Commands, Skills Overview, and Contributing sections with 2-line summaries and links. Target: README under 200 lines.

6. **Add `validate-skills.py` step to CONTRIBUTING.md.** Insert between "Test Your Changes" and "Commit Your Changes."

7. **Standardize reference file line guidance.** Pick one range (recommend 100-600 from CLAUDE.md) and use it in README.md, CONTRIBUTING.md, and CLAUDE.md consistently.

### Medium Priority (Docs Site Prep)

8. **Add introduction and navigation links to SKILLS_GUIDE.md.** A 3-line preamble with links to README and QUICKSTART.

9. **Trim SKILLS_GUIDE.md examples section.** Keep top 16 general examples; move framework-specific and platform-specific examples to a separate section or file.

10. **Expand QUICKSTART.md troubleshooting.** Add "how to update," "skills conflict with local files," and "which installation method should I choose."

11. **Add workflow command contribution guidance to CONTRIBUTING.md.**

12. **Restructure QUICKSTART.md "First Steps" into a linear tutorial flow.**

### Nice-to-Have (Future)

13. **Add "Last updated" or version reference to SKILLS_GUIDE.md and QUICKSTART.md.**

14. **Create or link CONTRIBUTORS.md** referenced in CONTRIBUTING.md Recognition section.

15. **Replace minimal Code of Conduct with Contributor Covenant link.**

16. **Move Tech Stack Coverage from README to SKILLS_GUIDE.md** where it provides navigational context next to the decision trees.

17. **Remove "Tips for Effective Use" from SKILLS_GUIDE.md** (merge into QUICKSTART.md best practices).

18. **Standardize tone across all documents.** QUICKSTART.md ends with "Happy coding!" and uses emoji bullets in the Support section. Other documents maintain a more neutral professional tone. Pick one voice and apply it everywhere.

---

## SEO Readiness Assessment

| Criterion | README | QUICKSTART | SKILLS_GUIDE | CONTRIBUTING |
|-----------|--------|------------|--------------|--------------|
| Descriptive H1 | No (image banner, no text H1) | Yes | Yes | Yes |
| Unique page title potential | Yes ("Claude Skills") | Yes ("Quick Start Guide") | Yes ("Skills Quick Reference") | Yes ("Contributing") |
| Scannable headings | Mixed (some headings are vague: "Architecture," "Usage Patterns") | Yes | Yes | Yes |
| Keyword density | High (tech stack list) | Medium | High (skill names, frameworks) | Low (process-focused) |
| Internal linking | Good (links to all major docs) | Weak (3 links) | None | Weak (1 link) |
| External linking | Good (GitHub, LinkedIn) | Weak (1 GitHub link) | None | Weak (1 GitHub link) |
| Meta description potential | Implicit in first paragraph | Implicit | Missing (no intro paragraph) | Implicit |
| Standalone readability | No (assumes GitHub context) | Mostly yes | No (no intro, no install link) | Yes |

**Key SEO gaps:**
- SKILLS_GUIDE.md has zero internal or external links. On a docs site, it would be an isolated page with no link equity flow.
- README.md has no text-based H1. The project name is embedded in an image. Search engines may not extract it.
- None of the documents have a meta-description-ready opening sentence that summarizes the page in under 160 characters.

---

## Relationship to docs/ideas/documentation-site.md

This audit directly satisfies **Phase 1** of the documentation site plan. The findings here feed into Phase 2 (Content Restructuring). Specifically:

- The redundancy map above identifies exactly which content to deduplicate before building the site
- The proposed restructuring section provides a content-to-URL mapping for the Astro site structure
- The priority ranking ensures the most impactful fixes happen before the site build, reducing rework
- The SEO readiness assessment identifies gaps that the docs site should address with proper meta tags, H1 elements, and internal linking

**Recommended next step:** Execute Critical and High Priority items (1-7) in the current repo before beginning Phase 4 (Astro setup). These fixes improve the current GitHub-based experience and reduce content migration work.
