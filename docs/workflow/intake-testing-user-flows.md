# intake:testing-user-flows

Write end-to-end tests for critical user journeys at two layers: backend flows through the real datastore and handlers, and UI flows driven through the actual screens.

**Step:** capture-behavior (intake phase) · **Procedure file:** `references/intake/procedures/testing-user-flows.md` · **Run:** `intake testing-user-flows`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `user-flow-tests` | directory | (integration flow tests + e2e UI specs) | End-to-end tests for critical journeys at two layers: backend flows through the real datastore/handlers (integration harness) asserting end-state and side effects, and UI flows driven through the actual screens with an e2e driver. Each journey adds UI and API parity cases (INV-5: every control the UI hides or disables is refused by the server, and every action the UI offers is confirmed by re-reading server state) and one negative variant where the wrong principal or state attempts the key step. The coverage map has a column for each. Driver-unreachable steps stay in the backend layer; known-bug end-states are characterized and paired with a skipped intended-state test cross-referencing the finding id. |

## How it runs

The procedure reads the matching documentation doc, stops at a checkpoint to confirm scope, writes tests that characterize current behavior, then runs them and reports fresh output. In an attended run the agent stops at the checkpoint so you can confirm or correct the scope; in a goal run it records the scope as a draft in the checklist note and goes on (see the [intake phase](intake-phase.md)). A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id.

Each journey also checks that the UI and the server agree. When the UI hides or disables a control, the test sends that operation straight to the server and expects a refusal. When the UI offers an action, the test performs it and then reads the server state back, which catches a button that reports success and changes nothing. Every journey gets one negative variant too, where the wrong user or an object in the wrong state tries the key step. A hidden operation the server accepts, an offered action that changes nothing, or a negative variant that succeeds each becomes a finding.

Run it after `intake:document-codebase`. Capture-behavior procedures other than `intake:testing-setup` also need the harness that procedure builds. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
