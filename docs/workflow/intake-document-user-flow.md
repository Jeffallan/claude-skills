# intake:document-user-flow

Write a user-flow reference (routes, entry points, end-to-end journeys with per-journey flowcharts) read from the project's routing and navigation layer.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-user-flow.md` · **Run:** `intake document-user-flow`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `user-flow-doc` | file | docs/flows/user-flow.md | User-flow reference covering the application's routes/entry points, end-to-end user journeys grounded in real routes and handlers, per-journey numbered steps, and a Mermaid flowchart for each journey. |

## How it runs

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
