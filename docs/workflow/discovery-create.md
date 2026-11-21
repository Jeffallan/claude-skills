# discovery:create

Turn a feature set, requirement, build request or unclear ticket into a discovery topic with proposed tickets.

---

## Overview

The command lists each item in the input, runs a light `spec-miner` pass so proposed tickets reflect the existing code, and routes each item: clear items get proposed tickets, vague ones go through a Feature Forge interview saved in the topic folder, and items with real unknowns go to research.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic-input` | string | yes | Feature sets, business requirements, a build request, or an existing ticket ID with real unknowns |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `discovery-document` | file | `{specsRoot}/todo/discovery/{topic}/discovery.md` | Feature list, open questions, proposed tickets and status |

## Next Steps

Either way, run `discovery:approve` next. With research items, gather findings in `sources/` first: `discovery:approve` synthesizes them before it asks for decisions.
