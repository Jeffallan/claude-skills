# spec:triage

Group open tickets into specs and, after approval, create each spec's tracker group, `Spec:` lines and branch.

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `scope` | string | no | Ticket IDs, a tracker query, `discovery:<topic>`, or a grouping such as "A, B and C together; D alone". With none, the open ungrouped tickets |

## Outputs

- One tracker group per approved spec, with its tickets linked and a `Spec: <spec-name>` line on each
- One `spec/<spec-name>` branch per spec, cut from the default branch
- A proposed build order across the specs (`After:` lines)

## How it runs

1. **Reads the scope.** With no argument it lists open tickets that belong to no group. For Jira and Linear only tickets matching the repo filter in `.claude/workflow-config.json` are read.
2. **Sorts out the rest.** Closed and cross-repo tickets are left out with a reason. A ticket nobody can write acceptance criteria for yet stays in its group, flagged with a `discovery:create` suggestion, when you named it; the no-argument sweep leaves such tickets out. A ticket in a spec that has already started is never moved. An open ticket left in a spec under `completed/` by an older `spec:complete` gets a proposed release (unlinked, with a Released line) and is eligible once you approve it. Stale tickets (30 days idle, naming files that are gone, or already mentioned by a merged PR) are flagged, never closed.
3. **Proposes specs.** Each grouping states the signals behind it, strongest first: tracker links, a shared discovery topic, shared labels, shared files or feature areas, then wording. A grouping you type in the argument wins over all of them. Every ticket you asked about lands in a spec: one that contradicts another ticket, the code or a settled decision stays in the group and is flagged for `spec:create`, which blocks it until you decide. Above 10 tickets it suggests a split, shown beside the default grouping and never applied by dropping tickets. Several specs get a build order through `After:` lines.
4. **Writes after your yes.** It finds or creates each group by its exact name, links the tickets, appends `Spec: <spec-name>` to each, adds blocked-by links where the tracker has them, adds the spec issue and its tickets to the GitHub Project when one is configured, and cuts `spec/<spec-name>` from the default branch. With the text adapter it commits the ticket-file edits on the spec branch, locally and without a push. A rerun after a partial failure finishes the rest without duplicates.

Inside a goal run it writes nothing and ends with `BLOCKED:`.

## Next Steps

Run `spec:create <spec-name>` for the first spec in the build order.
