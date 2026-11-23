# ticket:complete

Check a ticket's evidence, update the Completion Status table and commit the ticket.

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ticket-id` | string | no | Ticket ID; optional while a ticket marker exists, since the marker names the ticket in progress |

## Outputs

- One commit with the ticket's work, its Completion Status row and the evidence summary

## How it runs

0. **Finds the marker.** `guard marker status` names the ticket. When the marker was lost and no clear was logged, the evidence can't be trusted as it stands. A goal run blocks the ticket with `guard block <ticket> "marker lost"`, passing `--start <sha>` when the evidence has no open start. Attended, it runs the boundary checks with `--ticket <ticket>`, and only when they pass may you accept the ticket with `guard summary --ticket <ticket> --accept-lost-marker`.
1. **Boundary checks.** `guard rerun` runs the work in a clean temporary worktree. `guard red-replay` puts only the new tests on the start commit and expects them to fail. `guard tamper-scan` flags deleted tests, added skips, changed snapshots and assertion-free tests. Attended, you can explain a flag, and the scan reruns with `--reason <ID>=<line>`; the rest get fixed.
2. **Evidence summary.** `guard summary` prints the line for the Completion Status notes, or fails when RED or GREEN evidence is missing or an affected doc was neither updated nor checked. A RED or GREEN script outside the repo also counts as missing evidence: a reboot deletes it, and nothing can rerun it later.
3. **One commit.** The work and the updated row go into the same commit, with a neutral `Ticket: <id>` trailer that no tracker integration acts on. Attended, it shows the message and the staged files and commits on your yes. The project's commit hooks always run; they are never skipped.
4. **Clears the marker** after the commit.

It never writes to the tracker. In a goal run a failed check blocks the ticket through `guard block` instead of stopping the run.

## Next Steps

Run `ticket:execute` for the next ticket, or `spec:review` when every ticket is Done or Blocked.
