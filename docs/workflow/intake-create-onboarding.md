# intake:create-onboarding

Write the onboarding index, `docs/README.md`, which ties together the project overview, quickstart, and links to all intake reference docs.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/create-onboarding.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `onboarding-doc` | file | docs/README.md | Onboarding index covering project overview, quickstart (setup and run), a structure pointer, and a linked index of all intake docs. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
