# intake:testing-setup

Bootstrap a runnable test harness (unit, integration, and end-to-end layers) for a project that has none, or extend an existing one, so the domain testing procedures can run.

**Step:** capture-behavior (intake phase) · **Procedure file:** `references/intake/procedures/testing-setup.md` · **Run:** `intake testing-setup`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `test-harness` | directory | (runner config, package scripts, integration-backend config, e2e driver config, tests/helpers) | A runnable test harness: a unit/component runner wired to the stack, an integration harness for the real datastore/backend, an end-to-end driver for the UI, shared fixtures/helpers, per-layer scripts, a safety guard that fails the test session closed unless the database host, mail backend, payment, storage and external API base URLs point at local or test resources, and one smoke test per layer (the guard included) proven to execute. |

## How it runs

The procedure checks what test tooling exists, picks a runner for each layer, and stops at a checkpoint to confirm the toolchain. It then installs the tools, adds the scripts and helpers, and proves each layer with a smoke test. Before any adversarial test can run, it adds a safety guard to the start of the test session: when the database host, mail backend, payment, storage or an external API URL points anywhere other than a local or test resource, the guard stops the run. An unset value counts as unsafe. The guard gets its own smoke test, and the targets it checks go in the checklist note.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
