# Goal Runs

A goal run works through a spec's tickets on its own: one ticket at a time, a failing test first, one commit per ticket, and no writes outside your repo. This page covers how to launch one, what it does when something goes wrong, and how to check its result.

---

## Launching

`spec:create` prints two commands for the spec's `goal-prompt.md`. Pick one per run.

- **Whole spec:** one session works every ticket, across as many compactions as it needs.
- **Next batch:** the next few tickets that are neither Done nor Blocked (`goal.batchSize`, default 3), then it stops. Run `/compact` and launch the next batch in the same session, or start a fresh one; the run picks up from the plan and `git log` either way.

For batches without anyone watching, `guard run-batches <spec-name>` runs the batches headless in one session, compacting between them. `guard` is the ticket guard that ships inside the plugin, `runtime/guard.pyz`; `spec:create` prints the full command with your plugin's path.

Each launch starts a **new** session. Never paste the `/goal` line into a session that's already running: the denies below only apply to the session they start.

## What a launch denies

Every launch command passes `--disallowedTools` for each write the run must not make:

- `AskUserQuestion`, since nobody is there to answer
- `git push` and `git tag`
- PR writes (`gh pr create`, `merge`, `comment`, `review`, `edit`, `close`, `reopen`, `ready`) and issue writes (`gh issue create`, `edit`, `close`, `comment`, `reopen`, `delete`, `transfer`)
- `gh api` with a method flag, fields or `--input`, attached or not, which covers every way it sends a write, including GraphQL mutations. GraphQL reads are denied too; a goal run reads through `gh issue` and `gh pr`
- every `gh project` write (reads such as `item-list` and `view` stay allowed) and `gh release`
- `guard decide` and `guard decisions import`, because only you record owner decisions
- `git rebase`, `git reset` and `git commit --amend`, since a run never rewrites history
- `ScheduleWakeup`, `CronCreate` and `RemoteTrigger`, so nothing starts work after the run ends
- the tracker MCP write tools you list in `goal.deny`

Reads stay allowed. The launch also passes `--allowedTools 'Skill(fullstack-dev-skills:ticket-guard)'`, so a headless session can load the skill that carries the ticket rules. The guard hooks don't depend on it: they ship in the plugin's `hooks/hooks.json` and run in every session while a ticket's marker exists. `ticket:execute` checks that the hooks claimed the marker and stops the run if they didn't.

## The goal condition

The `/goal` line is the condition the goal evaluator checks after every turn: every condition in `<done_when>` holds and the latest message shows the evidence, or the latest message starts with `BLOCKED:` and names a stop from `<stops>`. A condition such as "Read the goal prompt" would be met as soon as the file was read, ending the run after one turn, which is why the line names an end state.

The goal prompt records its start commit, and `<done_when>` counts commits from there: one per Done ticket, plus any commits that record Blocked rows in the plan and one human-voice pass commit when that pass changed wording. That's why earlier commits on the branch never upset a later run.

## When something goes wrong

**A stuck ticket doesn't stop the run.** When a ticket's steps would have to change, a prerequisite is missing, three attempts at the same problem fail, or a question can't be answered, the run blocks that ticket:

```bash
guard block <ticket> "<reason>"
```

This saves the ticket's changes to `.git/ticket-guard/blocked/<ticket>.patch` (new files go in a tarball beside it), restores the tree to where the ticket started, and marks the ticket Blocked in the plan. Tickets that depend on it are marked "depends on" it, and the run carries on with everything else. To pick a blocked ticket back up later, apply the patch with `git apply` and unpack the tarball.

**Questions wait for you.** If a ticket or a skill needs an answer the run can't get, the question goes into the plan's Open questions and the ticket is Blocked: question. The run never picks a default for you.

**New issues aren't worked.** Anything the run notices that's outside the spec goes into the plan's Proposed tracker changes, with an example, the files involved and a duplicate check. `spec:complete` offers to file them later.

**`BLOCKED:` is for the whole spec.** A run ends with `BLOCKED:` only when nothing more can be done: the environment won't build, the sources contradict each other on something every ticket needs, and the like. A run where only blocked tickets remain finishes normally and lists them first in its report.

## What keeps a run honest

The commands, the companion skill's hooks and the runtime check each other.

| Check | When | What it catches |
|-------|------|-----------------|
| Clean start | `ticket:execute` | Leftovers from another ticket |
| RED record | Before any implementation edit | A test that never failed, or failed only because it couldn't import |
| Test freeze (hook) | Every edit after RED | Weakening the test to get a pass. Goal runs are denied; attended runs are asked |
| GREEN re-run (Stop hook) | Each time a goal run tries to stop | Stopping with failing tests. After three failures it lets the stop through and the ticket fails at `ticket:complete` |
| Compaction recovery (hook) | After a compaction | Lost context: it prints the ticket, the mode and the next step |
| Clean re-run | `ticket:complete` | Work that only passes in the dirty tree |
| RED replay | `ticket:complete` | New tests that would pass without the change |
| Tamper scan | `ticket:complete` | Deleted tests, added skips, changed snapshots, assertion-free tests |

All of this state lives under `.git/ticket-guard/`, so nothing is committed and each worktree has its own.

## Checking a run

Judge a run by its final message, never by its exit code. A headless run can exit successfully after hitting the Stop-hook limit with the goal unmet. The final message either shows each `<done_when>` check with its output, or starts with `BLOCKED:`.

If the run ended with Blocked tickets that weren't committed yet, `spec:review` commits them first with `guard commit-plan`.

## The spec index

`docs/specs/INDEX.md` lists every spec with its status, discovery topics, feature areas and predecessors. It's generated from four header lines at the top of each `overview.md`:

```
**Spec:** <spec-name>
**Discovery:** <topic>, <topic>
**After:** <spec-name>
**Feature areas:** <area>, <area>
```

`guard spec-index` rewrites it, and `--check` fails when it's out of date or a name doesn't match a spec or a topic. `spec:create` and `spec:complete` run it whenever they change a header or move a spec, so you never edit the index by hand.
