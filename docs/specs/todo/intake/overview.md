# Intake (v0.5.x)

**Spec:** intake
**Discovery:** none
**After:** none
**Feature areas:** intake, documentation, characterization-tests
**Status:** In progress, local goal run
**Branch:** feat/v0.5.x-intake, base feat/v0.5.0-workflow at c8300d5
**Created:** 2026-11-11

---

## Readiness

| Ticket | Readiness | Evidence or question |
|--------|-----------|----------------------|
| I1 | Ready | The 13 documentation and 5 testing command specs are staged in the planning notes with their YAML contracts |
| I2 | Ready | The staged README and CHECKLIST define the findings tracker, the `docs/` layout, the checkpoint, the accuracy audit and run-and-verify |
| I3 | Ready | #120 and CHECKLIST Phase 1 describe the docstring pass; `commands/intake/document-codebase.yaml` exists as `planned` |
| I4 | Ready | The roadmap's v0.5.x line defines the baseline spec and the system-description flow; `references/specs/layout.md` defines `completed/` and the index |
| I5 | Ready | `references/specs/templates/goal-prompt.md`, `references/specs/launch.md` and the staged `goal-checklist-runner.md` exist |
| I6 | Ready | `evals/workflow/` and `scripts/eval_workflow_run.py` give the eval shape and the transcript checks |
| I7 | Ready | Depends on I1 to I6 only |
| I8 | Ready | The Timekeeper repo exists and a `timekeeper` session owns it; the runbook lives in the intake notes, outside this repo |

## 1. Purpose

Ship the intake phase: the commands that turn an existing, undocumented codebase into agent-readable reference docs, a characterization test suite and a findings tracker, and that retrofit the result into the spec model as a baseline spec and a living system description. Intake has been a set of `planned` placeholders since v0.5.0; this spec promotes the staged command set and makes it runnable as a goal.

## 2. Scope

**In:**
- I1: the staged `document-*`, `testing-*` and `create-onboarding` commands promoted to `commands/intake/`, registered and documented.
- I2: `references/intake/`, the rules every intake command shares, including the unattended behavior.
- I3: `intake:document-codebase`, the docstring pass.
- I4: the baseline spec, `intake:create-system-description`, and the system-description step in `spec:complete`.
- I5: `references/intake/checklist.md` and the intake goal-prompt template.
- I6: `evals/intake/`, a scorer for finished intake runs, tested on synthetic runs in `make test`.
- I7: the intake guide and the docs that point to it.
- I8: the Timekeeper pilot runbook, handed to the `timekeeper` session.

**Out:**
- Running the pilot itself (the `timekeeper` session runs it).
- A gold set for the intake eval (the pilot supplies the first).
- The PR gate wiring of CHECKLIST Phase 4 as a command (it stays a checklist item).
- Any change to skill-linter.

## 3. Success criteria

- `make validate` reports 0 errors and `make test` passes, including the intake eval tests.
- A `--plugin-dir` session lists every `fullstack-dev-skills:intake:*` command (`make evidence`).
- `guard spec-index --check` passes.

## 4. Design

| Area | Decision |
|------|----------|
| Capture behavior | The planned `capture-behavior.yaml` is replaced by the five `testing-*` commands; `intake:capture-behavior` survives only as the name of the testing step in the docs |
| Phase | Every intake command uses `phase: intake` (skill-linter's allowed phases); the staged `phase: capture-behavior` is folded in |
| Unattended | Documentation and testing commands are `unattended: true` and use no adapter operations. In a goal run a checkpoint becomes a draft plus open questions in the findings tracker |
| Characterize, don't fix | A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id |
| Baseline spec | Intake writes `docs/specs/completed/baseline/overview.md` so the spec index knows the existing system |
| System description | `create-system-description` reads the spec index and completed specs; `spec:complete` proposes updates once per spec, attended |

## 5. Reuse

- `references/specs/layout.md`, `references/specs/unattended.md`, `references/specs/launch.md` and `references/specs/templates/goal-prompt.md`.
- `scripts/eval_workflow_run.py` and `evals/workflow/EVAL.md` for the eval's transcript checks and shape.
- `skills/spec-miner`, `skills/code-documenter`, `skills/test-master` and the language and framework skills, unchanged.

## 6. Debt in scope

- `commands/intake/capture-behavior.yaml` and the three `planned` intake definitions (I1, I3, I4).
- `docs/workflow/intake-*.md` pages that describe the v0.5.0 plan's three-command intake (I1, I7).

## 7. Risks

- The staged specs came from one dogfood pass; the Timekeeper pilot (I8) is the first test on a second stack.
- The eval has no gold set, so its thresholds are untested on a real run until the pilot.
- Goal runs can stall on a checkpoint; I2's unattended rule and the launch deny set cover it.

## 8. Linked tickets

Local IDs I0 to I8, no tracker group yet.
