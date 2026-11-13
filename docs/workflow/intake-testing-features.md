# intake:testing-features

Write unit and component characterization tests for domain/service logic, pure functions, constant/type parity, and view logic, with a deliberate mocking boundary.

**Step:** capture-behavior (intake phase) · **Command file:** `commands/intake/testing-features.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `feature-tests` | directory | (test directory; unit, parity, and view tests) | Unit and component characterization tests for domain/service functions, pure helpers, constant/enumeration parity between duplicated sources of truth, type vs view-model contracts, and view/screen logic, with a deliberate mocking boundary. Known bugs are characterized and paired with a skipped intended-fix test cross-referencing the finding id. |

## How it runs

The command reads the matching documentation doc, stops at a checkpoint to confirm scope, writes tests that characterize current behavior, then runs them and reports fresh output. A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id.

Run it after `intake:document-codebase`. Capture-behavior commands other than `intake:testing-setup` also need the harness that command builds. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
