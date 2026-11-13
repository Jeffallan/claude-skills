# intake:document-analytics

Write a product-analytics reference (telemetry setup, an event catalog, and identity wiring) read from the instrumentation.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-analytics.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `analytics-events-doc` | file | docs/operations/analytics-events.md | Product-analytics reference: telemetry setup and enablement, an event catalog table (event, when it fires, params, call site), identity and user-property wiring, and flags for events defined-but-never-fired and fired-but-undefined. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
