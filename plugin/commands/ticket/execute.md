---
name: execute
description: Implement one ticket test-first from its spec's implementation plan, with RED and GREEN evidence recorded
argument-hint: "<ticket-id>"
---

# Ticket Execute

Implement one ticket from a spec's `implementation-plan.md`: failing test first, then the code, with RED and GREEN evidence recorded by the workflow runtime. The ticket's changes stay uncommitted; `ticket:complete` checks the evidence and commits. This command never writes to the tracker, attended or not.

**Target ticket:** `$ARGUMENTS`

## Mode

Read `${CLAUDE_PLUGIN_ROOT}/references/specs/unattended.md` before Step 1.

- **Goal mode:** the goal prompt runs this command "under its unattended rules", or a goal is active. Never call `AskUserQuestion`, skip every checkpoint, and block a stuck ticket with `guard block` instead of asking.
- **Attended:** stop at the checkpoints marked below.
- **Neither:** no goal is active and `AskUserQuestion` is unavailable. Take the wrong-session stop in `unattended.md` before the first checkpoint; never fall back to goal mode.

`guard <command>` below means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`, the ticket guard bundled with this plugin. Type it out each time, or define a shell function (`guard() { uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" "$@"; }`); a variable holding the command fails in zsh, which doesn't split it into words.

## Step 1: Find the ticket

1. Read `.claude/workflow-config.json` for `specsRoot` and `verify`. When it is missing: attended, run the config wizard in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`; goal mode, end with `BLOCKED: no workflow config`.
2. Find the spec whose `implementation-plan.md` under `<specsRoot>/todo/` lists the ticket in its Completion Status table. Read the ticket's section, the Execution Order, the overview, and the goal prompt's `<decisions_already_made>` when one exists. The plan is the source of truth; the tracker is never needed to run a ticket.
3. Check the row:
   - Done: report it and stop.
   - Blocked: report the reason and stop.
   - A dependency is Blocked: run `guard block <ticket> "depends on <dependency>"` and stop.
   - A dependency is not Done: attended, ask whether to continue; goal mode, take the next ticket in order instead.
4. The ticket section must name its acceptance criteria, its RED check and its `Skill:` line. When one is missing: attended, offer to draft it from the codebase for the owner's approval; goal mode, run `guard block <ticket> "question: <what is missing>" --question "<what is missing>"`, which adds the gap to the plan's Open questions in the same commit as the Blocked row.

## Step 2: Start clean and claim the ticket

1. Run `git status --porcelain`. Only the spec's own `implementation-plan.md` may show (a Blocked row that `guard block` couldn't commit). Anything else:
   - Attended: ask the owner to commit or stash it, then rerun.
   - Goal mode: run `guard block <ticket> "dirty working tree at start"` and go to the next ticket.
2. Start the marker. It records the mode, the branch and the start SHA, and resumes the same ticket when it already exists:

   ```bash
   guard marker start <spec-name> <ticket> --mode goal   # or --mode attended
   ```

   A marker for another ticket is refused: finish that ticket with `ticket:complete` or block it first. A warning about the marker's age names an abandoned ticket; attended, show it to the owner.
3. Invoke the `fullstack-dev-skills:ticket-guard` skill. Its body carries the ticket rules that must survive a compaction. The guard hooks themselves ship in the plugin's `hooks/hooks.json`, so they run in every session, a resumed one included, and act only while a marker exists: they freeze the RED tests, keep goal runs out of the text tickets folder and re-run GREEN before a goal-mode stop.
   Then confirm the hooks are live: run `guard marker status` and check that `session_id` is set (the first hook call claims the marker). An empty `session_id` means the plugin's hooks didn't run (plugin disabled, or hooks turned off in settings), and every ticket in the run is unguarded: attended, tell the owner; goal mode, end with `BLOCKED: ticket-guard hooks did not register` (a spec-wide stop).
4. Invoke the skill on the ticket's `Skill:` line, when it names one.

**Attended checkpoint:** summarize the ticket, the files you expect to touch and the RED check, and confirm with the owner.

## Step 3: Read the code

Read the files the ticket names and the patterns the overview's Reuse section points to. For broad searches, start `fullstack-dev-skills:code-reader` agents, which only read and return text, in one message so they run together; brief them as "Use the <skill> skill to ...", tell them not to write files or change the tracker, and ask them to end with the skills they loaded. Every edit happens in this session.

## Step 4: RED

Write the failing test before any implementation edit.

1. Write tests for the acceptance criteria in the repo's test suite, where CI runs them. Import the symbol under test **inside the test body**, not at the top of the file: RED is strict, and a collection or import error never counts as RED.
2. When the project has a typecheck or compile step (the plan's typecheck command, `tsc --noEmit`, `mypy`, `cargo check`), run it on the new test files first and fix what it reports. The guard can't tell a type error from a real failure in every language, and a test that doesn't typecheck fails for the wrong reason.
3. Run them through the runtime, which records the RED evidence and then freezes the test files:

   ```bash
   guard run red -- <command that runs the new tests>
   ```

   It counts as RED only when the command fails, no non-test file has changed since the start SHA, and the failure is not a collection or import error. When it doesn't count, fix the test (not the code) and run it again.

   Every script a RED or GREEN command runs lives in the repo and is committed with the ticket, never a scratch path (`/tmp`, `$TMPDIR`, a session scratchpad), which a reboot or cleanup deletes along with the evidence. Put a new helper script with the ticket's tests, where the guard treats it as a test file and freezes it at RED. A fix ticket from `spec:review` runs its frozen reproduction from the spec's `review/repro/`, already committed.
4. Other ticket types:
   - **No code** (docs, prompts, configuration): `guard run red --type stand-in -- "<check>"`, where the check is the one the plan names (a validator, a grep, a fixture run) and fails before the change. Quote a check with spaces or `&&` as one string, as in `guard run red --type stand-in -- "test -f docs/units.md && grep -q x docs/units.md"`; the guard refuses `sh -c` followed by unquoted words.
   - **Refactor fix ticket:** first read the spec's `review/metrics.md` (rerunning `guard metrics` here would change a tracked file before RED). When the tool that proves the ticket (`jscpd` for duplication, `vulture` or `knip` for dead code, `lizard` for complexity) is missing, refuse the ticket: nothing could show the target gone. A missing tool's section says it `did not run`, and the bold line under the changed files names it after `Not installed, so unmeasured:` or `No metric tool ran (not installed:`, the same `missing` list `guard metrics --json` prints. Attended, tell the owner which tool to install; goal mode, `guard block <ticket> "metric unavailable: <tool> did not run"`. Otherwise `guard run red --type refactor -- "<full suite>"`, quoted the same way. The suite must pass, and every test file is frozen.

After RED, the frozen tests can't be edited. In goal mode the hook denies the edit; attended it asks, and each approved edit is logged as an amendment. GREEN accepts an amended test, and the ticket's summary names it.

## Step 5: Implement

Follow the ticket's steps until the new tests and the existing suite pass. Reuse what the overview names. Then refactor with the tests green.

- **Deviation** (the steps must change): attended, stop and ask with the planned approach, the change, why, and the impact; record an approved deviation for the summary. Goal mode: `guard block <ticket> "<why the steps must change>"`.
- **Blocker** (missing access or prerequisite, a denied action, three failed attempts at the same problem, a contradiction with the spec): attended, report and wait; goal mode, `guard block`, then block each dependent with `"depends on <ticket>"`. A blocker that leaves a question for the owner passes `--question "<question>"` too.
- **A question only someone else can answer:** attended, add it to the plan's Open questions table and ask the owner; goal mode `guard block <ticket> "question: <question>" --question "<question>"`, which writes the Open questions row in the same commit as the Blocked row. Don't edit the plan by hand first.
- **A test added after RED:** allowed only for coverage the RED tests couldn't hold, such as a helper's own unit test or a regression the implementation exposed. A missing acceptance-criterion test is a deviation, handled as above, because RED can't be rerun once implementation has started. The guard doesn't freeze a file added after RED, so list each one with its reason under **Tests added after RED** in the summary. Show each one failing without the fix, in a scratch worktree (`git worktree add --detach "$(mktemp -d)" <start-sha>`), and record the baseline and exit code next to the reason, then remove the worktree. The baseline is the start SHA for a regression in code that existed before the ticket, or the start SHA plus the ticket's earlier implementation for a flaw in the ticket's own code fixed after RED (that flaw never existed at the start SHA). When it can run at neither (it tests a helper the ticket created), say that instead.
- **New issue found:** never work it. Append it to the plan's Proposed tracker changes (title, plain example, files, duplicate check against open tickets) and continue.

## Step 6: GREEN

```bash
guard run green -- <command that runs the ticket's tests>
```

Then run each `verify` command from the config (else the plan's verification commands) and show every exit code. In goal mode the Stop hook re-runs the latest GREEN command before letting the turn end.

Check each acceptance criterion against a command you ran and its output. A criterion with no check is not met.

## Step 6a: Docs

The ticket isn't done until the docs it affects say what the code now does. List them from the diff, not from the plan alone:

```bash
guard docs-affected
```

It lists each doc under the docs root (`docsRoot`, default `docs`) that cites a symbol the diff touches (`` `path::symbol` ``) or whose `sources:` globs match a file the ticket adds (an edit to an existing file is covered by the citations), and each doc a changed doc names in its `related:` frontmatter, one hop. A doc the diff adds or changes is listed `updated`, with the reason `added in the diff` or `changed in the diff`. Include the docs on the ticket's `Docs:` line too. For each one:

- **Update it** in this ticket's work (leave its `verified:` as it is; the ticket's commit counts as the update): correct the claims, cite symbols as `` `path::symbol` `` (never bare line numbers), keep each fact in one doc and link to it from the others, and keep its `related:` list two-way. Invoke the `fullstack-dev-skills:code-documenter` skill for the edit.
- **Or record that it needs no change**, with the reason: `guard docs-checked <doc> --reason "<why it still holds>"`. Read the doc first.

Run `guard docs-check` and fix what it reports. `guard summary` refuses while an affected doc is neither updated nor checked.

## Step 7: Hand off

Show this summary, then run `ticket:complete <ticket>` (goal mode: at once; attended: when the owner is ready):

```markdown
## <ticket>: <title>

| Check | Command | Exit |
|-------|---------|------|
| RED | <command> | <non-zero> |
| GREEN | <command> | 0 |
| <verify command> | <command> | 0 |

**Acceptance criteria:** each criterion, with the check that proves it
**Files changed:** <list>
**Docs:** each affected doc, updated or checked with its reason, or none
**Deviations:** <approved deviations, or none>
**Tests added after RED:** <file: reason, baseline and exit code, or none>
**Proposed tracker changes added:** <titles, or none>
**Suggested commit subject:** <type(scope): summary>
```

## Rules

- No tracker writes and no status moves, attended or not. `spec:complete` closes tickets.
- No parallel ticket work: one ticket at a time, every edit in this session.
- Never delete, skip or weaken a test to get a pass.
- RED, GREEN and verify commands run only files in the repo, never a scratch path.
- Use the project's own checks, not a fixed coverage number.
