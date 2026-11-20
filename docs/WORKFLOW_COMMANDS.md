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
- [Goal runs](#goal-runs)
- [What each command writes](#what-each-command-writes)
- [Command reference](#command-reference)

---

## How the workflow fits together

There are two ways in.

- **You already have tickets.** Start at `spec:triage`, which groups them into specs.
- **You have an idea, a feature list or a ticket nobody can plan yet.** Start at `discovery:create`, which turns it into tickets you approve before they reach the tracker.

```
discovery:create ─► discovery:synthesize (only after research) ─► discovery:approve
                                                                       │ tickets
existing tickets ──────────────────────────────────────────────────────┤
                                                                       ▼
spec:triage ─► spec:create ─► ticket:execute + ticket:complete (per ticket, often one goal run)
                                                                       │
                                     spec:complete ◄─ spec:review ◄────┘
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
- **Configure the tracker.** The first attended command that needs `.claude/workflow-config.json` offers a setup wizard. It detects your GitHub remote, a Jira or Linear MCP server or a text-ticket tool, and asks one question at a time. See [Tracker Setup](TRACKER_SETUP.md) for every adapter.
- **Know which commands need you.** `discovery:approve`, `spec:triage`, `spec:create`, the triage step of `spec:review`, `spec:complete` and the wizard are attended. Run inside a goal, they write nothing, print what they would have done and stop with `BLOCKED:`.

## Intake

Intake runs once, when you adopt an existing codebase, before the first spec. It needs no tracker and no code host. It documents the code for agents, writes tests that pin current behavior and records every bug in `docs/intake-findings.md` instead of fixing it.

- **`intake:existing-docs`** lists the docs the project already has, maps them to the intake topics and checks their claims against the code. Wrong claims become findings; your docs are never edited.
- **`intake:document-codebase`** adds docstrings across the code. It runs your tests before and after and checks that no executable line changed.
- **Twelve `intake:document-*` commands** each write one reference doc under `docs/` (data model, file tree, integrations, API, user model, features, glossary, security, authorization, user flow, configuration, analytics), and each ends with an accuracy audit. **`intake:create-onboarding`** links them from `docs/README.md`.
- **`intake:testing-setup`** builds the test harness and proves each layer with a smoke test. **`intake:testing-features`**, **`-authorization`**, **`-owasp`** and **`-user-flows`** then write characterization tests, each reading its matching doc. Together these five are the capture-behavior step.
- **`intake:create-system-description`** writes a baseline spec into `docs/specs/completed/baseline/`, so the spec index knows the existing system, and `docs/system-description.md`. Later, `spec:complete` proposes updates to it once per spec. With `--roadmap` it writes only `docs/architecture-roadmap.md`, a plan view of where the outstanding specs take the architecture.

Every intake command can run in a goal run: none asks a question there, and a checkpoint becomes a draft plus an open question in the findings tracker. [Intake](INTAKE.md) covers the checklist, the goal run and close-out.

## Discovery

Discovery is optional. Use it when there are no tickets yet, or when `spec:triage` sends a ticket back because nobody can write its acceptance criteria.

- **`discovery:create <topic-or-ticket>`** splits your input into items, reads the existing code for each one, and routes it. Clear items become proposed tickets straight away. Vague items go through a Feature Forge interview whose output is saved in the topic folder. Items with real unknowns go to research. It writes `docs/specs/todo/discovery/<topic>/discovery.md`.
- **`discovery:synthesize <topic>`** runs only after research. It reads the topic's `sources/` and writes `synthesis.md`, with findings that cite their sources, blocking decisions and proposed tickets.
- **`discovery:approve <topic>`** is the gate before anything reaches the tracker. It walks you through the blocking decisions one at a time, lets you edit or drop tickets, then creates the rest, each with a `Discovery: <topic>` line. It never groups them; it points you to `spec:triage`. A topic that ends with no tickets moves to `completed/`.

## Specs

**`spec:triage [ticket IDs | query | discovery:<topic>]`** proposes how to group open tickets into specs, and explains each grouping by its strongest signal: tracker links, a shared discovery topic, shared labels, shared files or feature areas, then wording. A grouping you type in the argument beats every signal. It flags stale tickets without closing them, refuses to move a ticket out of a spec that has started, warns above 10 tickets per spec, and suggests a build order with `After:` lines. Once you approve, it creates or finds each spec's group in the tracker, links the tickets, appends `Spec: <spec-name>` to each one and cuts `spec/<spec-name>` from your default branch. Nothing is pushed.

**`spec:create <spec-name>`** plans one spec:

1. It refuses to start while the spec's predecessor (`After:`) hasn't merged, unless you override, and rebases the branch when it has.
2. It sends read-only subagents to map the code: `spec-miner` always; `architecture-designer`, `security-reviewer` and `api-designer` when the spec touches their area.
3. It writes `overview.md` with the Readiness table first. Each ticket is Ready, Blocked (a question, a decision, or not enough detail) or Already done, and Already done needs commit evidence from `git log --grep`, `git grep` or `git merge-base`. Questions you can answer now go through Feature Forge. You can ask for a challenge pass with `the-fool`.
4. After you approve the overview, it writes `implementation-plan.md` (only Ready tickets, each with a `Skill:` line and a RED check) and `goal-prompt.md`, and commits all three.
5. It makes a few planning writes in the tracker, each behind a permission prompt: links, a comment naming the spec files, an appended plan section, story points. Anything bigger waits in the plan's Proposed tracker changes.
6. It prints the two launch commands for a goal run and proposes the "ask" permission rules for your shared settings.

## Tickets

**`ticket:execute <ticket-id>`** works one ticket from the plan, never from the tracker, so a run can resume without tracker access.

- It needs a clean working tree and records the start commit in a marker under `.git/ticket-guard/`.
- It invokes the `ticket-guard` skill, whose hooks freeze the RED tests, keep goal runs out of the text-ticket folder and re-run the tests before a goal run may stop.
- The failing test comes first and is recorded with `guard run red`. A collection or import error doesn't count as RED, so new tests import the code under test inside the test body.
- After RED, the code is written until `guard run green` passes, along with the project's `verify` commands.
- New issues found along the way go to the plan's Proposed tracker changes. Questions go to its Open questions. Neither is worked during the run.

**`ticket:complete [ticket-id]`** reruns the work in a clean worktree, replays the new tests against the start commit (they must fail there), and scans for deleted tests, added skips and assertion-free tests. It writes the evidence summary into the ticket's Completion Status row and commits the work and the row together with a neutral `Ticket: <id>` trailer, then clears the marker.

Neither ticket command writes to the tracker or moves a ticket's status. A ticket that can't be finished is blocked with `guard block <ticket> "<reason>"`, which saves its changes as a patch, restores the tree and marks it Blocked. Tickets that depend on it are marked "depends on" it. The run carries on with everything else.

## Where each spec stands

**`spec:status`** lists every spec with its state (Triaged, Drafting, Planned, In progress, Ready for review, In review, Ready to complete, PR open, Completed), its ticket counts, what it waits on, the ticket in progress, its pull request and the next command to run. It reads each spec branch from git. In a GitHub project it also shows each spec's pull request, through `gh`; `status.pullRequests` in the config turns that off. Completed specs are hidden unless you add `--all`.

## Review and completion

**`spec:review <spec-name>`** reviews the whole branch diff once.

1. `guard metrics` writes duplication, dead code and complexity numbers for the changed files.
2. A panel of reviewer subagents reads the diff without commit messages: `code-reviewer` and `test-master` always, plus `security-reviewer`, `architecture-designer`, `api-designer`, `secure-code-guardian` and the stack skill when the diff touches their area. Each one writes its own file.
3. Each blocking or warning finding goes to a fresh, blind verifier. It sees the claim, the code and the ticket's acceptance criteria, but not who raised it, the tier or the reasoning. It returns confirmed, rejected or unresolved, with proof.
4. `guard rollup` builds `review/rollup.md`, including each verifier's token and minute cost.
5. You decide what to fix. Won't-fix and accepted rejections are recorded with `guard decide`. Fixes become new tickets in the plan, typed behavior (their own failing test) or refactor (suite green before and after, tests untouched), with a fresh goal prompt. A later `spec:review` rechecks them.

**`spec:complete <spec-name>`** finishes the spec, and you can rerun it at any point. It is the only command that closes tickets. See the [spec:complete page](workflow/spec-complete.md) for the full PR loop. In short:

1. **Gate:** `guard gate` passes only when every blocking finding is fixed and verified or decided, every PR-feedback row is closed, and every ticket is Done, Already done, or Blocked and accepted by you.
2. **PR:** it pushes the branch and opens or reuses the PR. The body says `Closes #N` only for Done and Already done GitHub tickets.
3. **Feedback:** comments from people with write access become numbered findings. You mark each as fix, won't fix or question. Fixes go through the ticket commands, and replies are posted only when you approve them.
4. **Merge:** with CI green, an approval and no open threads, it moves the spec to `completed/` in the last commit before the merge, asks "Merge PR #N now?", and merges on yes.
5. **Close:** it closes each remaining ticket, then the group.

## Goal runs

A goal run works through a spec's tickets without you. `spec:create` prints two launch commands for the same `goal-prompt.md`:

- **Whole spec:** one run across compactions.
- **Next batch:** the next few tickets (`goal.batchSize`, default 3), then stop. For headless runs, `guard run-batches <spec-name>` loops batches in one session and compacts between them.

Each launch command starts a new session with `--disallowedTools` for every write the run must not make: `AskUserQuestion`, `git push`, PR and issue writes, API writes and `guard decide`. It also allows the `ticket-guard` skill, which the hooks need. Judge a run by its final message, never by its exit code. [Goal Runs](GOAL_RUNS.md) covers what happens inside a run.

## What each command writes

| Command | Local files | Tracker | Branch or PR |
|---------|-------------|---------|--------------|
| `intake:*` | Docs, docstrings, tests, `docs/intake-findings.md`, the baseline spec | None | None |
| `discovery:create` | Topic folder | None | None |
| `discovery:synthesize` | `synthesis.md` | None | None |
| `discovery:approve` | Topic file | Creates tickets | None |
| `spec:triage` | Text-ticket edits only | Groups, links, `Spec:` lines, blocked-by | Creates `spec/<spec-name>` |
| `spec:create` | The three spec files, `INDEX.md` | Links, a comment, an appended plan, points | Commits on the spec branch |
| `ticket:execute` | Code and tests (uncommitted) | None | None |
| `ticket:complete` | Plan row | None | One commit per ticket |
| `spec:review` | `review/`, fix tickets | None | Commits on the spec branch |
| `spec:complete` | Completion report, moves | Closes tickets and the group | Pushes, opens and merges the PR |
| `spec:status` | Nothing | None | None (reads branches and PRs) |

## Command reference

| Command | Arguments | Attended only |
|---------|-----------|---------------|
| `intake:*` | `[directory]`; `create-system-description` takes `[--full] [--roadmap]` | No, runs in goal runs |
| `discovery:create` | `<topic-or-ticket>` | No |
| `discovery:synthesize` | `<topic>` | No |
| `discovery:approve` | `<topic> [--decision=<id>:<value>...]` | Yes |
| `spec:triage` | `[ticket-ids \| tracker-query \| discovery:<topic>]` | Yes |
| `spec:create` | `<spec-name>` | Yes |
| `ticket:execute` | `<ticket-id>` | No, runs in goal runs |
| `ticket:complete` | `[ticket-id]` | No, runs in goal runs |
| `spec:review` | `<spec-name>` | Its triage step |
| `spec:complete` | `<spec-name>` | Yes |
| `spec:status` | `[--all]` | No |

`common-ground` sits outside the workflow and can run at any point. See [Common Ground](COMMON_GROUND.md).
