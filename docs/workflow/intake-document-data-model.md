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
| `data-model-doc` | file | docs/architecture/data-model.md | Data model reference: entities (tables/collections), field shapes with enforced constraints, relationships, enumerations, and an ER diagram. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
