---
name: testing-owasp
description: Map the OWASP Top 10 to the project's real surfaces and generate adversarial tests for each applicable category, characterizing current behavior and flagging (not hiding) known weaknesses.
argument-hint: "[directory]"
---

# intake:testing-owasp

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce tests that probe the project from an attacker's perspective, organized by the OWASP Top 10. Per
category, first decide whether it applies to this codebase and why, then write tests that exercise the real
surface. **Ground every test in a real surface in the code. Characterize current behavior, including weaknesses;
flag a known weakness with its tracked finding id rather than asserting it is safe.**

This command is adversarial coverage over the same surfaces that `intake:testing-authorization` (the access
matrix) and `intake:testing-features` (functional behavior) cover positively. Read `docs/security/security.md` and
`docs/security/authorization.md` if present.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the run-and-verify phase and the goal-run behavior.

## When to use

Run during the capture-behavior step, after `intake:testing-setup` and (ideally) `intake:document-security`.
Re-run when input surfaces, authentication, or configuration change. Idempotent for the tests it owns.

## Skills to invoke

- **`fullstack-dev-skills:security-reviewer`**: map each OWASP category to the codebase's real surfaces and rate
  applicability; lead the threat enumeration.
- **`fullstack-dev-skills:secure-code-guardian`**: turn each threat into a concrete test (injection payloads,
  access-control bypass attempts, auth-failure cases, validation probes).
- **`fullstack-dev-skills:test-master`**: structure the suite and fixtures, and set the boundary between
  unit-level validation tests and integration-level probes.
- **`fullstack-dev-skills:the-fool`**: adversarial pre-mortem on coverage; surface the categories and edge cases
  the others assumed away.

## Workflow

### Phase 1: Map the Top 10 to real surfaces
Per category, name the concrete surfaces in this codebase, or mark it **N/A with a reason**. Do not write a
test for a surface that does not exist. Surfaces include every endpoint a dependency mounts (an auth library's
account endpoints, an admin site), taken from `docs/architecture/api-reference.md` or the resolved route table,
not only routes the app defines. Probe account-lifecycle paths across states: what a deactivated, unverified
or deleted account can still do through them, and what an admin view shows of other users' secrets: check each model the framework's admin site registers, not only the app's own views.
- **A01 Broken Access Control:** cross-principal read/write, IDOR, missing ownership checks.
- **A02 Cryptographic Failures:** secrets in source or config, transport security, at-rest handling of sensitive
  fields.
- **A03 Injection:** every input that reaches a query, command, template, or other interpreter; validation gaps.
- **A04 Insecure Design:** rate limiting, abuse loops, moderation, business-logic invariants that fail open.
- **A05 Security Misconfiguration:** default-permissive config, missing rules or headers, disabled hardening,
  debug surfaces.
- **A06 Vulnerable and Outdated Components:** known-vulnerable dependencies, unpinned or unmaintained packages.
- **A07 Identification and Authentication Failures:** auth gates, verification gates, session and token handling,
  credential validation.
- **A08 Software and Data Integrity Failures:** unverified update or data paths, unsafe deserialization,
  supply-chain integrity.
- **A09 Security Logging and Monitoring Failures:** security-relevant events that are or are not recorded.
- **A10 Server-Side Request Forgery:** server-side fetches of user-controlled URLs.

### Phase 2: Design adversarial cases
Per applicable category, design tests that attempt the abuse and assert the outcome. Where the app defends
correctly, assert the defense holds. Where it does not, the test characterizes the current (weak) behavior and is
paired with an intended-fix test (see below). Use `fullstack-dev-skills:the-fool` to widen coverage before writing.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the category-to-surface mapping (with N/A
reasons), the count of tests per category, which tests characterize known weaknesses, and where the tests will
live. Do not write until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 3: Write the tests
Mix integration probes (against the real backend and datastore via the harness) with unit tests on validators and
pure guards. Name each test by category and threat. Keep payloads realistic and minimal.

### Phase 4: Run and verify (required)
Run the suite and capture fresh output. A passing security test must pass because the defense worked, not because
an unrelated error was raised, so assert the specific outcome. Keep the type-checker clean.

### Handling known weaknesses
When a category exposes a real weakness, write a passing test that **characterizes current behavior** plus a
skipped or expected-fail test asserting the **hardened** behavior, both cross-referencing the tracked finding id.
The suite stays green while the gap stays visible. This is a documentation-and-regression task, not a remediation
task; do not fix the code here.

## Output template

The deliverable is tests plus a coverage map:

```
<test dir>/owasp/
  a01-access-control.test.*
  a03-injection.test.*
  ...                       # one file per applicable category
```

Coverage map (one row per category):

| OWASP | Applies? | Surfaces | Tests | Defended / Characterized-weakness | Finding refs |
|---|---|---|---|---|---|

## Failure conditions

- **A category does not apply:** record it N/A with a one-line reason; do not fabricate a surface.
- **Scope creep into remediation:** if you start fixing the code, stop; characterize and flag instead.
- **A probe cannot run without a live external service:** stub the boundary, mark the reduced fidelity, and do not
  claim full coverage.

## Output

The test files above, plus a summary: categories covered vs N/A, test counts, weaknesses characterized with their
finding ids, and run results with command output.
