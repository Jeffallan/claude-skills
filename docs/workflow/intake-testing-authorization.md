# intake:testing-authorization

Write table-driven characterization tests that run every cell of the project's access matrix (operation x principal) through the real request stack, plus a route ratchet that fails on any route with no access decision.

**Step:** capture-behavior (intake phase) · **Procedure file:** `references/intake/procedures/testing-authorization.md` · **Run:** `intake testing-authorization`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `authorization-tests` | directory | (test directory; the matrix table, the route ratchet, fixtures per principal) | Table-driven characterization tests over the access matrix: one row per operation and principal (cited by OP id and principal) with its expected outcome, plus object-level (other owner, other tenant), protected-field and state-transition rows, sent through the real request stack and re-reading stored state after every write. A route ratchet fails on any resolved route with no table row. A sample of deny rows is proven to fail with the guard removed in a scratch copy. Known bugs are characterized and paired with an expected-fail twin row carrying the finding id. A separate commit updates the matrix cell statuses in docs/security/authorization.md to [t] or [n: reason], leaving no [x]. |

## How it runs

The procedure reads the access matrix in `docs/security/authorization.md` and the operation inventory, then stops at a checkpoint to confirm scope. Each matrix cell becomes one row of a single table-driven test, named by its operation id and principal. Rows for other owners' and other tenants' objects, protected fields and state transitions go in the same table. Requests pass through the real login and token handling, and every write is checked by reading the stored data back. A route ratchet lists the app's routes at test time and fails when one has no row, so a new route can't ship without an access decision.

To show the deny rows can fail, the procedure copies the project to a scratch folder, removes the guard behind at least five of them, and checks that each one fails. Your repo stays untouched, and the results go in the checklist note. A known bug gets a passing row for today's behavior and an expected-fail twin for the intended one, both naming the finding id. A final commit marks each matrix cell `[t]` (tested) or `[n: reason]`.

Run it after `intake:testing-setup` and `intake:document-authorization`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
