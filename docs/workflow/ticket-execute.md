# ticket:execute

Implement one ticket test-first from the spec's implementation plan.

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ticket-id` | string | yes | Ticket ID from the spec's implementation plan |

## Outputs

- The ticket's changes, uncommitted, with RED and GREEN evidence recorded under the git directory

## How it runs

1. **Finds the ticket** in the spec's plan. It never needs the tracker, so a run can resume offline.
2. **Starts clean.** The working tree must be clean. `guard marker start` records the mode and the start commit.
3. **Loads the guard.** It invokes the `ticket-guard` skill, checks that its hooks registered, then loads the skill on the ticket's `Skill:` line.
4. **RED.** It writes the failing test first and records it with `guard run red`. The test imports the code under test inside its body, so an import error never passes as RED. Any script a RED or GREEN command runs is committed in the repo with the ticket's tests, never left in `/tmp` or a scratchpad. From then on the test files are frozen.
5. **Implements and records GREEN** with `guard run green`, then runs the project's `verify` commands.
6. **Updates the docs.** `guard docs-affected` lists every doc that cites code the ticket changed, plus the docs those link to in their `related:` frontmatter, and every doc the ticket adds or changes. Each one gets updated in the ticket's work, or recorded as needing no change with `guard docs-checked` and a reason. The ticket isn't done until every doc is one or the other.

In a goal run it never asks a question. A stuck ticket goes through `guard block`, which saves the work as a patch and restores the tree, and the run moves on.

## Next Steps

Run `ticket:complete` to check the evidence and commit.
