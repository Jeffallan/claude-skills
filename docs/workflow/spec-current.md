# spec:current

See what is true of the system now: its components, open findings and docs that have drifted from the code.

---

`spec:current` checks `docs/system-description.md` against the code and the specs completed since it was last updated. The `architect` agent proposes the changes, each with its source, and you pick which to apply; the command commits them. It then runs `guard current-state`, which compiles `docs/current-state.json` from three places: the component table in section 2 of the system description (each component `wired`, `built, not wired` or `planned`), the open rows of the findings table in `docs/intake-findings.md`, and `guard docs-drift`. Every row in the JSON names its source, and the compiler refuses a malformed table or an unknown status instead of guessing.

The report lists the components with their status, the open findings, the docs in drift with the procedure that fixes each (`intake <procedure>`), and any description changes you didn't apply.

Under a goal run it changes no doc. It still compiles the JSON from the description as it stands and lists the proposed changes as pending.

People read the system description; `spec:diff`, `common-ground` and the evals read the JSON. Never edit the JSON by hand: rerun `spec:current`.
