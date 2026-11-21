# intake:document-glossary

Write an alphabetical glossary of the project's domain and product vocabulary, each term defined and grounded in the code that defines or uses it.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-glossary.md` · **Run:** `intake document-glossary`

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

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract. In an attended run the agent stops at the checkpoint so you can confirm or correct the scope; in a goal run it records the scope as a draft in the checklist note and goes on (see the [intake phase](intake-phase.md)).

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
