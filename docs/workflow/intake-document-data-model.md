# intake:document-data-model

Write a data-model reference (entities, fields, relationships, ER diagram) read from the project's persistence layer.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-data-model.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `data-model-doc` | file | docs/architecture/data-model.md | Data model reference: entities (tables/collections), field shapes with enforced constraints and a Flags column marking state, ownership/tenant, privilege and money/quantity fields, relationships, enumerations, and an ER diagram. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Each entity table has a `Flags` column. It marks fields that hold state (status enums, active or verified flags, soft-delete stamps), ownership and tenant keys, fields that grant privilege (a role, an admin flag), and money or quantity fields. The authorization doc builds its access matrix from these flags. A flagged field a caller can write with no check goes into the findings tracker.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
