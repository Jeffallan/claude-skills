# intake:document-api

Write an API reference for the backend surface (REST, GraphQL, RPC, and serverless/event-triggered functions) read from the handlers.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-api.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `api-reference-doc` | file | docs/architecture/api-reference.md | API reference for the backend surface: a summary table of every operation plus per-operation entries (trigger/route/method, request or event shape, behavior, side effects, errors, auth) across REST, GraphQL, RPC, and serverless/event-triggered shapes. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
