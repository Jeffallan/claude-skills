# Goal Launch Commands

How `spec:create`, `spec:review` and `spec:complete` print the commands that start a goal run over a spec's `goal-prompt.md`. A goal run is never started by pasting `/goal` into a running session: each launch command starts a new session with the writes-only deny set, so the denies hold for the whole run, compactions included.

The goal-run session is for the run only. `/goal clear` ends the goal but keeps the session's `--disallowedTools` flags, so `AskUserQuestion`, `guard decide` and tracker writes stay denied for as long as the session lives. Do the attended work that follows a run (`spec:review` and its triage, fix-round decisions, `spec:complete`, the intake commands) in a fresh session started with only `--plugin-dir` and your usual permission mode.

## The guard

The workflow runtime is the ticket guard bundled with the plugin, `runtime/guard.pyz`, versioned with it. Commands, references, templates and spec files write it as `guard <command>`; the calling command or the `ticket-guard` skill runs it as `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`. A spec file never holds the plugin path, which differs per machine. Workflow users need uv, which supplies Python 3.11 or later when the machine lacks it.

## The kickoff lines

The text after `/goal` is the condition the goal evaluator checks after every turn, so it names the end state and the stop clause, never "Read the file". A condition such as "Read goal-prompt.md" is met as soon as the file is read, and the run ends after one turn.

**Whole spec**, one run across compactions:

```
/goal Every condition in <done_when> in <specsRoot>/todo/<spec-name>/goal-prompt.md holds, with every ticket in that file Done or Blocked with its reason, and your latest message shows the evidence, or your latest message starts with BLOCKED: and names a spec-wide stop from <stops> in that file. Read that file first, and again after any compaction.
```

**Next batch**, the next N tickets that are neither Done nor Blocked, in Execution Order. N is `goal.batchSize` in `.claude/workflow-config.json`, default 3. The line names the batch's tickets:

```
/goal Every condition in <done_when> in <specsRoot>/todo/<spec-name>/goal-prompt.md holds for the next batch (tickets <T1>, <T2>, <T3>), each Done or Blocked with its reason, and your latest message shows the evidence, or your latest message starts with BLOCKED: and names a spec-wide stop from <stops> in that file. Do only these tickets, in Execution Order, update the Completion Status table, then stop. Read that file first, and again after any compaction.
```

After a batch, the owner runs `/compact` and launches the next batch in the same session (`claude --resume <session> ...`), or starts a fresh session the same way; `ticket:execute` re-claims the marker either way. Claude cannot run `/compact` on itself.

## The deny set

Every launch carries these rules, each as its own `--disallowedTools` argument. They deny writes only; reads stay allowed, since the frozen-scope duplicate check reads open tickets.

| Rule | Blocks |
|------|--------|
| `AskUserQuestion` | Questions nobody is there to answer; the run records them as open questions instead |
| `Bash(git push:*)`, `Bash(git tag:*)` | Publishing the branch or a tag |
| `Bash(gh pr create:*)`, `Bash(gh pr merge:*)`, `Bash(gh pr comment:*)`, `Bash(gh pr review:*)`, `Bash(gh pr edit:*)`, `Bash(gh pr close:*)`, `Bash(gh pr reopen:*)`, `Bash(gh pr ready:*)` | PR writes |
| `Bash(gh issue create:*)`, `Bash(gh issue edit:*)`, `Bash(gh issue close:*)`, `Bash(gh issue comment:*)`, `Bash(gh issue reopen:*)`, `Bash(gh issue delete:*)`, `Bash(gh issue transfer:*)` | Issue writes |
| `Bash(gh api -X*)`, `Bash(gh api * -X*)`, `Bash(gh api -f*)`, `Bash(gh api * -f*)`, `Bash(gh api -F*)`, `Bash(gh api * -F*)`, `Bash(gh api --method*)`, `Bash(gh api * --method*)`, `Bash(gh api --field*)`, `Bash(gh api * --field*)`, `Bash(gh api --raw-field*)`, `Bash(gh api * --raw-field*)`, `Bash(gh api --input*)`, `Bash(gh api * --input*)` | API writes, in every form `gh api` accepts: a method flag anywhere, attached or not (`-X POST`, `-XPOST`, `--method=POST`), and fields or `--input`, which make the request a POST. GraphQL mutations go through `-f query=`. Reads with fields (a GraphQL query, `-X GET`) match too: attended they ask, and a goal run, which is denied them, reads through `gh issue view`, `gh issue list` and `gh pr view` |
| `Bash(gh project close:*)`, `Bash(gh project copy:*)`, `Bash(gh project create:*)`, `Bash(gh project delete:*)`, `Bash(gh project edit:*)`, `Bash(gh project field-create:*)`, `Bash(gh project field-delete:*)`, `Bash(gh project item-add:*)`, `Bash(gh project item-archive:*)`, `Bash(gh project item-create:*)`, `Bash(gh project item-delete:*)`, `Bash(gh project item-edit:*)`, `Bash(gh project link:*)`, `Bash(gh project mark-template:*)`, `Bash(gh project unlink:*)`, `Bash(gh release:*)` | Project writes and releases; Project reads (`list`, `view`, `field-list`, `item-list`) stay allowed |
| `Bash(*guard.pyz* decide *)`, `Bash(*ticket_guard* decide *)`, `Bash(*runtime* decide *)` | Owner-only decisions; a goal run must never record its own |
| `Bash(git rebase:*)`, `Bash(git reset:*)`, `Bash(git commit --amend:*)` | Rewriting history. A goal run never removes, squashes or amends a commit; a ticket found wrong after its commit stays committed and goes in the final report |
| Each tool name in `goal.deny` | The tracker MCP server's write tools, listed per project in `.claude/workflow-config.json` |

Text-ticket edits are blocked separately, by the companion skill's goal-mode hook on `text.ticketsDir`.

## The allow rule

Every launch also carries `--allowedTools 'Skill(fullstack-dev-skills:ticket-guard)'`. Without it a headless or goal session can be denied the Skill tool and the ticket rules in the skill's body never load. The guard hooks (test freeze, GREEN re-run, compaction recovery) ship in the plugin's `hooks/hooks.json` and run regardless; `ticket:execute` checks that they claimed the marker and stops the run when they didn't.

## The launch commands

`spec:create` prints both, filled in, and the owner picks one per run. When the project signs commits, launch from a shell where signing works (`ssh-add -l` lists the key): a new tmux window may not inherit `SSH_AUTH_SOCK`, and every commit in the run then fails or goes unsigned. `--allowedTools` and `--disallowedTools` each take a list of values, so without the `--` before the prompt they swallow it as one more rule and the session starts with no prompt. A launched session serves its run and nothing after it: start attended follow-up work in a fresh session without these flags.

```bash
# Whole spec
claude \
  --permission-mode <goal.permissionMode, default auto> \
  <goal.extraArgs, such as --plugin-dir> \
  --allowedTools 'Skill(fullstack-dev-skills:ticket-guard)' \
  --disallowedTools AskUserQuestion \
  --disallowedTools 'Bash(git push:*)' --disallowedTools 'Bash(git tag:*)' \
  --disallowedTools 'Bash(gh pr create:*)' --disallowedTools 'Bash(gh pr merge:*)' \
  --disallowedTools 'Bash(gh pr comment:*)' --disallowedTools 'Bash(gh pr review:*)' \
  --disallowedTools 'Bash(gh pr edit:*)' --disallowedTools 'Bash(gh pr close:*)' \
  --disallowedTools 'Bash(gh pr reopen:*)' --disallowedTools 'Bash(gh pr ready:*)' \
  --disallowedTools 'Bash(gh issue create:*)' --disallowedTools 'Bash(gh issue edit:*)' \
  --disallowedTools 'Bash(gh issue close:*)' --disallowedTools 'Bash(gh issue comment:*)' \
  --disallowedTools 'Bash(gh issue reopen:*)' --disallowedTools 'Bash(gh issue delete:*)' \
  --disallowedTools 'Bash(gh issue transfer:*)' --disallowedTools 'Bash(gh api -X*)' \
  --disallowedTools 'Bash(gh api * -X*)' --disallowedTools 'Bash(gh api -f*)' \
  --disallowedTools 'Bash(gh api * -f*)' --disallowedTools 'Bash(gh api -F*)' \
  --disallowedTools 'Bash(gh api * -F*)' --disallowedTools 'Bash(gh api --method*)' \
  --disallowedTools 'Bash(gh api * --method*)' --disallowedTools 'Bash(gh api --field*)' \
  --disallowedTools 'Bash(gh api * --field*)' --disallowedTools 'Bash(gh api --raw-field*)' \
  --disallowedTools 'Bash(gh api * --raw-field*)' --disallowedTools 'Bash(gh api --input*)' \
  --disallowedTools 'Bash(gh api * --input*)' --disallowedTools 'Bash(gh project close:*)' \
  --disallowedTools 'Bash(gh project copy:*)' --disallowedTools 'Bash(gh project create:*)' \
  --disallowedTools 'Bash(gh project delete:*)' --disallowedTools 'Bash(gh project edit:*)' \
  --disallowedTools 'Bash(gh project field-create:*)' --disallowedTools 'Bash(gh project field-delete:*)' \
  --disallowedTools 'Bash(gh project item-add:*)' --disallowedTools 'Bash(gh project item-archive:*)' \
  --disallowedTools 'Bash(gh project item-create:*)' --disallowedTools 'Bash(gh project item-delete:*)' \
  --disallowedTools 'Bash(gh project item-edit:*)' --disallowedTools 'Bash(gh project link:*)' \
  --disallowedTools 'Bash(gh project mark-template:*)' --disallowedTools 'Bash(gh project unlink:*)' \
  --disallowedTools 'Bash(gh release:*)' \
  --disallowedTools 'Bash(*guard.pyz* decide *)' \
  --disallowedTools 'Bash(*ticket_guard* decide *)' \
  --disallowedTools 'Bash(*runtime* decide *)' \
  --disallowedTools 'Bash(git rebase:*)' --disallowedTools 'Bash(git reset:*)' \
  --disallowedTools 'Bash(git commit --amend:*)' \
  <one --disallowedTools per goal.deny entry> \
  -- "/goal Every condition in <done_when> in <specsRoot>/todo/<spec-name>/goal-prompt.md holds, with every ticket in that file Done or Blocked with its reason, and your latest message shows the evidence, or your latest message starts with BLOCKED: and names a spec-wide stop from <stops> in that file. Read that file first, and again after any compaction."

# Next batch: the same flags, with -- and the next-batch kickoff line as the last arguments
```

**Headless batches:** `guard run-batches <spec-name>` runs the next-batch goal with the same deny set and allow rule (it adds `goal.deny` and `goal.allow` itself), with `--permission-mode` from `goal.permissionMode` (default `auto`; a headless session without one has every edit refused) and any `goal.extraArgs` such as `--plugin-dir`, judges each batch by its final message and the plan, compacts in the same session, repeats until every ticket is Done or Blocked, and runs `guard commit-plan` at the end. `--batch-size N` overrides `goal.batchSize`.

## Shared ask rules

Attended commands (`spec:triage`, `spec:create`, `spec:complete`) push, write PRs and write to the tracker, and the owner approves each write when Claude Code asks. `spec:create` proposes these rules for the project's shared `.claude/settings.json`; they ask, never deny, so attended work still runs:

```json
{
  "permissions": {
    "ask": [
      "Bash(git push:*)",
      "Bash(git tag:*)",
      "Bash(gh pr create:*)",
      "Bash(gh pr merge:*)",
      "Bash(gh pr comment:*)",
      "Bash(gh pr review:*)",
      "Bash(gh pr edit:*)",
      "Bash(gh pr close:*)",
      "Bash(gh pr reopen:*)",
      "Bash(gh pr ready:*)",
      "Bash(gh issue create:*)",
      "Bash(gh issue edit:*)",
      "Bash(gh issue close:*)",
      "Bash(gh issue comment:*)",
      "Bash(gh issue reopen:*)",
      "Bash(gh issue delete:*)",
      "Bash(gh issue transfer:*)",
      "Bash(gh api -X*)",
      "Bash(gh api * -X*)",
      "Bash(gh api -f*)",
      "Bash(gh api * -f*)",
      "Bash(gh api -F*)",
      "Bash(gh api * -F*)",
      "Bash(gh api --method*)",
      "Bash(gh api * --method*)",
      "Bash(gh api --field*)",
      "Bash(gh api * --field*)",
      "Bash(gh api --raw-field*)",
      "Bash(gh api * --raw-field*)",
      "Bash(gh api --input*)",
      "Bash(gh api * --input*)",
      "Bash(gh project close:*)",
      "Bash(gh project copy:*)",
      "Bash(gh project create:*)",
      "Bash(gh project delete:*)",
      "Bash(gh project edit:*)",
      "Bash(gh project field-create:*)",
      "Bash(gh project field-delete:*)",
      "Bash(gh project item-add:*)",
      "Bash(gh project item-archive:*)",
      "Bash(gh project item-create:*)",
      "Bash(gh project item-delete:*)",
      "Bash(gh project item-edit:*)",
      "Bash(gh project link:*)",
      "Bash(gh project mark-template:*)",
      "Bash(gh project unlink:*)",
      "Bash(gh release:*)",
      "Bash(*guard.pyz* decide *)",
      "Bash(*ticket_guard* decide *)",
      "Bash(*runtime* decide *)"
    ]
  }
}
```

Add the tracker MCP server's write tools (the same names as `goal.deny`). Never put `AskUserQuestion` or the goal deny rules in shared settings: a deny there would break Feature Forge interviews and every attended command.

## Judging a run

Judge every run by its final message, never by its exit status. A headless goal run can exit `success` after the Stop-hook block cap with the goal unmet. The final message either shows each `<done_when>` check with its output, or starts with `BLOCKED:` and names a stop.

## Blocked rows left uncommitted

`guard block` commits the Blocked row on its own, as `docs(<spec-name>): record Blocked rows in the plan`, once no ticket holds the marker, so the row never lands in another ticket's commit. It leaves the row uncommitted only when another ticket is in progress or other files are dirty. A whole-spec run commits what's left in its `<final_report>` step with `guard commit-plan <spec-name>`. When a run ended before that step, `spec:review` runs the same command first. The batch runner does it after its last batch.
