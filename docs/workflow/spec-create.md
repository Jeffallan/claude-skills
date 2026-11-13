# spec:create

Plan one spec as three local files and print the commands that launch its goal run.

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `spec-name` | string | yes | The kebab-case spec name `spec:triage` created |

## Outputs

- `overview.md`, with the Readiness table first
- `implementation-plan.md`, with the Completion Status table and Proposed tracker changes
- `goal-prompt.md`, plus two launch commands: whole spec and next batch

## How it runs

1. **Checks the order.** It refuses while the spec's `After:` predecessor hasn't merged, unless you override, and rebases the spec branch when it has.
2. **Maps the code.** Read-only subagents report on affected code, reuse and debt (`spec-miner`), on structure, security and APIs when the spec touches them, and on the docs each ticket will affect (`code-documenter`).
3. **Writes the overview.** Header lines first, then the Readiness table: every ticket is Ready, Blocked (question, decision or needs more detail) or Already done with commit evidence. Questions you can answer now go through a Feature Forge interview.
4. **Waits for your approval.** You can ask for a challenge pass with `the-fool` first.
5. **Writes the plan and the goal prompt.** Only Ready tickets get plan sections, each with a `Skill:` line, a `Docs:` line, a type and a RED check. The three files are committed together on the spec branch.
6. **Prints the launch commands.** Whole spec and next batch, each carrying the writes-only deny set, plus the "ask" rules to add to your shared settings. See [Goal Runs](../GOAL_RUNS.md).

## Next Steps

Launch the goal run with one of the printed commands, or run `ticket:execute` by hand.
