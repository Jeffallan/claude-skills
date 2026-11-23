---
name: complete
description: Check a ticket's evidence, update its Completion Status row and commit the ticket with its evidence summary
argument-hint: "[ticket-id]"
---

# Ticket Complete

Finish the ticket `ticket:execute` worked on: run the boundary checks, update its Completion Status row with the evidence summary, commit the ticket's work and the row together, and clear the marker. This command never writes to the tracker, attended or not.

**Target ticket:** `$ARGUMENTS` (optional: the marker names the ticket in progress)

## Mode

Read `${CLAUDE_PLUGIN_ROOT}/references/specs/unattended.md`. In goal mode (the goal prompt runs this command "under its unattended rules", or a goal is active) never call `AskUserQuestion` and skip the checkpoints; a check that fails blocks the ticket through `guard block`. Attended, stop at the checkpoints below. With no goal active and `AskUserQuestion` unavailable, take the wrong-session stop in `unattended.md` before the first checkpoint; never fall back to goal mode.

`guard <command>` below means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`, the ticket guard bundled with this plugin. Type it out each time, or define a shell function (`guard() { uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" "$@"; }`); a variable holding the command fails in zsh, which doesn't split it into words.

## Step 1: Find the ticket and its marker

```bash
guard marker status
```

- The marker names the ticket (and `$ARGUMENTS`, when given, matches it): continue.
- No marker, and the evidence record shows a clear for this ticket: it was already completed or blocked; report that and stop.
- **No marker and no logged clear** (the marker was lost): the evidence can't be trusted as it stands.
  - Goal mode: `guard block <ticket> "marker lost"`. Without a marker it takes the start SHA from the ticket's last `marker_start` event, saves the patch and the untracked files, restores the tree and writes the Blocked row; pass `--start <sha>` when the evidence has no open start. Then go to the next ticket.
  - Attended: show what is missing, run Step 2 with `--ticket <ticket>`, and only when the re-run, RED replay and tamper scan pass may the owner accept the ticket with `guard summary --ticket <ticket> --accept-lost-marker` in Step 3.

Build the summary of what changed from `git diff` against the marker's start SHA and the ticket's section in the plan, never from memory of the conversation.

## Step 2: Boundary checks

Run each and show its output and exit code:

```bash
guard rerun          # the work in a clean temporary worktree: each verify command, else the last GREEN
guard red-replay     # the new tests must fail against the start SHA (refactor tickets skip it)
guard tamper-scan    # deleted tests, added skips, changed snapshots, assertion-free tests
```

- **Re-run or replay fails:** attended, report it and stop with the marker kept, so the owner can fix and rerun; goal mode, `guard block <ticket> "<check> failed: <one line>"`.
- **Tamper scan flags something:** attended, show each flag; for each one the owner explains, rerun with `--reason <ID>=<one line>`, and fix the rest. Goal mode: the runtime ignores `--reason`, so `guard block <ticket> "tamper scan: <flags>"`.

## Step 3: Evidence summary

```bash
guard summary
```

It prints the notes line (RED and GREEN commands with exit codes, the test digest, the re-run, the replay, the tamper flags with reasons, the docs updated or checked) and exits 1 with a list when any evidence is missing. An affected doc that is neither updated nor checked is missing evidence: go back to `ticket:execute` Step 6a. A ticket with no RED or GREEN record fails here: attended, report what is missing and stop; goal mode, `guard block <ticket> "evidence missing: <list>"`.

Then check that every script the RED and GREEN commands run is in the repo, committed already or staged for this commit (with the ticket's tests, or under the spec's `review/` folder), never a scratch path such as `/tmp`, `$TMPDIR` or a session scratchpad. Evidence that points outside the repo is missing evidence: a reboot deletes it, and `guard red-replay` can't rerun it later. Attended, report it and stop; goal mode, `guard block <ticket> "evidence outside the repo: <path>"`.

## Step 4: Update the plan

In the spec's `implementation-plan.md`, set the ticket's Completion Status row:

| Column | Value |
|--------|-------|
| Status | Done |
| Completed Date | Today, `YYYY-MM-DD` |
| Notes | The `guard summary` line, plus approved deviations in a few words |

The table holds no SHAs: the row is committed with the ticket, so `git log --grep "Ticket: <id>"` finds it. Leave Proposed tracker changes and Open questions entries from `ticket:execute` in place; they go in the same commit.

## Step 5: Commit

Stage the ticket's changes and the plan, and commit them in the same commit:

```
<type>(<scope>): <summary>

<what changed and why, in two to four lines>

Ticket: <id>
```

- Use the project's conventional commit types and any trailers the project requires after `Ticket:`.
- Keep `Ticket:` and every other trailer (`Co-Authored-By:`, `Signed-off-by:`, any line the project or the session adds) in one final block with no blank line between them. Git reads only the last paragraph as trailers, so a separate attribution paragraph hides `Ticket:` from `git log --format='%(trailers)'`.
- Never put a Linear issue ID or a Jira `#transition` token in the subject or body; the `Ticket: <id>` trailer is the only reference.
- Attended checkpoint: show the message and the staged file list, and commit on the owner's yes.

Run the project's commit hooks; never skip them. When a hook fails, fix the cause and commit again; after three failures, attended stop and report, goal mode `guard block <ticket> "commit hook: <one line>"` (the commit never happened, so the block can restore the tree).

## Step 6: Clear the marker

```bash
guard marker clear
```

Clear it only after the commit succeeds. When any step above stopped attended, the marker stays and the ticket stays open.

## Output

```markdown
## <ticket> complete

| Check | Exit |
|-------|------|
| rerun | 0 |
| red-replay | 0 (or skipped: refactor) |
| tamper-scan | 0 |
| summary | 0 |

**Commit:** <short SHA> <subject>
**Completion Status:** Done, <notes line>
**Next:** <next ticket in Execution Order, or `spec:review <spec-name>` when every ticket is Done or Blocked>
```

## Rules

- No tracker writes and no status moves. Tracker status changes only in `spec:complete`.
- One commit per ticket, holding the work, the Completion Status row and the evidence summary.
- Never push.
