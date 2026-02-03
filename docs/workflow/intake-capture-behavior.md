# intake:capture-behavior

Scan for untested behavior and write characterization tests that assert current functionality as a safety net for future changes.

**Status:** Planned

---

## Overview

The agent identifies functions, endpoints, and components with no test coverage and builds a test plan based on what the code *currently does* — not what it should do. These characterization tests capture existing behavior so that future changes will immediately surface regressions. Tests are run against the live code to verify they pass before being committed.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to scan for untested behavior. Defaults to project root. |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `characterization-tests` | file | Test files asserting current behavior |
| `coverage-report` | report | Summary of behavior captured and coverage added |

## Prerequisites

- Documented codebase (from `intake:document-codebase`)
- Project test framework configured and runnable

## Next Steps

After capturing behavior, run `intake:create-system-description` to generate the living system description.
