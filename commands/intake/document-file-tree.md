---
name: document-file-tree
description: Generate an annotated repository map (directory tree with per-path roles, the framework's routing/structure conventions, and a "where new code goes" table) by reverse-engineering the project's layout.
argument-hint: "[directory]"
---

# intake:document-file-tree

**Argument:** `$ARGUMENTS`: optional root directory to analyze (defaults to the project root).

Produce a file-tree reference at `docs/architecture/file-tree.md` (configurable): an annotated map of where each
kind of code lives, how the framework turns the layout into routes or modules, and where to add new code. Written
for an AI agent or engineer to navigate the repository without re-deriving its structure. **Annotate only what the
layout and code prove. Never invent a directory, convention, or routing rule the project does not use.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when the directory layout, framework, or routing
conventions change (a rerun edits the existing document in place and keeps hand edits; see "Reruns" in `references/intake/rules.md`).

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the layout; infer each path's role and the framework's conventions from code.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **The project's framework / structure skill**, chosen by stack, for the routing and layout conventions, e.g.
  `fullstack-dev-skills:react-native-expert`, `fullstack-dev-skills:nextjs-developer`, `fullstack-dev-skills:react-expert`, `fullstack-dev-skills:vue-expert` for file-based or component-based
  front ends; `fullstack-dev-skills:django-expert`, `fullstack-dev-skills:rails-expert`, `fullstack-dev-skills:spring-boot-engineer`, `fullstack-dev-skills:nestjs-expert` for convention-based
  back ends.

## Workflow

### Phase 1: Discover the layout
Walk the directory tree from the analysis root. Identify, in priority order:
1. The build system and framework (manifest/lockfile, framework config, declared entry point).
2. The entry point(s) and how the app boots.
3. The directory or mechanism that defines structure: a routes directory for file-based routing
   (e.g. `app/`, `pages/`, `routes/`), or the package/module layout for convention-based frameworks
   (e.g. MVC apps, layered services).
4. Root configuration files and what each controls.

Ignore generated and vendored paths (dependency directories, build output, caches). Note any sub-package with its
own manifest and build (a nested package, a serverless functions package, a workspace member).

### Phase 2: Extract the role of each path
Per significant directory and notable file, write a one-line role: what kind of code it holds and what it is
responsible for. Distinguish first-party code from framework scaffolding or starter-template leftovers. Record
which files are entry points, which are config, and which define cross-cutting infrastructure (initialization,
shared types, constants/lookup data).

### Phase 3: Extract the routing / structure convention
Capture how the framework derives behavior from the layout, using the framework's own vocabulary:
- **File-based routing** (the file path becomes the route): document the mapping rules (index files, route groups,
  dynamic segments, layout/wrapper files, platform or environment extensions) and produce a real route map from the
  actual files.
- **Convention-based structure** (directory or naming maps to a layer/module): document the layer boundaries
  (e.g. models, views/controllers, services, migrations) and how the framework discovers them.
Note where structure is type-checked or validated (generated route types, autoloading, dependency injection).

### Phase 4: Extract "where new code goes"
Per common kind of change, determine the canonical location from the existing layout, plus any rule that
governs it (where a given construct must live, where it must not, import-path conventions, sync requirements with
another file). Build the placement table from observed practice, not from a generic ideal.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the detected stack/framework, the top-level
directories and their roles, the routing/structure model, and the output path. Do not write the document until the
user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 5: Write
Write the document at the output path using the template below.

### Phase 6: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the repository: each path exists and its role is correct, every routing rule resolves
to a real file, the route/module map matches the layout, and each "where new code goes" row reflects actual
practice. Ground any example in a real path or call site. Remove anything not provable from the repository. Prefer
"unknown" over a guess.

## Output template

```markdown
---
command: intake:document-file-tree
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# File Tree

<1-2 sentence overview: the stack/framework and what this map covers.>

**Sources of truth (read these if this doc and the repo disagree):**
- <the directory/mechanism that defines routing or module structure>
- <framework config, manifest/entry point, language/build config>

> <cross-links: data/model shapes, end-to-end flows, and configuration/operations docs, if they exist>

## Annotated directory tree
` ` `
<tree of significant directories and files, each with a one-line role annotation;
 generated/vendored paths omitted>
` ` `

## <Framework> routing / structure convention
<how the framework turns the layout into routes or modules, in its own vocabulary>

| Convention | Meaning | Example in repo |
|---|---|---|

<real route map (file -> route) for file-based routing, OR the layer/module map for convention-based frameworks>

## Where new code goes
| You are adding... | Put it in... | Notes |
|---|---|---|

## Config files
| File | Purpose |
|---|---|

## Gotchas for implementers
<non-obvious layout rules: hidden/aliased routes, duplicated-elsewhere data that must stay in sync,
 separate sub-packages with their own deps, platform/environment file resolution, scaffolding to avoid>
```

## Failure conditions

- **No discernible framework or convention**: describe the raw layout plainly and stop; do not impose a routing
  model the project does not use.
- **Layout and config disagree** (e.g. a declared routes directory that does not match the files, or an entry point
  that points elsewhere): document **both** and flag the discrepancy; do not silently pick one.

## Output

A single document at the output path, plus a short summary: the framework/structure model identified, the number of
top-level areas annotated, and any discrepancies or unknowns surfaced for follow-up.
