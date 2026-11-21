# intake:document-features

Write a feature catalog (what the application does today, grouped by area, with user-visible behavior and implementing files), the state machines of entities with a status, and the business rules the features imply, all read from the code.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-features.md` · **Run:** `intake document-features`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `features-doc` | file | docs/domain/features.md | Feature catalog: a Feature/Area/Key-files summary table plus per-feature subsections (what it does, user-visible behavior, implementing files), covering only features present in the code; state machines for domain entities with a status (every writer of each state field as a transition, with its routes by operation id and who may call them); and project invariants INV-7 onward, each citing evidence of intent. Breaks go to the findings tracker. |

## How it runs

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract. In an attended run the agent stops at the checkpoint so you can confirm or correct the scope; in a goal run it records the scope as a draft in the checklist note and goes on (see the [intake phase](intake-phase.md)).

For each entity with a status (an order, an invoice, a subscription, a booking), the procedure builds a state machine from every place that writes the status: your code, library routes and webhooks, the admin site, background jobs, signals and hooks, and migrations. Each transition lists the operations that reach it (by id from `docs/architecture/api-reference.md`) and who may call them. A transition with no named actor is a finding. The procedure also writes down the business rules your features imply, such as "a refund never exceeds the charge", as `INV-7` onward. Each rule cites the validator, test, comment or doc showing you intend it. A path that breaks a rule is a finding, and `intake:document-authorization` and `intake:testing-owasp` test the rules by id. The table and the invariants are defined in `references/intake/access-control.md`.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
