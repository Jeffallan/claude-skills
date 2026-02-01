# Intake Phase

One-time project onboarding that establishes baseline understanding of an existing codebase. Run once when first adopting a project; results feed every subsequent phase.

---

## Purpose

Before any feature work begins, the team needs documented code, behavioral safety nets, and a shared system overview. Intake produces all three artifacts in sequence.

## Commands

| Order | Command | Summary |
|-------|---------|---------|
| 1 | `intake:document-codebase` | Scan and document all undocumented functions, classes, and modules |
| 2 | `intake:capture-behavior` | Write characterization tests asserting current behavior |
| 3 | `intake:create-system-description` | Generate a living system description at `docs/system-description.md` |

## Outputs

- **Documented codebase** — Docstrings/JSDoc/XML docs on every public API and module
- **Characterization tests** — Safety net that detects unintended behavior changes
- **System description** — Architecture overview, API surface, security patterns, external dependencies

## Prerequisites

- Access to the project codebase
- No external tooling (ticketing/documentation) required

## Next Steps

After intake, the system description is available for `feature-forge` to read during feature definition. If discovery is needed, proceed to the [Discovery Phase](discovery-phase.md). Otherwise, skip to [Planning](planning-phase.md).
