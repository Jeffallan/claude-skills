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

### Phase 3: Complete #69 — Skill Metadata Enhancement (BLOCKING)

**This phase must complete before site generator setup.** The Astro content collection schemas depend on the finalized metadata structure. Building the site before #69 means defining the schema twice — once provisionally, then again when the metadata spec lands.

#69 determines:
- What fields exist in SKILL.md frontmatter vs. the `metadata.*` key
- How relationship types are structured (complementary, prerequisite, alternative)
- Whether domain tags, compatibility info, or other new metadata lives under `metadata.*`
- The finalized schema that both the agent runtime AND the docs site consume

The content collection schema, the internal link graph, the per-page meta tags, and the `llms.txt` index all derive from whatever #69 produces. Get the data model right first.

**What CAN proceed in parallel with #69:**
- Phase 1 (audit) and Phase 2 (content restructuring) — these are about the docs content, not the schema
- Evaluating Astro + Starlight with a proof-of-concept using current frontmatter fields
- Setting up the repo structure for the docs site (Astro project scaffolding)

### Phase 4: Site Generator Setup — Astro + Starlight

#### Decision: Astro + Starlight

After evaluating Docusaurus, Hugo, MkDocs Material, and VitePress against the hard requirements (dual-format output, auto-generation from YAML/markdown, SEO), **Astro + Starlight** is the recommended choice.

**Why Astro wins for this project:**

| Requirement | How Astro Handles It |
|---|---|
| **Dual-format (HTML+MD)** | Custom endpoints serve raw markdown at `/skills/react-expert/index.md` alongside HTML at `/skills/react-expert/`. Supported pattern, not a hack. |
| **Auto-gen from YAML/SKILL.md** | Content collections: define a schema matching SKILL.md frontmatter, point at `skills/*/SKILL.md`, pages are auto-generated with typed data. Command YAML files become a second collection. |
| **SEO out of the box** | 100/100 Lighthouse scores. Auto sitemap, meta tags, OpenGraph. Starlight adds search, navigation, TOC. |
| **Zero JS shipped** | Pure static HTML by default. No SPA hydration overhead. Instant loads for developers hitting docs from Google or LLM referrals. |
| **Social cards** | Existing `scripts/capture-screenshot.js` can be adapted for per-page OG images. |

**Why not the others:**

- **Docusaurus** — Best SEO defaults, but ships a React SPA (unnecessary JS weight) and has no native content collection concept. Dual-format requires a custom plugin.
- **Hugo** — Only SSG with first-class dual-format output (custom output formats). But Go templating for auto-generation from structured YAML is more manual wiring than Astro content collections. Strong fallback if Astro proves problematic.
- **MkDocs Material** — Unique auto social card generation, but weakest on dual-format and programmatic page generation. Too opinionated about directory structure.
- **VitePress** — Fast and clean, but less mature plugin ecosystem and no content collections.

**Ecosystem fit:** The project targets TypeScript/JavaScript developers. Astro uses TypeScript natively. Existing Python scripts (`validate-skills.py`, `update-docs.py`) remain as CI validation — the site generator doesn't replace them.

#### How Content Collections Map to This Project

```
// Astro content collection schema (conceptual)
// IMPORTANT: Final schema depends on #69 metadata enhancement

skills collection:
  source: skills/*/SKILL.md
  schema:
    name: string          ← from frontmatter
    description: string   ← from frontmatter (max 1024 chars)
    triggers: string[]    ← from frontmatter
    role: enum            ← specialist | expert | architect
    scope: enum           ← implementation | review | design | ...
    output-format: enum   ← code | document | report | ...
    metadata:             ← from #69, structure TBD
      related: object[]   ← typed relationships (complementary, prerequisite, etc.)
      domain: string[]    ← domain tags
      ...

commands collection:
  source: commands/**/*.yaml
  schema:
    command: string       ← phase:action identifier
    phase: string         ← intake | discovery | planning | ...
    inputs: object[]      ← typed input definitions
    outputs: object[]     ← typed output definitions
    requires: string[]    ← ticketing | documentation
    status: enum          ← existing | planned | deprecated

workflows collection:
  source: commands/workflow-manifest.yaml
  schema:
    phases: object        ← DAG definition with depends_on edges
    utilities: object[]   ← on-demand commands
```

### Phase 5: Build and Deploy

1. Define Astro content collection schemas from finalized #69 metadata spec
2. Build page templates for skills, commands, workflows
3. Implement dual-format endpoints (HTML + markdown per page)
4. Generate `llms.txt` from content collections at build time
5. Deploy to GitHub Pages with custom domain
6. Submit sitemap to Google Search Console
7. Add sponsor badges to site and repo README
8. Set up GitHub Actions for auto-deploy on push to main

### Phase 6: Ongoing Maintenance

- CI check: validate that every skill/command has a corresponding docs page
- CI check: validate internal links (extends #100 cross-reference validation)
- Auto-regenerate `llms.txt` on release
- Auto-regenerate sitemap on content changes
- Content collection schema validation catches broken frontmatter at build time

---

## Dependency Chain

```
#69 Skill Metadata Enhancement
 ├── Docs site content collection schemas (can't finalize without #69)
 ├── #65 Cross-Domain Recommendations (content work, depends on #69)
 ├── #66 Enhanced Routing Logic (better descriptions = better page titles)
 └── Internal link graph (relationship metadata → <a href> links)

#100 Cross-Reference Validation
 └── Docs site link validation (same check, dual purpose)

#68 Skill Dependency Mapping
 └── DAG visualization page on docs site

Phase 1 (Audit) ──────────────────── can start NOW
Phase 2 (Content restructuring) ──── can start NOW
Phase 3 (#69 metadata) ──────────── BLOCKING for site schema
Phase 4 (Astro setup) ───────────── after #69
Phase 5 (Build and deploy) ──────── after Phase 4
Phase 6 (Maintenance) ───────────── ongoing after Phase 5
```

---

## Open Questions

1. **Custom domain?** — `docs.claudeskills.dev`, `skills.jeffallan.dev`, or subdirectory of existing site?
2. **Versioned docs?** — Do we need docs for multiple versions, or just latest?
3. **Search** — Starlight built-in search vs. Algolia DocSearch (free for open source)?
4. **Docs site repo** — Same repo (monorepo with `/site` directory) or separate repo?
