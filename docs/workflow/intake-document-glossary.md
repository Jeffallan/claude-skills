# intake:document-glossary

Write an alphabetical glossary of the project's domain and product vocabulary, each term defined and grounded in the code that defines or uses it.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-glossary.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `glossary-doc` | file | docs/domain/glossary.md | Alphabetical glossary of the project's domain and product vocabulary, every term defined and grounded in the code that defines or uses it. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
