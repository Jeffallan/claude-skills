# Intake Access Control

How the intake procedures find access-control and business-logic bugs: one operation inventory, one access matrix that joins it with every principal and state, a set of default rules that say what "wrong" looks like, and table-driven tests that execute every cell. Each procedure named below reads this file before its first phase. Findings follow `references/intake/findings.md`; everything else follows `references/intake/rules.md`.

## Why a matrix and not a reminder

A run can hold every fact it needs and still miss a bug, because the facts sit in different docs: the API reference lists an account route a library mounts, the user model lists a blocked state, and nothing crosses the two. A sentence asking the run to "probe lifecycle paths" produces nothing anyone can check. The matrix is that check. Every operation meets every principal, every cell gets an expected outcome and a status, and a cell no one examined says so.

## Who owns what

| Artifact | Owner | Section |
|---|---|---|
| Operation inventory | `intake:document-api` | `## Operations` in `docs/architecture/api-reference.md` |
| Library security settings | `intake:document-config` | `## Library security settings` in `docs/operations/configuration.md` |
| Test versus deployed settings | `intake:document-config` | `## Security settings: test versus deployed` in `docs/operations/configuration.md` |
| Security-relevant fields | `intake:document-data-model` | the `Flags` column of each entity table in `docs/architecture/data-model.md` |
| Actor states and transitions | `intake:document-user-model` | `## Lifecycle state machine` and `## Blocking states` in `docs/domain/user-model.md` |
| Domain-entity states and transitions, project invariants | `intake:document-features` | `## State machines` and `## Project invariants` in `docs/domain/features.md` |
| Access matrix, invariants, channels | `intake:document-authorization` | `## Access invariants`, `## Access matrix`, `## Channels per protected object` in `docs/security/authorization.md` |
| Token properties | `intake:document-security` | `## Tokens` in `docs/security/security.md` |
| Matrix tests, route ratchet | `intake:testing-authorization` | the project's test tree |
| Logic, credential and configuration tests, and the access-control cases a cell can't hold (server-side request forgery, path traversal, CSRF and CORS under deployed settings) | `intake:testing-owasp` | the project's test tree |
| UI and API parity | `intake:testing-user-flows` | the project's test tree |

The matrix is the one place facts from other docs are joined on purpose. It cites the operation ids and the state names; it doesn't restate the routes' details or the states' definitions ("Keep each fact in one doc", `rules.md`).

## Operation inventory

`intake:document-api` lists every operation the running application exposes, taken from the framework's resolved route table (the router's own listing command, a URL resolver dump, the OpenAPI schema the framework generates), never only from the routes the app's code declares. Libraries mount routes the app never wrote: an auth library's account endpoints, an admin site, a health or debug endpoint, a GraphQL endpoint, an older API version still mounted.

```markdown
## Operations

Route listing: `<command>` (<N> routes at <short sha>).

| Id | Method | Path | Source | Handler | Authentication | Permission (resolved) |
|----|--------|------|--------|---------|----------------|------------------------|
| OP-001 | POST | /api/v1/auth/token/login/ | library: <name> | `path::symbol` | none | AllowAny (library default) |
```

- One row per method and path. Non-CRUD operations (custom actions, account endpoints, exports, bulk, webhooks, sockets) are rows like any other. An operation with no HTTP method puts its kind in `Method` (`QUERY`, `MUTATION`, `RPC`, `EVENT`, `JOB`) and its name or binding in `Path`; the matrix covers it like any row.
- `Source` is `app`, `library: <name>` or `framework`.
- `Permission (resolved)` is what actually runs, with the setting or default that produced it. A library default the project never set is written as such: "(library default)".
- Ids are stable: a rerun keeps existing ids and appends new ones. A route that disappears keeps its row, marked `removed` in its `Permission` cell, so citations still resolve; removed rows leave the counts and the matrix. Other docs and tests cite operations by id.
- A later command that finds an operation the inventory lacks (a state writer reachable through an unlisted route) adds the row to `api-reference.md` in its own commit (`rules.md`, "Output layout").
- The checklist note records the listing command and its count, so the eval can compare the inventory with the route table.

## Principals

The matrix's columns. Start from this list and keep the ones the project has:

- `anonymous`: no credentials.
- `authenticated`: a valid account with no relation to the object.
- `owner`: the account that owns the object (or its tenant).
- one column per role or privilege level the code checks (`admin`, `staff`, `manager`).
- one column per **blocking state** of the actor (`deactivated`, `unverified`, `suspended`, `deleted`), holding the credentials the account had before it entered that state.

A state the code never checks still gets a column when the model has it: the matrix then shows that nothing stops it.

## Access invariants

The default rules every cell is checked against. They hold unless the code states otherwise, with evidence:

1. **INV-1** Anonymous changes nothing, apart from the operations listed as public (sign-up, login, password reset request).
2. **INV-2** A blocking state allows no operation, no self-service way out of the state, and no credential that outlives entering it.
3. **INV-3** A non-owner neither reads nor changes the object, and every list returns only what the caller may read.
4. **INV-4** No principal raises its own privilege or writes its own role, state or ownership fields.
5. **INV-5** The server refuses whatever the UI hides, and whatever the UI offers changes server state.
6. **INV-6** Every state transition has a named actor allowed to make it; no route reaches a transition its actor list omits.

A project adds its own invariants (a booking can't overlap another, a refund never exceeds the charge) as `INV-7` onward, each citing the code, test, comment or doc that states the intent. `intake:document-features` numbers them in `## Project invariants`; `intake:document-authorization` lists INV-1 to INV-6 with the source "intake default", cites the project's invariants by id, and continues the numbering for any access-only invariant it adds.

A cell that breaks an invariant is a finding, unless the doc cites evidence of intent for it (a comment, a test, a doc, a setting the project chose). "The library does it by default" is not evidence of intent. When intent can't be settled either way, the cell is an Open question with a draft answer, never left silent.

## Access matrix

`intake:document-authorization` writes it after the inventory, the user model, the features and the security doc exist.

```markdown
## Access matrix

Rows: <N> operations from the inventory (all of them). Cells: expected outcome, then status.

| Op | anonymous | authenticated | owner | admin | deactivated | Fields written | List scope |
|----|-----------|---------------|-------|-------|-------------|----------------|------------|
| OP-014 | deny 401 [x] | deny 403 [x] | allow [x] | allow [x] | deny 401 [x] | `name`, `phone` | none |
| OP-015 | deny 401 [x] | allow [x] | allow [x] | allow [x] | deny 401 [x] | none | own rows only |
```

- One row per inventory operation. Row count equals the inventory count; a row left out is a gap the eval reports.
- Outcomes: `allow`, `own` (allowed on the caller's own object only), `deny <status>` (the specific refusal), `n/a` (the principal can't reach it at all, with the reason in a note).
- Status, in brackets: `[t]` tested (the test row exists and runs), `[n: <reason>]` not tested and why, `[x]` not examined yet. The documentation command writes `[x]`; `intake:testing-authorization` changes each cell it executes to `[t]` or `[n: <reason>]` in its item's commit, beside the tests. A finished intake leaves no `[x]`, and the intake eval checks that.
- `Fields written` lists the fields the operation lets the caller set; protected fields (role, state, owner, price) the operation should never accept go in the row note.
- `List scope` says what a list operation returns per caller.
- A cell that breaks an invariant carries the finding id after its status: `allow [t] F-012`.

## Channels per protected object

For each object a principal may own or be denied (accounts, profiles, orders, files), list every channel that returns or changes it, and the operation ids for each: detail, list, search, filter and ordering parameters, nested includes in another object's response, exports, file and media URLs, bulk operations, sockets, webhooks, background jobs, older API versions. The ownership rule must hold on each. Add the indirect leaks: filtering or ordering on a field the caller can't read, and a 403 where another object gives 404 (or error text) that reveals the object exists.

## Security-relevant fields

`intake:document-data-model` marks each field in the `Flags` column with any of: `state` (status enums, active or verified flags, soft-delete and expiry stamps), `owner` (owner and tenant keys), `privilege` (role, admin flag, permissions, plan or tier), `money` (amounts, balances, quantities, counts). The matrix's field-level cases and the transition search start from these.

## Transitions and blocking states

`intake:document-user-model` (for the actor) and `intake:document-features` (for domain entities with a status: orders, invoices, subscriptions) find transitions by listing every writer of each state field: app code, library code, the admin site, background jobs, signals and hooks, migrations. A transition the code never names but a library performs (a payment library's webhook handler that marks an invoice paid) is a transition.

| From | To | Trigger | Routes | Who may call | Mechanism |
|------|----|---------|--------|--------------|-----------|
| issued | paid | provider webhook | OP-022 | the payment provider (signed request) | `path::symbol` |

Each blocking state gets a section: the operations still allowed in it, every way out of it with its routes and callers, and the credentials (sessions, tokens, API keys, reset or activation links) that survive entering it.

## Tokens

`intake:document-security` lists every token the system issues (session, access and refresh, API key, password reset, activation, invite, email change) with its properties: expiry, single use, bound to one user, bound to one purpose, and voided when the state it relates to changes (password change, email change, deactivation, logout, role change). A property that doesn't apply to a token's kind (single use on a session) is `n/a` with the reason; a property that applies and is missing, without evidence of intent, is a finding. `intake:testing-owasp` tests each property: replay the token twice, replay it after the state change, and freeze the clock at the expiry boundary.

## Library security settings

`intake:document-config` lists, for each auth, admin and API library, the settings that bear on security with their effective values, defaults the project never set included, and the source of each value (`settings.py::<NAME>`, "library default"). A default nobody chose is attack surface, and one that weakens a control is a finding. Then the table of security settings that differ between the test settings and the deployed ones (debug, CORS, allowed hosts, throttles, cookie flags, password rules, email backend): a test passing under settings that turn a control off says nothing about that control. A control only the test settings turn off is a row in that table, not a finding; one the deployed settings turn off is a finding.

## Testing the matrix

`intake:testing-authorization` turns the matrix into tests:

- **One table-driven test.** Each row is an operation, a principal and the expected outcome, generated from or checked against the matrix. The table is the coverage map. Cite each row by operation id and principal so a reviewer can find it.
- **A route ratchet.** A test that lists the framework's resolved routes at runtime and fails on a route with no table row. It keeps guarding after intake: a new route without an access decision fails the build. Operations the framework can't list at runtime (sockets, jobs, webhooks registered elsewhere) stay out of the ratchet; the inventory's audit covers them.
- **The real request stack.** Send credentials the way a client does (a login, a token header, a session cookie). A test helper that forces a logged-in user, or a direct call into a handler, skips the authentication layer under test. Blocking-state columns use the credentials the account held before it entered the state.
- **Effects, not status codes.** After every write, allowed or denied, re-read the stored state and assert it. A 200 that changed nothing and a 200 that wrote look the same from the response.
- **Object-level cases** for every operation that takes an id: another owner's id, another tenant's id. Seed ids that differ across tables (`rules.md`, "Run and verify").
- **Field-level cases:** write each protected field through each operation that accepts the object, then re-read it.
- **Transition cases:** each trigger as each principal, the subject itself and anonymous included; assert the state afterward.
- **Prove the deny tests can fail.** For a sample of deny rows (at least five, or all when fewer), copy the working tree to a scratch folder outside the repo (a plain copy, never a git worktree, which writes into `.git`), remove the guard, run the row, see it fail, and delete the copy. Record the rows and results in the checklist note. Nothing in the repo changes.

## An independent second pass

One pass over a codebase misses things another pass finds, and a reviewer shown the answers tends to agree with them. After the matrix is written, `intake:document-authorization` hands fresh read-only subagents the inventory, the principals and the invariants, with a copy of the code taken before the docstring pass (so no comment names a finding), and asks them to derive every cell themselves. They never see the matrix or the findings tracker. The command compares their cells with the matrix, checks each real disagreement against the code and the running app, and probes every other defect they report. Corrected cells and new findings are cited in the matrix, and the counts go in the checklist note.

## Findings from the matrix

A matrix finding names the operation ids, the principal column and the invariant broken: "OP-031, OP-032 as `authenticated`: INV-3, any account can download another account's invoice export". One finding per root cause: when one missing guard opens ten rows, it's one finding citing ten rows. The characterization test is the table row as it behaves today; the intended-behavior test is the same row expected to fail. A matrix finding is a security finding: the tracker entry and the matrix give the rows and the invariant in plain terms, and the requests, ids, tokens and steps that exploit it go only in `docs/intake-findings-restricted.md` (`findings.md`, "Security detail stays out of git").

## Safety of the run

Adversarial tests send real requests. Before any of them, `intake:testing-setup` asserts the harness points only at local resources (the database host, the mail backend, payment, storage and any external API base URL) and fails closed otherwise. A test that would email a real address or charge a real card stops the run instead.
