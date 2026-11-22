---
name: create
description: Plan one spec as overview, implementation plan and goal prompt on its spec branch, and print its goal launch commands
argument-hint: "<spec-name>"
---

# Spec Create

Plan one spec that `spec:triage` grouped. Write `overview.md` first, with a Readiness table that checks every ticket against the code; after the owner approves it, write `implementation-plan.md` and `goal-prompt.md`, commit all three on the spec branch, and print the two launch commands. Rerunning picks up at the plan when an approved `overview.md` already exists, so plans can be regenerated.

## Unattended guard

Attended only. Read `${CLAUDE_PLUGIN_ROOT}/references/specs/unattended.md`. When a goal is active, write nothing: print the proposed overview and end with `BLOCKED: spec:create needs the owner's approval`. When `AskUserQuestion` is unavailable and no goal is active, take that file's wrong-session stop.

## Setup

`guard <command>` below means `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" <command>`, the ticket guard bundled with this plugin. Type it out each time, or define a shell function (`guard() { uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" "$@"; }`); a variable holding the command fails in zsh, which doesn't split it into words.

1. Read `.claude/workflow-config.json` (the config wizard in `${CLAUDE_PLUGIN_ROOT}/references/adapters/operations.md` runs when it is missing) and load the tracker's adapter file.
2. Read `${CLAUDE_PLUGIN_ROOT}/references/specs/layout.md` and `<specsRoot>/INDEX.md`. Earlier specs and topics with the same feature areas are context for this one.
3. Read the group's `After:` line. When the predecessor has not merged into the default branch, refuse and name it, unless the owner overrides.
4. Check out `spec/<spec-name>` (made by `spec:triage`; when missing, send the owner back to triage). The working tree must be clean. When the predecessor has merged, rebase onto the current default branch first: `git fetch origin && git rebase origin/<default-branch>`.
5. List the spec's tickets with `list-spec-tickets` and `read` each one.

## Step 1: Codebase analysis

Start `fullstack-dev-skills:code-reader` agents with this brief shape:

```
Use the fullstack-dev-skills:<skill> skill to <task>.
Read: the tickets below and the code under <paths>.
Return: <exact format>. Do not write files or change the tracker.
End your report with the skills you loaded.
```

| Subagent | When | Task |
|----------|------|------|
| `spec-miner` | Always | Map affected code, patterns and test conventions; inventory reusable utilities, components and shared modules (Reuse); list debt in the touched files (Debt in scope) |
| `architecture-designer` | The spec changes system structure | Design constraints and integration points |
| `security-reviewer` | It touches auth or sensitive data | Security requirements |
| `api-designer` | It touches routes, schemas, public interfaces or third-party integrations | API design constraints |
| `code-documenter` | The docs root (`docsRoot`, default `docs`) holds docs outside the specs root | Per ticket, the docs it will affect: each doc citing a symbol the ticket changes (`` `path::symbol` ``), plus the docs those name in their `related:` frontmatter, one hop. Return the doc paths with the cited symbol or link that puts each on the list |

They only read: start every subagent the table calls for in one message so they run together. Rerun a subagent whose report doesn't list the skill it was told to load.

## Step 2: Readiness

Check every ticket against the code before planning it, and sort it:

| Readiness | When | Evidence column |
|-----------|------|-----------------|
| Ready | Acceptance criteria can be written and nothing blocks it | Why it can be planned now |
| Blocked: question | Someone must answer something first | The exact question and who can answer |
| Blocked: decision | The owner must choose between options | The decision and its options |
| Blocked: needs-spec | The ticket lacks what's needed to plan it | What is missing |
| Already done | The code already does it | Commit SHA and the check: `git log --grep "<id or key phrase>"`, `git grep "<symbol>"`, `git merge-base --is-ancestor <sha> HEAD` |

Already done needs commit evidence from these checks, never the ticket's status.

**Open questions.** For Blocked: question and Blocked: decision tickets the owner can answer now, invoke the `fullstack-dev-skills:feature-forge` skill in this session for the interview, saving its output to `<specsRoot>/todo/discovery/<topic>/<feature>.md` when the ticket has a discovery topic. Answered tickets become Ready. Unknowns that need research go to `discovery:create`.

## Step 3: Overview

Write `<specsRoot>/todo/<spec-name>/overview.md` from `${CLAUDE_PLUGIN_ROOT}/references/specs/templates/overview.md`: the four header lines (copy `After:` from the group; `Discovery:` from the tickets' `Discovery:` lines), the Readiness table first, then purpose, scope, success criteria, design, Reuse, Debt in scope, risks and linked tickets.

Run `guard spec-index` so `INDEX.md` lists the spec.

Show the overview. Offer an optional challenge pass with the `fullstack-dev-skills:the-fool` skill in this session. Ask the owner to approve, edit or stop. Nothing after this step runs before approval. On approval, set the overview's `**Status:**` line to `Approved <date>`.

## Step 4: Plan

After approval, start `fullstack-dev-skills:code-reader` agents per Ready ticket, all of them in one message so they run together (they only read), and fold their output into the plan:

| Subagent | Task | Skill |
|----------|------|-------|
| One per Ready ticket | Steps, files, acceptance criteria, naming what it reuses or extracts from the Reuse section | The ticket's stack skill, chosen from the ticket, the files it touches and the repo's manifests |
| One per Ready ticket | The failing tests to write first (the RED check), importing the symbol under test inside the test body. Assert the specific error (type or message), never a bare throw; cover each boundary the acceptance criteria name; after an expected throw, check the state is unchanged | `test-master` |
| One | Execution order, dependencies and risks (one ticket at a time, no waves) | None fits; the brief says so |

Write `<specsRoot>/todo/<spec-name>/implementation-plan.md` from `${CLAUDE_PLUGIN_ROOT}/references/specs/templates/implementation-plan.md`. Only Ready tickets get Completion Status rows, Execution Order rows and sections. Each section has a `Skill:` line naming up to two existing skills (or `none`), a `Docs:` line from the `code-documenter` report (or `none`), a `Type:` and a RED line. Where an owner decision changed what a ticket's text asks for, restate the decided acceptance criteria in its plan section.

Run `setup` from `.claude/workflow-config.json` first when the checkout lacks what it installs, then run every check command the plan names once before writing it in. A RED command must fail for the reason the ticket expects, never a collection, import or environment error; any other check must at least start. Rewrite a check that can't run in this repo (a missing package setup, a wrong path) before the plan goes to the goal run. Gated tracker changes (create, split, close, transition, membership, labels) go in Proposed tracker changes.

## Step 5: Planning writes

Attended only, each raising the shared "ask" prompt, with no separate approval step:

- `link` related tickets the plan connects
- `comment` on each Ready ticket naming the spec files (`Spec: <spec-name>`, files by name)
- `update` each Ready ticket by appending an "Implementation plan" section; never rewrite existing text
- `update` story points where the field exists

Make these writes before the plan commit. With the text tracker they edit ticket files, so they go in the same commit as the spec files; made after it, they would land inside the goal run's commit range or leave the tree dirty. Keep any trailing line the ticket convention requires last (for example `Spec: <spec-name>`), inserting the new text above it.

Everything else waits in Proposed tracker changes for the owner, or for `spec:complete`.

## Step 6: Goal prompt and commit

1. When `.claude/settings.json` lacks the shared "ask" rules from `${CLAUDE_PLUGIN_ROOT}/references/specs/launch.md`, propose them, so attended commands prompt before pushes, PR writes, tracker writes and self-scheduling (`ScheduleWakeup`, `CronCreate`, `RemoteTrigger`). On the owner's yes they go in the plan commit.
2. Write `<specsRoot>/todo/<spec-name>/goal-prompt.md` from `${CLAUDE_PLUGIN_ROOT}/references/specs/templates/goal-prompt.md`: the Ready tickets in Execution Order, the verification commands (each one a ticket in this run creates marked `(needs <ticket> Done)`), the run's limits, the spec-wide stops and the settled decisions. Copy every owner decision from this session (Readiness answers, Feature Forge answers, accepted challenge-pass mitigations) into `<decisions_already_made>`: a run reads the ticket text literally and would otherwise block on a contradiction the owner already settled. Use the `fullstack-dev-skills:prompt-engineer` skill for the wording.
3. Commit the three files, `INDEX.md`, any approved `.claude/settings.json` change and any ticket-file edits from Step 5 on the spec branch in one commit: `docs(<spec-name>): plan the spec`. That commit is the run's start SHA: the goal prompt resolves it with `git log -1 --format=%h -- <path to goal-prompt.md>`, so `<done_when>` never counts this commit or any earlier one.

## Step 7: Launch commands and permission rules

Print, filled in from `${CLAUDE_PLUGIN_ROOT}/references/specs/launch.md`:

- **Whole spec:** one goal run across compactions.
- **Next batch:** the next `goal.batchSize` (3) tickets that are neither Done nor Blocked; or `guard run-batches <spec-name>` headless, printed with the full `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz"` path so the owner can paste it into a shell.

Both carry the full writes-only deny set, `--permission-mode` and `goal.deny`. Never put the goal deny rules in the shared settings.

Tell the owner to start attended follow-up work (`spec:review` triage, `spec:complete`) in a fresh session without the goal flags, since `/goal clear` keeps the session's denies.

After the plan commit, the spec branch takes no commit before the run: the start SHA is the last commit touching `goal-prompt.md`, and any later commit would fall inside the run's range.

## Rules

- Subagents read and return text; only this session writes files and changes the tracker.
- No tracker write outside Step 5 and no status change.
- Links by name, never by path.
