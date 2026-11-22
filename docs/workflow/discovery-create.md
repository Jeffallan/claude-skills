# discovery:create

Turn a feature set, requirement, build request or unclear ticket into a discovery topic with proposed tickets.

---

## Overview

The command lists each item in the input, runs a light `spec-miner` pass so proposed tickets reflect the existing code, and routes each item: clear items get proposed tickets, vague ones go through a Feature Forge interview saved in the topic folder, and items with real unknowns go to research. When a goal is active, it skips the interviews, records each vague item's open questions in `discovery.md` and asks you to rerun attended.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic-input` | string | yes | Feature sets, business requirements, a build request, or an existing ticket ID with real unknowns |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `discovery-document` | file | `{specsRoot}/todo/discovery/{topic}/discovery.md` | Feature list, open questions, proposed tickets and status |
| `feature-specs` | files | `{specsRoot}/todo/discovery/{topic}/{feature}.md` | One Feature Forge specification per vague item |
| `sources` | directory | `{specsRoot}/todo/discovery/{topic}/sources/` | Created for research items; research results go here as markdown |

## Next Steps

Either way, run `discovery:approve` next. With research items, gather findings in `sources/` first: `discovery:approve` synthesizes them before it asks for decisions.
