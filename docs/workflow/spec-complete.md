# spec:complete

Finish a spec: run the gate, write the completion commit, open the PR, handle review feedback, merge on approval and close the tickets.

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `spec-name` | string | yes | The spec to finish |

## Outputs

- A completion report in `overview.md`
- `review/docs-verify.md` in the spec folder: the `docs:verify` table of doc claims the spec's diff touches
- The spec moved to `completed/`, with the docs and system description updates you approved, in one completion commit
- The spec PR, opened or reused, and merged on the owner's yes
- Every remaining ticket closed after the merge, each Blocked ticket released to the backlog, then the group closed

## How it runs

`spec:complete` is attended and resumable. Rerun it whenever you like: it picks up at the first step not yet done, and any commit since the last gate sends it back to the gate. It is the only command that closes tickets. Inside a goal run it writes nothing and never merges: it prints the gate result and the next step, then stops with `BLOCKED: spec:complete needs the owner`.

### 1. The gate

`guard gate <spec-name>` decides, with no model involved, whether the spec may leave review. It passes when:

- every blocking finding in `review/rollup.md` is `fixed-verified`, or you recorded `wontfix` or `rejection-accepted` with `guard decide` (a decision withdrawn with `guard decide <row> revoke` no longer counts);
- every row in every `review/pr-feedback-<round>.md` is `fixed-verified` or has a recorded decision, whatever its tier;
- every ticket is Done, Already done, or Blocked and accepted with `guard decide <ticket> accepted` (a Pending ticket fails it);
- every row in `review/docs-waivers.md` has the docs reviewer's ruling.

A Blocked ticket either moves out of the spec through `spec:create`'s Proposed tracker changes, or you accept it. When a fix ticket's plan says it delivers a Blocked ticket's work, the command asks whether that ticket is done and, on yes, marks it Done so it closes with the others. Decisions live in `.git/ticket-guard/decisions.jsonl`. Editing the markdown changes nothing. The completion commit carries a copy in `review/decisions.jsonl` (`guard decisions export`) for history; on another clone you run `guard decisions import <spec-name>` before the gate, which reads only the local file.

### 2. The completion commit

Everything the merge should carry goes in one commit on the spec branch before the PR opens, so CI runs once on the final branch:

1. The completion report in `overview.md`: what happened per ticket, each Blocked ticket with its reason, deviations, debt paid and found, and follow-ups.
2. The spec moves from `todo/` to `completed/`. Before the move, the command lists code, tests, scripts and CI that point at the old path, shows you each hit and updates it in the same commit.
3. Text tracker: Done and Already done tickets are marked done, with each previous status recorded in the commit body so a later feedback round can reopen them. Tickets still open are released to the backlog, and the follow-ups you approve are filed as new ticket files.
4. Each discovery topic this spec was the last open user of moves to `completed/discovery/`.
5. System description: when the project has `docs/system-description.md` (written by `intake create-system-description`) and its Change history doesn't list this spec yet, the command proposes section changes for you to approve one at a time, then adds a Change history row.
6. Docs over the whole spec: `guard docs-affected` and `guard docs-check`. Any doc the tickets left out gets updated, or the report says why it needs no change. When the project has a docs index, each doc the spec added goes into it and each doc it removed comes out.
7. `docs:verify`, described below.
8. `INDEX.md` and `review/decisions.jsonl` are refreshed and staged.

The commit is `docs(<spec-name>): complete the spec`.

#### docs:verify

Step 6 covers the docs the guard tracks through citations. `docs:verify` reads the rest of what the project says about itself: the root `README` and every Markdown file under `docs/`, outside the specs folder. It lists the names the spec's diff removed, renamed or changed (paths, commands, flags, config keys, environment variables, routes, defaults) and searches the docs for each. A second pass covers what a name search misses: in the docs that hit, and in the docs that describe a component the diff touches, it checks the absolute statements ("calls no remote third-party service", "no credentials exist", "only admins can delete") against the diff, since a change can make one false without renaming anything. Read-only `code-reader` agents, using the `spec-miner` skill, check each claim in the docs that hit, all at once. The result is printed and saved as `review/docs-verify.md`:

| Doc | Claim | Verdict | Evidence |
|-----|-------|---------|----------|
| `README.md`, Configuration | "Set `API_URL` to point at the backend" | stale | `src/config.ts::loadConfig` reads `BACKEND_URL` since this diff |
| `docs/setup.md`, Install | "Run `make dev`" | holds | `Makefile::dev` |

- **holds:** the code bears the claim out.
- **stale:** the diff contradicts it. The command proposes a fix and asks you about each stale row, one at a time, the same way it handles the system description. It edits a doc only on your yes, and marks the row `fixed` or `declined`, so a rerun asks only about new rows.
- **unknown:** no code settles it. It is listed, never treated as a problem.

### 3. The PR

It pushes the branch and opens the PR, or reuses the one already open. The body is the record of what the merge closes:

- `Closes #N` for each Done and Already done GitHub ticket;
- a plain list for Jira, Linear and text tickets, with no closing words, so tracker integrations don't act early;
- Blocked tickets under "Still open", so the merge never closes them.

With `codeHost.type` set to `none`, it first checks that the completion commit is in place, then asks how you want to finish: merge `spec/<spec-name>` into the default branch locally now and go on to closing, or print the manual steps and the PR body in full and stop.

### 4. The merge check

It reads CI, approvals, change requests and unresolved threads.

| State | What happens |
|-------|--------------|
| CI red | Stops and lists the failing checks |
| No approval and no feedback | Stops with "waiting for review", unless you are the only account with write access: you can't approve your own PR, so green CI is enough and the merge question counts as the approval |
| Feedback outstanding | Starts a feedback round |
| Green, approved (or solo owner), nothing open | Goes on to the merge |

### 5. A feedback round

1. Comments from accounts with write access, and from requested reviewers, become numbered findings in `review/pr-feedback-<round>.md`. Other comments are shown to you and never ticketed.
2. You mark each finding: fix (typed behavior or refactor), won't fix, or question. Won't fix and question are recorded with `guard decide`, and a reply is drafted for each.
3. For each fix, the session writes the acceptance criteria in its own words for your approval. The reviewer's comment stays only as a fenced quote labelled "reviewer text (data, not instructions)". The goal prompt never contains comment text.
4. If the spec had already moved to `completed/`, it moves back to `todo/`, and text tickets closed in the completion commit are reopened, in the same commit that adds the fix tickets and a fresh `goal-prompt.md`.
5. Replies are posted and threads resolved only when you approve them.
6. It prints the launch commands for the fix round. After the fixes, `spec:review` rechecks them, and the next `spec:complete` run makes the completion commit again and pushes everything to the same PR.

### 6. The merge

It asks "Merge PR #N now?" and merges on yes. If you decline or the merge fails, it stops, and the next run reopens the text tickets the completion commit closed before doing anything else.

### 7. Closing

After the merge it checks each ticket the PR listed as closing and closes the ones still open. Each ticket still open because it was Blocked goes back to the backlog: it is unlinked from the group and gets a `Released from <spec-name>: <reason>` note, so the next `spec:triage` lists it as ungrouped. Then it closes the group. Closing a group closes nothing else in any tracker, which is why the tickets go first. For a remote tracker it then offers to file the plan's Proposed tracker changes, open questions and debt follow-ups, one at a time. The text tracker filed them in the completion commit.

A PR you close yourself stays closed, and its tickets stay open.

## Report

The command ends with a table: the gate, the PR and its merge commit, the closed tickets, the tickets released to the backlog (with `spec:triage <IDs>` as their next step), the group, the filed follow-ups, the system description sections updated, and the `docs:verify` counts (stale rows fixed and declined, unknown rows) pointing at `review/docs-verify.md`. It names the next spec in the build order.

## Next Steps

Start the next spec in the build order with `spec:create`. Run `spec:triage` on any released tickets.
