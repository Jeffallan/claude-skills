# intake:testing-owasp

**Options:** what follows the procedure name in `intake <procedure> ...`, passed on in the brief: an optional root directory to analyze (defaults to the project root).

Produce tests that probe the project from an attacker's perspective, organized by the OWASP Top 10. Per
category, first decide whether it applies to this codebase and why, then apply the category's techniques to the
real surfaces. **Ground every test in a real surface in the code. Characterize current behavior, including weaknesses;
flag a known weakness with its tracked finding id rather than asserting it is safe.**

This command is adversarial coverage over the same surfaces that `intake:testing-authorization` (the access
matrix) and `intake:testing-features` (functional behavior) cover positively. It owns the logic, credential and
configuration tests in `access-control.md` ("Who owns what"). Read `docs/security/security.md`,
`docs/security/authorization.md`, `docs/domain/features.md` and `docs/operations/configuration.md` if present.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the run-and-verify phase, the goal-run behavior, and the operation inventory, invariants, access matrix, tokens and settings tables this command tests against.

**In a parallel batch** ("Parallel testing writers" in the `intake` command, which runs this procedure beside the other two testing procedures): never edit `docs/intake-findings.md`. Give each new finding a provisional id from the range your brief names, run only your own test files, and report every tracker change under `Tracker edits:` in your item report (`references/intake/rules.md`, "The item report"). The command assigns the real ids in checklist order and applies the edits. Everything else in this procedure applies as written.

## When to use

Run during the capture-behavior step, after `intake:testing-setup`, `intake:testing-authorization` and (ideally)
`intake:document-security`. Re-run when input surfaces, authentication, or configuration change. Idempotent for
the tests it owns.

## Skills to load

- **`fullstack-dev-skills:security-reviewer`**: map each OWASP category to the codebase's real surfaces and rate
  applicability; lead the threat enumeration and run the scanners whose output is evidence.
- **`fullstack-dev-skills:secure-code-guardian`**: turn each threat into a concrete test (injection payloads,
  logic abuse, credential-lifecycle cases, fail-open probes).
- **`fullstack-dev-skills:test-master`**: structure the suite and fixtures, and set the boundary between
  unit-level validation tests and integration-level probes.
- **`fullstack-dev-skills:the-fool`**: adversarial pre-mortem on coverage; surface the categories and edge cases
  the others assumed away.

## Workflow

### Phase 1: Map the Top 10 to real surfaces
Use the current OWASP Top 10 edition and its ids and names. At the time of writing that is the 2025 edition
(`https://top10.owasp.org/2025/`); when a newer one is published, use it and map the techniques below to its
categories. Name the edition in the coverage map.

Per category, name the concrete surfaces in this codebase, or mark it **N/A with a reason**. Do not write a test
for a surface that does not exist. Request-path surfaces are the operation ids from the inventory (`## Operations`
in `docs/architecture/api-reference.md`), library-mounted and framework routes included. The surfaces outside the
request path are listed under "Outside the request path" below. Each category lists its techniques; apply every
technique that has a surface, and give each one a coverage-map row.

- **A01:2025 Broken Access Control.** The access matrix owns it: `intake:testing-authorization` executes every
  operation-by-principal cell, the object-level, field-level and transition cases, and the channels per protected
  object. Do not re-derive any of it. Cite its table in the coverage map (row count, the test's path) and test here
  only what a matrix cell can't express:
  - server-side request forgery: every server-side fetch of a caller-supplied URL or host, with an internal address,
    a cloud metadata address, a redirect to either, another scheme (`file:`, `gopher:`) and an alternate IP encoding;
  - path traversal: every caller-supplied file name or path that reaches the filesystem or object storage;
  - cross-site request forgery and CORS: a state-changing operation sent cross-origin with the victim's ambient
    credentials, and the CORS response to an untrusted origin under the deployed settings.
- **A02:2025 Security Misconfiguration.** Command evidence plus targeted tests:
  - run the framework's deployment check against the deployed settings (for example `manage.py check --deploy`,
    a production-mode config lint, a header scanner against a local production build) and record the command;
  - each row of `## Security settings: test versus deployed` in `docs/operations/configuration.md`: where the test
    value turns a control off (throttling, CSRF, password rules, cookie flags, debug), test the control under the
    deployed value with a per-test settings override, or cite the row in a `not tested` status with the reason;
  - each library default in `## Library security settings` that bears on security: test what it allows or record it;
  - debug, health, admin and metrics surfaces the inventory lists with `Source: library` or `framework`: reachable
    by whom, under the deployed settings;
  - error responses, security headers, XML parsers that resolve external entities.
- **A03:2025 Software Supply Chain Failures.** Command evidence: the stack's dependency audit (for example
  `npm audit`, `pip-audit`, `bundle audit`, `govulncheck`, `osv-scanner`) over every lockfile, with its output;
  lockfiles present and committed; CI actions, base images and install scripts pinned (no unpinned third-party
  action, no script piped from the network into a shell). A vulnerable or end-of-life dependency is a finding with a
  `none: ...; evidence:` line. Rate an advisory by the reach this app shows, never by the advisory's own score
  (`findings.md`, "Severity"): search the code for the function, option or input the advisory names.
  With no exposure path shown in this app, the finding is Low, however the advisory rates itself. Its `What:` line gives the
  advisory id, the advisory's own severity and what you searched, and its Recommendation names the fixed version
  without installing it. When the code does reach the vulnerable path, cite the call site and rate what it lets
  someone do here, by the same table.
- **A04:2025 Cryptographic Failures.** Command evidence plus tests:
  - the secrets scan over the full git history (see "Outside the request path");
  - the password hasher and its parameters under the deployed settings; a test that a stored password is hashed
    with it;
  - signed tokens and cookies: a token signed with another key, an unsigned token (`alg: none` for JWTs) and a
    tampered payload are refused;
  - random values that guard access (reset tokens, invite codes, API keys) come from a secure generator and are long
    enough to resist guessing;
  - every field the data model flags as secret (password hashes, tokens, keys, personal data marked sensitive) stays
    out of every read channel, the framework's admin views and library-mounted views included: render each and
    assert the value is absent or masked;
  - transport settings (HSTS, secure cookie flags, redirect to HTTPS) under the deployed settings.
- **A05:2025 Injection.** Find the sinks first, then the inputs that reach them: raw query APIs and query builders
  fed caller strings (sort and filter keys included), shell execution, templates built from strings, NoSQL operator
  objects in JSON bodies, header values (CRLF), server-rendered HTML. Test each reachable sink with one realistic
  payload and assert the input stays inert (stored or echoed literally, or refused with the specific error).
- **A06:2025 Insecure Design.** Business logic. Take each multi-step flow and each state machine (`## State
  machines` in `docs/domain/features.md`, the flows in `docs/flows/user-flow.md`) and apply:
  - **skip a step:** call step N without step N-1 (confirm without pay, publish without review);
  - **replay:** repeat a completed step (redeem a code twice, confirm twice);
  - **reorder:** run the steps out of order (cancel after fulfil, edit after submit);
  - **double-submit:** send the same write twice concurrently and assert exactly one effect;
  - **boundary and negative quantities:** zero, negative, one past the maximum, very large, fractional where only
    whole units make sense, and currency precision;
  - **limit bypass:** reach a rate limit, quota or per-user cap through parallel requests, another channel for the
    same operation, an identifier written another way (case, whitespace, Unicode lookalike), or a value the client
    computes and the server trusts (price, total, discount);
  - **one test per project invariant:** each `INV-7` onward (`## Project invariants` in
    `docs/domain/features.md`, plus any access-only one in `docs/security/authorization.md`), attacked directly.
- **A07:2025 Authentication Failures.**
  - **Credential lifecycle.** For each credential the system issues (session, access and refresh token, API key,
    password reset, activation, invite and email-change links) and each state change that should void it
    (deactivation or any other blocking state, password change, logout, role change, email change), use the
    credential after the change and assert it is refused. The matrix's blocking-state columns test operations; this
    tests the credentials themselves, links included.
  - **Token properties.** For each token in `## Tokens` of `docs/security/security.md`: replay it twice (single use),
    replay it after the state change it relates to (voided), freeze the clock one second before and at the expiry
    boundary (accepted, then refused), present it as another user (bound to one user) and for another purpose (a
    reset token as an activation token).
  - Login and reset throttling under the deployed settings, account enumeration (sign-up, login and reset responses
    that differ for a known and an unknown account), session rotation on login and privilege change, server-side
    invalidation on logout, any second factor skipped by calling the step after it.
- **A08:2025 Software or Data Integrity Failures.** Deserialization of caller-supplied data with an unsafe loader;
  webhooks and callbacks with no signature, a wrong signature and a replayed signed body; any client-held state the
  server trusts without a signature.
- **A09:2025 Security Logging and Alerting Failures.** Run the security events (failed login, denied access, role
  or password change, blocking-state entry) under captured logs and assert each is recorded with the actor. The
  reverse check, secrets in logs, is under "Outside the request path".
- **A10:2025 Mishandling of Exceptional Conditions.** Failing open. For each dependency a security decision reads
  (the permission lookup, the session or token store, an external identity provider, a feature-flag service, a
  payment or webhook verifier), make it raise or time out inside the real stack and assert the request is denied,
  not allowed. Also: a multi-step write that fails partway leaves no half-written state; malformed input (wrong type,
  missing field, oversized, invalid encoding) gets the specific client error, not a server error; error responses
  carry no stack trace, query or internal path.

### Outside the request path
These surfaces never appear in the route table, so the inventory misses them. Work through each item, prefer a
command whose output is the evidence, and give each a coverage-map row under the category it belongs to:

- [ ] **Secrets in git history** (A04): a secrets scanner over every commit, not only HEAD (for example
  `gitleaks detect --log-opts="--all"`, `trufflehog git file://.`). A secret removed from HEAD but present in history
  is still a finding: it needs rotating.
- [ ] **Seed data, fixtures and migrations** (A02, A04): default or demo accounts with known passwords, privileged
  accounts a data migration creates, real personal data. Evidence: the grep or listing command.
- [ ] **Dockerfile, compose, CI and infrastructure code** (A02, A03): a container running as root, secrets in build
  arguments or baked environment, debug flags, default credentials in compose files, CI jobs that run untrusted pull
  request code with secrets, unpinned actions, public storage or open network rules. Evidence: a config scanner
  (for example `hadolint`, `trivy config`, `checkov`, `zizmor`) or the grep command.
- [ ] **Client-side sinks** (A05, A04, A01): raw HTML rendering of caller data (`dangerouslySetInnerHTML`, `v-html`,
  `innerHTML`, a template's mark-safe filter), tokens kept in script-readable storage, open redirects through a
  return-URL parameter, secrets or source maps in the built bundle (build it, grep the output for keys, list `.map`
  files the server would serve).
- [ ] **File uploads** (A05, A01, A02): type checked by content and not only by name, size limit, the stored path
  free of caller input, served with a content type and disposition that stop it running as a page (HTML, SVG).
- [ ] **Secrets and tokens in logs** (A09, A04): run login, reset and token flows under captured logs and assert no
  password, token, key or session id appears; grep log statements that dump request bodies or headers.
- [ ] **Who can trigger an email or notification to whom** (A06, A07): for each operation that sends one, which
  principal can trigger it, to which address, how often, and whether a link in it is built from a request header the
  caller controls (the host header in a reset link).

### Phase 2: Design adversarial cases
Per applicable category, design tests that attempt the abuse and assert the outcome. Where the app defends
correctly, assert the defense holds. Where it does not, the test characterizes the current (weak) behavior and is
paired with an intended-fix test (see below). Use `fullstack-dev-skills:the-fool` to widen coverage before writing.
Before any request-sending test, confirm the harness guard from `intake:testing-setup` is in place
(`access-control.md`, "Safety of the run").

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the draft coverage map (category, surface,
technique, planned status), the N/A reasons, the evidence commands, which tests characterize known weaknesses, and
where the tests will live. Do not write until the user confirms. In a goal run, follow the checkpoint rule in
`references/intake/rules.md`.

### Phase 3: Write the tests
Mix integration probes (against the real backend and datastore via the harness, credentials sent the way a client
sends them) with unit tests on validators and pure guards. Name each test by category id and technique. Keep
payloads realistic and minimal. After every write a probe attempts, re-read the stored state and assert it. Run each
evidence command and keep the exact command line, so the CI gate can run it again.

### Phase 4: Run and verify (required)
Run the suite and capture fresh output. A passing security test must pass because the defense worked, not because
an unrelated error was raised, so assert the specific outcome. Keep the type-checker clean. Re-run each evidence
command and record its exit status and the count it reports.

### Handling known weaknesses
When a category exposes a real weakness, write a passing test that **characterizes current behavior** plus a
skipped or expected-fail test asserting the **hardened** behavior, both cross-referencing the tracked finding id.
A weakness only a command can show (a vulnerable dependency, a secret in history, a deploy setting) gets a finding
whose `Tests:` line reads `none: <why>; evidence: <command>` (`findings.md`, "Every finding has evidence").
The suite stays green while the gap stays visible. This is a documentation-and-regression task, not a remediation
task; do not fix the code here.

## Output template

The deliverable is tests plus a coverage map:

```
<test dir>/owasp/
  a02-misconfiguration.test.*
  a06-insecure-design.test.*
  a07-authentication.test.*
  ...                       # one file per applicable category, named by the edition's id
```

Coverage map, headed with the edition (`OWASP Top 10:2025`), one row per category, surface and technique:

| Category | Surface | Technique | Status | Test or evidence | Finding refs |
|---|---|---|---|---|---|
| A01:2025 | access matrix | operation x principal | tested | `<matrix test path>` (<N> rows, `intake:testing-authorization`) | |
| A06:2025 | OP-031 | double-submit | tested | `<test path>::<test id>` | F-014 |
| A03:2025 | lockfiles | dependency audit | tested | `npm audit --omit=dev` (exit 0) | |
| A10:2025 | identity provider | fail open | not tested: provider stubbed out by the harness | | |

Status is `tested` (a test, or an evidence command whose output is the check), `not tested: <reason>`, or
`not examined`. A category marked N/A gets one row with its reason.

## Failure conditions

- **A category does not apply:** record it N/A with a one-line reason; do not fabricate a surface.
- **The access matrix tests are missing:** do not rebuild them here; mark the A01 matrix row `not examined` and add
  an Open question pointing at `intake:testing-authorization`.
- **Scope creep into remediation:** if you start fixing the code, stop; characterize and flag instead.
- **A probe cannot run without a live external service:** stub the boundary, mark the reduced fidelity, and do not
  claim full coverage.
- **A scanner isn't installed:** run it without installing it into the project (`uvx`, `npx`, a container), or mark
  the row `not tested: <tool> unavailable`; never mark it tested.

## Output

The test files above, plus a summary: the edition used, the coverage map, test counts, the evidence commands with
their exit status, weaknesses characterized with their finding ids, and run results with command output.
