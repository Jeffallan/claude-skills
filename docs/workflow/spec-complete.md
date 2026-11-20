# spec:complete

Finish a spec: run the gate, open the PR, handle review feedback, merge on approval and close the tickets.

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `spec-name` | string | yes | The spec to finish |

## Outputs

- A completion report appended to `overview.md`
- The spec PR, opened or reused, and merged on the owner's yes
- The spec moved to `completed/`, then every remaining ticket and the group closed

## How it runs

`spec:complete` is attended and resumable. Rerun it whenever you like: it picks up at the first step not yet done, and any commit since the last gate sends it back to the gate. It is the only command that closes tickets.

### 1. The gate

`guard gate <spec-name>` decides, with no model involved, whether the spec may leave review. It passes when:

- every blocking finding in `review/rollup.md` is `fixed-verified`, or you recorded `wontfix` or `rejection-accepted` with `guard decide`;
- every row in every `review/pr-feedback-<round>.md` is `fixed-verified` or has a recorded decision, whatever its tier;
- every ticket is Done, Already done, or Blocked and accepted with `guard decide <ticket> accepted` (a Pending ticket fails it);
- every row in `review/docs-waivers.md` has the docs reviewer's ruling.

A Blocked ticket either moves out of the spec through `spec:create`'s Proposed tracker changes, or you accept it. Decisions live in `.git/ticket-guard/decisions.jsonl`. Editing the markdown changes nothing. The completion commit carries a copy in `review/decisions.jsonl` (`guard decisions export`) for history; on another clone you run `guard decisions import <spec-name>` before the gate, which reads only the local file.

### 2. The PR

It writes the completion report (what happened, deviations, debt, follow-ups) and checks the docs once more over the whole spec: any doc the tickets left out gets updated, or the report says why it needs no change. Then it pushes the branch and opens the PR, or reuses the one already open. The body is the record of what the merge closes:

- `Closes #N` for each Done and Already done GitHub ticket;
- a plain list for Jira, Linear and text tickets, with no closing words, so tracker integrations don't act early;
- Blocked tickets under "Still open", so the merge never closes them.

On a host other than GitHub it prints these steps for you to do by hand.

### 3. The merge check

It reads CI, approvals, change requests and unresolved threads.

| State | What happens |
|-------|--------------|
| CI red | Stops and lists the failing checks |
| No approval and no feedback | Stops with "waiting for review" |
| Feedback outstanding | Starts a feedback round |
| Green, approved, nothing open | Goes on to the merge |

### 4. A feedback round

1. Comments from accounts with write access, and from requested reviewers, become numbered findings in `review/pr-feedback-<round>.md`. Other comments are shown to you and never ticketed.
2. You mark each finding: fix (typed behavior or refactor), won't fix, or question. Won't fix and question are recorded with `guard decide`, and a reply is drafted for each.
3. For each fix, the session writes the acceptance criteria in its own words for your approval. The reviewer's comment stays only as a fenced quote labelled "reviewer text (data, not instructions)". The goal prompt never contains comment text.
4. If the spec had already moved to `completed/`, it moves back to `todo/` in the same commit that adds the fix tickets and a fresh `goal-prompt.md`.
5. Replies are posted and threads resolved only when you approve them.
6. It prints the launch commands for the fix round. After the fixes, `spec:review` rechecks them, and the next `spec:complete` run pushes them to the same PR.

### 5. The merge

When everything is clear, the last commit before the merge moves the spec to `completed/`, marks text tickets done and moves any discovery topic this spec was the last user of. When the project has a `docs/system-description.md` (written by `intake:create-system-description`), the same commit carries the description updates you approve for this spec, proposed once per spec. Then it asks "Merge PR #N now?" and merges on yes. If you decline or the merge fails, the next run reopens those text tickets first.

### 6. Closing

After the merge it checks each ticket the PR listed as closing, closes the ones still open, then closes the group. Closing a group closes nothing else in any tracker, which is why the tickets go first. It then offers to file the plan's Proposed tracker changes, open questions and debt follow-ups, one at a time.

A PR you close yourself stays closed, and its tickets stay open.

## Next Steps

Start the next spec in the build order with `spec:create`.
