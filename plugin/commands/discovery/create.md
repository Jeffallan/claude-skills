---
name: create
description: Turn a feature set, requirement, build request or unclear ticket into a discovery topic with proposed tickets
argument-hint: "<topic-or-ticket>"
---

# Discovery Create

Turn what the owner wants built into a discovery topic: a feature list, the open questions, and proposed tickets that reflect the existing code. Use it when there are no tickets yet, or when `spec:triage` sent a ticket back because it has real unknowns. Tickets that are already clear skip discovery and go straight to `spec:triage`.

## Input

`$ARGUMENTS` is one of:

- A feature set, business requirements or a build request, as text or as paths to local files (notes, PDFs, exported pages).
- An existing ticket ID with real unknowns. Read it through the tracker adapter's `read` operation; this command may refine or replace it, and the result returns through `spec:triage`.

When `$ARGUMENTS` is empty, ask the owner what they want built.

## Before you start

1. Read `.claude/workflow-config.json`. When it is missing, run the config wizard in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md`.
2. Read `${CLAUDE_PLUGIN_ROOT}/references/specs/layout.md` for the folder layout and naming rules.
3. Pick a kebab-case topic name from the input and confirm it with the owner. The topic folder is `<specsRoot>/todo/discovery/<topic>/`. Refuse a name that already exists under `todo/` or `completed/` unless the owner wants to continue that topic.

## Step 1: Split the input into items

List each feature or requirement as one item: a short title, one sentence on what it does for the user, and the input it came from. Merge duplicates. Show the list and let the owner add, drop or split items.

## Step 2: Read the existing code

Start one `fullstack-dev-skills:code-reader` agent with this brief:

```
Use the fullstack-dev-skills:spec-miner skill to check how this codebase already handles the items below.
Items: <the item list>
For each item return: existing code that does part of it (paths), helpers or patterns to reuse, and constraints the code imposes. Keep it to what you can cite with a path.
Do not write files or change the tracker. End your report with the skills you loaded.
```

With more than ten items, split them across several such agents and start them all in one message so they run together. This is a light pass, so proposed tickets don't duplicate or contradict existing code. Architecture, security and API analysis wait for `spec:create`.

## Step 3: Route each item

| Item | Route |
|------|-------|
| Clear: you can write acceptance criteria without guessing | Propose tickets now |
| Vague: the owner can answer what is missing | Run Feature Forge, then propose tickets |
| Real unknowns: nobody can answer yet without research (user interviews, a spike, vendor terms) | Research route: list the questions, then `discovery:approve`, which synthesizes the research first |

Show the routing and let the owner move items between routes.

**Feature Forge.** For each vague item, invoke the `fullstack-dev-skills:feature-forge` skill in this session, with the spec-miner findings for that item as context. Tell it to save its specification to `<specsRoot>/todo/discovery/<topic>/<feature>.md` (kebab-case feature name), not to its default `specs/` folder. Every interview question offers "Needs additional discovery"; items the owner flags that way move to the research route.

When a goal is active, skip the interviews: record each vague item's open questions in `discovery.md` and tell the owner to rerun attended. When `AskUserQuestion` is unavailable and no goal is active, take the wrong-session stop in `${CLAUDE_PLUGIN_ROOT}/references/specs/unattended.md` before the interviews.

## Step 4: Write `discovery.md`

Write `<specsRoot>/todo/discovery/<topic>/discovery.md`:

```markdown
# <Topic title>

**Topic:** <topic>
**Status:** Proposed | Research | Ready for approval | Tickets created
**Input:** <what the owner gave, with paths or ticket IDs>

## Features

| # | Item | Route | Feature Forge file |
|---|------|-------|--------------------|
| F1 | <title> | Clear / Feature Forge / Research | <feature>.md or - |

## Existing code

<spec-miner findings per item: reuse and constraints, with paths>

## Open questions

| # | Question | Item | How to answer | Who |
|---|----------|------|---------------|-----|
| Q1 | <question> | F2 | Interview / Spike / Owner decision | <role> |

## Blocking decisions

| # | Decision | Options | Recommendation | Blocks |
|---|----------|---------|----------------|--------|
| D1 | <decision> | A) ..., B) ... | <option and why> | P2, P3 |

## Proposed tickets

| # | Title | Item | Depends on | Blocked by decisions |
|---|-------|------|------------|----------------------|
| P1 | <title> | F1 | - | - |

### P1: <title>

<What to build in plain terms, the reuse it should follow, and the files it likely touches.>

**Acceptance criteria:**
- [ ] <observable result>
```

Only clear and Feature Forge items get proposed tickets now. Research items get open questions; their tickets come from the synthesis `discovery:approve` runs.

**Research route.** Create `<specsRoot>/todo/discovery/<topic>/sources/`. Agents can take spikes and competitive research when the owner asks; list the rest (interviews, vendor calls) for the owner. Results go in `sources/` as markdown.

## Step 5: Hand off

Show the owner the file. Then tell them the next step:

- Research items remain: gather findings in `sources/`, then run `discovery:approve <topic>`, which synthesizes them before approval.
- No research: run `discovery:approve <topic>` to create the tickets.

Commit `discovery.md`, any Feature Forge files and `sources/` on a small branch of their own when the owner asks; topics reach the default branch through their own PR. Write nothing to the tracker: only `discovery:approve` creates tickets.

## Rules

- Never take a group key or offer to create a group. Grouping happens only in `spec:triage`.
- Links use names, never paths: a ticket says `Discovery: <topic>`.
- Subagents read and return text; only this session writes files.

[Documentation](https://jeffallan.github.io/claude-skills/workflows/discovery-create/)
