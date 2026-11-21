# intake:testing-setup

**Options:** what follows the procedure name in `intake <procedure> ...`, passed on in the brief: an optional root directory to analyze (defaults to the project root).

Stand up the test harness the rest of the testing suite depends on: a runner wired to the project's stack, an
integration harness for the real datastore and backend, an end-to-end driver for the UI, shared fixtures, and the
scripts to run each layer. **Configure only what the stack actually needs, and prove it runs with a smoke test
per layer before finishing. Never leave a harness that has not executed.**

This command is the prerequisite for `intake:testing-authorization`, `intake:testing-owasp`,
`intake:testing-features`, and `intake:testing-user-flows`; they assume the layout, scripts, and helpers it
produces.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the run-and-verify phase, the goal-run behavior, and the safety guard this command adds before any adversarial test runs ("Safety of the run" in `access-control.md`).

## When to use

Run once during the capture-behavior step, after `intake:document-codebase` (ideally after the documentation
suite, so the domain testing commands can read the contract docs). Re-run when the stack or test toolchain
changes. This command is idempotent for the config it owns; it will not clobber hand-written tests.

## Skills to load

- **`fullstack-dev-skills:test-master`**: choose the test architecture, runner, and layering; define the mocking
  and fixture strategy.
- **The project's framework skill** for the runner that matches the stack, e.g.
  `fullstack-dev-skills:react-native-expert`, `fullstack-dev-skills:nextjs-developer`,
  `fullstack-dev-skills:django-expert`, `fullstack-dev-skills:fastapi-expert`.
- **`fullstack-dev-skills:devops-engineer`**: wire the integration backend (emulator, test containers, or
  in-memory double), env vars, and the CI invocation.
- **The project's language skill** for typed, idiomatic test code, e.g. `fullstack-dev-skills:typescript-pro`,
  `fullstack-dev-skills:python-pro`.

## Workflow

### Phase 1: Discover the current test reality
Establish what exists before adding anything:
1. Runner and scripts: a `test` script, a configured runner (Jest, Vitest, pytest, Go test), or none.
2. Existing tests, their location and convention, and any CI that runs them.
3. Test-relevant dependencies already present (testing libraries, mock or emulator tooling).
4. The execution environments the code needs: a browser/DOM env, a native env, a server env, a real datastore.

### Phase 2: Detect the stack and choose the toolchain
Pick the minimum toolchain that covers three layers. A repo with more than one codebase (a backend and a frontend, a server and a mobile app) gets a unit layer for each: "there are no tests there yet" is the reason to add one, never to skip it. State each choice and the reason:
- **Unit/component runner** matching the framework (the framework's conventional preset wins, e.g. an Expo preset
  for React Native, the framework's test client for a web app).
- **Integration harness** for the real backend and datastore: a local emulator, test containers, or an in-memory
  double. Prefer testing against the real enforcement layer (database rules, real handlers) over mocks when an
  emulator or container exists.
- **End-to-end driver** for the UI, chosen by platform: a browser driver (Playwright, Cypress) for a web or
  web-capable build; a device driver (Maestro, Detox) for native-only. Record which build target makes one viable
  and another not.

### Phase 3: Plan layout, config, scripts, and fixtures
- **Layout:** one directory per layer (unit, integration/rules, e2e) plus a shared helpers/fixtures location.
- **Config:** if layers need different execution environments, use a multi-project or multi-config runner setup
  rather than forcing one environment.
- **Scripts:** a script per layer plus an aggregate, and a wrapper that boots the integration backend around the
  integration and e2e runs.
- **Fixtures/helpers:** authenticated-context builders, seed-data factories, deterministic clock and ID helpers,
  and backend setup/teardown.
- **Safety guard:** list every outbound target the test settings resolve: the database host, the mail backend,
  payment, storage, and each external API base URL the code reads from settings or the environment. Plan a check
  that runs once before any test session and aborts it when any target is not local or a test resource (a
  loopback or container host, an in-memory or file mail backend, a provider's test mode or sandbox key, a local
  storage emulator). An unknown or unset target counts as not local: the guard fails closed.

**MANDATORY CHECKPOINT: confirm scope before installing.** Present the chosen toolchain per layer, the
dependencies to add, the directory layout, the scripts, and the integration-backend choice, and the outbound targets the safety guard will check. Do not install or
write config until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Install and configure
Pick test dev-dependency versions that fit the runtime dependencies already installed, never the reverse: never upgrade, downgrade or re-resolve a runtime dependency to make newer test tools fit, and leave the lockfile's existing runtime entries byte-identical (Vue 2.6 takes `@vue/test-utils` 1.x and a runner that supports Vue 2 and the project's Node, not the latest releases that pull Vue 3).

Install the dependencies, write the runner config(s), add the scripts, create the helpers and fixtures, and add
one **smoke test per layer**: a trivial assertion that exercises the layer's wiring (a pure assertion for unit, a
single allowed-plus-denied datastore operation for integration, a single screen load for e2e).

Install the **safety guard** in the runner's session-start hook (a root `conftest.py`, a global setup file, a
`TestMain`), so it runs before every layer and every later testing command's tests. It reads the effective
settings the tests run with, not the settings file's text. Add a smoke test for it like the other layers: one
case where every target is local and the guard passes, and one per target kind where that target points at a
non-local host and the guard aborts. When a target can only be made local by changing application code, record
a finding and leave the code alone (`rules.md`, "What intake may change").

### Phase 5: Run and verify (required; the harness must execute)
Run each layer's script and capture fresh output. Every smoke test must pass, the safety guard's included. When a layer genuinely cannot
run in this environment, report the blocker explicitly; do not hide it. Keep the type-checker clean if the project
is typed. Do not claim the harness works without command output proving it.

## Output template

The deliverable is config and scaffolding, not a document. Produce:

```
<runner config>                 # e.g. jest config (multi-project), vitest.config, pytest.ini
<scripts in package manifest>   # test, test:unit, test:integration, test:e2e, aggregate
<integration backend config>    # emulator/container config + env wiring
<e2e driver config>             # playwright/cypress/maestro config
tests/ (or framework convention)
  unit/         + one smoke test
  integration/  + one smoke test (allowed + denied operation)
  e2e/          + one smoke test (screen loads)
  helpers/      # auth-context builder, fixtures, seed data, setup/teardown
<session-start hook>  # the safety guard, + its smoke test (passes local, aborts non-local)
```

Plus a short "how to run" note: the command for each layer and any prerequisite (a running emulator, a built web
bundle).

## Failure conditions

- **A runner already exists:** extend it; do not replace a working setup or rewrite existing tests.
- **No integration backend is feasible** (no emulator or container for the datastore): say so, fall back to a
  documented in-memory or mock double for the integration layer, and flag the reduced fidelity.
- **An e2e layer cannot run in this environment** (no display, no device): scaffold it, mark it as not-yet-run
  with the reason, and do not claim it passes.

## Output

The harness files above, plus a short summary: the toolchain chosen per layer, the scripts added, the smoke-test
results (with command output), and any layer that could not be executed and why.

Record the safety guard in this item's note in `docs/intake-checklist.md`: where it runs, each target it checks
with its test value, and its smoke-test result.

The summary ends with one `Test paths:` line listing a glob for every folder or file pattern that holds tests, fixtures
or test helpers, comma-separated, for example `Test paths: backend/api/apps/*/tests.py, frontend/tests/*, e2e/*`. Copy the
line into this item's note in `docs/intake-checklist.md`. The intake eval reads it to tell test changes from application
changes, so list test trees only, never a glob that would also match application code.
