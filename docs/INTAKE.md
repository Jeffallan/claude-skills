# Intake

Intake is how you adopt an existing codebase. It documents the code for the agents that will change it, writes tests that pin what the code does today, and records every bug it finds in one tracker. It runs once per project, before the first spec.

---

## What you get

| Output | Where | Written by |
|--------|-------|------------|
| Docstrings and module comments | Across the code | `document-codebase` |
| Reference docs, one aspect each | `docs/architecture/`, `docs/domain/`, `docs/security/`, `docs/flows/`, `docs/operations/` | the twelve `document-*` procedures |
| An index of those docs | `docs/README.md`, or `docs/README-intake.md` beside your own | `create-onboarding` |
| A test harness with a smoke test per layer | Your test tree and package scripts | `testing-setup` |
| Characterization tests | Your test tree | `testing-features`, `-authorization`, `-owasp`, `-user-flows` |
| The findings tracker | `docs/intake-findings.md` | every procedure, appending; the intake session applies the parallel testing batch's entries |
| A baseline spec | `docs/specs/completed/baseline/overview.md` | `create-system-description` |
| A system description | `docs/system-description.md` | `create-system-description` |

The docs are written for an agent to rely on as the implementation contract, so every documentation command ends with an accuracy audit against the code. They cite only the project's own code; for an installed dependency they name the package and the version the lockfile pins, never a path inside `node_modules/` or another vendored folder. The testing commands end by running what they wrote and showing the output.

## Characterize, don't fix

Intake changes docs, tests, test configuration and docstrings. It never changes how the application behaves, even when it finds a bug.

A bug gets an id in `docs/intake-findings.md` (`F-001`, `F-002`, ...) and, when a test touches it, two tests: one that passes and pins what the code does now, and a twin, skipped or marked expected-fail, that asserts what it should do. Both name the id. When someone fixes the bug later, the first test fails and the twin starts passing, which is the signal to delete one and un-skip the other.

You decide what happens to each finding at close-out: ticket it, accept the risk, or mark it invalid.

Every finding is committed with its severity. A security finding, at any severity and in any repo, keeps its reproduction detail (the requests, payloads, credentials and exploit steps) in `docs/intake-findings-restricted.md`. Intake adds that file to `.git/info/exclude` so it is never committed, and the tracker describes the problem in plain terms. The tests that pin the finding are committed, named for what they check and not for how to exploit it. Someone who reads them can still work out the attack, so they are the exposure that remains. Keep the restricted file somewhere safe until the findings are fixed: git doesn't carry it, so a fresh clone or another machine won't have it.

## Running it by hand

Run `/fullstack-dev-skills:intake` on a branch of its own. It creates `docs/intake-checklist.md` when it is missing and works it in order, one procedure per item. Each procedure runs in one of the plugin's agents (`doc-writer`, `test-writer`, `security-prober`, `architect`). The agent stops at a checkpoint to show you its scope, you confirm or correct it, and the same agent then writes. The command reviews what the agent changed and commits the item. Stop whenever you like; the next run starts from the first unchecked item. `intake <procedure>` runs or reruns one procedure.

1. **Findings tracker and existing docs.** The command starts `docs/intake-findings.md`, then `existing-docs` maps the docs you already have and checks them against the code.
2. **Docstrings.** `document-codebase`. It runs your tests before and after and checks that no executable line changed.
3. **Reference docs.** The `document-*` procedures, then `create-onboarding` last so it can link them.
4. **Harness.** `testing-setup` proves each layer (unit, integration, end-to-end) with a smoke test before any real test is written.
5. **Tests.** `testing-features`, `-authorization` and `-owasp` write at the same time, and the command commits them one at a time. `-user-flows` runs after them. Each reads its matching doc.
6. **System description.** `create-system-description` writes the baseline spec and `docs/system-description.md`.
7. **Gate and close-out.** You do this by hand after the command ends: wire the cheap test layers into your PR checks and settle every finding.

The full checklist, with a copy-ready template, is `references/intake/checklist.md` in the plugin.

## Running it as a goal

Intake suits an unattended goal run: the work is long, every item has a check, and nothing in it needs a tracker or a push.

1. Cut a local branch, copy the checklist template to `docs/intake-checklist.md`, and fill the goal-prompt template (`references/intake/goal-prompt.md`) into `docs/intake-goal-prompt.md`. Commit both: that commit is the start SHA.
2. Launch a new session with the command in the template. It denies `AskUserQuestion`, pushes, PR and issue writes, and history rewrites for the whole run.
3. The run calls the `intake` command for each checklist item, one commit per item, and stops before the gate.

In a goal run nothing asks you anything, so no agent stops at its checkpoint. Each one does its item in one pass and reports the scope it would have shown as a draft, which goes in the item's checklist note. A choice you could reasonably make differently goes into the Open questions table of `docs/intake-findings.md` with the run's own best answer. The run carries on, and while one item writes, read-only agents already gather facts for the next. Read that table first when the run ends.

Judge the run by its final message. It shows each `<done_when>` check, or starts with `BLOCKED:` and names the stop. It also gives the full suite's counts, the blocked count among them, with each test layer that couldn't run here and why. A suite that exits 0 with blocked tests is not green.

## After intake

The baseline spec puts the existing system in the spec index, so `spec:create` finds it when a new spec touches the same feature areas. When a spec finishes, `spec:complete` proposes updates to `docs/system-description.md` for that spec, once, and applies the ones you approve. `spec:current` compiles the description into `docs/current-state.json`, which `spec:diff` and `common-ground` read.

## Scoring a run

The plugin repo has an eval for finished intake runs (`evals/intake/EVAL.md`). Save the reflog, the goal-session transcript and the test output when the run ends; the eval reads them alongside the repo and reports a pass or fail for each guarantee: docs with their audits, tests that cite findings, a green suite, a diff limited to docs and tests, and a clean goal session.

## Commands

| Command | Page |
|---------|------|
| All intake procedures, in order | [Intake phase](workflow/intake-phase.md) |
| The five testing procedures | [Capture behavior](workflow/intake-capture-behavior.md) |
| Every workflow command | [Workflow Commands](WORKFLOW_COMMANDS.md) |
