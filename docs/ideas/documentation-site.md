# Documentation Site

Proposal for a standalone documentation site for the claude-skills project.

---

## Motivation

### The Problem

All project content currently lives on `github.com/jeffallan/claude-skills`. This means:

- **No Google Search Console access** — can't see which queries drive traffic, can't submit sitemaps, can't control indexing
- **No control over meta tags** — page titles, OpenGraph, structured data are all GitHub's defaults
- **One giant README** — 65 skills, 9 workflows, 356 reference files collapsed into a single page
- **No individual skill URLs** — a skill can't be linked to, shared, or indexed independently

### The Opportunity

Current traffic data (2-week snapshot, Jan 2026) shows strong organic discovery already happening without any SEO effort:

| Source | Views | Unique Visitors |
|--------|-------|-----------------|
| Google | 5,532 | 1,026 |
| github.com | 2,646 | 516 |
| t.co (Twitter/X) | 570 | 208 |
| statics.teams.cdn.office.net (MS Teams) | 170 | 37 |
| chatgpt.com | 100 | 22 |
| claude.ai | 58 | 12 |
| com.reddit.frontpage | 49 | 12 |
| bytedance.larkoffice.com (ByteDance internal) | 33 | 6 |

Additional metrics: 197 stars, 9.5k downloads (skills.sh), 4,560 unique cloners, 4,008 unique visitors in 2 weeks.

Key signals:
- **Enterprise adoption** — traffic from Microsoft Teams and ByteDance's internal Lark platform indicates workplace sharing
- **AI platform discovery** — ChatGPT and Claude.ai are referring users organically
- **Google dominance** — 1,026 unique visitors from search with zero SEO optimization suggests significant upside once proper pages exist

### The Insight: Skill Linking = Internal Link Graph

Issue #69 (Skill Metadata Enhancement) plans to formalize the existing static `## Related Skills` sections into typed `metadata.*` relationships (complementary, prerequisite, alternative). This metadata serves two consumers simultaneously:

1. **Agent runtime** — Claude follows structured links to load related skills contextually
2. **Documentation site** — The same relationships become real `<a href>` links between skill pages, creating a dense internal link graph

This is exactly what both classic SEO and LLM retrieval reward:
- Google uses internal link structure to understand page relationships and distribute authority
- LLMs doing retrieval follow link structure to build richer context about what the project offers

**One schema, two consumers.** Relationship data written once in YAML generates both runtime cross-references and HTML internal links.

Issue #100 (Cross-Reference Validation) also becomes dual-purpose — it validates both agent behavior and docs site link integrity.

---

## Hard Requirement: Dual-Format Serving (HTML + Markdown)

The site MUST serve every content page in two formats from the same URL:

- **HTML** — for human consumption (styled, navigable, searchable)
- **Markdown** — for agent consumption (clean, context-efficient, directly loadable)

Format selection via content negotiation (`Accept: text/markdown`) or URL convention (e.g., `/skills/react-expert.md` or `?format=md`).

### Why This Matters

The docs site isn't just for humans. Agents are a first-class consumer. When an agent needs to understand what `react-expert` does, it should be able to fetch the markdown directly from the docs site URL — not scrape HTML and hope the conversion is clean.

This turns the entire docs site into an **agent-consumable API**:

- `llms.txt` becomes a routing file pointing agents to markdown endpoints for every skill and command
- An agent can fetch `/skills/react-expert.md` and get the same content that generates the HTML page — no lossy HTML-to-markdown conversion
- The skill's reference files are available at `/skills/react-expert/server-components.md` — agents can selectively load exactly what they need
- Workflow commands with typed inputs/outputs are available as structured markdown at `/commands/discovery/create.md`

### Implementation Approaches

**Option A: Static .md file co-generation**
- During build, output both `index.html` and `index.md` for every page
- Simple, no runtime logic, works with any CDN/static host
- URL convention: `/skills/react-expert/` (HTML) vs `/skills/react-expert/index.md` (markdown)

**Option B: Content negotiation middleware**
- Server checks `Accept` header and returns appropriate format
- Cleaner URLs but requires a server or edge function (not pure static)

**Option C: Query parameter**
- `/skills/react-expert/?format=md` returns markdown
- Works with edge functions on static hosts (Cloudflare Pages, Vercel)

**Recommendation:** Option A (static co-generation) as the baseline — it works everywhere, requires no runtime, and the `.md` files are just the source markdown the site was built from. Options B or C can be layered on later if cleaner URLs are desired.

### Impact on Site Generator Selection

This requirement narrows the field. The generator must support outputting both HTML and raw markdown for each content page. This is a build-step concern, not a runtime concern — the generator (or a post-build script) writes both formats to the output directory.

### Impact on llms.txt

With dual-format serving, `llms.txt` evolves from a static summary into a structured index with direct markdown URLs:

```
# Claude Skills
> 65 specialized skills for full-stack developers

## Skills

- [React Expert](/skills/react-expert/index.md): React 18+ with Server Components, hooks, state management
- [NestJS Expert](/skills/nestjs-expert/index.md): NestJS modules, controllers, services, TypeORM/Prisma
- [Python Pro](/skills/python-pro/index.md): Python 3.11+ with type safety, async, pytest
...

## Workflows

- [Discovery Phase](/workflows/discovery/index.md): Research, synthesize, and approve requirements
- [Planning Phase](/workflows/planning/index.md): Analyze codebase and create execution plans
...
```

Every line is a fetchable markdown URL. An agent reading `llms.txt` can navigate the entire project without touching HTML.

---

## Architecture: The Autodoc Analogy

The project already has the equivalent of Python's autodoc infrastructure:

| Python autodoc | Claude Skills equivalent |
|---|---|
| Package | Phase (intake, discovery, planning, execution, retrospective) |
| Module | Skill or Command |
| Docstring | `SKILL.md` body / command description `.md` |
| Type annotations | YAML `inputs`/`outputs` with typed fields |
| `__init__.py` exports | `workflow-manifest.yaml` |
| Cross-references | `metadata.*` relationships, `external_skills`, `depends_on` |
| Module index page | Skills overview / workflow DAG visualization |
| Sub-module docs | Reference files under each skill |

A static site generator consumes the existing YAML definitions and markdown files directly — minimal glue code, not a rewrite.

### Content Sources (Already Exist)

| Source | Generates |
|--------|-----------|
| `skills/*/SKILL.md` frontmatter | Skill index page, per-skill metadata cards |
| `skills/*/SKILL.md` body | Individual skill pages |
| `skills/*/references/*.md` | Sub-pages under each skill |
| `commands/*/*.yaml` | Command reference pages with typed inputs/outputs |
| `commands/workflow-manifest.yaml` | DAG visualization, phase overview pages |
| `docs/workflow/*.md` | Phase and command description pages |
| `SKILLS_GUIDE.md` | Category navigation, decision trees |
| `README.md` | Landing page (simplified) |
| `CHANGELOG.md` | Release history page |

### Content to Create

| Content | Purpose |
|---------|---------|
| `llms.txt` | Structured project summary for LLM discoverability |
| Landing page | Simplified hero + quick start (not the full README) |
| Search / filter UI | Filter skills by category, language, framework |
| Sitemap | Auto-generated from skill/command pages |
| OpenGraph meta tags | Per-skill social previews for link sharing |

---

## Proposed Site Structure

```
/                                   ← Landing page (hero, quick start, stats)
/skills/                            ← Skill index (filterable by category)
/skills/react-expert/               ← Generated from SKILL.md
/skills/react-expert/server-components/  ← Generated from references/
/skills/react-expert/performance/        ← Generated from references/
/commands/                          ← Command index
/commands/common-ground/            ← Generated from command YAML + description .md
/workflows/                         ← DAG visualization of all phases
/workflows/discovery/               ← Phase overview (from docs/workflow/discovery-phase.md)
/workflows/discovery/create/        ← Command detail (from YAML + description .md)
/guide/                             ← Skills guide (from SKILLS_GUIDE.md)
/guide/decision-trees/              ← When to use which skill
/changelog/                         ← Release history
/llms.txt                           ← LLM-consumable project summary
```

Each skill page would include:
- Frontmatter metadata rendered as structured sidebar (role, scope, triggers)
- Skill body (workflow, constraints, output templates)
- Related Skills as internal links (from `metadata.*` once #69 lands; from static sections until then)
- Reference files as sub-navigation
- "Install this skill" code snippet

Each command page would include:
- Inputs table (from YAML `inputs` with types)
- Outputs table (from YAML `outputs` with types)
- Requirements badges (ticketing, documentation)
- Phase context (where it sits in the DAG)
- Upstream/downstream commands

---

## AI Discoverability: llms.txt

Add an `llms.txt` file to both the repo root and the docs site root. Content auto-generated from:

- Skill names, descriptions, and triggers (from SKILL.md frontmatter)
- Workflow phases and command summaries (from workflow-manifest.yaml)
- Project stats (skill count, reference count, framework coverage)
- Installation instructions

This gives LLM retrieval systems (Perplexity, ChatGPT browsing, Claude.ai web search) a structured index without requiring them to parse the full site.

---

## Plan: Documentation Review and Restructure

### Phase 1: Audit Current Documentation

Use a technical writing agent to:

1. **Inventory all existing docs** — README, SKILLS_GUIDE, CONTRIBUTING, docs/*.md, workflow docs, skill SKILL.md files
2. **Identify redundancy** — content duplicated across README, SKILLS_GUIDE, and individual docs
3. **Identify gaps** — missing docs, outdated sections, broken cross-references
4. **Assess voice consistency** — do all docs follow the same tone, structure, terminology?
5. **Map content to site structure** — which existing doc maps to which site page?

### Phase 2: Content Restructuring

1. **Separate concerns** — README becomes a short landing page pointing to the docs site; detailed content moves to docs
2. **Deduplicate** — single source of truth for each topic; other locations link to it
3. **Standardize structure** — every skill page follows the same template; every command page follows the same template
4. **Write missing content** — landing page copy, category descriptions, getting started guide
5. **Refresh stale content** — update any sections referencing old versions or outdated patterns

### Phase 3: Site Generator Selection and Setup

Evaluate based on:
- **[HARD] Dual-format output** — Can it output both HTML and raw markdown for every page?
- Can it consume YAML frontmatter and generate pages programmatically?
- Does it support auto-generation from structured data (like the command YAML files)?
- Does it handle markdown with embedded code blocks well?
- Does it support sitemap generation, meta tags, OpenGraph?
- Can it deploy to GitHub Pages?

Candidates:
- **MkDocs + Material theme** — Python ecosystem, strong autodoc mindset, YAML-native config, good search. Dual-format: would need a plugin or post-build script to copy source .md files to output.
- **Astro + Starlight** — Modern, content-collection-based, supports YAML/MDX, fast builds. Dual-format: Astro's build pipeline can output multiple formats per route via custom endpoints.
- **Docusaurus** — React-based, good for versioned docs, plugin ecosystem. Dual-format: would need a custom plugin to emit .md alongside HTML.
- **VitePress** — Vue-based, fast, good defaults for technical docs. Dual-format: would need a post-build step.

Note: Since the source content is already markdown, the simplest dual-format approach for any generator is a post-build script that copies the source `.md` files into the output directory mirroring the HTML route structure. This is generator-agnostic and avoids lock-in.

### Phase 4: Build and Deploy

1. Set up the selected generator with the proposed site structure
2. Write generator plugins/scripts to consume YAML definitions and produce pages
3. Deploy to GitHub Pages with custom domain
4. Submit sitemap to Google Search Console
5. Add `llms.txt` to site root
6. Add sponsor badges to site and repo README
7. Set up GitHub Actions for auto-deploy on push to main

### Phase 5: Ongoing Maintenance

- CI check: validate that every skill/command has a corresponding docs page
- CI check: validate internal links (extends #100 cross-reference validation)
- Auto-regenerate `llms.txt` on release
- Auto-regenerate sitemap on content changes

---

## Relationship to Existing Issues

| Issue | Relationship |
|-------|-------------|
| #69 — Skill Metadata Enhancement | Prerequisite for structured internal linking; can proceed with static `## Related Skills` sections initially |
| #100 — Cross-Reference Validation | Extends to docs site link validation |
| #65 — Cross-Domain Recommendations | Content improvements that directly improve docs site quality |
| #66 — Enhanced Routing Logic | Better descriptions/triggers = better page titles and meta descriptions |
| #68 — Skill Dependency Mapping | Visual DAG representation becomes a docs site page |

---

## Open Questions

1. **Custom domain?** — `docs.claudeskills.dev`, `skills.jeffallan.dev`, or subdirectory of existing site?
2. **Versioned docs?** — Do we need docs for multiple versions, or just latest?
3. **Search** — Built-in site search vs. Algolia DocSearch (free for open source)?
4. **When to start?** — Can begin Phase 1 (audit) independently of #69 metadata work
