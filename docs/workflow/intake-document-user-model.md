# intake:document-user-model

Write a model of the application's primary actor (representations, identity, lifecycle state machine, blocking states, completeness rules, account lifecycle) read from the auth and profile layers.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-user-model.md` · **Run:** `intake document-user-model`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `user-model-doc` | file | docs/domain/user-model.md | Primary-actor model reference: the principal entity's representations (public/own/stored), identity, lifecycle state machine (every writer of each state field as a transition, with its routes by operation id and who may call them), blocking states (operations still allowed, every way out, credentials that survive entry), completeness/validation rules, and account lifecycle. INV-2 and INV-6 breaks go to the findings tracker. |

## How it runs

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

The procedure finds transitions by searching for every place that writes a state field: your own code, the routes a library mounts, the admin site, background jobs, signals and hooks, and migrations. Each transition lists the operations that reach it (by id from `docs/architecture/api-reference.md`) and who may call them. Each blocking state, such as deactivated or suspended, gets its own section: what the account can still do, every way out, and which sessions, tokens and emailed links still work after the account enters it. A way out the account can take on its own, or a credential that keeps working, is a finding unless the code or docs show you meant it. The same goes for a transition with no named actor. The access matrix in `intake:document-authorization` uses each blocking state as a column. The table and the invariants are defined in `references/intake/access-control.md`.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
