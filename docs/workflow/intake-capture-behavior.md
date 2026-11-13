# Capture behavior

The intake step that writes a runnable test suite pinning the codebase's current behavior, through the five `intake:testing-*` commands.

**Status:** Step name only. There is no `intake:capture-behavior` command; the step runs as the commands below.

---

## Commands

Run them in this order. Each later command needs the harness from `intake:testing-setup` and reads its paired documentation doc.

| Order | Command | Reads | Writes |
|-------|---------|-------|--------|
| 1 | [`intake:testing-setup`](intake-testing-setup.md) | the codebase | unit, integration and e2e harness, one smoke test per layer |
| 2 | [`intake:testing-features`](intake-testing-features.md) | `docs/domain/features.md` | unit, component and parity tests |
| 3 | [`intake:testing-authorization`](intake-testing-authorization.md) | `docs/security/authorization.md` | allow and deny tests per resource and verb |
| 4 | [`intake:testing-owasp`](intake-testing-owasp.md) | `docs/security/security.md` | adversarial tests per OWASP category |
| 5 | [`intake:testing-user-flows`](intake-testing-user-flows.md) | `docs/flows/user-flow.md` | backend and UI end-to-end tests |

## Characterize, don't fix

The tests record what the code does today. A known bug gets a passing test that pins the current behavior and a sibling skipped or expected-fail test for the intended behavior, both naming the finding id from `docs/intake-findings.md`. Intake never fixes a bug and never asserts one as correct.

## Why five commands

The v0.5.0 plan had a single `capture-behavior` command. The dogfood pass that produced the intake specs showed each layer needs its own harness checks, fixtures and paired doc, so the step was split. The name stays as the label for the step.
