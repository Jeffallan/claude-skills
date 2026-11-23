# Spec Assumptions

How `spec:diff` and `common-ground` list the assumptions a spec makes about the system as it stands, so both commands list the same ones and `common-ground` can check them against `docs/current-state.json`.

## When to use

- `spec:diff`: list each selected spec's assumptions beside its changes.
- `common-ground`: list them again for the specs it checks, then hand them to the `assumption-checker` agent.

Not for assumptions about tools, coding standards or the owner's preferences: those are `common-ground`'s own Surface step (`references/common-ground/assumption-classification.md`).

## Which specs

Spec names given on the command line, in that order. With none, every outstanding spec from `guard spec-status` (any state but Completed), in its listed order. A spec name that doesn't resolve to `<specsRoot>/todo/<spec>/` is refused with the list of outstanding specs.

Read each spec's `overview.md` and `implementation-plan.md`. A Triaged spec with no overview yet is read from its triage tickets; say so in its row.

## What counts as an assumption

A statement the spec relies on about the current system that the spec itself doesn't create. Look for:

| Kind | Examples |
|------|----------|
| `component` | A component exists, or has a status (`wired`, `built, not wired`): "extends the existing export worker" |
| `interface` | A route, function, schema, event or config key exists with a shape: "`POST /invoices` returns the invoice id" |
| `flow` | Data moves a certain way: "payments reach the ledger through the queue" |
| `finding` | A known bug is still open, or already fixed: "after F-003 is fixed" |
| `doc` | A doc's claim is current: "as `docs/security/authorization.md` describes" |
| `order` | Another spec lands first, or doesn't: "once billing-v2 adds the plan table" |

Skip what the spec builds itself, and restatements of the acceptance criteria.

Two kinds are easy to miss:

- Every sentence that says how the system works now is an assumption, wherever it sits (Purpose, Scope, Design, a ticket): "today", "currently", "already", "existing", "the same X the server uses". Those sentences are the spec's beliefs about the present.
- When a sentence says component A uses B ("the export worker posts through the ledger client"), list "A can reach B" as its own `interface` assumption, beside any row about B itself, unless the spec adds that connection. A spec often relies on wiring that isn't there.

## The list

One row per assumption, numbered per spec (`<spec>:A1`, `<spec>:A2`, ...):

```markdown
| ID | Spec | Kind | Assumption | Quoted from | Checked against |
|----|------|------|------------|-------------|-----------------|
| billing-v2:A1 | billing-v2 | component | The export worker is wired | overview.md, "Approach" | components: Exporter |
```

- **Quoted from** names the file and section the assumption comes from, so the owner can find the sentence.
- **Checked against** names where the answer lives: a `components`, `findings` or `drift` row of `docs/current-state.json`, section 3 of `docs/system-description.md` for a flow, a `path::symbol` for an interface, or another spec for `order`.
- When an open finding in `docs/current-state.json` touches the assumption, name it in **Checked against** as well, beside the code or component (`src/export/worker.ts::postInvoice; F-003`). A long list makes these easy to drop.

## Order between specs

The specs are taken in the given order. A later spec's assumption that an earlier one changes is checked against the state after the earlier spec, and its row says so (`after billing-v2`). Two specs that touch one component, or one that removes what another assumes, go in the overlaps table `spec:diff` prints.

## Rules

- List, never judge: holds, conflicts and unknown are the `assumption-checker`'s answer, never this list's.
- Quote; never paraphrase into a stronger claim than the spec makes.
- An assumption with no place to check it is still listed, with `Checked against: nothing` so the owner sees the gap.
