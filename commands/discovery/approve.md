---
name: approve
description: Resolve a discovery topic's blocking decisions and create its approved tickets in the configured tracker
argument-hint: "<topic> [--decision=<id>:<value>...]"
---

# Discovery Approve

The one approval gate between discovery and the tracker, on both discovery paths. It resolves blocking decisions, lets the owner edit the proposed tickets, creates the approved ones through the tracker adapter, and points to `spec:triage`. It never creates a group, spec or branch: `spec:triage` groups the new tickets.


`guard <command>` below means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`, the ticket guard bundled with this plugin.

## Unattended guard

This command is attended only. When a goal is active, write nothing: print the proposed tickets and unresolved decisions as a read-only proposal and end with `BLOCKED: discovery:approve needs the owner`. When `AskUserQuestion` is unavailable and no goal is active, take the wrong-session stop in `${CLAUDE_PLUGIN_ROOT}/references/specs/unattended.md`.

## Input

`$ARGUMENTS`: a topic name, then optional `--decision=<id>:<value>` pairs (for example `--decision=D1:B`) that answer blocking decisions in advance.

1. Read `.claude/workflow-config.json`; when it is missing, run the config wizard in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`.
2. Load the adapter file for the configured tracker, listed in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`.
3. Find `<specsRoot>/todo/discovery/<topic>/`. Read `discovery.md`, then `synthesis.md` when it exists. Proposed tickets come from both files, minus those marked "Replaced" or "Dropped".
4. Refuse when `discovery.md` lists research items and `synthesis.md` is missing; suggest `discovery:synthesize <topic>`.

## Step 1: Resolve blocking decisions

Apply the `--decision` pairs, refusing any ID or option that doesn't exist. For each decision still open, ask the owner with `AskUserQuestion`, one decision at a time: the options as choices, the recommendation first and marked "(Recommended)", and the tickets it blocks in the question text. Record each answer in the topic file's Blocking decisions table (chosen option, date). Update or drop the tickets an answer changes, and show what changed.

## Step 2: Review the tickets

Show the proposed tickets as a table (ID, title, depends on, acceptance criteria count). Ask the owner to approve all, edit, or drop tickets. Apply edits to the topic file before creating anything, so the file and the tracker agree.

When every ticket is dropped, or there were none, go to Step 4's "no tickets" path.

## Step 3: Create the tickets

For each approved ticket, in dependency order, call the adapter's `create` operation (see `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`) with no group. The body is:

```markdown
<What to build>

**Acceptance criteria:**
- [ ] <criterion>

**Notes from discovery:** <findings and decisions that shaped it, by ID>

Discovery: <topic>
```

Each write raises the shared "ask" permission prompt; the owner approves it. Record the returned ticket ID next to the proposed ticket in the topic file ("Created as <ID>"). When a create fails, stop, report which tickets exist, and leave the rest for a rerun; a rerun skips tickets that already show "Created as".

Never call `ensure-group` or `link`, and never write a `Spec:` line. Grouping belongs to `spec:triage`.

## Step 4: Close out the topic

- **Tickets created:** set the topic status to "Tickets created" and list the IDs. The topic stays in `todo/`; `spec:complete` moves it to `completed/` when the last spec linked to it finishes.
- **No tickets** (research said don't build it, or every ticket was dropped): record why in the topic file, then move the topic and refresh the index in one commit:

  ```bash
  mkdir -p <specsRoot>/completed/discovery
  git mv <specsRoot>/todo/discovery/<topic> <specsRoot>/completed/discovery/<topic>
  guard spec-index
  git add <specsRoot>/INDEX.md
  git commit -m "docs(<topic>): close discovery topic with no tickets"
  ```

Commit the topic file changes on the topic's own branch when it has one. Never commit to the default branch directly.

## Output

```markdown
## Discovery approved: <topic>

### Decisions
| ID | Decision | Chosen |

### Tickets created
| Proposed | Ticket | Title |

### Next step
Run `spec:triage discovery:<topic>` to group these tickets into specs.
```

## Rules

- No group keys and no group fallbacks: a ticket leaves this command ungrouped.
- Links by name: `Discovery: <topic>`, never a path.
- The tracker is written only in Step 3, and only after the owner approves the tickets.
