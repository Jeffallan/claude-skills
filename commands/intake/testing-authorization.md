---
name: testing-authorization
description: Generate characterization tests that lock in the project's access-control model by asserting both authorized-allow and unauthorized-deny for every resource and verb against the real enforcement layer.
argument-hint: "[directory]"
---

# intake:testing-authorization

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce tests that pin the authorization model in place: for every resource and verb, assert what an authorized
principal **may** do and what an unauthorized principal **may not**. Test against the real enforcement layer
(database access rules, middleware, guards, policy engine) wherever a harness allows, so the test exercises the
rule and not a restatement of it. **Assert the access rules exactly as the code enforces them. Characterize
current behavior; never silently encode a known authorization bug as correct.**

This command tests the access matrix (*who may do what*). It pairs with `intake:testing-owasp`, which probes the
same surfaces adversarially. Read `docs/security/authorization.md` if it exists; it is the contract this command
verifies.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the run-and-verify phase and the goal-run behavior.

## When to use

Run during the capture-behavior step, after `intake:testing-setup` and (ideally) `intake:document-authorization`.
Re-run when access rules change. Idempotent for the tests it owns.

## Skills to invoke

- **`fullstack-dev-skills:test-master`**: design the principal x resource x verb test matrix and the fixture
  strategy.
- **`fullstack-dev-skills:secure-code-guardian`**: interpret each authorization primitive (token claims,
  ownership checks, participation/membership, policy predicates, ACL lookups) so every allow/deny case is precise.
- **`fullstack-dev-skills:security-reviewer`**: classify the model (RBAC, ABAC, ReBAC, ACL, or a mix) so the
  matrix covers the right principal classes; confirm no resource is missed.
- **The project's language skill** for typed test code, e.g. `fullstack-dev-skills:typescript-pro`,
  `fullstack-dev-skills:python-pro`.

## Workflow

### Phase 1: Read the enforcement layer and build the matrix
Identify where access decisions are made (database access rules, middleware, route guards, policy files, ACL
tables) and the authorization doc if present. Build the matrix axes:
- **Principal classes** the rules distinguish: anonymous, authenticated, owner/participant, each role or attribute
  tier, and any privileged server context that bypasses the rules.
- **Resources** (tables, collections, routes, RPCs) and the **verbs** each supports (read, create, update, delete,
  or the system's own verbs).
- **Gates** layered on the verb: authentication required, identity verification, ownership/participation,
  field-shape and immutability constraints.

### Phase 2: Design the allow and deny cases
Per meaningful cell, design at least one **positive** case (the authorized principal succeeds) and one
**negative** case (an unauthorized principal is denied). A test that only checks the happy path does not pin
authorization; the deny case is the point. Add cases for each gate: the unauthenticated caller, the non-owner, the
cross-tenant or cross-participant caller, the immutability violation, and any verb the system forbids to all
clients (assert it is denied, and note where it happens instead, for example server-only).

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the detected model, the principal classes, the
resource/verb matrix with the count of allow and deny cases, the harness used (real enforcement layer via
emulator/integration vs mocked), and where the tests will live. Do not write until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 3: Write the tests
Write against the real enforcement layer where the harness allows (preferred), seeding fixtures for each principal
class. Group by resource; within each, order allow then deny. Quote the rule being verified in the test name. For
verbs no client may perform, assert the denial.

### Phase 4: Run and verify (required)
Run the suite and capture fresh output. Confirm deny cases actually fail closed: a deny test that passes only
because the operation errored for an unrelated reason is a false pass, so assert the denial specifically. Keep the
type-checker clean.

### Handling known authorization bugs
When current behavior contradicts the intended model (for example a field documented as private is readable in
practice), write a passing test that **characterizes the current behavior** and a sibling skipped or
expected-fail test that asserts the **intended** behavior, each cross-referencing the tracked finding id. Do not
erase the discrepancy by asserting the buggy behavior is correct.

## Output template

The deliverable is tests plus a short coverage map:

```
<test dir>/authorization/
  <resource>.test.*   # allow + deny per verb, grouped by resource
```

Coverage map (one row per resource):

| Resource | Verbs covered | Allow cases | Deny cases | Harness | Known-bug refs |
|---|---|---|---|---|---|

## Failure conditions

- **No access-control code found:** state it and stop; do not invent a model or tests.
- **Cannot exercise the real enforcement layer:** fall back to the closest available harness, and flag that the
  test verifies a double rather than the deployed rule.
- **Rules and application code disagree:** test and document both; do not silently pick one.

## Output

The test files above, plus a summary: the model classified, resources covered, allow/deny counts, known-bug
characterizations with their finding ids, and the run results with command output.
