# intake:document-file-tree

Write an annotated repository map (directory tree with per-path roles, the framework's routing/structure conventions, and a "where new code goes" table) read from the project's layout.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-file-tree.md` · **Run:** `intake document-file-tree`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `file-tree-doc` | file | docs/architecture/file-tree.md | Annotated repository map: directory tree with the role of each significant path, the framework's routing/structure conventions, and a where-new-code-goes table. |

## How it runs

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
