# Workflow rewrite (v0.5.0)

**Status:** Draft, waiting for owner approval
**Spec:** workflow-rewrite
**Discovery:** none
**After:** none
**Feature areas:** workflow-commands, tracker-adapters, ticket-guard, review
**Origin:** the design came from planning sessions, summarized in #253
**Repo:** claude-skills, base `origin/main` at `078a25c`
**Created:** 2026-11-09

---

## 1. Purpose

Rebuild the project workflow commands into one path from tickets to a reviewed PR, and make ticketing tracker-agnostic. Specs live as local markdown files next to the code. Tickets live in Jira, GitHub Issues, GitHub Projects, Linear or text files in the repo, each reached through its own adapter.

The writing-with-agents v0.3.2 run is the model: three files (`overview.md`, `implementation-plan.md`, `goal-prompt.md`) and one `/goal` session that executed ten tickets with one commit each.

## 2. Scope

**In:**
- Command rework: `discovery:create`, `discovery:synthesize`, `discovery:approve`, `spec:triage`, `spec:create`, `spec:review`, `spec:complete`, `ticket:execute`, `ticket:complete`.
- Tracker adapters for Jira, GitHub Issues, GitHub Projects and Linear, plus a configurable text adapter.
- Local documentation under `docs/specs/{todo,completed}/`.
- Unattended rules for goal runs, the kickoff line, and the `goal-prompt.md` template.
- Enforcement: a companion skill carrying marker-guarded hooks, boundary scripts in `ticket:complete` and `spec:complete`.
- `spec:review` with blind per-finding verifiers, a rollup script and a gate.
- A pilot on a new test project, then a docs rewrite.

**Out:**
- The daily triage job, cross-repo or cross-tracker dependencies.
- Intake and the system description (v0.5.x).
- Parallel worktree waves (v0.6.x, after the setup skill).
- The per-project setup skill and the hook suggester (v0.6.0).
- Pluggable reviewers such as Ponytail or a CRAP check (later release).
- Confluence and every other documentation backend.

## 3. Success criteria

- A multi-ticket goal run on the test project completes, crosses an auto-compaction, and ends with every `<done_when>` condition shown in the transcript or a `BLOCKED:` stop.
- `ticket:complete` fails a ticket that has no RED record.
- `spec:complete` refuses to close while a blocking review row is open.
- No shipped page or command names a retired command.
- `make validate` and `make test` pass.

## 4. Design

The design is in #253 and in the planning notes. The decisions that shape the tickets:

| Area | Decision |
|---|---|
| Vocabulary | "Spec" replaces "epic" |
| Commands | Move to `commands/{discovery,spec,ticket}/` with #123. `complete-sprint` is deleted |
| Ways in | Existing tickets start at `spec:triage`. No tickets start at `discovery:create` |
| Text adapter | Generic. Each project points it at a CLI's help output, an existing skill, or its own markdown convention in `.claude/workflow-config.json` |
| Grouping and branches | `spec:triage` creates or finds each spec's tracker group, adds a `Spec:` line to each ticket, records an `After:` build order and creates the spec branch for every tracker. GitHub Issues groups with a parent issue and sub-issues |
| Tracker status and merge | `spec:complete` opens the PR, turns review feedback into fix tickets, merges on the owner's yes once CI is green and nothing is outstanding, then closes each ticket and the group. PR operations go through a code-host adapter (GitHub first). Commits use a neutral `Ticket:` trailer so tracker integrations don't move tickets early |
| Blocked tickets | Skipped with a Blocked row while independent tickets continue; new issues go to "Proposed tracker changes", never worked in the run |
| Spec index | `docs/specs/INDEX.md`, generated from overview header lines, links specs to discovery topics and feature areas |
| Goal run | Sequential tickets, every edit in the main session, no tracker writes during the run |
| Hooks | In a companion skill's frontmatter, invoked by `ticket:execute`, guarded by a marker file in the git directory. Plugin command hooks don't fire and plugin agent hooks are ignored |
| Workflow runtime | Hook, boundary, metrics, rollup and gate scripts live in skill-linter and run as `uvx skill-linter@<pin> guard ...`, shared across skills repos. Workflow users need `uv` |
| Review fixes | Run through `ticket:execute`, with the reproduction as the failing test |
| Text tickets | Never marked done during a run, the same as remote trackers |

## 5. Reuse

- `commands/project/**` holds today's nine commands and their YAML definitions. Most steps carry over under new names.
- `scripts/build-plugin-dist.sh` and `scripts/test-build-plugin-dist.sh` already build and test the shipped tree. Extend them for the companion skill and `references/adapters/` and `references/review/`.
- skill-linter already validates the YAML definitions, manifest and command docs (WF-01 to WF-06, H09 to H15). T0 extends it with the workflow runtime.
- `skills/spec-miner`, `skills/feature-forge`, `skills/test-master`, `skills/code-reviewer`, `skills/debugging-wizard` and `skills/the-fool` are used by the new commands without changes.
- The v0.3.2 reference set in writing-with-agents shows the target shape of the three spec files.

## 6. Debt in scope

- `commands/workflow-manifest.yaml` and the per-command YAML files describe the old command graph. Replace them in T4 and T11.
- `docs/v0.5.0-plan.md` and `docs/v0.5.0-narrative.md` describe an older v0.5.0. Mark them superseded in T13.
- `execute-ticket` writes tests at step 9, after the code. T7 moves RED first.

## 7. Risks

The planning notes keep a register of 23 risks. The ones that decide whether this spec works:

- Hooks registered by the companion skill may not survive auto-compaction. The pilot (T12) tests it.
- The `/goal` evaluator reads only the transcript, so evidence must appear in messages.
- The tracker mappings were checked against API docs on 2026-11-09; Linear's project relation parameters remain undocumented.
- The skill-linter release (T0) gates the hooks and the new command definitions.
- `uvx` costs about 80 ms per call, so hooks test for the marker in shell first (measured 2026-11-09).
- A headless goal run can exit as `success` with the goal unmet once the Stop-hook block cap is hit, so runs are judged by their final message.
- A skill that asks a question stalls an interactive goal run, so goal runs launch with `AskUserQuestion` denied and collect such questions for the owner.

## 8. Linked tickets

Tickets T0 to T13 are listed in `implementation-plan.md`. They get tracker IDs when this spec is triaged, and the local IDs stay in the plan as aliases.

## 9. Pending owner

None. The owner settled every open item on 2026-11-09; the answers are in the planning notes. Both pre-pilot experiments ran on 2026-11-09; their results are folded into T0, T7 and T12.
