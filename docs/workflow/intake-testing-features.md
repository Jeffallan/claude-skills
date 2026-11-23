# intake:testing-features

Write unit and component characterization tests for domain/service logic, pure functions, constant/type parity, and view logic, with a deliberate mocking boundary.

**Step:** capture-behavior (intake phase) · **Procedure file:** `references/intake/procedures/testing-features.md` · **Run:** `intake testing-features`

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

The procedure reads the matching documentation doc, stops at a checkpoint to confirm scope, writes tests that characterize current behavior, then runs them and reports fresh output. In an attended run the agent stops at the checkpoint so you can confirm or correct the scope; in a goal run it records the scope as a draft in the checklist note and goes on (see the [intake phase](intake-phase.md)). A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id.

Run it after `intake:testing-setup` and, ideally, `intake:document-features`. In a full intake run it writes at the same time as `intake:testing-authorization` and `intake:testing-owasp` (see the [intake phase](intake-phase.md)). A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
