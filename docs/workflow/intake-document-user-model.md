# intake:document-user-model

Write a model of the application's primary actor (representations, identity, lifecycle state machine, completeness rules, account lifecycle) read from the auth and profile layers.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-user-model.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `user-model-doc` | file | docs/domain/user-model.md | Primary-actor model reference: the principal entity's representations (public/own/stored), identity, lifecycle state machine, completeness/validation rules, and account lifecycle. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
