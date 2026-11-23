# intake:testing-authorization

**Options:** what follows the procedure name in `intake <procedure> ...`, passed on in the brief: an optional root directory to analyze (defaults to the project root).

Turn the access matrix into tests: one table-driven test whose rows are the matrix cells (operation x principal ->
expected outcome), a route ratchet that keeps the table complete, and the object-level, field-level and transition
cases the matrix implies. Send every request through the real request stack and assert the stored effect, not only
the status code. **Assert the access rules exactly as the code enforces them. Characterize current behavior;
never silently encode a known authorization bug as correct.**

This command tests the access matrix (*who may do what*). It pairs with `intake:testing-owasp`, which probes the
same surfaces adversarially. The matrix in `docs/security/authorization.md` is the contract this command verifies.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the run-and-verify phase, the goal-run behavior, and the operation inventory, principals, invariants, matrix and test rules this command executes ("Testing the matrix" in `access-control.md`).

**In a parallel batch** ("Parallel testing writers" in the `intake` command, which runs this procedure beside the other two testing procedures): never edit `docs/intake-findings.md`. Give each new finding a provisional id from the range your brief names, run only your own test files, and report every tracker change under `Tracker edits:` in your item report (`references/intake/rules.md`, "The item report"). The command assigns the real ids in checklist order and applies the edits. Everything else in this procedure applies as written.

## When to use

Run during the capture-behavior step, after `intake:testing-setup` and `intake:document-authorization`.
Re-run when routes or access rules change. Idempotent for the tests it owns.

## Skills to load

- **`fullstack-dev-skills:test-master`**: design the table, the fixtures per principal column and the
  parametrization so each row is one named case.
- **`fullstack-dev-skills:secure-code-guardian`**: interpret each authorization primitive (token claims,
  ownership checks, membership, policy predicates, ACL lookups) so every expected outcome is precise.
- **`fullstack-dev-skills:security-reviewer`**: check each cell against the invariants in `access-control.md`
  and name the guard each deny row depends on.
- **The project's language skill** for typed test code, e.g. `fullstack-dev-skills:typescript-pro`,
  `fullstack-dev-skills:python-pro`.

## Workflow

### Phase 1: Read the matrix and the enforcement layer
Read these, all defined in `access-control.md`: the operation inventory (`## Operations` in
`docs/architecture/api-reference.md`), the invariants, the access matrix and the channels per protected object
(`docs/security/authorization.md`), the blocking-state sections and transitions (`docs/domain/user-model.md`,
`docs/domain/features.md`), and the protected fields (the `Flags` column in `docs/architecture/data-model.md`).

Then read the code that enforces them: where access decisions run (middleware, guards, permission classes,
policies, database rules), how a client authenticates (a login route, a token header, a session cookie), and the
framework's API for listing its resolved routes at runtime (a URL resolver, the router's route list, the generated
OpenAPI schema).

When the matrix is missing, build the rows from the resolved route table and the code, and add an Open question
saying so. A cell whose expected outcome the docs and the code disagree on is tested as the code behaves, with a
finding for the disagreement.

### Phase 2: Design the table
One table-driven test is the coverage map. It replaces any per-resource or "per meaningful cell" sampling:

- **Matrix rows:** one row per matrix cell, keyed by operation id and principal (`OP-014-anonymous`). The
  expected outcome comes from the cell: `allow`, `own`, `deny <status>`, or `n/a` with its reason. An `n/a` row skips with an `n/a: <reason>` message; it is not a bug test and cites no finding.
- **Object-level rows** for every operation that takes an id: the caller acting on another owner's object and on
  another tenant's object. Lists assert the scope the matrix gives.
- **Field-level rows:** each protected field (role, state, owner, price, the `Flags` column) written through each
  operation that accepts the object, by each principal that may call it.
- **Transition rows:** each trigger in the transitions tables, called as each principal, the subject itself and
  anonymous included, asserting the state afterward.
- **Blocking-state rows:** each blocking-state column uses the credentials (session, token, API key, emailed link)
  the account held before it entered the state.

Each row cites its operation id and principal in its parameter id, so a reviewer finds it from the matrix and
the reverse. Check each cell against the invariants; a cell that breaks one is a finding (Phase 3 records it).

Plan the **route ratchet**: a test that lists the resolved routes at runtime, maps each method and path to an
inventory id, and fails on any route with no table row.

Plan the **deny-proof sample**: at least five deny rows (all of them when fewer), spread across different guards,
each with the guard (`path::symbol`) its removal should break.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the principal columns and how each authenticates,
the row counts per kind (matrix, object-level, field-level, transition), the route source for the ratchet, the
deny-proof sample, the suspected findings, and where the tests will live. Do not write until the user confirms. In
a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 3: Write the tests
- **Real request stack.** Authenticate the way a client does: call the login route, send the token header or the
  session cookie. Never use a helper that forces a logged-in user, and never call a handler directly, for an
  authentication or state case. For a blocking-state column, obtain the credential first, move the account into
  the state, then send the request with the held credential.
- **Effects, not status codes.** After every write, allowed or denied, re-read the stored state from the datastore
  (not from the response) and assert it: unchanged after a deny, changed as expected after an allow.
- **Specific denials.** A deny row asserts the matrix's status, never "any 4xx" or "it threw".
- **Distinct ids.** Seed fixtures so ids differ across tables and across owners and tenants (`rules.md`, "Run and
  verify").
- **The ratchet** reads routes from the framework at test time, never from a copied list.

**Findings.** Record each matrix finding in the shape of "Findings from the matrix" in `access-control.md`: the
operation ids, the principal column and the invariant broken, one finding per root cause citing every row it
opens. Append it to `docs/intake-findings.md` before writing a row that cites it. Rate it by `references/intake/severity.md`.

**Known bugs.** A row whose current outcome breaks an invariant gets two rows in the same table: the
characterization row asserting today's outcome, and the intended-behavior twin asserting the invariant's outcome,
marked strict expected-fail with the framework's own marker. Put the finding id on both: in the row's parameter
id (`OP-007-deactivated-F-012-current`, `OP-007-deactivated-F-012-intended`) or in a comment beside the row. The
id must sit within three lines of the expected-fail marker. When a helper builds the marker, pass it the literal
id at each call.

### Phase 4: Run and verify (required)
Follow "Run and verify" in `rules.md`. Then:

- **Prove the deny rows can fail.** Copy the working tree to a scratch folder outside the repo (never a git
  worktree or branch of it). For each row in the deny-proof sample, remove its guard in the copy, run that row,
  and confirm it fails on its access assertion, not on an import or setup error. Restore the guard before the
  next row, and delete the copy at the end. Nothing in the repo changes.
- Record in this item's checklist note: the ratchet's route count, each sampled row id, the guard removed and the
  result.

### Phase 5: Update the matrix statuses
In its own commit, after the tests and tracker commit, edit `docs/security/authorization.md` (`rules.md` lets a
later command correct an earlier doc):

- Each cell with a passing row goes from `[x]` to `[t]`. Each cell left untested gets `[n: <reason>]`.
- A cell that breaks an invariant carries its finding id after the status: `allow [t] F-012`.
- Leave no `[x]`. Add a dated line to the doc's `## Accuracy audit` naming the status change and the test file.

## Output template

```
<test dir>/authorization/
  <matrix test>.*        # the table: matrix, object-level, field-level and transition rows
  <route ratchet>.*      # resolved routes at runtime vs table rows
  <fixtures>.*           # one account per principal column, credentials obtained through the request stack
```

The coverage map is the table itself, plus the summary counts:

| Kind | Rows | Allow | Deny | Expected-fail (finding ids) |
|---|---|---|---|---|

## Failure conditions

- **No access-control code found:** state it and stop; do not invent a model or tests.
- **No harness reaches the real request stack:** fall back to the closest layer, mark the affected cells
  `[n: <reason>]`, and flag that those rows verify a double rather than the deployed rule.
- **The framework can't list its routes at runtime:** build the ratchet from the closest generated listing, say
  which, and add an Open question.
- **Docs and code disagree:** test the code, keep both in the finding; do not silently pick one.

## Output

The test files above, the matrix status commit, plus a summary: the row counts per kind, the ratchet's route
count, the deny-proof results, the findings with their row ids, and the run results with command output.
