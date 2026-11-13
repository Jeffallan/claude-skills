---
name: synthesize
description: Consolidate a discovery topic's research into findings, blocking decisions and proposed tickets
argument-hint: "<topic>"
---

# Discovery Synthesize

Consolidate the research for one discovery topic into `synthesis.md`: what was learned, the decisions it leaves, and the tickets it proposes. Run it only when `discovery:create` routed items to research and the findings are in.

## Input

`$ARGUMENTS` is a topic name. Find `<specsRoot>/todo/discovery/<topic>/` (read `specsRoot` from `.claude/workflow-config.json`, default `docs/specs`). Refuse when the folder or its `discovery.md` is missing, and suggest `discovery:create`.

## Step 1: Read the sources

Read `discovery.md`, every Feature Forge file in the folder, and everything in `sources/`. When `sources/` is empty, stop: there is nothing to synthesize yet. List each source with a one-line summary and ask the owner whether any are missing.

## Step 2: Analyze across sources

Spawn one read-only subagent per source group when there are more than five sources; otherwise work in this session. Brief:

```
Read <sources>. For each open question in discovery.md (Q1, Q2, ...), return what these sources say, quoting the line and file that supports it, and whether it answers the question, contradicts another source, or leaves it open.
Do not write files. End your report with the skills you loaded.
```

From the results, sort each open question into answered, contradicted (sources disagree) or still open. Every finding cites its source file.

## Step 3: Write `synthesis.md`

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

Number new proposed tickets after the last one in `discovery.md`, so `discovery:approve` reads both files without clashes. Research may also drop or change tickets `discovery.md` proposed; say so under that ticket in `discovery.md` and mark it "Replaced by P<n>" or "Dropped: <reason>".

When research says not to build anything, write that in the Summary and leave Proposed tickets empty. `discovery:approve` then closes the topic with no tickets.

## Step 4: Hand off

Set `discovery.md`'s status to "Ready for approval", show the owner `synthesis.md`, and point to `discovery:approve <topic>`. Write nothing to the tracker.
