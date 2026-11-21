---
name: document-glossary
description: Generate an alphabetical glossary of the project's domain and product vocabulary, each term defined and grounded in the code that defines or uses it.
argument-hint: "[directory]"
---

# intake:document-glossary

**Argument:** `$ARGUMENTS`: optional root directory to analyze (defaults to the project root).

Produce a glossary at `docs/domain/glossary.md` (configurable): an alphabetical reference so agents and humans share
one set of definitions for the project's domain and product terms. Many terms are domain-specific and do not mean
what they would in a generic product; capture the project's meaning. **Define only terms the code actually uses, and
ground every entry in the code that defines or uses it. Never invent a term or a meaning the code does not support.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when the domain vocabulary changes (new features,
renamed concepts, new enum values): A rerun edits the existing document in place and keeps hand edits ("Reruns" in `references/intake/rules.md`).

## Skills to load

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the domain language; extract concepts, actions, and enumerations from code.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.

## Workflow

### Phase 1: Discover the vocabulary
Collect candidate terms from where the project names its concepts, in priority order:
1. Domain type/model definitions and their doc comments (entities, value objects, DTOs/view models).
2. Enumerations and their display-label maps (stored code -> human label lookups).
3. Reference catalogs and constants (allow-lists, lookup tables, option sets).
4. Domain operations and their names (service/use-case functions, the verbs of the app).
5. User-facing surfaces (screens, routes, primary UI labels) and the terms they expose.

Prioritize terms that are **domain- or product-specific, overloaded, or non-obvious** to a newcomer. Skip generic
programming vocabulary that carries no project-specific meaning.

### Phase 2: Extract definition and location
Per term, write a precise one-to-three-sentence definition in the project's own meaning, including: what it is,
what it does or gates, and any constraint or nuance that distinguishes it (immutability, allowed values, scope,
who can read/write it). Record a **"where in code"** pointer to the definition and a representative use site. When a
term names a stored value (an enum code), give the stable value and note that display strings come from a label map.

### Phase 3: Resolve overlaps and aliases
Identify terms that are overloaded (one word, multiple meanings), aliased (a UI label differs from the stored field
name), or easily confused (two distinct enums with overlapping value names). Plan to disambiguate these explicitly
rather than collapse them.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the candidate term list, the sources used, and the
output path. Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write the document at the output path: terms sorted alphabetically, one row each, in the template below.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every entry against the code: the definition matches behavior, the constraint is actually enforced, the
allowed values are current, and each "where in code" pointer resolves to a real symbol or file. Remove any term the
code does not use and any meaning it does not support. Prefer "unknown" over a guess.

## Output template

```markdown
---
command: intake:document-glossary
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# Glossary

<1-2 sentence overview: what this glossary covers and why the project's terms can differ from generic usage.>

**Sources of truth (read these if this doc and the code disagree):**
- <domain type/model definitions; enum -> label maps; reference catalogs; key services and screens>

> <cross-links: the data-model doc for shapes/IDs/full enum value lists, and the features/flows doc for how terms
>  compose into user-facing behavior, if they exist>

## Terms

| Term | Definition | Where in code |
|---|---|---|

## Notes for implementers
<overloaded terms and which meaning applies where; distinct-but-similar enums not to conflate;
 stored-code vs display-label rendering conventions; terms that are server-only or write-only>
```

## Failure conditions

- **No domain vocabulary found** (e.g. a pure-infrastructure library with no product concepts): state that plainly
  and stop; do not pad the table with generic programming terms.
- **A term is used with conflicting meanings** across the code: document **each** meaning as its own entry or note,
  and flag the overlap; do not silently merge them.

## Output

A single document at the output path, plus a short summary: number of terms defined, the sources mined, and any
overloaded or ambiguous terms surfaced for follow-up.
