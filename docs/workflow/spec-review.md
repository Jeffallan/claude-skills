# spec:review

Review a finished spec branch with adversarial reviewers, then check each finding with a blind verifier.

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `spec-name` | string | yes | The spec whose branch diff is reviewed |

## Outputs

- `review/metrics.md`, one file per reviewer, frozen reproductions in `review/repro/`, `review/verdicts.jsonl` and `review/rollup.md`
- `review/docs.md` and `review/docs-waivers.md` when the docs root holds docs
- `review/decisions.jsonl`, the owner's decision history
- Fix tickets added to the plan for the findings the owner picks, with a fresh `goal-prompt.md` for them

## How it runs

0. **Start clean.** Every ticket in the plan must be Done or Blocked; otherwise it points to the goal run and stops. It commits any Blocked rows a goal run left in the plan with `guard commit-plan`, and the working tree must be clean.
1. **Metrics.** `guard metrics` reports duplication, dead code and complexity for the files the spec changed. A tool that isn't installed means its check did not run, which proves nothing either way; with no tool at all it exits 3. Attended, the command shows each missing tool with its install hint and asks whether to go on; in a goal run it goes on and lists them first in its report. The code reviewer is told which checks did not run, and no refactor fix ticket relies on one.
2. **Panel.** Reviewer subagents read the diff without commit messages: `code-reviewer` and `test-master` always, `code-documenter` whenever the project has docs, others when the diff touches their area. `code-documenter` checks the docs the spec touched against the code, every doc the diff added or changed included: stale claims, broken citations, a fact repeated across docs, one-sided `related:` links. It also rules on every doc a ticket marked "checked, no change" and every doc changed by only a few words, so a goal run can't excuse its own stale docs; `guard gate` stays closed until each has a ruling. Each writes only its own file in `review/`.
3. **Verification.** Each blocking or warning finding goes to a fresh verifier in a scratch worktree. It sees the claim, the code and the ticket's acceptance criteria, never who raised the finding or why. Behavioral claims need a run; a reproduction that fails to run makes the verdict unresolved, never rejected. Reproductions are kept, frozen, in `review/repro/`. The verifiers start together, and the command waits for their reports; it never schedules a wakeup or loop as a fallback.
4. **Rollup.** `guard rollup` builds `review/rollup.md` with every finding, its verdict and the verifier's token and minute cost.
5. **Your triage.** You pick fixes and record won't-fix or accepted rejections with `guard decide`. `guard decide <row> revoke` withdraws a decision, so the gate judges the row afresh; a row you had decided and now want fixed is revoked before it becomes a ticket. Fixes become tickets in the plan, each typed `test`, `test-gap`, `stand-in` or `refactor`, with a fresh goal prompt.

Rerun it after the fix tickets land: it rechecks each fix against its frozen reproduction instead of starting a new panel.

Inside a goal run it stops after the rollup, records no decisions, adds no fix tickets and ends with `BLOCKED: spec:review triage needs the owner`.

## Next Steps

Run the fix tickets through `ticket:execute` or the printed goal run, then rerun `spec:review <spec-name>` for the recheck. Run `spec:complete` once `guard gate <spec-name>` would pass.
