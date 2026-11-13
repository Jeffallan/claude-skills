# intake:testing-user-flows

Write end-to-end tests for critical user journeys at two layers: backend flows through the real datastore and handlers, and UI flows driven through the actual screens.

**Step:** capture-behavior (intake phase) · **Command file:** `commands/intake/testing-user-flows.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `user-flow-tests` | directory | (integration flow tests + e2e UI specs) | End-to-end tests for critical journeys at two layers: backend flows through the real datastore/handlers (integration harness) asserting end-state and side effects, and UI flows driven through the actual screens with an e2e driver. Driver-unreachable steps stay in the backend layer; known-bug end-states are characterized and paired with a skipped intended-state test cross-referencing the finding id. |

## How it runs

The command reads the matching documentation doc, stops at a checkpoint to confirm scope, writes tests that characterize current behavior, then runs them and reports fresh output. A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id.

Run it after `intake:document-codebase`. Capture-behavior commands other than `intake:testing-setup` also need the harness that command builds. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
