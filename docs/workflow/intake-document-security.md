# intake:document-security

Write a security-mechanisms reference (defense layers, authentication/verification gates, tokens and their properties, input validation, rate limiting, content moderation, secrets/attestation status, abuse controls, deny-by-default) read from what the code enforces.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-security.md` · **Run:** `intake document-security`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `security-doc` | file | docs/security/security.md | Security mechanisms reference: the defense layers that protect the backend, with per-mechanism sections (authentication/verification gates, tokens, input/field validation, rate limiting, content moderation, secrets/attestation status, abuse controls, deny-by-default), each grounded in code. The Tokens section lists every token type the system issues with its expiry, single use, user and purpose binding, and the state changes that void it, each cited; a missing property without intent evidence becomes a finding in docs/intake-findings.md. |

## How it runs

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

The doc describes each mechanism as built. When a token lacks a property its kind needs, or a control breaks an access invariant, and nothing in the code or docs says the project meant it, the procedure files a finding and the doc cites its id. Where intent is unclear, it adds an Open question instead.

Run it after `intake:document-codebase` and `intake:document-user-model`, since token voiding is checked against the account states the user model lists. If the user model is missing, the procedure works from the code and adds an Open question. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
