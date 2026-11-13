# intake:document-features

Write a feature catalog (what the application does today, grouped by area, with user-visible behavior and implementing files) read from the code's behavioral surfaces.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-features.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `features-doc` | file | docs/domain/features.md | Feature catalog: a Feature/Area/Key-files summary table plus per-feature subsections (what it does, user-visible behavior, implementing files), covering only features present in the code. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
