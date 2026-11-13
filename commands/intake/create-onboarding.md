---
name: create-onboarding
description: Generate the onboarding index (docs/README.md, or docs/README-intake.md beside an owner README) tying together the project overview, quickstart, and links to all intake reference docs.
argument-hint: "[directory]"
---

# intake:create-onboarding

**Argument:** `$ARGUMENTS`: optional root directory to analyze (defaults to the project root).

Produce the docs index at `docs/README.md`, or at `docs/README-intake.md` when the project already has its own `docs/README.md` (`references/intake/rules.md`, "Existing docs"): the entry-point document a new engineer or AI agent reads first. It gives
a short project overview, a working quickstart (how to install and run), a pointer to the structure, and a linked
index of every other intake doc. Document only what the code and project config prove.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run LAST in the intake documentation suite, after the other `intake:document-*` commands, so it can link the docs
they produced. It degrades gracefully: link only the docs that exist.

## Skills to invoke

- **`fullstack-dev-skills:code-documenter`**: structure and format the onboarding doc and the documentation index.
- **The project's framework skill** (e.g. `fullstack-dev-skills:react-native-expert`, `fullstack-dev-skills:nextjs-developer`, `fullstack-dev-skills:django-expert`): derive the
  accurate install, run, and build commands for the stack.
- **`fullstack-dev-skills:spec-miner`**: confirm entry points, scripts, and prerequisites from the code and config.

## Workflow

### Phase 1: Gather
Read the package/build manifest(s) and their scripts, the run/entry configuration, and the existing `docs/` tree to
learn which reference docs exist. Identify any separate sub-packages (e.g. a `functions/` or `server/` package) with
their own setup.

### Phase 2: Derive the quickstart
From the real scripts and tooling, write the prerequisites, install steps, run/start commands, and
lint/type-check/test commands. Note any required-but-gitignored config (credentials, env files) without inventing
values.

### Phase 3: Assemble the index
List every reference doc under `docs/`, grouped by category, each with a one-line description and a relative link,
including `intake-findings.md` and `intake-existing-docs.md`. List the owner docs from `docs/intake-existing-docs.md`
in their own group, each marked "owner-written" with its open finding ids. Add a short "where to start" reading order.
Docs written after this command add themselves to the index in their own commit (`references/intake/rules.md`).

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the detected commands, the doc list, and the output
path. Do not write until confirmed. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write the docs index using the template below. When an owner `docs/README.md` exists, write `docs/README-intake.md` and list the owner README under Owner docs; never edit it.

### Phase 5: Accuracy audit (required)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Verify every command is grounded in a real script or runs as written, every linked doc path exists, and no step is
invented. Fix or remove anything unverified.

## Output template

```markdown
---
command: intake:create-onboarding
verified: <short SHA of HEAD when the accuracy audit ran>
sources: []
related: []
---
# <Project> Documentation

<1-2 sentence overview: what the project is and its stack.>

## Quickstart
<prerequisites; install; run; lint/type-check/test; any sub-packages>

## Project structure
<1-2 sentences plus a link to the file-tree doc>

## Documentation index
### <Category>
- [<Doc title>](<relative/path.md>): <one-line description>

### Owner docs
- [<Doc title>](<relative/path.md>): owner-written; open findings <F-NNN, ...> or none

## Where to start
<recommended reading order for a new engineer or agent>
```

## Failure conditions

- **No runnable app detected** (library or monorepo): describe how it is built and consumed instead of inventing
  run commands.
- **A linked doc does not exist**: omit the link rather than point at a missing file.

## Output

The docs index (`docs/README.md` or `docs/README-intake.md`), plus a short summary: commands captured and docs linked.
