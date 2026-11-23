# intake:testing-owasp

Map the current OWASP Top 10 (the 2025 edition when this was written) to the project's real surfaces and write adversarial tests for each category that applies. Current behavior is characterized, and each known weakness is recorded under its finding id.

**Step:** capture-behavior (intake phase) · **Procedure file:** `references/intake/procedures/testing-owasp.md` · **Run:** `intake testing-owasp`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `owasp-tests` | directory | (test directory; one file per applicable OWASP category) | Adversarial tests mapped to the current OWASP Top 10 edition (2025 at the time of writing), named in the coverage map. A01 cites the access matrix tests from intake:testing-authorization and adds only what a matrix cell can't express (SSRF, path traversal, CSRF and CORS). Each other category applies its techniques: business-logic abuse (skip, replay, reorder, double-submit, boundary quantities, limit bypass, one test per project invariant), the credential lifecycle and token properties, fail-open probes, and command evidence (dependency audit, secrets scan over git history, the framework's deployment check) for supply chain, crypto and misconfiguration. A checklist covers the surface outside the request path. The coverage map has one row per category, surface and technique with a status: tested, not tested with a reason, or not examined. Known weaknesses are characterized and paired with a skipped hardened-behavior test cross-referencing the finding id. |

## How it runs

The procedure reads the matching documentation doc, stops at a checkpoint to confirm scope, writes tests that characterize current behavior, then runs them and reports fresh output. In an attended run the agent stops at the checkpoint so you can confirm or correct the scope; in a goal run it records the scope as a draft in the checklist note and goes on (see the [intake phase](intake-phase.md)). A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id.

Broken access control (A01) belongs to the access matrix that `intake:testing-authorization` tests. This procedure cites that table and adds only the cases a cell can't hold: server-side request forgery, path traversal, and cross-origin requests. The other categories each come with techniques. Business logic gets skipped, replayed, reordered and doubled steps, boundary and negative quantities, limit bypasses, and one test for each project invariant from `INV-7` on. Authentication gets the credential lifecycle (does a session, token or emailed link still work after deactivation, a password change, logout or a role change?) and every property listed under `## Tokens` in `docs/security/security.md`. Supply chain, cryptography and misconfiguration are proven with commands: a dependency audit, a secrets scan over the whole git history, and the framework's deployment check. A dependency advisory is rated by what this app exposes, not by the advisory's own score: when nothing in the code reaches the vulnerable path, the finding is Low. A checklist covers what never shows up in the route table, such as seed data, container and CI files, client-side code, uploads, logs and outgoing email.

The coverage map has one row for each category, surface and technique. Every row says whether it was tested, not tested (and why), or not examined.

Run it after `intake:testing-setup` and, ideally, `intake:document-security`. It cites the access matrix tests from `intake:testing-authorization`; in a full intake run the two write at the same time in the parallel testing batch, beside `intake:testing-features`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
