# intake:testing-setup

Bootstrap a runnable test harness (unit, integration, and end-to-end layers) for a project that has none, or extend an existing one, so the domain testing commands can run.

**Step:** capture-behavior (intake phase) · **Command file:** `commands/intake/testing-setup.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `test-harness` | directory | (runner config, package scripts, integration-backend config, e2e driver config, tests/helpers) | A runnable test harness: a unit/component runner wired to the stack, an integration harness for the real datastore/backend, an end-to-end driver for the UI, shared fixtures/helpers, per-layer scripts, and one smoke test per layer proven to execute. |

## How it runs

The command reads the matching documentation doc, stops at a checkpoint to confirm scope, writes tests that characterize current behavior, then runs them and reports fresh output. A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
