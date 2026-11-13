---
name: testing-user-flows
description: Generate end-to-end tests for critical user journeys at two layers, backend flows through the real datastore and handlers, and UI flows driven through the actual screens.
argument-hint: "[directory]"
---

# intake:testing-user-flows

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce end-to-end tests for the application's critical journeys at two layers. **Backend flows** drive a journey
through the real datastore and handlers (via the integration harness) and assert the resulting state and side
effects. **UI flows** drive the same journeys through the actual screens with an end-to-end driver. **Assert the
behavior the running system exhibits. Characterize current behavior; flag a journey the driver cannot reach rather
than pretending it is covered.**

This command covers whole journeys. Single-unit behavior belongs to `intake:testing-features`; access rules to
`intake:testing-authorization`. It owns UI and API parity (`INV-5` in `access-control.md`): the server refuses
what the UI hides, and what the UI offers changes server state. Read `docs/flows/user-flow.md`,
`docs/security/authorization.md` and `docs/domain/user-model.md` if present.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the run-and-verify phase, the goal-run behavior, and the operation inventory, principals and invariants the parity and negative cases use.

## When to use

Run during the capture-behavior step, after `intake:testing-setup` and (ideally) `intake:document-user-flow`.
Re-run when journeys or routes change. Idempotent for the tests it owns.

## Skills to invoke

- **`fullstack-dev-skills:test-master`**: select the critical journeys, the two-layer split, and the seeding
  strategy.
- **The project's e2e driver skill**, chosen by platform: `fullstack-dev-skills:playwright-expert` for a web or
  web-capable build; a device-driver approach (Maestro, Detox) for native-only.
- **The project's framework skill** for selectors and screen structure, e.g.
  `fullstack-dev-skills:react-native-expert`, `fullstack-dev-skills:nextjs-developer`.
- **`fullstack-dev-skills:the-fool`**: pre-mortem the journeys for the unhappy paths and race conditions that get
  skipped.

## Workflow

### Phase 1: Enumerate the critical journeys
From the routes and the user-flow doc, list the journeys that matter: onboarding and auth, the core action loop,
the messaging or interaction path, the safety path (block, report), and account deletion. Per journey,
capture the **steps** a user takes and the **backend side effects** to assert (documents or rows written,
notifications or jobs enqueued, cascades performed).

Per journey, also record:
- **Parity surface:** each control the UI hides or disables for some principal or state (a button shown only to
  the owner, a form disabled after submit, a menu item missing for a blocked account), and each action the UI
  offers, with the operation id it calls from the inventory (`## Operations` in
  `docs/architecture/api-reference.md`).
- **Negative variant:** one attempt at the journey's key step by the wrong principal (another user, anonymous, an
  account in a blocking state) or in the wrong state (an object already closed, cancelled or consumed), with the
  refusal the matrix or the state machine expects.

### Phase 2: Choose the two-layer coverage
- **Backend flow layer (always):** drive each journey through the integration harness (real datastore, handlers,
  emulator), asserting end-state and side effects. This layer is fast, deterministic, and reaches logic the UI
  cannot.
- **UI flow layer (platform-dependent):** drive the journeys through the screens with the chosen driver, backed by
  the same integration harness. Note any journey the driver cannot reach (a native-only surface on a web driver, a
  hardware permission, an external redirect) and keep it in the backend layer only.
- **Parity cases (both layers):**
  - For each control the UI hides or disables, send the operation it would call straight to the server as the
    principal the UI hid it from, and assert the server refuses it and the stored state is unchanged. A hidden
    control the server still accepts breaks `INV-5`.
  - For each action the UI offers, perform it through the UI, then re-read the server state through the API or the
    datastore and assert it changed as the action claims. This catches a control that shows success and does
    nothing.
  - Cite the matrix cell a parity case shares (operation id and principal) rather than duplicating its test; the
    parity case adds the UI half.
- **Negative variant (one per journey):** the wrong principal or state attempts the journey's key step; assert the
  specific refusal and that no side effect happened (no row, no notification, no job).

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the journey list, which layer(s) cover each, the
parity cases and negative variant per journey, the e2e driver choice and why, the seeding strategy, and any
journey the UI driver cannot reach. Do not write until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 3: Write the tests
Write backend flow tests against the integration harness and UI flow tests with the driver, both seeded by shared
fixtures and backed by the same backend. Use stable, role- or text-based selectors over brittle ones. Keep each
test to one journey.

### Phase 4: Run and verify (required)
Run the backend flows under the integration backend and the UI flows against a running build; capture fresh output
for each. A journey that cannot execute in this environment must be reported as not-yet-run with the blocker, not
claimed as passing. Keep the type-checker clean.

### Handling known bugs
When a journey's current end-state is a known bug (for example a cascade that leaves an orphan), characterize the
current state with a passing assertion and pair it with a skipped or expected-fail assertion for the intended
end-state, cross-referencing the finding id. A hidden operation the server accepts, an offered action that leaves
server state unchanged, or a negative variant that succeeds is a finding naming the operation id, the principal and
`INV-5` (or the invariant it breaks), unless the docs cite evidence of intent (`access-control.md`, "Access invariants"); pin it the same way.

## Output template

The deliverable is tests plus a coverage map:

```
<test dir>/integration/flows/<journey>.test.*   # backend flow layer
e2e/<journey>.spec.*                             # UI flow layer (driver)
```

Coverage map (one row per journey):

| Journey | Backend flow | UI flow | Parity cases (hidden refused / offered changes state) | Negative variant | Driver-unreachable steps | Known-bug refs |
|---|---|---|---|---|---|---|

## Failure conditions

- **No integration harness:** run `intake:testing-setup` first; do not fake a flow with pure mocks and call it
  end-to-end.
- **The UI driver cannot run in this environment:** scaffold the specs, mark them not-yet-run with the reason, and
  keep the backend flow layer as the coverage of record.
- **A journey depends on a live external service:** stub the boundary, assert up to it, and flag the seam.

## Output

The test files above, plus a summary: journeys covered per layer, the parity cases and negative variants with
their results, the driver chosen, driver-unreachable steps,
known-bug characterizations with their finding ids, and run results with command output.
