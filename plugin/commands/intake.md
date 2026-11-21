---
name: intake
description: Run intake on an existing codebase, documenting and testing what it does today through the intake agents, one checklist item at a time
argument-hint: "[procedure]"
---

# Intake

**Arguments:** `$ARGUMENTS`

The one entry point for intake. It works `docs/intake-checklist.md` in order: for each item it starts the agent that does that kind of work on the item's procedure, settles the procedure's checkpoint (attended, the owner confirms the scope; in a goal run the agent drafts it and goes on), reviews the diff and commits. The agents write; this session decides, checks and commits. It ends with the system description.

- No argument: work the checklist from the first unchecked item without an unresolved `BLOCKED:` note, through Phase 3.
- A procedure name (`intake document-glossary`): run or rerun that one procedure. Anything after the name goes to the procedure as its options (`intake create-system-description --full`, `intake document-api backend/`).

Before the first item, read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/checklist.md`. Load the `SendMessage` tool with ToolSearch (`select:SendMessage`): it is deferred, and an attended checkpoint, `document-authorization`'s second pass and a rerun for a missing skill all resume an agent with it.

`guard <command>` below means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`, the ticket guard bundled with this plugin. Type it out each time, or define a shell function (`guard() { uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" "$@"; }`); a variable holding the command fails in zsh, which doesn't split it into words.

## Flow

```mermaid
flowchart TD
  start([intake]) --> ed[existing-docs: code-reader + doc-writer]
  ed --> dc[document-codebase: doc-writer]
  dc --> docs[document-* procedures in order: doc-writer, code-reader for facts]
  docs --> onb[create-onboarding: doc-writer]
  onb --> ts[testing-setup: test-writer]
  ts --> tf[testing-features, testing-user-flows: test-writer]
  ts --> tsec[testing-authorization, testing-owasp: security-prober]
  tf --> sd[create-system-description: architect]
  tsec --> sd
  sd --> done([report and checklist])
```

## Procedures and agents

Each procedure lives at `${CLAUDE_PLUGIN_ROOT}/references/intake/procedures/<procedure>.md` and runs in one agent. Its id in the checklist, its docs' `command:` frontmatter and its commits' `Intake:` trailer stays `intake:<procedure>`.

| Agent | Procedures |
|-------|------------|
| `fullstack-dev-skills:doc-writer` | `existing-docs`, `document-codebase`, `document-file-tree`, `document-data-model`, `document-integrations`, `document-api`, `document-user-model`, `document-features`, `document-glossary`, `document-security`, `document-authorization`, `document-user-flow`, `document-config`, `document-analytics`, `create-onboarding` |
| `fullstack-dev-skills:test-writer` | `testing-setup`, `testing-features`, `testing-user-flows` |
| `fullstack-dev-skills:security-prober` | `testing-authorization`, `testing-owasp` |
| `fullstack-dev-skills:architect` | `create-system-description` |
| `fullstack-dev-skills:code-reader` | Facts for any of the above: the blind batches of `document-authorization`'s second pass, and an area the writer's discovery would otherwise read whole (a large codebase) |

## Setup

1. When `docs/intake-checklist.md` is missing, copy the template from `references/intake/checklist.md` with the date, the branch and its start SHA filled in. Attended, show it and confirm the branch first; intake runs on its own branch (`intake/<YYYY-MM-DD>`), never the default branch.
2. Decide the mode by the table in `${CLAUDE_PLUGIN_ROOT}/references/specs/unattended.md`: goal mode under a `/goal`, attended when `AskUserQuestion` is available, otherwise the wrong-session stop.
3. Detect the stack once (the package manifest and lockfile, the framework config, the test config) and pick the matching `fullstack-dev-skills:` language and framework skills, as "Skills" in `references/intake/rules.md` describes.

## Per item

1. **Pick.** Re-read the checklist and take the item (the next unchecked one, or the named procedure). An item that names no procedure (start the findings tracker, link the docs index from `CLAUDE.md`) is done here in this session, then goes to step 7.
2. **Read the procedure** in this session: `${CLAUDE_PLUGIN_ROOT}/references/intake/procedures/<procedure>.md`. Note its "Skills to load" list and add the stack skills that apply. The intake eval opens the item at this read.
3. **Start the agent** with the brief below. When it needs facts from a large area, start `code-reader` agents first (they only read, so several may run at once) and pass their reports in the brief.
   - **Goal run: one pass.** The agent runs the whole procedure. At the checkpoint it puts the scope it would have shown in its report under `Checkpoint draft:`, adds an Open questions row only under the rule in `references/intake/rules.md` ("In a goal run"), and goes on to write, audit or run and verify. Nobody answers a goal-run checkpoint, so the agent never stops there.
   - **Attended: discovery, then resume.** The agent runs up to the checkpoint, returns the scope and writes nothing.
4. **Checkpoint.** Goal run: copy the agent's `Checkpoint draft:` into the item's checklist note. Attended: show the scope and wait for the owner to confirm or correct it.
5. **Write.** Attended, resume the same agent with `SendMessage`, giving the confirmed or corrected scope. It writes with its discovery still in context, runs the procedure's audit or run-and-verify phase, and reports. One writing agent runs at a time. When `document-authorization` returns its second-pass batches, start one fresh `code-reader` per batch with only what the procedure lists, then resume the writer with their reports.
6. **Check the report.** Its last line lists the skills it loaded. When a skill the brief named is missing, resume the agent to load it and redo the work that needed it; when it is still missing, start a fresh agent for the item. Then review the diff yourself: `git status --short` and `git diff` show only this item's files, and only what "What intake may change" in `references/intake/rules.md` allows. Run `guard docs-check` for a documentation item and the project's test command for a testing item, and read the fresh output.
7. **Commit.** Check the box with an indented note: the date, the evidence, the finding ids raised, the skills the agent reported loading (a skill it didn't load gets `<skill> not loaded: <reason>`), and its human-voice line for a documentation item. Commit the item's files and the checklist together, `<docs|test>(intake): <procedure>`, with the trailer `Intake: intake:<procedure>` in the message's last paragraph, beside any other trailer (`Co-Authored-By:`) with no blank line between them: git reads trailers only from the last paragraph, so an `Intake:` line followed by a blank line and `Co-Authored-By:` is not a trailer. Check it with `git log -1 --format='%(trailers:key=Intake,valueonly)'`, and fix a wrong one with a follow-up commit, never an amend. Agents never commit.

Attended runs stop after an item when the owner says so; the checklist is the state the next run starts from.

### The brief

Keep the line for the run's mode and drop the other.

```
Use the <skill> skill to <what this procedure produces>. Also load: <the other skills, each by exact name>.
Procedure: <plugin root>/references/intake/procedures/<procedure>.md. Read it and the files it names under <plugin root>/references/intake/ before anything else.
Plugin root: <the value of ${CLAUDE_PLUGIN_ROOT}>. Project root: <path>. Options: <what followed the procedure name, or none>. Mode: <attended|goal run>.
<goal run> One pass: don't stop at the procedure's checkpoint. Put the scope it shows in your report under "Checkpoint draft:", follow the goal-run rule in rules.md, and go on to write.
<attended> Discovery only: run the procedure up to its checkpoint and return the scope it shows. Write nothing until I resume you.
Facts already gathered: <code-reader reports, or none>.
End your report with "Skills loaded: ..." listing the skills you loaded.
```

## After the last item

Phase 4 (the gate) stays attended and outside this command. Report a table (item, commit, evidence, finding ids), any High security finding that affects the deployed system first (id and one line, no reproduction detail), then blocked items and open questions.

## Rules

- Agents write, one at a time, and never commit. This session reviews each agent's diff and commits it.
- Agents can't ask the owner: every question goes through this session's checkpoint.
- Never edit a file an agent is writing while it runs, and never run a writing agent while a ticket marker exists (`references/intake/rules.md`).
