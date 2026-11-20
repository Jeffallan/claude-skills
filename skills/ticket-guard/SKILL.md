---
name: ticket-guard
description: Guards one workflow ticket with marker-scoped hooks that freeze its RED tests, re-run GREEN before a goal-mode stop, and restore the ticket's context after compaction. Use when ticket:execute starts or resumes a ticket, or when a session must pick a ticket back up after compaction.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  company: https://synergetic.solutions
  version: "1.0.0"
  domain: workflow
  triggers: ticket guard, ticket marker, RED evidence, GREEN evidence, test freeze, goal run, compaction recovery
  role: engineer
  scope: testing
  output-format: report
  related-skills: test-master, debugging-wizard
---

# Ticket Guard

**Ticket rules, kept through compaction:**

1. RED first: the failing test and its `guard run red` record come before any implementation edit. A collection or import error is not RED.
2. After RED the test files are frozen. Never edit, delete, skip or weaken them to get a pass.
3. Under unattended rules: never call `AskUserQuestion`, never write to the tracker, never push. A stuck ticket goes through `guard block <ticket> "<reason>"`; its dependents get `"depends on <ticket>"`.
4. `BLOCKED:` ends a turn only for a spec-wide stop named in the goal prompt's `<stops>`.
5. After a compaction, re-read the spec's `goal-prompt.md` (goal runs) and rebuild state from the Completion Status table and `git log`, then continue at the step the session-start hook names.

## Role Definition

You are the guard for one ticket of a spec workflow. `ticket:execute` invokes this skill after `guard marker start` so the ticket rules above stay in context. The guard hooks ship in the plugin's `hooks/hooks.json`: they run on every edit, every stop and every compaction in every session, a resumed one included, and do nothing without a marker or for another session's marker. The work itself stays in `ticket:execute` and `ticket:complete`.

## When to Use This Skill

- `ticket:execute` has started or resumed a ticket and needs the hooks registered.
- A session resumed or compacted mid-ticket and must pick the ticket back up.
- You need to know what a guard hook did, or why it denied an edit or blocked a stop.

## Core Workflow

1. **Check the marker.** Run `guard marker status`; `guard <command>` means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>` (typed out or as a shell function, never a variable, which zsh doesn't split), and spec files and goal prompts write it that way. No marker means no ticket is in progress: say so and stop.
2. **Load the ticket.** Read the ticket's section of the spec's `implementation-plan.md` and the mode the marker records (`goal` or `attended`).
3. **Follow the ticket rules above** for the rest of the ticket. The hooks enforce the freeze and the GREEN re-run; the rules cover what they can't see.
4. **Record evidence through the runtime only:** `guard run red` and `guard run green`, never hand-written results.
5. **Hand off to `ticket:complete`,** which runs the boundary checks, commits and clears the marker. Never clear the marker yourself.

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Hooks and guard commands | `references/hooks-and-commands.md` | A hook denied or blocked something, or you need a guard command's behavior |

## Constraints

### MUST DO
- Keep every edit in the main session; subagents only read
- Leave the marker in place until `ticket:complete` clears it
- Report a hook denial in your next message, with the file and the rule
- In goal mode, block a ticket the Stop hook keeps failing instead of looping
- Update every doc `guard docs-affected` lists, or record it with `guard docs-checked` and the reason, before handing off

### MUST NOT DO
- Delete, move or edit `marker.json`, the evidence record or `decisions.jsonl`
- Run `guard decide`, or pass `--reason` or `--accept-lost-marker` under unattended rules
- Edit files under `text.ticketsDir` in goal mode
- Treat the hooks as the only check: `ticket:complete` re-runs everything in a clean worktree

## Output Templates

After a compaction, before continuing:

```markdown
Resuming <ticket> (<mode>) on <branch>, started at <start SHA>.
Evidence so far: RED <yes/no>, GREEN <yes/no>.
Next step: <the step the session-start hook named>.
```

## Knowledge Reference

Claude Code hooks (PreToolUse and Stop in skill frontmatter, SessionStart with the `compact` source in the plugin's hooks.json), the bundled guard runtime, `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz"` (marker, evidence JSONL, RED and GREEN records, test freeze, Stop-hook GREEN re-run, block, summary), goal runs and `/goal` evaluator behavior.

Maintained by [@jeffallan](https://github.com/jeffallan), Principal Consultant at [Synergetic Solutions](https://synergetic.solutions)

[Documentation](https://jeffallan.github.io/claude-skills/skills/workflow/ticket-guard/)
