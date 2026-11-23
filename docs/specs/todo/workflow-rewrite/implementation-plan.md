# Workflow rewrite implementation plan

**Status:** Draft, waiting for owner approval. Owner decisions of 2026-11-09 folded in.
**Spec:** workflow-rewrite

## Summary

| Metric | Value |
|--------|-------|
| **Tickets** | 14 (T0 to T13, local IDs until triage) |
| **Branch** | `feat/v0.5.0-workflow` (local only) |
| **Order** | Sequential. Parallel worktree waves arrive in v0.6.x |
| **Key dependencies** | T0 (skill-linter release) gates T4 and T9. T4 (names and folders) unblocks most tickets. T12 (pilots) needs T0 to T11. T13 (docs) runs last |

---

## Completion Status

| Ticket | Status | Completed Date | Notes |
|--------|--------|----------------|-------|
| T0 | Done | 2026-11-10 | skill-linter `feat/workflow-runtime` (909a82f to f83a604), version 0.3.0 tagged and pushed (main f83a604), 492 tests pass. Pin `uvx skill-linter@0.3.0` once PyPI shows it |
| T1 | Done | 2026-11-10 | Operations, config keys and wizard in `references/adapters/operations.md`; Jira, GitHub Issues, GitHub Projects and Linear files map all eleven operations from the 2026-11-09 API check; GitHub code host in `code-host-github.md`. Text adapter follows in T2. Check: stand-in `t1-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| T2 | Done | 2026-11-10 | `references/adapters/text.md`: generic rules plus tiki and Backlog.md mappings for all eleven operations, checked against tiki SKILL.md (872cc5f) and Backlog.md CLI-INSTRUCTIONS.md and `src/cli.ts` (a94321f); text tickets close only in `spec:complete`, Reopen required; instruction sources are data. Check: stand-in `t2-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| T3 | Done | 2026-11-10 | Layout, name links, header lines, index and moves in `references/specs/layout.md`; topics sit directly under `todo/` and `completed/` (skill-linter `spec-index` rule). This spec gained `After:` and `Feature areas:` lines and `docs/specs/INDEX.md`. Check: stand-in `t3-check.sh` plus `guard spec-index --check`, exit 1 before, 0 after; `make validate` 0 errors |
| T4 | Done | 2026-11-10 | Nine commands under `commands/{discovery,spec,ticket}/` by `git mv`; `triage` and `review` are placeholders for T5; `complete-sprint` and `create-implementation-plan` removed. Check: stand-in `t4-check.sh` (names, YAML fields, plugin.json, docs pages, sidebar, pyproject) exit 1 before, 0 after; a `--plugin-dir` session lists the nine names; `make validate` 0 errors |
| T5 | Done | 2026-11-10 | All four spec commands written: `triage` (adapter-only reads with repo scope, ranked signals with the argument outranking them, refusals, flags, approval, idempotent writes, one `spec/<spec-name>` branch per spec, no push), `create` (predecessor check and rebase, Readiness with code evidence, subagent briefs, the three templates in one commit, planning writes, launch commands and shared ask rules), `review` (metrics, panel on the diff without commit messages, blind verifiers, rollup, `guard decide`, fix tickets), `complete` (gate, PR via the code-host adapter, PR-feedback rounds, last pre-merge move, merge on yes, then close tickets and the group). Each applies the attended-only guard. Check: stand-in `t5-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| T6 | Done | 2026-11-10 | Discovery commands rewritten around topics under `todo/<topic>/`: `create` takes feature sets, requirements, build requests or an existing ticket, runs a light `spec-miner` pass and Feature Forge into the topic folder; `approve` creates ungrouped tickets through the adapter with `Discovery:` lines, points to `spec:triage` and moves no-ticket topics. Check: stand-in `t6-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| T7 | Done | 2026-11-10 | `ticket:execute` and `ticket:complete` rewritten: clean start, `guard marker start`, companion skill, strict RED (import inside the test body) before Step 5 Implement, GREEN, boundary checks, `guard summary` in the Completion Status row of the same commit, `Ticket:` trailer, no tracker writes, `guard block` for stuck tickets and dependents. Shared rules and the attended-only guard in `references/specs/unattended.md`; the spec commands adopt the guard in T5. Check: stand-in `t7-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| T8 | Done | 2026-11-10 | Templates in `references/specs/templates/` (overview with header lines and Readiness first, plan matching the runtime table parsers, goal prompt of 54 lines with `<done_when>` counting from the start SHA and `guard commit-plan` in `<final_report>`); kickoffs, deny set and launch commands in `references/specs/launch.md`. `spec:create` wiring lands with T5. Check: stand-in `t8-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| T9 | Done | 2026-11-10 | `skills/ticket-guard` ships its PreToolUse, Stop and SessionStart hooks in frontmatter, enabled by skill-linter 0.3.1 `allow_claude_hooks`; each hook tests for the marker in shell before `uvx`. Live `--plugin-dir` test in a scratch repo: the frozen-test edit was denied, the marker was claimed, and the Stop hook re-ran the failing check 3 times then logged `green_failure`. Found: headless launches must allow `Skill(fullstack-dev-skills:ticket-guard)`; launch commands now do, and `ticket:execute` stops when the marker is unclaimed. Check: `test-build-plugin-dist.sh` failed 5 before, passes after; `make validate` 0 errors |
| T10 | Done | 2026-11-10 | Verifier brief in `references/review/verifier.md` (one blind `debugging-wizard` verifier per merged blocking or warning finding, packet with acceptance criteria, scratch worktree with no gitignored files, frozen `review/repro/`, own RED test per fix, refactor stand-in, recheck); row format, verdicts file, cost columns and gate rules in `references/review/rollup.md`; `spec:review` and `spec:complete` cite both. Check: `scripts/test-review-wiring.sh` (in `make test`) runs the documented verdicts through `guard rollup`, `decide` and `gate`: failed before, 33 passed after; `make validate` 0 errors |
| T11 | Done | 2026-11-10 | `complete-sprint` gone (command file deleted in T4, the legacy copy under `.claude/old-commands/` here, the `WORKFLOW_COMMANDS.md` note reworded); manifest describes the discovery, spec and ticket graph with the skills each phase calls; `stamp --check` passes with `workflowCount` 9 (already 9, so nothing to stamp). Check: stand-in `t11-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| T12 | Pending | 2026-11-10 | Local pilots run 2026-11-10 (Python with Backlog.md, TypeScript with markdown tickets), triage to local merge; 23 findings, fixes in 197fe49, b3e75fd, 2dd429e, e054ce6; run-batches fixes requested from skill-linter. Remaining: the GitHub pilot and the R6 abort and resume checks. Report: claude-skills-v0.5.0-pilots/pilot-report.md in the planning notes |
| T13 | Done | 2026-11-10 | Workflow guide rewritten; new Tracker Setup and Goal Runs guides; every command page expanded (`spec:complete` covers the PR loop); schema doc gains `unattended` and `adapter-operations`; QUICKSTART, README, local development (`--plugin-dir`), Atlassian (Jira only), SKILLS_GUIDE, ROADMAP and CHANGELOG updated; old v0.5.0 plans marked superseded. Human-voice pass applied by the session; owner review pending. Written before the T12 pilot, so pilot findings may need edits. Check: stand-in `t13-check.sh` exit 1 before, 0 after; site build 102 pages, no broken links; `make validate` 0 errors |

The table is updated before each ticket's commit and committed with it, so it holds no SHAs. Each ticket's notes also carry the evidence summary `ticket:complete` copies from the run (RED and GREEN commands, exit codes, digests).

---

## Execution Order

| # | Ticket | Summary | Risk | Dependencies |
|---|--------|---------|------|--------------|
| 1 | T0 | skill-linter release: workflow runtime and new definition fields | High | None (separate repo) |
| 2 | T4 | Command names and folders | Medium | T0 |
| 3 | T3 | Local docs layout and spec index | Low | T4 |
| 4 | T8 | Spec file templates and kickoff line | Medium | T4 |
| 5 | T1 | Tracker adapters and config wizard | Medium | T4 |
| 6 | T2 | Text adapter | Medium | T1 |
| 7 | T6 | Discovery takes topics, Feature Forge wired in | Medium | T3, T4 |
| 8 | T7 | Unattended rules and RED first in the ticket commands | Medium | T4 |
| 9 | T9 | Companion skill and marker-guarded hooks | High | T0, T7 |
| 10 | T5 | `spec:triage`, `spec:create`, `spec:review`, `spec:complete` | High | T1, T3, T8 |
| 11 | T10 | Verifier brief, rollup and gate | Medium | T0, T5 |
| 12 | T11 | Delete `complete-sprint`, update the manifest and counts | Low | T4 |
| 13 | T12 | Pilots: two local repos, then a private GitHub repo | High | T0 to T11 |
| 14 | T13 | Docs rewrite with a human-voice pass per page | Medium | T12 |

T5 is the largest ticket. Split it into one ticket per command at triage if it runs long.

---

## Tickets

### T0: skill-linter release

**Skill:** python-pro
**Repo:** skill-linter (handbook), not claude-skills

The workflow's runtime scripts move into skill-linter as a command group that every skills repo can share, run as `uvx skill-linter@<pin> guard ...`. The release also adds the new workflow definition fields.

**Acceptance criteria:**
- [ ] Hook entry points for the companion skill: evidence record, RED and GREEN records, test freeze, Stop-hook GREEN re-run (goal mode only) that ignores `stop_hook_active`, counts consecutive GREEN failures in the marker, blocks up to about 3 times then allows and records the failure, and always allows a final message starting with `BLOCKED:`
- [ ] A batch runner (`guard run-batches <spec>`): run the next-batch goal headless, judge the final message, `claude -p "/compact" --resume <session>`, repeat until every ticket is Done or Blocked
- [ ] `guard block <ticket> <reason>`: saves the ticket's diff to `$(git rev-parse --git-dir)/ticket-guard/blocked/<ticket>.patch` and new untracked files to a tarball beside it, restores the tree to the ticket's start SHA, writes the Blocked row and clears the marker; refuses and reports if HEAD has moved past the start SHA
- [ ] `guard decide <row> <status>`: records owner-only statuses (wontfix, rejection-accepted, accepted Blocked rows) in `decisions.jsonl` beside the marker; the gate reads statuses only from that log
- [ ] Marker handling at `$(git rev-parse --git-dir)/ticket-guard/marker.json`, with the ticket's start SHA: JSON, written by temp file and `mv`, session claim on first hook, stand down on another session or branch, warn past a configurable age (default 24 hours)
- [ ] Evidence JSONL at `$(git rev-parse --git-dir)/ticket-guard/evidence/<ticket>.jsonl`, plus a summary command for `ticket:complete`
- [ ] Boundary commands: clean re-run in a temporary worktree, RED replay against the base commit, tamper scan
- [ ] Review commands: metrics, rollup (with tokens and minutes per verifier), gate
- [ ] Spec index generator for `docs/specs/INDEX.md`, with a `--check` mode
- [ ] New workflow definition fields validated by WF-01 and WF-02 (candidates: `unattended`, adapter operations used; exact fields decided in this ticket)
- [ ] Each command has tests; a new version is published and pinned in claude-skills

### T1: Tracker adapters and config wizard

**Skill:** prompt-engineer
**Related:** #62, #119

A code-host adapter for PR operations (open or reuse, read reviews and threads, reply and resolve, CI and approvals, merge), GitHub through `gh` only in v0.5.0; on other hosts `spec:complete` prints the manual steps. Six tracker reference files under `references/adapters/`: `operations.md` (the operations and `.claude/workflow-config.json`) and one each for Jira, GitHub Issues, GitHub Projects, Linear and text. Operations: create, read, list a spec's tickets, link a ticket to a spec, update (append text, set a field), comment, close, reopen, ensure group, link groups, and optional list ungrouped.

**Acceptance criteria:**
- [ ] Each tracker file maps every operation, using the endpoints in the 2026-11-09 tracker API check
- [ ] Jira and Linear files are marked "docs-verified, not live-tested" and list their open items; GitHub and text are marked live-tested after T12
- [ ] The config holds a per-tracker filter that scopes tickets to this repo (Jira component or label, Linear team or label), proposed by the wizard
- [ ] GitHub Issues groups with a parent spec issue and sub-issues; a ticket that already has a parent is refused unless the owner approves `replace_parent`
- [ ] GitHub Projects are named by owner and project number; the `project` token scope is documented
- [ ] "Ensure group" matches names exactly and refuses when two groups share a name
- [ ] Jira close picks a transition into a Done-category status
- [ ] With no config, attended commands run a wizard with `AskUserQuestion`, recommending detected values; unattended runs end with `BLOCKED:`
- [ ] Config shape: `version`, `tracker`, `specsRoot`, one block per tracker, `triage.staleDays` (30), `triage.warnAboveTickets` (10), `verify`, and the marker age setting

### T2: Text adapter

**Skill:** prompt-engineer

A generic adapter for tickets kept as text in the repo. The project points `text.instructions` at a CLI's help output, an existing skill (for example tiki's, Discussion #114) or a markdown file describing its own convention.

**Acceptance criteria:**
- [ ] The operations are checked against at least two real tools before the reference file is final
- [ ] Text tickets are never marked done during a run; `spec:complete` closes them

### T3: Local docs layout and spec index

**Skill:** prompt-engineer

Commands write specs under `docs/specs/{todo,completed}/`, with discovery topics directly under `todo/` and `completed/`. Each overview carries `Spec:`, `Discovery:`, `After:` and `Feature areas:` header lines, and `docs/specs/INDEX.md` is generated from them.

**Acceptance criteria:**
- [ ] The layout matches the design's folder tree, including `review/`
- [ ] Links between files and tickets use names, never paths
- [ ] `INDEX.md` lists every spec in `todo/` and `completed/` with status, discovery topics, feature areas and predecessors; its `--check` mode fails on a stale index or a broken name link
- [ ] `spec:complete` moves a finished spec with `git mv`; `discovery:approve` moves a topic that ends with no tickets

### T4: Command names and folders

**Skill:** prompt-engineer
**Related:** #123

One commit moves each surviving command with `git mv` to `commands/discovery/{create,synthesize,approve}.md`, `commands/spec/{triage,create,review,complete}.md` and `commands/ticket/{execute,complete}.md`, with `<action>.yaml` beside each. `plugin.json` keys give the names (`spec:create` and so on). Rewrites follow in later tickets. `spec:create` starts from the larger planning file.

**Acceptance criteria:**
- [ ] Every command loads under its new name in a `--plugin-dir` session
- [ ] `commands/project/` is gone, and `pyproject.toml` has the new `workflow_glob`, phases (retrospective out, spec and ticket in) and `requires` without `documentation`
- [ ] Each command has a short `docs/workflow/` page and a sidebar entry, so H13 and H15 pass
- [ ] `make validate` passes with the T0 pin

### T5: The four spec commands

**Skill:** prompt-engineer

- `spec:triage`, from its spec: ensure group and link tickets, add a `Spec:` line to each ticket, create the `spec/<name>` branch from the default branch for every tracker, show ranked grouping reasons (links, discovery topic, labels, files and feature areas, wording), read only tickets matching the repo filter, propose several specs per run with an `After:` build order and blocked-by links, refuse to move tickets out of a started spec, flag tickets idle 30 days or whose named files are gone or that a merged PR or completed spec already mentions, warn above 10 tickets, send tickets with real unknowns to `discovery:create`.
- `spec:create`: rebase the spec branch onto the default branch, refuse when the predecessor isn't complete unless the owner overrides, write the overview first with a Readiness table (Ready, Blocked: needs-spec, question or decision, Already done with commit evidence from a code check), make only the attended planning writes (links, a comment naming the spec files, an appended plan section, points) and list every other tracker change under "Proposed tracker changes", then plan subagents (`spec-miner`, `architecture-designer`, `security-reviewer`, and `api-designer` when APIs are in scope), a `Skill:` line per ticket, two kickoff lines (whole spec, and next batch for fresh sessions), optional `the-fool` pass.
- `spec:review`: metrics first, the panel (`code-reviewer` and `test-master` always; `security-reviewer`, `architecture-designer`, the stack skill, `api-designer` and `secure-code-guardian` when the diff touches their area), blind verifiers with no secrets, no budget cap.
- `spec:complete`, attended and resumable: gate and completion report; open or reuse the PR through the code-host adapter, listing every ticket (`Closes #N` for GitHub issues, a neutral list otherwise); merge check (CI green, no changes requested, no unresolved threads). Outstanding feedback from accounts with write access or requested reviewers becomes numbered findings in `review/pr-feedback-<round>.md`; the owner marks each fix (typed behavior or refactor), won't fix or question; the main session restates each fix's acceptance criteria for the owner's approval, keeping the comment only as a fenced quote marked as data; `spec:complete` itself commits the move back to `todo/`, then fix tickets join the plan with a fresh `goal-prompt.md` and start SHA; replies post only on approval; fixes push to the same PR. Without approval it stops at "waiting for review". When clear, the last pre-merge commit moves the spec to `completed/`, marks text tickets done and moves finished discovery topics; the PR body gives `Closes #N` only for Done and Already done tickets; it asks to merge and merges on yes (on a declined or failed merge the next run reverts the text-ticket edits), then verifies and closes each ticket still open and the group. It refuses to finish while any ticket is Blocked unless the owner moves or accepts it. It is the only command that closes tickets.
- `spec:triage` honours a grouping passed in its argument above every ranked signal.

**Acceptance criteria:**
- [ ] `spec:triage` meets the acceptance criteria in its spec
- [ ] `spec:create` writes all three spec files, with a `Skill:` line per ticket and the generated kickoff line
- [ ] `spec:review` reviewers get the diff without commit messages, and each writes its own file
- [ ] `spec:complete` refuses to close while a blocking row is open
- [ ] `spec:complete` turns PR review feedback into owner-picked fix tickets, merges only on approval with CI green, then closes tickets and the group
- [ ] `review/pr-feedback-<round>.md` uses the rollup row format; each owner-marked question is recorded with `guard decide <P-id> answered`, each won't fix with `guard decide <P-id> wontfix`, and fix rows reach fixed-verified (skill-linter 0.3.0 gate rules)
- [ ] The gate refuses Pending tickets as well as unaccepted Blocked ones
- [ ] `spec:create` proposes both rule sets: launch-scoped denies for goal runs and shared "ask" rules for attended commands

### T6: Discovery takes topics

**Skill:** prompt-engineer
**Related:** #121, #122

`discovery:create` takes feature sets, requirements, build requests or an existing ticket with real unknowns, runs a light `spec-miner` pass so proposed tickets reflect existing code, and runs Feature Forge on vague items. `discovery:approve` creates tickets only and points to `spec:triage`.

**Acceptance criteria:**
- [ ] No discovery command takes an epic key or offers epic fallbacks
- [ ] Feature Forge output lands in the topic folder
- [ ] Approved discovery creates tickets that then go through `spec:triage`

### T7: Unattended rules and RED first

**Skill:** prompt-engineer

`ticket:execute` and `ticket:complete` skip approvals in goal mode, never call `AskUserQuestion` (goal runs launch with it denied for the session), and end a stopped run with `BLOCKED:`. The failing test comes before the code. Subagents only read and return text. Neither command changes tracker status, and the system-description step is removed (it returns in `spec:complete` in v0.5.x). Commits reference tickets with a neutral `Ticket: <id>` trailer, never Linear IDs or Jira `#transition` tokens. `ticket:execute` starts only on a clean working tree and records the start SHA. A ticket that can't be finished goes through `guard block` (patch saved, tree restored), and tickets that depend on it are marked "Blocked: depends on"; the run continues and finishes normally. `BLOCKED:` is reserved for spec-wide stops. New issues found during a run, and any question a skill needs answered, go to the plan's end-of-run collection of open questions and proposed tracker changes and are never worked in that run; a ticket waiting on an answer is marked Blocked: question. A run where only blocked tickets remain finishes normally and lists them first.

**Acceptance criteria:**
- [ ] A goal-mode ticket runs with no question asked
- [ ] The RED record exists before any implementation edit
- [ ] RED is strict: a collection or import error is not RED, so new tests import the symbol under test inside the test body
- [ ] Under unattended rules a tamper-scan flag means `guard block`; `--reason` is attended only (goal mode ignores it)
- [ ] `ticket:complete` commits with the Completion Status table and evidence summary in the same commit
- [ ] No tracker write from either command
- [ ] A blocked ticket is saved as a patch and skipped, its dependents are marked Blocked, independent tickets still run, and the run finishes normally; `BLOCKED:` only for spec-wide stops
- [ ] Every attended-only command (`discovery:approve`, `spec:triage`, `spec:create`, `spec:review` triage, `spec:complete`, the config wizard) writes nothing and ends with `BLOCKED:` when a goal is active or `AskUserQuestion` is unavailable

### T8: Spec file templates and kickoff line

**Skill:** prompt-engineer

Templates for `overview.md` (header lines from T3, Reuse and Debt in scope sections), `implementation-plan.md` (Completion Status table) and `goal-prompt.md` (40 to 60 lines), plus two launch commands (`claude --disallowedTools <write set> "/goal ..."` for whole spec and next batch of N, default 3) with the `BLOCKED:` clause. `<done_when>` counts one commit per Done ticket since the recorded start SHA, accepts each ticket as Done or Blocked with its reason, and names the GREEN evidence.

**Acceptance criteria:**
- [ ] `spec:create` fills all three templates from one overview
- [ ] The generated `goal-prompt.md` holds only per-run content
- [ ] The kickoff line names `<done_when>` and `<stops>` and asks for a re-read after compaction
- [ ] The printed launch commands carry the full write deny set, including `Bash(skill-linter guard decide:*)`, `Bash(uvx skill-linter* guard decide*)` and `Bash(uv run skill-linter guard decide*)`
- [ ] The `<final_report>` step of a whole-spec run (or the start of `spec:review`) runs `guard commit-plan <spec>` to commit uncommitted Blocked rows; the batch runner does this itself after the last batch

### T9: Companion skill and marker-guarded hooks

**Skill:** cli-developer

A small skill whose frontmatter hooks test for the marker in shell first (about 2 ms) and only `exec uvx skill-linter@<pin> guard ...` during ticket work (about 80 ms per call, measured 2026-11-09). The must-not-lose ticket rules sit at the top of its body, which is re-injected after compaction, and a `SessionStart` hook with source `compact` prints the ticket, mode and next step when a marker exists. `ticket:execute` writes the marker and invokes the skill; `ticket:complete` checks the evidence and clears the marker.

**Acceptance criteria:**
- [ ] Hooks fire from a plugin install, and do nothing without a marker or for another session
- [ ] `ticket:complete` fails a ticket with no evidence record
- [ ] A marker removed without a logged clear ends a goal-mode ticket with `BLOCKED:`; attended, the owner may accept once the boundary checks pass
- [ ] The config wizard checks that `uv` is installed
- [ ] `scripts/build-plugin-dist.sh` ships the skill, and `scripts/test-build-plugin-dist.sh` checks it

### T10: Verifier, rollup and gate

**Skill:** test-master

The blind verifier brief (`debugging-wizard` limited to reproduce, isolate and hypothesize) in `references/review/`, wired to the rollup and gate commands from T0.

**Acceptance criteria:**
- [ ] One verifier per merged blocking or warning finding, with no reviewer, tier or reasoning in its input, and no secrets in its worktree
- [ ] A reproduction stays frozen in `review/repro/`; the fix ticket writes its own RED test
- [ ] The rollup lists every finding with its verdict and cost columns (tokens, minutes), read from each verifier's transcript usage
- [ ] Each verifier packet carries the ticket's acceptance criteria
- [ ] Refactor fix tickets pass with a stand-in check (suite green before and after, test files unchanged by digest, metrics show the clone or dead code gone) instead of RED
- [ ] The gate passes only when every blocking row is `fixed-verified`, `wontfix` or `rejection-accepted`

### T11: Delete `complete-sprint`, update manifest and counts

**Skill:** none needed

**Acceptance criteria:**
- [ ] `complete-sprint` and its references are gone
- [ ] `commands/workflow-manifest.yaml` describes the new command graph
- [ ] `uvx skill-linter@<pin> stamp --check` passes

### T12: Pilots

**Skill:** none (run by the owner)

Goal runs launch with the writes-only deny set (git push and tag, gh PR and issue writes, `gh api` POST, PATCH and DELETE, tracker MCP writes, `AskUserQuestion`; reads allowed) passed on the command line; shared settings carry "ask" rules for the same actions, so attended `spec:complete` raises a prompt the owner approves. Two local test repos (Python with pytest, TypeScript with vitest) loaded with `claude --plugin-dir` from the build output; each runs a spec sized to cross an automatic compaction (forced earlier with `/autocompact <tokens>` if needed). Then a GitHub pilot on a throwaway private repo, deleted when done. Every run is judged by its final message (`<done_when>` evidence or `BLOCKED:`), never the exit status: a `-p` goal run can return `success` after the Stop-hook block cap with the goal unmet.

**Acceptance criteria:**
- [ ] Run 1 crosses an auto-compaction: `goal-prompt.md` is re-read, the evaluator still cites `<done_when>`, hooks still fire, state is rebuilt from the plan and `git log`
- [ ] Each run ends with `<done_when>` evidence or a `BLOCKED:` stop
- [ ] The marker abort, resume and `BLOCKED:` checks pass
- [ ] Seeded cases behave: one already-done ticket lands in Readiness, one blocked ticket is skipped while the rest run, one new issue and one skill question land in the open-questions collection, the batch runner compacts between batches with the same session id
- [ ] The evaluator's false-accept rate is recorded by comparing each "met" verdict with the boundary scripts and the gate
- [ ] The GitHub pilot covers sub-issues, blocked-by, the Project, `spec:complete` closing tickets then the group, the `Ticket:` trailer triggering no integration, `Closes #N` closing the GitHub issues at merge, and the `spec:complete` PR-feedback loop on a PR with "changes requested"
- [ ] Each deny pattern is confirmed, including from a subagent; `guard block`, `guard decide`, a refactor fix ticket, and a PR comment from a non-write account behave as designed
- [ ] Risks R for verifier secrets, unprotected marker files, `uvx` failing open, dependency pinning, token breadth and text-adapter instruction trust are checked and recorded
- [ ] Every finding is written up and either fixed or ticketed; the private repo is deleted

### T13: Docs rewrite

**Skill:** code-documenter

Rewrite every page that describes the workflow, as listed in the docs issue draft, building on the short pages from T4. Each changed or new page gets a human-voice pass reviewed by the owner.

**Acceptance criteria:**
- [ ] No page names a retired command
- [ ] Every changed or new page has had a human-voice pass
- [ ] `make validate` and the site build pass
