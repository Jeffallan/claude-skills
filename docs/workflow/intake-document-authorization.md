# intake:document-authorization

Write an authorization reference grounded in code. It names the project's real authorization model (RBAC, ABAC, ownership/relationship-based, ACL, or a mix), then crosses every operation in the API inventory with every principal, blocking states included, and checks each cell against a set of access invariants.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-authorization.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `authorization-doc` | file | docs/security/authorization.md | Authorization and access-control reference: the actual authorization model (RBAC, ABAC, ownership/relationship-based, ACL, or a mix), the identity/claims basis and primitives, the principals (one column per role and per blocking state), the access invariants with cited intent evidence for each deviation, an access matrix with one row per inventory operation (outcome and status per principal, fields written, list scope, finding ids on deviating cells), and every channel to each protected object with its indirect leaks. Deviating cells become findings or Open questions in docs/intake-findings.md. |

## How it runs

The command reads the code and the docs it joins, stops at a checkpoint to confirm scope, and writes its document. Each matrix row is one operation from the API inventory, so the row count has to match the inventory. A cell that breaks an access invariant, with nothing in the code or docs saying the project meant it, goes to the findings tracker; when intent is unclear it becomes an Open question instead. The doc itself stays descriptive and cites the finding id.

Once the matrix is written, a fresh read-only subagent goes over it a second time without seeing the findings tracker. The command checks each cell it reports against the code, files the ones that hold, and records both counts in the checklist note. An accuracy audit against the code comes last, because agents read the result as the implementation contract.

Run it after `intake:document-api`, `intake:document-user-model`, `intake:document-features` and `intake:document-security`. If one of those docs is missing, the command works from the code and adds an Open question. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
