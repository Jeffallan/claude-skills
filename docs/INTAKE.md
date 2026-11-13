# Intake

Intake is how you adopt an existing codebase. It documents the code for the agents that will change it, writes tests that pin what the code does today, and records every bug it finds in one tracker. It runs once per project, before the first spec.

---

## What you get

| Output | Where | Written by |
|--------|-------|------------|
| Docstrings and module comments | Across the code | `intake:document-codebase` |
| Reference docs, one aspect each | `docs/architecture/`, `docs/domain/`, `docs/security/`, `docs/flows/`, `docs/operations/` | the twelve `intake:document-*` commands |
| An index of those docs | `docs/README.md` | `intake:create-onboarding` |
| A test harness with a smoke test per layer | Your test tree and package scripts | `intake:testing-setup` |
| Characterization tests | Your test tree | `intake:testing-features`, `-authorization`, `-owasp`, `-user-flows` |
| The findings tracker | `docs/intake-findings.md` | every command, appending |
| A baseline spec | `docs/specs/completed/baseline/overview.md` | `intake:create-system-description` |
| A system description | `docs/system-description.md` | `intake:create-system-description` |

The docs are written for an agent to rely on as the implementation contract, so every documentation command ends with an accuracy audit against the code. The testing commands end by running what they wrote and showing the output.

## Characterize, don't fix

Intake changes docs, tests, test configuration and docstrings. It never changes how the application behaves, even when it finds a bug.

A bug gets an id in `docs/intake-findings.md` (`F-001`, `F-002`, ...) and, when a test touches it, two tests: one that passes and pins what the code does now, and a twin, skipped or marked expected-fail, that asserts what it should do. Both name the id. When someone fixes the bug later, the first test fails and the twin starts passing, which is the signal to delete one and un-skip the other.

You decide what happens to each finding at close-out: ticket it, accept the risk, or mark it invalid.

## Running it by hand

Work through the checklist in order. Each item is one command.

1. **Docstrings.** `/fullstack-dev-skills:intake:document-codebase`. It runs your tests before and after and checks that no executable line changed.
2. **Reference docs.** The `intake:document-*` commands, then `intake:create-onboarding` last so it can link them. Each one stops at a checkpoint to show you its scope before writing.
3. **Harness.** `intake:testing-setup` proves each layer (unit, integration, end-to-end) with a smoke test before any real test is written.
4. **Tests.** `intake:testing-features`, then `-authorization`, `-owasp` and `-user-flows`. Each reads its matching doc.
5. **System description.** `intake:create-system-description` writes the baseline spec and `docs/system-description.md`.
6. **Gate and close-out.** Wire the cheap test layers into your PR checks and settle every finding.

The full checklist, with a copy-ready template, is `references/intake/checklist.md` in the plugin.

## Running it as a goal

Intake suits an unattended goal run: the work is long, every item has a check, and nothing in it needs a tracker or a push.

1. Cut a local branch, copy the checklist template to `docs/intake-checklist.md`, and fill the goal-prompt template (`references/intake/goal-prompt.md`) into `docs/intake-goal-prompt.md`. Commit both: that commit is the start SHA.
2. Launch a new session with the command in the template. It denies `AskUserQuestion`, pushes, PR and issue writes, and history rewrites for the whole run.
3. The run works one checklist item per command and one commit per item, and stops before the gate.

In a goal run no command asks you anything. A checkpoint becomes a draft: the command writes the question it would have asked, with its own best answer, into the Open questions table of `docs/intake-findings.md`, and carries on. Read that table first when the run ends.

Judge the run by its final message. It shows each `<done_when>` check, or starts with `BLOCKED:` and names the stop.

## After intake

The baseline spec puts the existing system in the spec index, so `spec:create` finds it when a new spec touches the same feature areas. When a spec finishes, `spec:complete` proposes updates to `docs/system-description.md` for that spec, once, and applies the ones you approve.

## Scoring a run

The plugin repo has an eval for finished intake runs (`evals/intake/EVAL.md`). Save the reflog, the goal-session transcript and the test output when the run ends; the eval reads them alongside the repo and reports a pass or fail for each guarantee: docs with their audits, tests that cite findings, a green suite, a diff limited to docs and tests, and a clean goal session.

## Commands

| Command | Page |
|---------|------|
| All intake commands, in order | [Intake phase](workflow/intake-phase.md) |
| The five testing commands | [Capture behavior](workflow/intake-capture-behavior.md) |
| Every workflow command | [Workflow Commands](WORKFLOW_COMMANDS.md) |
