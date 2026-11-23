# Workflow Commands Reference

The workflow commands take a group of tickets from your tracker to a reviewed, merged pull request. Specs live as markdown next to your code. Tickets stay in Jira, GitHub Issues, GitHub Projects, Linear or text files in the repo, and each tracker is reached through its own adapter.

---

## Table of Contents

- [How the workflow fits together](#how-the-workflow-fits-together)
- [Before you start](#before-you-start)
- [Intake](#intake)
- [Discovery](#discovery)
- [Specs](#specs)
- [Tickets](#tickets)
- [Review and completion](#review-and-completion)
- [Current state and assumptions](#current-state-and-assumptions)
- [Agents](#agents)
- [Goal runs](#goal-runs)
- [What each command writes](#what-each-command-writes)
- [Command reference](#command-reference)

---

## How the workflow fits together

There are two ways in.

- **You already have tickets.** Start at `spec:triage`, which groups them into specs.
- **You have an idea, a feature list or a ticket nobody can plan yet.** Start at `discovery:create`, which turns it into tickets you approve before they reach the tracker.

```
discovery:create ─► discovery:approve (synthesizes research first, when there is some)
                                                                       │ tickets
existing tickets ──────────────────────────────────────────────────────┤
                                                                       ▼
spec:triage ─► spec:create ─► ticket:execute + ticket:complete (per ticket, often one goal run)
                                                                       │
                                     spec:complete ◄─ spec:review ◄────┘
                                           │
                                           ▼
                     spec:current ─► spec:diff ─► common-ground ─► (a conflict: back to spec:create)
```

A **spec** is a named group of tickets built on one branch, `spec/<spec-name>`, and merged in one PR. Its files sit in `docs/specs/todo/<spec-name>/` and move to `docs/specs/completed/` when the spec finishes:

| File | Holds |
|------|-------|
| `overview.md` | What the spec changes and why, with a Readiness table that checks every ticket against the code |
| `implementation-plan.md` | The Ready tickets with their steps, `Skill:` lines and RED checks, plus the Completion Status table |
| `goal-prompt.md` | What one goal run needs: tickets, order, checks, stops |
| `review/` | Metrics, reviewer findings, frozen reproductions and the rollup |

`docs/specs/INDEX.md` lists every spec. It is generated from each overview's header lines, so nobody edits it by hand.

## Before you start

- **Install the plugin** and **[uv](https://docs.astral.sh/uv/)**, which runs the guard with a suitable Python, fetching one if needed. The commands call a small runtime that ships inside the plugin, the ticket guard (`guard ...`), for evidence, hooks, the review gate and the spec index.
- **Configure the tracker.** The first attended command that needs `.claude/workflow-config.json` offers a setup wizard. It recommends a tracker only from what the repo shows (an existing config, a tickets folder, a GitHub remote), lists a connected Jira or Linear MCP server as available without recommending it, and asks one question at a time. See [Tracker Setup](TRACKER_SETUP.md) for every adapter.
- **Know which commands need you.** `discovery:approve`, `spec:triage`, `spec:create`, the triage step of `spec:review`, `spec:complete`, `common-ground` (but `--list`) and the wizard are attended. Run inside a goal, they write nothing, print what they would have done and stop with `BLOCKED:`.

## Intake

Intake runs once, when you adopt an existing codebase, before the first spec. It needs no tracker and no code host. It documents the code for agents, writes tests that pin current behavior and records every bug in `docs/intake-findings.md` instead of fixing it.

**`intake [procedure]`** is the one command. It works `docs/intake-checklist.md` from the first unchecked item, creating the checklist when it is missing. Each item is a procedure that runs in one of the plugin's agents: the agent first reports what it found and what it plans to write, you confirm or correct that scope, and then the same agent writes. In a goal run the agent does the item in one pass. While a writer runs, read-only `code-reader` agents gather facts for the next item. The command reviews the agent's diff and commits the item. Name a procedure to run or rerun just that one: `intake document-glossary`, or `intake create-system-description --full`.

- **`existing-docs`** lists the docs the project already has, maps them to the intake topics and checks their claims against the code. Wrong claims become findings; your docs are never edited.
- **`document-codebase`** adds docstrings across the code. It runs your tests before and after and checks that no executable line changed.
- **Twelve `document-*` procedures** each write one reference doc under `docs/` (data model, file tree, integrations, API, user model, features, glossary, security, authorization, user flow, configuration, analytics), and each ends with an accuracy audit. **`create-onboarding`** links them from `docs/README.md`, or from `docs/README-intake.md` when the project already has its own `docs/README.md`.
- **`testing-setup`** builds the test harness and proves each layer with a smoke test. **`testing-features`**, **`-authorization`** and **`-owasp`** then write characterization tests at the same time, each reading its matching doc, and **`-user-flows`** follows them. Together these five are the capture-behavior step.
- **`create-system-description`** writes a baseline spec into `docs/specs/completed/baseline/`, so the spec index knows the existing system, and `docs/system-description.md`. Later, `spec:complete` proposes updates to it once per spec, and `spec:current` folds in whatever is still missing.

`intake` can run in a goal run: it never asks a question there, and a checkpoint becomes a draft in the checklist note, plus an open question in the findings tracker when you could reasonably choose otherwise. [Intake](INTAKE.md) covers the checklist, the goal run and close-out.

## Discovery

Discovery is optional. Use it when there are no tickets yet, or when `spec:triage` sends a ticket back because nobody can write its acceptance criteria.

- **`discovery:create <topic-or-ticket>`** splits your input into items, reads the existing code for each one, and routes it. Clear items become proposed tickets straight away. Vague items go through a Feature Forge interview whose output is saved in the topic folder. Items with real unknowns go to research. It writes `docs/specs/todo/discovery/<topic>/discovery.md`.
- **`discovery:approve <topic>`** is the gate before anything reaches the tracker. When the topic went to research and has no `synthesis.md` yet, it first reads the topic's `sources/` and writes one, with findings that cite their sources, blocking decisions and proposed tickets. Then it walks you through the blocking decisions one at a time, lets you edit or drop tickets, then creates the rest, each with a `Discovery: <topic>` line. It never groups them; it points you to `spec:triage`. A topic that ends with no tickets moves to `completed/`.

## Specs

**`spec:triage [ticket IDs | query | discovery:<topic> | grouping]`** proposes how to group open tickets into specs, and explains each grouping by its strongest signal: tracker links, a shared discovery topic, shared labels, shared files or feature areas, then wording. A grouping you type in the argument beats every signal. It flags stale tickets without closing them, refuses to move a ticket out of a spec that has started, warns above 10 tickets per spec, and suggests a build order with `After:` lines. Every ticket you name lands in a spec: a ticket that contradicts another, the code or a settled decision stays in its group, flagged for `spec:create` to settle, and a split is only a suggestion. Once you approve, it creates or finds each spec's group in the tracker, links the tickets, appends `Spec: <spec-name>` to each one and cuts `spec/<spec-name>` from your default branch. Nothing is pushed.

**`spec:create <spec-name>`** plans one spec:

1. It refuses to start while the spec's predecessor (`After:`) hasn't merged, unless you override, and rebases the branch when it has.
2. It sends `code-reader` agents to map the code: `spec-miner` always; `architecture-designer`, `security-reviewer` and `api-designer` when the spec touches their area; `code-documenter` for the docs each ticket will affect when the docs root holds docs.
3. It writes `overview.md` with the Readiness table first. Each ticket is Ready, Blocked (a question, a decision, or not enough detail) or Already done, and Already done needs commit evidence from `git log --grep`, `git grep` or `git merge-base`. Questions you can answer now go through Feature Forge. You can ask for a challenge pass with `the-fool`.
4. After you approve the overview, it writes `implementation-plan.md` (only Ready tickets, each with a `Skill:` line and a RED check) and `goal-prompt.md`, and commits all three.
5. It makes a few planning writes in the tracker, each behind a permission prompt: links, a comment naming the spec files, an appended plan section, story points. Anything bigger waits in the plan's Proposed tracker changes.
6. It prints the two launch commands for a goal run and proposes the "ask" permission rules for your shared settings, which go in the plan commit on your yes.

## Tickets

**`ticket:execute <ticket-id>`** works one ticket from the plan, never from the tracker, so a run can resume without tracker access.

- It needs a clean working tree (only the spec's own `implementation-plan.md` may show changes) and records the start commit in a marker under `.git/ticket-guard/`.
- It invokes the `ticket-guard` skill, which carries the ticket rules. The plugin's guard hooks freeze the RED tests, keep goal runs out of the text-ticket folder and re-run the tests before a goal run may stop.
- The failing test comes first and is recorded with `guard run red` (`--type stand-in` for a docs or configuration ticket, `--type refactor` for a refactor, which is refused when its metric tool didn't run). A collection or import error doesn't count as RED, so new tests import the code under test inside the test body.
- After RED, the code is written until `guard run green` passes, along with the project's `verify` commands.
- New issues found along the way go to the plan's Proposed tracker changes. Questions go to its Open questions. Neither is worked during the run.

**`ticket:complete [ticket-id]`** reruns the work in a clean worktree, replays the new tests against the start commit (they must fail there), and scans for deleted tests, added skips and assertion-free tests. Every script the RED and GREEN commands ran must be in the repo, never a scratch path such as `/tmp`. It writes the evidence summary into the ticket's Completion Status row and commits the work and the row together with a neutral `Ticket: <id>` trailer, then clears the marker.

Neither ticket command writes to the tracker or moves a ticket's status. A ticket that can't be finished is blocked with `guard block <ticket> "<reason>"`, which saves its changes as a patch, restores the tree and marks it Blocked. Tickets that depend on it are marked "depends on" it. The run carries on with everything else.

## Where each spec stands

**`spec:status`** lists every spec with its state (Unbranched, Triaged, Drafting, Planned, In progress, Ready for review, In review, Ready to complete, PR open, Completed), its ticket counts, what it waits on, the ticket in progress, its pull request and the next command to run. It reads each spec branch from git. In a GitHub project it also shows each spec's pull request, through `gh`; `status.pullRequests` in the config turns that off. Completed specs are hidden unless you add `--all`. A spec that exists only as a folder on your current branch shows as `Unbranched (on <branch>)`, with no branch or PR, until `spec:triage` gives it a branch or you merge it into the default branch.

## Review and completion

**`spec:review <spec-name>`** reviews the whole branch diff once.

1. `guard metrics` writes duplication, dead code and complexity numbers for the changed files. When a metric tool isn't installed, it says which checks did not run (exit 3 when none ran), and the command warns you before the panel starts.
2. A panel of `reviewer` agents reads the diff without commit messages: `code-reviewer` and `test-master` always, plus `security-reviewer`, `architecture-designer`, `api-designer`, `secure-code-guardian` and the stack skill when the diff touches their area, and `code-documenter` for the docs when the project has them. Each one writes its own file.
3. Each blocking or warning finding goes to a fresh, blind `verifier` agent. It sees the claim, the code and the ticket's acceptance criteria, but not who raised it, the tier or the reasoning. It returns confirmed, rejected or unresolved, with proof. The verifiers start together, and the command waits for their reports without scheduling a fallback.
4. `guard rollup` builds `review/rollup.md`, including each verifier's token and minute cost.
5. You decide what to fix. Won't-fix and accepted rejections are recorded with `guard decide`, and `guard decide <row> revoke` withdraws one, which you do before a decided row becomes a fix. Fixes become new tickets in the plan, each typed `test` (a defect, with its own failing test), `test-gap` (correct code missing a test), `stand-in` (docs or configuration) or `refactor` (suite green before and after, tests untouched), with a fresh goal prompt. A later `spec:review` rechecks them.

**`spec:complete <spec-name>`** finishes the spec, and you can rerun it at any point. It is the only command that closes tickets. See the [spec:complete page](workflow/spec-complete.md) for the full PR loop. In short:

1. **Gate:** `guard gate` passes only when every blocking finding is fixed and verified or decided, every PR-feedback row is closed, and every ticket is Done, Already done, or Blocked and accepted by you.
2. **Completion commit:** before the PR, one commit writes the completion report, moves the spec to `completed/`, and carries the system description and docs updates you approve. Its `docs:verify` step checks the root `README` and `docs/` for claims the spec's diff made stale (the names it changed, and absolute statements such as "no credentials exist" in docs about the components it touched), saves a `| Doc | Claim | Verdict | Evidence |` table (holds, stale or unknown) in `review/docs-verify.md`, and fixes each stale claim only on your yes.
3. **PR:** it pushes the branch and opens or reuses the PR. The body says `Closes #N` only for Done and Already done GitHub tickets.
4. **Feedback:** comments from people with write access become numbered findings. You mark each as fix, won't fix or question. Fixes go through the ticket commands, and replies are posted only when you approve them.
5. **Merge:** with CI green, an approval (or green CI alone when you are the repo's only writer) and no open threads, it asks "Merge PR #N now?", and merges on yes.
6. **Close:** it closes each remaining ticket, releases each Blocked one back to the backlog, then closes the group.

## Current state and assumptions

**`spec:current`** says what is true now. The `architect` agent checks `docs/system-description.md` against the code and the specs completed since its last update, and proposes changes for you to approve. Then `guard current-state` compiles `docs/current-state.json`: every component with its status (`wired`, `built, not wired`, `planned`), the open findings and the docs that have drifted from the code, each row naming its source. The report lists all three, plus any description changes you skipped.

**`spec:diff [spec ...]`** shows what changes if the given specs land, in that order (every outstanding spec when you name none): the current component diagram beside the target, a table per spec, the overlaps where two specs touch one component or one removes what another needs, and the assumptions each spec makes about the current system. It writes nothing.

**`common-ground [--list] [--check] [--graph] [spec ...]`** checks those assumptions against `docs/current-state.json` through the `assumption-checker` agent and lists each as holds, conflicts or unknown with its source. A conflict points to `spec:create <spec>` to rework the spec, or to `spec:current` when the state is what's wrong. It also surfaces the assumptions Claude is making about the project for you to confirm, and keeps them in `docs/COMMON-GROUND.md`, committed. See [Common Ground](COMMON_GROUND.md).

## Agents

Long or parallel work runs in the plugin's agents. Each one is defined by the kind of work it does; the command that starts it names the procedure and the skills in its brief, and the agent ends its report with the skills it loaded so the command can rerun it when one is missing.

| Agent | Does | Started by |
|-------|------|------------|
| `code-reader` | Reads code and returns facts cited as `path::symbol`; never writes | `intake`, `discovery:create`, `discovery:approve`, `spec:triage`, `spec:create`, `spec:diff`, `spec:complete`, `ticket:execute`, `common-ground` |
| `doc-writer` | Writes one doc from a procedure and audits it against the code | `intake` |
| `test-writer` | Writes characterization tests and proves they run | `intake` |
| `security-prober` | Runs the authorization and OWASP test procedures | `intake` |
| `architect` | Component, status and data-flow views | `intake`, `spec:current`, `spec:diff` |
| `reviewer` | One review pass over a spec diff, into its own review file | `spec:review` |
| `verifier` | Decides whether one finding is real, in a scratch worktree | `spec:review` |
| `assumption-checker` | Checks spec assumptions against the current state; never writes | `common-ground` |

Agents never commit, and only one writing agent runs at a time. Independent read-only agents start in one message so they run together; the command reviews each writer's diff and commits it. Agents can't ask you anything, so every question stays in the command. During ticket work no agent writes: `ticket:execute` and `ticket:complete` keep every edit in the main session, where the guard's hooks apply.

## Goal runs

A goal run works through a spec's tickets without you. `spec:create` prints two launch commands for the same `goal-prompt.md`:

- **Whole spec:** one run across compactions.
- **Next batch:** the next few tickets (`goal.batchSize`, default 3), then stop. For headless runs, `guard run-batches <spec-name>` loops batches in one session and compacts between them.

Each launch command starts a new session with `--disallowedTools` for every write the run must not make: `AskUserQuestion`, `git push`, PR and issue writes, API writes, `guard decide` and `guard decisions import`. It also allows the `ticket-guard` skill, which carries the ticket rules; the hooks run without it. Judge a run by its final message, never by its exit code. [Goal Runs](GOAL_RUNS.md) covers what happens inside a run.

## What each command writes

| Command | Local files | Tracker | Branch or PR |
|---------|-------------|---------|--------------|
| `intake` | Docs, docstrings, tests, `docs/intake-findings.md`, the checklist, the baseline spec | None | One commit per checklist item |
| `discovery:create` | Topic folder | None | Commits on a small topic branch when you ask |
| `discovery:approve` | `synthesis.md` when research ran, the topic file; a topic with no tickets moves to `completed/` and `INDEX.md` is refreshed | Creates tickets | Commits on the topic's branch, never the default branch |
| `spec:triage` | Text-ticket edits only | Groups, links, `Spec:` lines, blocked-by | Creates `spec/<spec-name>` |
| `spec:create` | The three spec files, `INDEX.md` | Links, a comment, an appended plan, points | Commits on the spec branch |
| `ticket:execute` | Code and tests (uncommitted) | None | None |
| `ticket:complete` | Plan row | None | One commit per ticket |
| `spec:review` | `review/`, fix tickets | None | Commits on the spec branch |
| `spec:complete` | Completion report, `review/docs-verify.md`, the doc fixes you approve, moves | Closes tickets, releases Blocked ones, closes the group | Pushes, opens and merges the PR |
| `spec:status` | Nothing | None | None (reads branches and PRs) |
| `spec:current` | `docs/system-description.md` (the changes you approve), `docs/current-state.json` | None | Commits on the current branch |
| `spec:diff` | Nothing | None | None |
| `common-ground` | `docs/COMMON-GROUND.md`, `docs/ground.index.json` | None | Commits on the current branch |

## Command reference

| Command | Arguments | Attended only |
|---------|-----------|---------------|
| `intake` | `[procedure]`, then the procedure's options (`[directory]`; `create-system-description` takes `[--full]`) | No, runs in goal runs |
| `discovery:create` | `<topic-or-ticket>` | No; under a goal it skips the interviews and asks for an attended rerun |
| `discovery:approve` | `<topic> [--decision=<id>:<value>...]` | Yes |
| `spec:triage` | `[ticket-ids \| tracker-query \| discovery:<topic> \| grouping]` | Yes |
| `spec:create` | `<spec-name>` | Yes |
| `ticket:execute` | `<ticket-id>` | No, runs in goal runs |
| `ticket:complete` | `[ticket-id]` | No, runs in goal runs |
| `spec:review` | `<spec-name>` | Its triage step |
| `spec:complete` | `<spec-name>` | Yes |
| `spec:status` | `[--all]` | No |
| `spec:current` | none | No; under a goal it changes no doc |
| `spec:diff` | `[spec ...]` | No |
| `common-ground` | `[--list] [--check] [--graph] [spec ...]` | Yes, but `--list`; under a goal the rest stop with `BLOCKED:` |

Thirteen commands in all. `common-ground` can also run on its own at any point. See [Common Ground](COMMON_GROUND.md).
