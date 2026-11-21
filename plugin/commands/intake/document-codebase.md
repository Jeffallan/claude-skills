---
name: document-codebase
description: Add accurate, agent-readable docstrings and module comments across an existing codebase without changing a single executable line.
argument-hint: "[directory]"
---

# intake:document-codebase

**Argument:** `$ARGUMENTS`: optional root directory to document (defaults to the project root).

Add docstrings and module comments to the code so an agent can learn what a function, class or module does, what it takes, what it returns and how it fails without tracing its implementation. This is the first item of the intake checklist and every other intake command reads its result. **Write for an agent that will implement against the code: accuracy over polish. Change comments and docstrings only; never change an executable line.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set what intake may change, the findings tracker, the checkpoint and the goal-run behavior.

## When to use

Run once at the start of intake, before any `intake:document-*` or `intake:testing-*` command. Rerun on code that changed since: it is idempotent and leaves accurate docstrings alone.

## Skills to load

- **`fullstack-dev-skills:code-documenter`**: docstring formats, coverage counting and the report.
- **`fullstack-dev-skills:spec-miner`**: read what a function really does, including side effects and error paths, before describing it.
- **The language skill, by detection**: `fullstack-dev-skills:python-pro`, `fullstack-dev-skills:typescript-pro`, `fullstack-dev-skills:javascript-pro`, `fullstack-dev-skills:golang-pro`, `fullstack-dev-skills:java-architect`, `fullstack-dev-skills:php-pro`, `fullstack-dev-skills:csharp-developer`, `fullstack-dev-skills:rust-engineer` and so on.
- **The framework skill, by detection**: for example `fullstack-dev-skills:django-expert`, `fullstack-dev-skills:vue-expert-js`, `fullstack-dev-skills:react-expert`, `fullstack-dev-skills:laravel-specialist`, `fullstack-dev-skills:rails-expert`, `fullstack-dev-skills:nestjs-expert`. Framework conventions decide what a view, model, serializer or component docstring should say.

Detect the stack from the package manifests and lockfiles (`package.json`, `pyproject.toml`, `requirements*.txt`, `composer.json`, `go.mod`, `Gemfile`, `*.csproj`), the framework config and the file extensions. A mixed repo (a Python backend with a Vue frontend) gets one language and framework skill per part.

## Workflow

### Phase 1: Baseline
1. Record the start commit: `git rev-parse HEAD`. The diff check in Phase 6 compares against it.
2. Find the project's test command (package scripts, `Makefile`, CI config, the framework's runner) and run it. Save the command, the pass, fail and skip counts and the exit code. A suite that already fails is the baseline, not a blocker; record the failing tests by name.
3. A project with no tests records "no test suite" and leans on the diff check alone.

### Phase 2: Detect conventions
Find the docstring style the code already uses (Google, NumPy or Sphinx for Python; JSDoc or TSDoc; PHPDoc; XML docs; Go doc comments) and keep it. With no existing style, use the language's most common one: Google style for Python, TSDoc for TypeScript, JSDoc for JavaScript, Go doc comments for Go. Never mix styles in one project part.

### Phase 3: Inventory
List every module, class, function, method and endpoint handler without a docstring, and every docstring that the code contradicts. Prioritize:
1. Public APIs and entry points: route handlers, views, controllers, exported functions, CLI commands, jobs.
2. Domain logic: models, services, permission checks, validators, serializers.
3. Shared helpers called from several places.
4. Private helpers, only when their behavior isn't obvious from the name and signature.

Skip generated code, vendored code, migrations, minified bundles, lockfiles and test files.

Framework component files are source code and in scope by default: the `<script>` or `<script setup>` block of every `.vue` and `.svelte` file, and every `.jsx` and `.tsx` component. Document the component itself (what it shows and when, from the parent's view), its props, the events it emits, its computed properties and its methods and handlers, and rank each by the list above. Leave templates and styles alone. Don't leave components to the user-flow or features docs, and don't raise their scope as an Open question.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the detected languages and frameworks, the docstring style per part, the inventory counts by priority, the excluded paths and the baseline test result. Do not write until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write the docstrings
Read each unit's body and its callers before describing it. Each docstring states:
- **What it does**, in one line, from the caller's view.
- **Parameters and return value**, with types where the signature lacks them and the units or allowed values where the code enforces them.
- **Errors**: what it raises or returns on failure, and when.
- **Side effects**: writes to the database, files, caches, queues, network calls, emitted events, signals.
- **Access**: the permission or ownership check it applies, or that it applies none.

Module docstrings say what the module holds and which other modules depend on it. Keep a docstring short when the code is short; never restate the obvious. A docstring is a comment: it must not change the code's behavior, so watch languages where it can (a Python docstring placed as the first statement is fine; one placed after code is a no-op string; a PHP attribute or a Java annotation is code, never a comment).

### Phase 5: Record findings
Documentation always surfaces bugs. When the code contradicts its name, its type, its comment or another part of the code, describe what the code does, add a finding to `docs/intake-findings.md` with the next id and put the id in the docstring: `Note: returns inactive users too (F-007).` Never fix it.

### Phase 6: Prove no executable line changed (required)
1. Rerun the test command from Phase 1. The counts and the exit code must match the baseline; a test that changed state is a stop for this command.
2. Check the diff against the start commit with `git diff <start>` and confirm every changed hunk is a comment or a docstring:
   - **Python**: for each changed file, compare `ast.dump` of the file at the start commit and now, with docstring nodes removed from both. Any difference means code changed.
   - **JavaScript and TypeScript**: compare the files with comments stripped, for example `npx esbuild <file> --loader=ts --minify-whitespace` (or `--loader=js`) at both commits; or confirm every added and removed line of `git diff -U0` sits inside a `//` or `/* */` comment.
   - **Vue and Svelte single-file components**: the `<template>` and `<style>` blocks must be byte-identical at both commits. Extract the `<script>` block from each version and compare it as JavaScript or TypeScript, as above.
   - **Other languages**: confirm every added and removed line of `git diff -U0` is a comment line or inside a doc comment block, using the language's comment syntax.
3. Revert any hunk that touches an executable line, whatever the reason, then rerun the check.

## Output template

The deliverable is the docstrings plus a report:

```markdown
## Docstring pass

**Start commit:** <sha> · **Style:** <style per part> · **Skills:** <skills this session loaded with the Skill tool; any listed skill it didn't load as `<skill> not loaded: <reason>`>

| Part | Modules | Classes | Functions | Before | After |
|------|---------|---------|-----------|--------|-------|
| <backend> | <n> | <n> | <n> | <documented %> | <documented %> |

**Tests before:** `<command>`: <passed> passed, <failed> failed, <skipped> skipped, exit <code>
**Tests after:** `<command>`: <same counts>, exit <code>
**Executable-line check:** <method per language>: no executable change in <n> files
**Findings raised:** F-<id>, F-<id>
**Skipped paths:** <generated, vendored, migrations>
```

## Failure conditions

- **The tests can't run** (missing services, secrets): record why, and rely on the diff check alone. Say so in the report.
- **The tests change after the pass**: revert the offending files to the start commit, rerun, and report which files could not be documented safely.
- **A file can't be parsed for the diff check**: leave it undocumented and list it in the report.

## Output

Docstrings across the code, new findings in `docs/intake-findings.md`, and the report above with the before and after test runs and the executable-line check.
