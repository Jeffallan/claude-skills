# discovery:approve

Synthesize a discovery topic's research when it has some, resolve its blocking decisions and create its approved tickets in the configured tracker.

---

## Overview

The one approval gate before tickets exist. When `discovery:create` routed items to research and the topic has no `synthesis.md` yet, it first reads `discovery.md`, the Feature Forge files and `sources/`, answers each open question with cited findings, and writes `synthesis.md` with the remaining unknowns, blocking decisions and the tickets the research supports. It commits that and shows it to you. Then it resolves blocking decisions with the owner, lets them edit or drop proposed tickets, and creates the rest through the tracker adapter, each with a `Discovery: <topic>` line. It forms no groups. A topic that ends with no tickets moves to `completed/`.

It runs attended only. When a goal is active it writes nothing: it prints the proposed tickets and open decisions as a read-only proposal and ends with `BLOCKED: discovery:approve needs the owner`. When `discovery.md` lists research items and `sources/` is empty, it stops and asks you to add the research under `sources/` and rerun.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic` | string | yes | Discovery topic name to approve |
| `decisions` | list[string] | no | Pre-resolved blocking decisions (e.g., --decision=D1:B --decision=D2:Y) |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `synthesis-document` | file | Findings, unknowns, decisions and proposed tickets in `{specsRoot}/todo/discovery/{topic}/synthesis.md`, written first when research ran and no synthesis exists |
| `created-tickets` | tickets | Tickets created in the configured tracker, ready for `spec:triage` |
| `topic-updates` | file | The topic file, `discovery.md`, updated: decisions with the chosen option, "Created as <ID>" beside each created ticket, and the topic status ("Tickets created"), or the reason it closed with no tickets |

## Next Steps

Run `spec:triage discovery:<topic>` to group the new tickets into specs.
