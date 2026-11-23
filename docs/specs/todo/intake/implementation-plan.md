# Intake implementation plan

**Spec:** intake
**Status:** In progress, local goal run

## Summary

| Metric | Value |
|--------|-------|
| **Tickets** | 8 (I1 to I8; I0 records this plan) |
| **Branch** | `feat/v0.5.x-intake` (local only) |
| **Verification** | `make validate`, `make test`, `make evidence` |

---

## Completion Status

| Ticket | Status | Completed Date | Notes |
|--------|--------|----------------|-------|
| I1 | Done | 2026-11-11 | 18 commands promoted to `commands/intake/` (12 `document-*`, `create-onboarding`, 5 `testing-*`), `status: existing`, `unattended: true`, no adapter operations; registered in plugin.json, the manifest's `run_once` intake phase, a docs page each and the sidebar; `capture-behavior.yaml` replaced, the name kept as the step page; `requires` emptied (skill-linter allows only `ticketing`), order kept in prose; workflowCount stamped 9 to 27. Check: stand-in `i1-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| I2 | Done | 2026-11-11 | `references/intake/findings.md` (tracker shape, `F-NNN` ids, characterize don't fix with paired characterization and skipped or expected-fail tests, close-out) and `references/intake/rules.md` (output layout, what intake may change, checkpoint, accuracy audit, run and verify, goal-run behavior: no `AskUserQuestion`, checkpoint becomes a draft plus Open questions in the tracker); all 18 intake commands cite both and drop the old non-interactive rule. Check: stand-in `i2-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| I3 | Done | 2026-11-11 | `intake:document-codebase` written: baseline test run and start commit, docstring style kept or chosen per language, public-API-first inventory, docstrings stating behavior, errors, side effects and access, findings with ids instead of fixes; proof is the same test result before and after plus a diff check (AST for Python, comment-stripped compare for JS and TS, comment-line check elsewhere). `existing`, registered, page rewritten; workflowCount stamped to 28. Check: stand-in `i3-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| I4 | Done | 2026-11-11 | `intake:create-system-description` written: first run writes `docs/specs/completed/baseline/overview.md` (`Spec: baseline`, feature areas from `docs/domain/features.md` plus security, data-model, integrations) and regenerates the index; full pass first, then folds in completed specs missing from its Change history. `spec:complete` Step 6 gains one attended, once-per-spec proposal of description updates, plus a Report row. Baseline template checked with `guard spec-index` in a scratch repo (exit 0). Check: stand-in `i4-check.sh` exit 1 before, 0 after; `make validate` 0 errors; workflowCount 29 |
| I5 | Done | 2026-11-11 | `references/intake/checklist.md` (four phases, one item per command, smoke test before real tests, verify before checking, Phase 4 attended) and `references/intake/goal-prompt.md` (template on the spec goal prompt and the checklist runner: start SHA from the prompt's commit, one commit per item with an `Intake:` trailer, diff limited to docs and tests, stops, launch command with the `launch.md` deny set minus the ticket-guard allow, reflog, transcript and test output saved for scoring). Check: stand-in `i5-check.sh` exit 1 before, 0 after; `make validate` 0 errors |
| I6 | Done | 2026-11-11 | `scripts/eval_intake_run.py` scores a finished intake run on 7 repo checks (docs with accuracy audit, findings tracker, skipped or expected-fail tests citing tracked ids, suite green, diff limited to docs, tests, test config and docstrings, one `Intake:` commit per item, no history rewrite) plus the 4 transcript checks reused from `eval_workflow_run.py`; `evals/intake/EVAL.md`, `make eval-intake`. No gold set yet. RED: `bash scripts/test-eval-intake.sh` 1 passed, 18 failed before; GREEN: 19 passed, in `make test`; `make validate` 0 errors Follow-up 2026-11-11: test files now come from the `Test paths:` line `intake:testing-setup` records, plus `--test-path`, with a wider fallback (Django `tests.py`, `Tests/`, `*.Tests/`, `__mocks__/`, `androidTest/`, `*_spec.rb`) and `spec/`, `fixtures/`, `testing/` counted only inside a test tree; test 18 passed, 6 failed before, 24 passed after |
| I7 | Done | 2026-11-11 | `docs/INTAKE.md` guide (outputs, characterize don't fix, by hand, as a goal, after intake, scoring), synced to `/guides/intake/` and in the sidebar; Intake section, table rows and TOC entry in `docs/WORKFLOW_COMMANDS.md`; QUICKSTART and README mentions; six Unreleased CHANGELOG entries. Human-voice pass on the guide and the intake workflow pages fixed two quoted openings and the repeated "Generate an accurate, agent-readable ... by reverse-engineering" openings. Check: stand-in `i7-check.sh` exit 1 before, 0 after; site build 120 pages, links valid; `make validate` 0 errors |
| I8 | Done | 2026-11-11 | Runbook written in the intake notes folder (`timekeeper-pilot-runbook.md`, outside this repo): build the plugin and confirm the 20 intake commands load, prepare a local Timekeeper branch with the checklist and goal prompt, launch with `--plugin-dir`, expected output per command, score with `make eval-intake`, report back. Path sent to the `timekeeper` session by message (delivered). Check: stand-in `i8-check.sh` exit 1 before, 0 after |

Each row is updated in its ticket's commit, so the table holds no SHAs; `git log --grep "Ticket: <ID>"` finds the commit.

---

## Execution Order

| # | Ticket | Summary | Risk | Dependencies |
|---|--------|---------|------|--------------|
| 1 | I1 | Promote the intake command set | Medium | None |
| 2 | I2 | Shared intake reference | Low | I1 |
| 3 | I3 | `intake:document-codebase` | Low | I2 |
| 4 | I4 | Baseline spec and `intake:create-system-description` | Medium | I2 |
| 5 | I5 | Running intake as a goal | Medium | I1 to I4 |
| 6 | I6 | The intake eval | Medium | I2, I5 |
| 7 | I7 | Documentation | Low | I1 to I6 |
| 8 | I8 | Timekeeper pilot runbook | Low | I1 to I7 |

---

## Tickets

### I1: Promote the intake command set

**Skill:** prompt-engineer
**Type:** stand-in

Copy each staged `document-*`, `testing-*` and `create-onboarding` spec into `commands/intake/<name>.md` with its `<name>.yaml`, adapted to this repo (`${CLAUDE_PLUGIN_ROOT}` paths, `fullstack-dev-skills:` skill names, frontmatter, prose rules). Definitions get `status: existing`, `unattended` and `adapter-operations`. Register each in `plugin.json`, the manifest's `intake` phase and a `docs/workflow/intake-<name>.md` page with a sidebar entry. Replace `capture-behavior.yaml` with the `testing-*` set. Stamp the workflow count.

**Acceptance criteria:**
- [ ] Stand-in check: every staged command has a `.md`, a `.yaml` with `status: existing`, a plugin entry, a manifest entry and a docs page; `capture-behavior.yaml` is gone
- [ ] `make validate` 0 errors, `stamp --check` passes

### I2: Shared intake reference

**Skill:** prompt-engineer
**Type:** stand-in

`references/intake/`: the findings tracker (`docs/intake-findings.md`, finding ids, characterize don't fix), the `docs/` output layout, the checkpoint and accuracy audit of documentation commands, the run-and-verify phase of testing commands, and the unattended behavior (no `AskUserQuestion` in a goal run; a checkpoint becomes a draft plus open questions in the tracker). Every intake command points at it.

**Acceptance criteria:**
- [ ] Stand-in check: the reference covers each topic and every intake command cites it
- [ ] `make validate` 0 errors

### I3: `intake:document-codebase`

**Skill:** code-documenter
**Type:** stand-in

The docstring pass from #120 and CHECKLIST Phase 1, written for agents, naming the language and framework skill by detection. It changes comments and docstrings only, proven by the project's test suite passing before and after and a diff check that no executable line changed.

**Acceptance criteria:**
- [ ] Stand-in check: the command exists as `existing`, names the before/after test run and the executable-line diff check
- [ ] `make validate` 0 errors

### I4: Baseline spec and `intake:create-system-description`

**Skill:** architecture-designer
**Type:** stand-in

Intake writes `docs/specs/completed/baseline/overview.md` (`Spec: baseline`, `Feature areas:` from the documentation phase). `create-system-description` reads the spec index and completed specs and writes `docs/system-description.md`, with a full pass on the first run. `spec:complete` gains one attended step that proposes system-description updates for the finished spec.

**Acceptance criteria:**
- [ ] Stand-in check: the command, its baseline-spec step and the `spec:complete` step exist
- [ ] `make validate` 0 errors

### I5: Running intake as a goal

**Skill:** prompt-engineer
**Type:** stand-in

`references/intake/checklist.md` and an intake goal-prompt template on `references/specs/templates/goal-prompt.md` and the checklist runner: one command per item, the harness proven by a smoke test first, findings collected, the launch command and deny set from `references/specs/launch.md`, and the transcript, reflog and results saved for scoring.

**Acceptance criteria:**
- [ ] Stand-in check: both files exist with each named element
- [ ] `make validate` 0 errors

### I6: The intake eval

**Skill:** test-master
**Type:** test

`evals/intake/EVAL.md` and a scorer for a finished intake run: each documentation doc exists with its accuracy-audit section; the findings tracker exists and every bug-pinning test names a finding id; the characterization suite runs green; the diff since the intake start touches only docs, tests, test config and docstrings; plus the transcript checks of `scripts/eval_workflow_run.py`. Tested on a synthetic good run and a synthetic bad run in `make test`.

**RED:** `bash scripts/test-eval-intake.sh` fails before the scorer exists.

**Acceptance criteria:**
- [ ] The good run passes every check and the bad run fails the expected ones, in `make test`
- [ ] `make validate` 0 errors

### I7: Documentation

**Skill:** code-documenter
**Type:** stand-in

An intake section in `docs/WORKFLOW_COMMANDS.md`, `docs/INTAKE.md` (synced and in the sidebar), QUICKSTART and README mentions, Unreleased CHANGELOG entries, and a human-voice pass on the guide and the workflow pages.

**Acceptance criteria:**
- [ ] Stand-in check: each document mentions intake and the guide is in the sidebar
- [ ] `make validate` 0 errors

### I8: Timekeeper pilot runbook

**Skill:** none
**Type:** stand-in

`timekeeper-pilot-runbook.md` in the intake notes folder, outside this repo: build the plugin, run intake on a local Timekeeper branch, what each command should produce, and how to score it with the I6 eval. Its path goes to the `timekeeper` session, which runs the pilot.

**Acceptance criteria:**
- [ ] Stand-in check: the runbook exists and names each section
- [ ] The `timekeeper` session got the path
