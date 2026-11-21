# intake:testing-features

**Options:** what follows the procedure name in `intake <procedure> ...`, passed on in the brief: an optional root directory to analyze (defaults to the project root).

Produce unit and component tests that lock in how the application's features behave today: the domain and service
functions that orchestrate writes and build identifiers, the pure helpers, the parity between duplicated sources
of truth, and the logic inside views and screens. **Assert behavior the code actually exhibits. Characterize
current behavior; never silently encode a known bug as correct.**

This command covers functional behavior at the unit level. End-to-end journeys belong to
`intake:testing-user-flows`; access rules to `intake:testing-authorization`. Read `docs/domain/features.md` and
`docs/architecture/data-model.md` if present.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the run-and-verify phase and the goal-run behavior.

## When to use

Run during the capture-behavior step, after `intake:testing-setup` and (ideally) `intake:document-features`.
Re-run when feature logic changes. Idempotent for the tests it owns.

## Skills to load

- **`fullstack-dev-skills:test-master`**: inventory testable units, design cases per branch, and set the mocking
  boundary.
- **The project's framework skill** for component and view tests, e.g. `fullstack-dev-skills:react-native-expert`,
  `fullstack-dev-skills:react-expert`, `fullstack-dev-skills:vue-expert`.
- **The project's language skill** for typed tests and parity assertions, e.g.
  `fullstack-dev-skills:typescript-pro`, `fullstack-dev-skills:python-pro`.

## Workflow

### Phase 1: Inventory the testable units
From the code and the features doc, list:
- **Domain and service functions:** multi-write orchestration, deterministic ID construction, batch/transaction
  logic, error handling. These are the highest-value unit targets.
- **Pure functions:** parsing and formatting, validation, derivations (dates, ages, money), mappers between stored
  and view shapes.
- **Constant and enumeration tables**, and any value list duplicated in more than one source of truth (for example
  an allow-list in application code and in database rules). These get parity tests.
- **Type and view-model contracts:** the stored shape vs the DTO or view model, and any field the code writes but
  the declared type omits.
- **View and screen logic:** filtering, routing or branching, and form validation that lives in the component.

### Phase 2: Design cases and the mocking boundary
Per unit, design the happy path plus each branch plus edge cases (empty, boundary, invalid). Set the mocking
boundary deliberately: mock I/O and external clients at their module seam, and do not mock the unit under test. For
parity, assert the two sources agree and fail loudly when they drift. In view logic, prefer the framework's
testing library over snapshot-only tests.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the unit inventory grouped by kind, the count of
cases, the mocking boundaries, and where the tests will live. Do not write until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 3: Write the tests
Write unit tests with the chosen doubles, component tests via the framework library, and parity tests that read
both sources at test time. Name tests by behavior, not by implementation.

### Phase 4: Run and verify (required)
Run the suite and capture fresh output. Confirm each test would fail if the behavior changed: a characterization
test that cannot fail is not pinning anything. Keep the type-checker clean.

### Handling known bugs
When a unit's current behavior is a known bug, characterize it with a passing test and pair it with a skipped or
expected-fail test for the intended behavior, cross-referencing the finding id.

## Output template

The deliverable is tests plus a coverage map:

```
<test dir>/unit/
  services/<service>.test.*
  lib/<helper>.test.*
  parity/<list>.parity.test.*
  views/<screen>.test.*
```

Coverage map:

| Unit | Kind | Cases | Mocked seam | Known-bug refs |
|---|---|---|---|---|

## Failure conditions

- **A unit is untestable without heavy refactoring:** note it and the missing seam; do not refactor production
  code in a characterization task.
- **Two sources of truth already disagree:** the parity test should fail; record the drift with its finding id
  rather than loosening the test.

## Output

The test files above, plus a summary: units covered by kind, case counts, parity drifts and known bugs with their
finding ids, and run results with command output.
