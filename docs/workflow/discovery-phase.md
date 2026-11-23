# Discovery Phase

Optional phase that turns a feature set, a set of requirements or an unclear ticket into approved tickets, through a discovery topic kept next to the code.

---

## Purpose

Use discovery when there are no tickets yet, or when `spec:triage` sends back a ticket with real unknowns. Each topic lives in `docs/specs/todo/discovery/<topic>/`. Clear items become proposed tickets at once, vague items go through a Feature Forge interview, and items with real unknowns go to research first.

## Commands

| Order | Command | Summary |
|-------|---------|---------|
| 1 | `discovery:create` | Split the input into items, read the existing code, route each item, and write `discovery.md` |
| 2 | `discovery:approve` | After research, consolidate the findings into `synthesis.md` first; then resolve blocking decisions and create the approved tickets in the tracker |

## Outputs

- `discovery.md`, with features, open questions, blocking decisions and proposed tickets
- One Feature Forge specification per vague item, in the topic folder
- `synthesis.md` and `sources/` when research ran
- Tickets in the configured tracker, each with a `Discovery: <topic>` line

## Next Steps

After discovery, proceed to the [Spec Phase](spec-phase.md): `spec:triage` groups the created tickets into specs.
