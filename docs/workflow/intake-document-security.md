# intake:document-security

Write a security-mechanisms reference (defense layers, authentication/verification gates, input validation, rate limiting, content moderation, secrets/attestation status, abuse controls, deny-by-default) read from what the code enforces.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-security.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `security-doc` | file | docs/security/security.md | Security mechanisms reference: the defense layers that protect the backend, with per-mechanism sections (authentication/verification gates, input/field validation, rate limiting, content moderation, secrets/attestation status, abuse controls, deny-by-default), each grounded in code. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. It is idempotent: a rerun overwrites what it owns. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
