# intake:document-api

Write an API reference for the backend surface (REST, GraphQL, RPC, and serverless/event-triggered functions) read from the handlers.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-api.md` · **Run:** `intake document-api`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `api-reference-doc` | file | docs/architecture/api-reference.md | API reference for the backend surface: the `## Operations` inventory built from the framework's resolved route table (one row per method and path with a stable OP-NNN id, source app/library/framework, and the resolved permission with the setting or default behind it, plus the listing command and its route count), then per-operation entries (trigger/route/method, request or event shape, behavior, side effects, errors, auth) across REST, GraphQL, RPC, and serverless/event-triggered shapes. |

## How it runs

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

The `## Operations` table comes from the route list the framework itself prints, so routes mounted by an auth library, an admin site or an older API version appear beside the app's own. Each row has an `OP-NNN` id that stays put across reruns, its source (the app, a named library, or the framework) and the permission that actually applies, with the setting or library default behind it. The doc and the checklist note both record the listing command and how many routes it printed, and the audit checks the table against that count. A permission that breaks an access rule, or contradicts what the code or docs say was intended, goes into the findings tracker.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
