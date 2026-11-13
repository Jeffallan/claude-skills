# ticket:complete

Check a ticket's evidence, update the Completion Status table and commit the ticket.

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ticket-id` | string | no | Ticket ID; optional when `ticket:execute` ran in this session |

## Outputs

- One commit with the ticket's work, its Completion Status row and the evidence summary

## How it runs

1. **Boundary checks.** `guard rerun` runs the work in a clean temporary worktree. `guard red-replay` puts only the new tests on the start commit and expects them to fail. `guard tamper-scan` flags deleted tests, added skips, changed snapshots and assertion-free tests.
2. **Evidence summary.** `guard summary` prints the line for the Completion Status notes, or fails when RED or GREEN evidence is missing or an affected doc was neither updated nor checked.
3. **One commit.** The work and the updated row go into the same commit, with a neutral `Ticket: <id>` trailer that no tracker integration acts on.
4. **Clears the marker** after the commit.

It never writes to the tracker. In a goal run a failed check blocks the ticket through `guard block` instead of stopping the run.

## Next Steps

Run `ticket:execute` for the next ticket, or `spec:review` when every ticket is Done or Blocked.
