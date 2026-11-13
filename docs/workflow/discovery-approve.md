# discovery:approve

Resolve a discovery topic's blocking decisions and create its approved tickets in the configured tracker.

---

## Overview

The one approval gate before tickets exist. It resolves blocking decisions with the owner, lets them edit or drop proposed tickets, and creates the rest through the tracker adapter, each with a `Discovery: <topic>` line. It forms no groups. A topic that ends with no tickets moves to `completed/`.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic` | string | yes | Discovery topic name to approve |
| `decisions` | list[string] | no | Pre-resolved blocking decisions (e.g., --decision=D1:B --decision=D2:Y) |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `created-tickets` | tickets | Tickets created in the configured tracker, ready for `spec:triage` |

## Next Steps

Run `spec:triage discovery:<topic>` to group the new tickets into specs.
