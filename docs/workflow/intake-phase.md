# Intake Phase

One-time onboarding of an existing codebase: reference docs agents can rely on, a characterization test suite, and a findings tracker. Run it once when you adopt a project; every later phase reads its output.

---

## Purpose

Before feature work starts, agents need documented code, docs that describe what the code does today, and tests that catch an unintended change. Intake writes all three and records every bug it finds instead of fixing it.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `procedure` | string | no | One procedure to run or rerun, followed by its options (`intake document-api backend/`, `intake create-system-description --full`). Without it, the checklist is worked from the first unchecked item |

## Command

One command runs the phase: `intake [procedure]`. It works `docs/intake-checklist.md` from the first unchecked item; a procedure name runs or reruns that one. Each procedure runs in one agent. Attended, it stops at a checkpoint to show its scope, then writes; in a goal run it does the item in one pass and its scope goes in the checklist note as a draft. Only one agent writes at a time, but read-only `code-reader` agents gather facts for the next item while the current one writes. The one exception: after `intake:testing-setup` is committed, `intake:testing-features`, `intake:testing-authorization` and `intake:testing-owasp` write at once, and the command commits them one at a time. The command reviews the diff and commits the item. The phase runs once (`run_once` in the manifest). Procedures run in the order of the table, which is the checklist order. The command runs through the system description; wiring the PR gate and closing out the findings tracker stay attended and outside it.

| Step | Procedure | Output |
|------|---------|--------|
| Existing docs, first | [`intake:existing-docs`](intake-existing-docs.md) | `docs/intake-existing-docs.md` |
| Docstrings | [`intake:document-codebase`](intake-document-codebase.md) | Docstrings and module comments across the code |
| Documentation | [`intake:document-file-tree`](intake-document-file-tree.md) | `docs/architecture/file-tree.md` |
| Documentation | [`intake:document-data-model`](intake-document-data-model.md) | `docs/architecture/data-model.md` |
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
| System description | [`intake:create-system-description`](intake-create-system-description.md) | `docs/system-description.md` |

## Prerequisites

- Access to the project codebase and a way to run its tests
- No tracker or code host: intake uses no adapter operations

## Next Steps

After intake, `feature-forge` and the spec commands read the docs. If discovery is needed, go to the [Discovery Phase](discovery-phase.md). Otherwise, go to the [Spec Phase](spec-phase.md).
