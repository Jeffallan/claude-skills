# spec:diff

See what changes if a set of specs lands, in the order you give.

---

`spec:diff [spec ...]` prints a plan beside the current system: the component diagram from `docs/system-description.md` unchanged, a target diagram with every changed node labeled by the spec that changes it, a table per spec of what it adds, changes or removes, and the overlaps where two specs touch the same component or one removes what a later one relies on. With no spec names it takes every outstanding spec in the order `guard spec-status` lists them.

It also lists the assumptions each spec makes about the current system, with `references/specs/assumptions.md`: which components, interfaces, flows, findings and docs it takes for granted, and where each can be checked. `common-ground` checks that list against `docs/current-state.json`.

The command writes nothing, so it runs the same attended or under a goal. It replaces the `--roadmap` mode of `intake:create-system-description`, which wrote a roadmap page into `docs/`. When `docs/current-state.json` is older than the system description, it says so and suggests `spec:current`.
