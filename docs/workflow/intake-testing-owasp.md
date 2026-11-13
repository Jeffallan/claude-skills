# intake:testing-owasp

Map the OWASP Top 10 to the project's real surfaces and generate adversarial tests for each applicable category, characterizing current behavior and recording known weaknesses by finding id.

**Step:** capture-behavior (intake phase) · **Command file:** `commands/intake/testing-owasp.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `owasp-tests` | directory | (test directory; one file per applicable OWASP category) | Adversarial tests mapped to the OWASP Top 10: each category is mapped to real surfaces in the code or marked N/A with a reason, then probed (access-control bypass, injection, insecure-design abuse, misconfiguration, auth failures). Known weaknesses are characterized and paired with a skipped hardened-behavior test cross-referencing the finding id. |

## How it runs

The command reads the matching documentation doc, stops at a checkpoint to confirm scope, writes tests that characterize current behavior, then runs them and reports fresh output. A known bug gets a passing characterization test and a skipped or expected-fail test for the intended behavior, both naming the finding id.

Run it after `intake:document-codebase`. Capture-behavior commands other than `intake:testing-setup` also need the harness that command builds. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
