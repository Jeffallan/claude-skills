# intake:testing-authorization

Write characterization tests that lock in the project's access-control model by asserting both authorized-allow and unauthorized-deny for every resource and verb against the real enforcement layer.

**Step:** capture-behavior (intake phase) · **Command file:** `commands/intake/testing-authorization.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `authorization-tests` | directory | (test directory; one file per resource) | Characterization tests for the access-control model: authorized-allow and unauthorized-deny per resource and verb, plus the gates (authentication, identity verification, ownership/participation, immutability), run against the real enforcement layer where the harness allows. Known authorization bugs are characterized and paired with a skipped intended-fix test cross-referencing the finding id. |

## How it runs

The command reads the matching documentation doc, stops at a checkpoint to confirm scope, writes tests that characterize current behavior, then runs them and reports fresh output. A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id.

Run it after `intake:document-codebase`. Capture-behavior commands other than `intake:testing-setup` also need the harness that command builds. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
