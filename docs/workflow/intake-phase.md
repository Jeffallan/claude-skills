# Intake Phase

One-time onboarding of an existing codebase: reference docs agents can rely on, a characterization test suite, and a findings tracker. Run it once when you adopt a project; every later phase reads its output.

---

## Purpose

Before feature work starts, agents need documented code, docs that describe what the code does today, and tests that catch an unintended change. Intake writes all three and records every bug it finds instead of fixing it.

## Commands

The phase runs once (`run_once` in the manifest). Commands within a step can run in any order unless a row says otherwise.

| Step | Command | Output |
|------|---------|--------|
| Existing docs, first | [`intake:existing-docs`](intake-existing-docs.md) | `docs/intake-existing-docs.md` |
| Docstrings | `intake:document-codebase` | Docstrings and module comments across the code |
| Documentation | [`intake:document-data-model`](intake-document-data-model.md) | `docs/architecture/data-model.md` |
| Documentation | [`intake:document-file-tree`](intake-document-file-tree.md) | `docs/architecture/file-tree.md` |
| Documentation | [`intake:document-integrations`](intake-document-integrations.md) | `docs/architecture/external-integrations.md` |
| Documentation | [`intake:document-api`](intake-document-api.md) | `docs/architecture/api-reference.md` |
| Documentation | [`intake:document-user-model`](intake-document-user-model.md) | `docs/domain/user-model.md` |
| Documentation | [`intake:document-features`](intake-document-features.md) | `docs/domain/features.md` |
| Documentation | [`intake:document-glossary`](intake-document-glossary.md) | `docs/domain/glossary.md` |
| Documentation | [`intake:document-security`](intake-document-security.md) | `docs/security/security.md` |
| Documentation | [`intake:document-authorization`](intake-document-authorization.md) | `docs/security/authorization.md` |
| Documentation | [`intake:document-user-flow`](intake-document-user-flow.md) | `docs/flows/user-flow.md` |
| Documentation | [`intake:document-config`](intake-document-config.md) | `docs/operations/configuration.md` |
| Documentation | [`intake:document-analytics`](intake-document-analytics.md) | `docs/operations/analytics-events.md` |
| Documentation, last | [`intake:create-onboarding`](intake-create-onboarding.md) | `docs/README.md`, or `docs/README-intake.md` beside your own |
| [Capture behavior](intake-capture-behavior.md), first | [`intake:testing-setup`](intake-testing-setup.md) | Test harness with a smoke test per layer |
| Capture behavior | [`intake:testing-features`](intake-testing-features.md) | Feature characterization tests |
| Capture behavior | [`intake:testing-authorization`](intake-testing-authorization.md) | Authorization matrix tests |
| Capture behavior | [`intake:testing-owasp`](intake-testing-owasp.md) | OWASP Top 10 tests |
| Capture behavior | [`intake:testing-user-flows`](intake-testing-user-flows.md) | Backend and UI flow tests |
| System description | `intake:create-system-description` | `docs/system-description.md` |

## Prerequisites

- Access to the project codebase and a way to run its tests
- No tracker or code host: intake commands use no adapter operations

## Next Steps

After intake, `feature-forge` and the spec commands read the docs. If discovery is needed, go to the [Discovery Phase](discovery-phase.md). Otherwise, go to the [Spec Phase](spec-phase.md).
