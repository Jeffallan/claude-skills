---
name: approve
description: Synthesize a discovery topic's research when it has some, resolve its blocking decisions and create its approved tickets in the configured tracker
argument-hint: "<topic> [--decision=<id>:<value>...]"
---

# Discovery Approve

The one approval gate between discovery and the tracker, on both discovery paths. When the topic has research and no synthesis yet, it synthesizes first. It then resolves blocking decisions, lets the owner edit the proposed tickets, creates the approved ones through the tracker adapter, and points to `spec:triage`. It never creates a group, spec or branch: `spec:triage` groups the new tickets.


`guard <command>` below means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`, the ticket guard bundled with this plugin. Type it out each time, or define a shell function (`guard() { uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" "$@"; }`); a variable holding the command fails in zsh, which doesn't split it into words.

## Unattended guard

This command is attended only. When a goal is active, write nothing: print the proposed tickets and unresolved decisions (and, when Step 0 would run, what the sources say) as a read-only proposal and end with `BLOCKED: discovery:approve needs the owner`. When `AskUserQuestion` is unavailable and no goal is active, take the wrong-session stop in `${CLAUDE_PLUGIN_ROOT}/references/specs/unattended.md`.

## Input

`$ARGUMENTS`: a topic name, then optional `--decision=<id>:<value>` pairs (for example `--decision=D1:B`) that answer blocking decisions in advance.

1. Read `.claude/workflow-config.json`; when it is missing, run the config wizard in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`.
2. Load the adapter file for the configured tracker, listed in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`.
3. Find `<specsRoot>/todo/discovery/<topic>/`. Read `discovery.md`, then `synthesis.md` when it exists. Proposed tickets come from both files, minus those marked "Replaced" or "Dropped".
4. When `discovery.md` lists research items and `synthesis.md` is missing, run Step 0 first.

## Step 0: Synthesize research

Runs only when `discovery.md` routed items to research (`sources/` holds files) and `synthesis.md` doesn't exist yet. Otherwise go to Step 1.

### Read the sources

Read `discovery.md`, every Feature Forge file in the folder, and everything in `sources/`. List each source with a one-line summary and ask the owner whether any are missing. When `sources/` is empty but `discovery.md` lists research items, stop: the research isn't in yet, so there is nothing to approve. Tell the owner to add it under `sources/` and rerun.

### Analyze across sources

Start one `fullstack-dev-skills:code-reader` agent per source group when there are more than five sources; otherwise work in this session. Brief:

```
Read <sources>. For each open question in discovery.md (Q1, Q2, ...), return what these sources say, quoting the line and file that supports it, and whether it answers the question, contradicts another source, or leaves it open.
Do not write files. End your report with the skills you loaded.
```

From the results, sort each open question into answered, contradicted (sources disagree) or still open. Every finding cites its source file.

### Write `synthesis.md`

Write `<specsRoot>/todo/discovery/<topic>/synthesis.md`:

```markdown
# <Topic title>: synthesis

**Topic:** <topic>
**Status:** Ready for approval
**Sources:** <count>, listed in Source index

## Summary

<Three to five sentences: what research showed and what it means for the build.>

## Findings

| # | Finding | Answers | Sources |
|---|---------|---------|---------|
| R1 | <finding> | Q1 | sources/<file>.md |

## Still open

| # | Question | Why it is still open | Effect if built anyway |
|---|----------|----------------------|------------------------|

## Blocking decisions

| # | Decision | Options | Recommendation | Blocks |
|---|----------|---------|----------------|--------|
| D1 | <decision> | A) ..., B) ... | <option, citing findings> | P4 |

## Proposed tickets

| # | Title | Item | Depends on | Blocked by decisions |
|---|-------|------|------------|----------------------|
| P4 | <title> | F3 | - | D1 |

### P4: <title>

<What to build, why the findings support it, the reuse from discovery.md's Existing code.>

**Acceptance criteria:**
- [ ] <observable result>

**From research:** <finding IDs>

## Source index

| File | What it is | Date |
|------|------------|------|
```

Number new proposed tickets after the last one in `discovery.md`, so the steps below read both files without clashes. Research may also drop or change tickets `discovery.md` proposed; say so under that ticket in `discovery.md` and mark it "Replaced by P<n>" or "Dropped: <reason>".

When research says not to build anything, write that in the Summary and leave Proposed tickets empty. Step 4 then closes the topic with no tickets.

### Show it

Set `discovery.md`'s status to "Ready for approval", commit `synthesis.md` and the topic file (`docs(<topic>): synthesize discovery research`), show the owner the summary, the decisions and the proposed tickets, and continue with Step 1.

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
