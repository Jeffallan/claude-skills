# intake:document-integrations

Write a reference of every external service and SDK the project talks to (purpose, configuration, integration points, credentials, topology diagram) read from the code.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-integrations.md` · **Run:** `intake document-integrations`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `external-integrations-doc` | file | docs/architecture/external-integrations.md | External integrations reference. Covers every external service and SDK the project talks to, with purpose, where each is configured, in-code integration points, credentials/setup (no secret values), and a topology diagram. |

## How it runs

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract. In an attended run the agent stops at the checkpoint so you can confirm or correct the scope; in a goal run it records the scope as a draft in the checklist note and goes on (see the [intake phase](intake-phase.md)).

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
