# intake:document-authorization

Write an authorization reference by first detecting the project's real authorization model (RBAC, ABAC, ownership/relationship-based, ACL, or a mix) and then documenting the identity/claims basis, the helper/primitive inventory, and a per-resource access matrix grounded in code.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-authorization.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `authorization-doc` | file | docs/security/authorization.md | Authorization and access-control reference: the project's actual authorization model (RBAC, ABAC, ownership/relationship-based, ACL, or a mix), the identity/claims basis, the helper/primitive inventory, and a per-resource access matrix (resource | read | create | update | delete) with the real conditions, plus server-only resources and the default rule. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
