# intake:document-codebase

Scan the entire codebase and generate documentation for all undocumented functions, classes, modules, and endpoints.

**Status:** Planned

---

## Overview

The agent scans the codebase, identifies every function, class, module, and endpoint that lacks documentation, and prioritizes public APIs and external-facing interfaces first. Before generating anything, it presents a scope summary for approval. It then generates docstrings/JSDoc/XML docs throughout the codebase so that any developer or agent can understand function signatures without tracing implementations.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to scan. Defaults to project root. |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `documentation-report` | report | Summary of documentation added: function count, class count, module count |

## Prerequisites

- Access to the project codebase
- No external tooling required

## Next Steps

After documenting the codebase, run `intake:capture-behavior` to create characterization tests for the newly-documented code.
