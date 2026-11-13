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
`intake:testing-authorization`. Read `docs/flows/user-flow.md` if present.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the run-and-verify phase and the goal-run behavior.

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

### Phase 2: Choose the two-layer coverage
- **Backend flow layer (always):** drive each journey through the integration harness (real datastore, handlers,
  emulator), asserting end-state and side effects. This layer is fast, deterministic, and reaches logic the UI
  cannot.
- **UI flow layer (platform-dependent):** drive the journeys through the screens with the chosen driver, backed by
  the same integration harness. Note any journey the driver cannot reach (a native-only surface on a web driver, a
  hardware permission, an external redirect) and keep it in the backend layer only.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the journey list, which layer(s) cover each, the
e2e driver choice and why, the seeding strategy, and any journey the UI driver cannot reach. Do not write until the
user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

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
end-state, cross-referencing the finding id.

## Output template

The deliverable is tests plus a coverage map:

```
<test dir>/integration/flows/<journey>.test.*   # backend flow layer
e2e/<journey>.spec.*                             # UI flow layer (driver)
```

Coverage map (one row per journey):

| Journey | Backend flow | UI flow | Driver-unreachable steps | Known-bug refs |
|---|---|---|---|---|

## Failure conditions

- **No integration harness:** run `intake:testing-setup` first; do not fake a flow with pure mocks and call it
  end-to-end.
- **The UI driver cannot run in this environment:** scaffold the specs, mark them not-yet-run with the reason, and
  keep the backend flow layer as the coverage of record.
- **A journey depends on a live external service:** stub the boundary, assert up to it, and flag the seam.

## Output

The test files above, plus a summary: journeys covered per layer, the driver chosen, driver-unreachable steps,
known-bug characterizations with their finding ids, and run results with command output.
