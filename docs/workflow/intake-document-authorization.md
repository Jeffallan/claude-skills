# intake:document-authorization

Write an authorization reference grounded in code. It names the project's real authorization model (RBAC, ABAC, ownership/relationship-based, ACL, or a mix), then crosses every operation in the API inventory with every principal, blocking states included, and checks each cell against a set of access invariants.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-authorization.md` · **Run:** `intake document-authorization`

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

The procedure reads the code and the docs it joins, stops at a checkpoint to confirm scope, and writes its document. In an attended run the agent stops at the checkpoint so you can confirm or correct the scope; in a goal run it records the scope as a draft in the checklist note and goes on (see the [intake phase](intake-phase.md)). Each matrix row is one operation from the API inventory, so the row count has to match the inventory. A cell that breaks an access invariant, with nothing in the code or docs saying the project meant it, goes to the findings tracker; when intent is unclear it becomes an Open question instead. The doc itself stays descriptive and cites the finding id.

Once the matrix is written, a second pass derives the cells blind. The procedure extracts a clean copy of the code from before the docstring pass, so no comment names a finding, and splits the inventory into batches of about 60 operations. The intake command starts one fresh `code-reader` per batch, all at once, with only the batch's rows, the principals, the invariants and the clean copy, never the matrix or the findings tracker. The procedure checks each disagreement and each other defect a reader reports against the code and the running app, corrects the cells the matrix got wrong, files the findings that hold, and records the counts in the checklist note: cells derived, disagreements, cells corrected, other defects reported and new findings. An accuracy audit against the code comes last, because agents read the result as the implementation contract.

Run it after `intake:document-api`, `intake:document-user-model`, `intake:document-features` and `intake:document-security`. If one of those docs is missing, the procedure works from the code and adds an Open question. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
