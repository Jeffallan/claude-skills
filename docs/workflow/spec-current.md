# spec:current

See what is true of the system now: its components, open findings and docs that have drifted from the code.

---

When `docs/system-description.md` is missing, it stops: "No system description yet. Run `intake create-system-description` first."

`spec:current` checks `docs/system-description.md` against the code and the specs completed since it was last updated. The `architect` agent proposes the changes, each with its source, and you pick which to apply; the command commits them. Applying them counts as a full audit, so the description's `verified:` frontmatter moves to the commit the audit checked, and `guard docs-check` must pass before the commit. It then runs `guard current-state`, which compiles `docs/current-state.json` from three places: the component table in section 2 of the system description (each component `wired`, `built, not wired` or `planned`), the open rows of the findings table in `docs/intake-findings.md`, and `guard docs-drift`. Every row in the JSON names its source. A malformed table or an unknown status stops the compiler with an error naming the row. The command commits `docs/current-state.json` on its own, in a goal run too.

The report lists the components with their status, the open findings, the docs in drift with the procedure that fixes each (`intake <procedure>`), and any description changes you didn't apply.

Under a goal run it changes no doc. It still compiles and commits the JSON from the description as it stands and lists the proposed changes as pending.

People read the system description; `spec:diff`, `common-ground` and the evals read the JSON. Never edit the JSON by hand: rerun `spec:current`.
