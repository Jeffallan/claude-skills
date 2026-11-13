---
name: triage
description: Group open tickets into specs, create each spec's tracker group and branch after approval
argument-hint: "[ticket-ids | tracker-query | discovery:<topic>]"
---

# Spec Triage

Group open tickets into specs. After the owner approves, create or find each spec's tracker group, link its tickets, append a `Spec: <spec-name>` line to each, record the build order, and cut one `spec/<spec-name>` branch per spec from the default branch. This is the only command that forms new groups. It never changes a ticket's status, closes a ticket, or creates, comments on or reopens one.

## Unattended guard

Attended only. Read `${CLAUDE_PLUGIN_ROOT}/references/specs/unattended.md`. When a goal is active or `AskUserQuestion` is unavailable, make no tracker write, branch or file edit: print the proposal read-only and end with `BLOCKED: spec:triage needs the owner's approval`.

## Setup

1. Read `.claude/workflow-config.json`. When it is missing, run the config wizard in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`. When the configured tracker's block is incomplete, name the missing key and stop.
2. Load the tracker's adapter file (listed in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`). Every tracker call below goes through its operations.
3. Read `${CLAUDE_PLUGIN_ROOT}/references/specs/layout.md` and `<specsRoot>/INDEX.md`.

## Step 1: Read the scope

`$ARGUMENTS` is one optional free-form argument. Work out which it is:

| Argument | Scope |
|----------|-------|
| Ticket IDs | Those tickets |
| A tracker query | The tickets it returns |
| `discovery:<topic>` | Tickets whose body says `Discovery: <topic>` |
| A grouping ("A, B and C together; D alone") | Those tickets, grouped as given |
| Nothing | Open ungrouped tickets: `list-ungrouped`, or all open tickets minus those already in a group |

For Jira and Linear, every list applies the `repoScope` filter, so only this repo's tickets are read. GitHub tickets carry their repo, and text tickets live in it. Read each ticket with `read`. For large sets, spawn read-only subagents that summarize tickets and return text.

With no tickets in scope, say so, suggest `discovery:create`, and stop without writing.

## Step 2: Sort out what can't be grouped

| Ticket | Handling |
|--------|----------|
| Closed or done | Excluded and listed |
| In another repo (a Project spanning repos, cross-repo work) | Excluded. A ticket spanning repos: propose splitting it, one ticket per repo, through `discovery:create` or the owner |
| Real unknowns (nobody can write acceptance criteria yet) | Left ungrouped; suggest `discovery:create <ticket>` |
| Already in a spec that hasn't started | Shown under that spec; moving it needs its own named approval |
| Already in a started spec (any Completion Status row past Pending, read from the plan on the `spec/<spec-name>` branch) | Refused: changes to a started spec go through `spec:create`. Say why |
| Released (a Released line after its last `Spec:` line, see `references/adapters/operations.md`) | Eligible like an ungrouped ticket; show the old spec and the reason |
| Open, in a spec that sits in `completed/`, not released (left by an older `spec:complete`) | Propose releasing it as `spec:complete` Step 7 does (`unlink`, then the Released line), in the same proposal; eligible once approved |
| GitHub ticket with a parent issue | Attached only when the owner approves `replace_parent` by name |
| Group set but no `Spec:` line, or the reverse | Reported, with the fix in the same proposal |
| Grouped under a name that isn't a spec name (an old release group) | Reported; treated as ungrouped only if the owner says so |

Flag, never close or skip: no update in `triage.staleDays` (30) days; files the ticket names that no longer exist (`git ls-files`); a merged PR or a completed spec that already mentions it (`gh pr list --state merged --search <id>`, `git grep <id> <specsRoot>/completed`).

## Step 3: Propose specs

A grouping the owner passed in the argument outranks every signal. Otherwise group by these signals, strongest first, and state the signals behind every grouping:

1. Explicit tracker links: grouping links (a parent issue or an existing group) and dependency links (blocks, relates)
2. A shared discovery topic
3. Shared labels or components
4. Shared files or feature areas, from `INDEX.md` plus a light read of the code
5. Wording

Rules:

- **One repo per spec.** Refuse a group that would mix repos; propose one spec per repo.
- **Names** are kebab-case (lowercase letters, numbers, hyphens), used unchanged for the folder, the branch suffix and the group title. Refuse a name already used in `todo/`, `completed/` or the tracker for a different set of tickets.
- **Size:** above `triage.warnAboveTickets` (10) tickets, warn and suggest a split; allow it if the owner keeps it. A spec should fit one goal run.
- **Build order:** with several specs, propose an order. Each later spec gets `After: <spec-name>` naming its predecessor, plus a blocked-by link where the tracker has one.

## Step 4: Approval

Show, before any write:

- How you read the argument.
- Each spec: name, tickets (ID and title), the signals behind it, and its `After:` predecessor.
- Flags and exclusions with reasons, and the size warnings.
- The exact writes per spec: `ensure-group`, each `link`, each `update` appending `Spec: <spec-name>`, `link-groups`, and the branch `spec/<spec-name>`.

Ask with `AskUserQuestion`: approve, edit (rename, move, drop, split, merge, reorder) or cancel. Edits return to this step. Moves out of an unstarted spec and `replace_parent` each need their own yes.

## Step 5: Write

On approval, per spec in build order. Each tracker write raises the shared "ask" permission prompt.

1. `ensure-group <spec-name>`: exact name match; when two groups share it, stop and name both.
2. `link` each ticket to the group, skipping tickets already linked to it, so a rerun is idempotent.
3. `update` each ticket: append `Spec: <spec-name>` when the body doesn't already have it. Never write a path, and never change any other text.
4. `link-groups` for `After:`, best effort; report when the tracker doesn't support it. With the text adapter, `After:` lives where the instructions say, else only in the spec's future `overview.md`.
5. GitHub Projects: add the spec issue and each ticket to the configured Project.
6. Cut the branch from the default branch, never from the current branch, and push nothing:

   ```bash
   git fetch origin <default-branch> 2>/dev/null; git branch spec/<spec-name> origin/<default-branch> || git branch spec/<spec-name> <default-branch>
   ```

7. Text adapter: check out the spec branch, commit the ticket-file edits there (`docs(<spec-name>): group tickets into spec`, with a `Ticket:` trailer per ticket), then return to the original branch. Local only, no push.

When a write fails, stop and report what was written and what wasn't. A rerun with the same input finishes the rest and duplicates nothing.

Write no triage record file: the group, the `Spec:` lines and the branch are the record.

## Report

```markdown
## Triage: <n> specs

| Order | Spec | Branch | Tickets | After | Group |
|-------|------|--------|---------|-------|-------|

### Writes
| Spec | Operation | Ticket | Tracker reference | Result |

### Left out
| Ticket | Reason |

### Flags
| Ticket | Flag |

### Next
- `spec:create <spec-name>` for each spec, in build order
```
