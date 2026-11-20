# Intake Goal Prompt Template

Runs the intake checklist (`references/intake/checklist.md`) as one `/goal` session: one checklist item per command, in order, with a commit per item. It follows the shape of `references/specs/templates/goal-prompt.md` and the checklist-runner loop: all state lives in the checklist file, and the run re-reads it after every compaction. The intake commands carry their own steps and goal-run rules (`references/intake/rules.md`), so never copy those steps here.

Save the filled prompt as `docs/intake-goal-prompt.md` on the intake branch and commit it with the checklist. That commit is the start SHA: `git log -1 --format=%h -- docs/intake-goal-prompt.md`.

## Template

```markdown
Run intake on branch <intake-branch>: every unchecked item of docs/intake-checklist.md in Phases 1 to 3, in order, one item per command. Stop before Phase 4: Gate. Start SHA: the output of `git log -1 --format=%h -- docs/intake-goal-prompt.md`; resolve it once and print it.
<done_when>
Rerun these in your final turn and show the output:
1. `git log --format='%h %(trailers:key=Intake,valueonly,separator=%x2C) %s' <start-sha>..HEAD` shows exactly one `Intake:` trailer on every commit, each naming a checklist item, and every item checked since the start has at least one commit. BLOCKED notes, unblocking and follow-up fixes are commits like any other, each naming its item.
2. Every item in Phases 1 to 3 is checked with a dated evidence note, or carries a `BLOCKED:` note with its reason.
3. `<test:all command>` exits 0; its pass, fail and skip counts are shown. `git status --short` is empty.
4. `git diff --stat <start-sha>..HEAD` touches only docs, tests, test config, test scripts and docstrings.
5. The scoring files are saved (see <final_report>) and <final_report> is posted, ending with the line "Ready for Phase 4 (attended)."
</done_when>
<hard_rules>
- Characterize, don't fix: never change application behavior, build or deploy config. Record every bug in docs/intake-findings.md with its id.
- Never commit vendored or installed packages. Never change runtime dependencies or what ships (dependencies, main, bin, type, engines, the build). Test dev-dependencies, test configuration and test-only package.json files are allowed, since intake must be able to install test tooling to write tests on observed behavior. Pick test dev-dependency versions that fit the runtime dependencies already installed, never the reverse: never upgrade, downgrade or re-resolve a runtime dependency to make newer test tools fit, and leave the lockfile's existing runtime entries byte-identical (Vue 2.6 takes `@vue/test-utils` 1.x and a runner that supports Vue 2 and the project's Node, not the latest releases that pull Vue 3).
- Prove each harness layer with a smoke test before writing any real test in that layer.
- Never call AskUserQuestion. A routine scope confirmation goes in the item's checklist note; an Open questions row in docs/intake-findings.md is only for a choice the owner could reasonably reverse. The run continues either way.
- Reach the intake references only through the intake commands, which name their plugin path. Never search the filesystem for them.
- Never push, tag, open PRs or write to a tracker. Never rewrite history: no rebase, reset, amend or squash.
- Never delete, skip or weaken a test to get a pass, other than the intended-behavior twin of a finding.
- <limits specific to this project: paths not to touch, services not to call>
</hard_rules>
<stops>
An item is blocked when its command can't run here (a layer that won't start, a missing secret), its input is missing and the code can't stand in, or 3 attempts at the same problem fail. Add an indented `BLOCKED: <what is needed>` note under it, commit the checklist alone with the item's `Intake: <command>` trailer, and continue with the next item that doesn't depend on it.
End your turn with `BLOCKED: <stop>`, what you need, and `git status --short` only for a run-wide stop:
- The project won't install or build, so no command can verify anything.
- The existing test suite can't run at all before intake starts.
- A <done_when> condition can be met only by a forbidden action (a history rewrite, a weakened test): name the condition and the commits involved.
- <other run-wide stops for this project>
</stops>
<per_item_loop>
Each item, in order:
1. Re-read docs/intake-checklist.md and take the first unchecked item without an unresolved BLOCKED note.
2. Load the skills in its command's "Skills to load" list with the Skill tool ("Skills" in references/intake/rules.md), then run the command under the goal-run rules there.
3. Verify with fresh output: the command's accuracy audit or run-and-verify phase, then `<test:all command>`.
4. Check the box with an indented note (date, evidence, finding ids raised), then commit the item's files and the checklist together: `<docs|test>(intake): <command>` with the trailer `Intake: <command>` in the message's last paragraph, beside any other trailer (`Co-Authored-By:`) and with no blank line between them. Git only reads trailers from the last paragraph. Change only this item's checklist note in its commit.
5. Check the commit you just made: `git log -1 --format='%(trailers:key=Intake,valueonly)'` prints this item's command, and `git show --stat HEAD` lists only this item's files. When either is wrong, never amend: fix it with a follow-up commit carrying the same item's trailer.
</per_item_loop>
<context_hygiene>
After a compaction or resume, re-read this file and the checklist, and rebuild state from them and `git log`, never from memory. Delegate broad code searches to read-only subagents; every edit happens in the main session.
</context_hygiene>
<final_report>
Save the scoring files to <results-dir> (outside the repo):
- `git reflog --date=iso-strict --format='%gd%x00%gs' > <results-dir>/intake.reflog`
- `<test:all command>` output as <results-dir>/test-all.txt
Then rerun <done_when>, quoting each condition before its output. Phase 4 items stay unchecked: they are attended and out of this run's scope. Lead with any High security finding that affects the deployed system (id and one line, no reproduction detail), then blocked items and open questions, then a table: item, commit, evidence, finding ids. Then the findings by severity, and "Ready for Phase 4 (attended)."
</final_report>
Reminder: every commit names its item with one `Intake:` trailer on <intake-branch>, characterize don't fix, no push, stop before Phase 4.
```

## Filling it

| Placeholder | Source |
|-------------|--------|
| `<intake-branch>` | A local branch cut for intake, for example `intake/<YYYY-MM-DD>` |
| `<test:all command>` | The combined script `intake:testing-setup` wires; before that item runs, the project's existing test command |
| `<results-dir>` | A folder outside the repo where the owner keeps eval results, never one that holds a gold set or pilot notes the run could read |
| Limits and run-wide stops | Paths the run must not touch (vendored code, generated clients), services it must not call (production APIs, paid sandboxes). Never list a gitignored install directory (`node_modules` and the like) as off-limits, and never word a limit as "never change dependencies": the template's dependency rule already covers it. Before launch, read each project limit and confirm it doesn't block a layer `intake:testing-setup` must build |

## Launching it

Start a new session with the deny set from `references/specs/launch.md`, so the denies hold for the whole run. Intake runs no ticket commands, so the `ticket-guard` allow rule isn't needed. When the project signs commits, launch from a shell where signing works (`ssh-add -l` lists the key, or `git commit --allow-empty` signs in a scratch clone): a new tmux window may not inherit `SSH_AUTH_SOCK`, and every commit in the run then fails or goes unsigned. `--disallowedTools` takes a list, so the `--` before the prompt is required. The session serves the run only: run Phase 4 and any other attended intake command in a fresh session without these flags.

```bash
claude \
  --disallowedTools AskUserQuestion \
  --disallowedTools 'Bash(git push:*)' --disallowedTools 'Bash(git tag:*)' \
  --disallowedTools 'Bash(gh pr create:*)' --disallowedTools 'Bash(gh pr merge:*)' \
  --disallowedTools 'Bash(gh pr comment:*)' --disallowedTools 'Bash(gh pr review:*)' \
  --disallowedTools 'Bash(gh pr edit:*)' \
  --disallowedTools 'Bash(gh issue create:*)' --disallowedTools 'Bash(gh issue edit:*)' \
  --disallowedTools 'Bash(gh issue close:*)' --disallowedTools 'Bash(gh issue comment:*)' \
  --disallowedTools 'Bash(gh api * -X POST *)' --disallowedTools 'Bash(gh api * -X PATCH *)' \
  --disallowedTools 'Bash(gh api * -X DELETE *)' --disallowedTools 'Bash(gh api * --method POST *)' \
  --disallowedTools 'Bash(gh api * --method PATCH *)' --disallowedTools 'Bash(gh api * --method DELETE *)' \
  --disallowedTools 'Bash(git rebase:*)' --disallowedTools 'Bash(git reset:*)' \
  --disallowedTools 'Bash(git commit --amend:*)' \
  <one --disallowedTools per goal.deny entry> \
  -- "/goal Every condition in <done_when> in docs/intake-goal-prompt.md holds (Phase 4 items stay unchecked: they are out of scope) and your latest message quotes each condition with its evidence, or your latest message starts with BLOCKED: and names a stop from <stops> in that file. Read that file and docs/intake-checklist.md first, and again after any compaction."
```

The kickoff line names the end state, never "read the file", for the reason `references/specs/launch.md` gives. Judge the run by its final message, never its exit status.

## Scoring the run

The reflog snapshot, the transcript and the test output are what the intake eval (`evals/intake/` in the claude-skills repo) reads. Save them before deleting the branch or the clone: git prunes reflog entries after about 30 days, and transcripts stay only on the machine that ran the session.

The run saves the reflog and the test output itself. Record the transcript path yourself once the run ends: it is the `~/.claude/projects/<project>/<session>.jsonl` file whose first prompt is the /goal. The run can't do it, because a fair run denies it every read of `~/.claude/projects`, and it can't confirm a file it can't open.

## What never goes in

- Command steps or the rules already in `references/intake/rules.md`.
- Secrets, credentials or production URLs.
- Findings text; findings live in `docs/intake-findings.md`.
