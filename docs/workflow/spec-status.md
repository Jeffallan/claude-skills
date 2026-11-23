# spec:status

See where every spec stands, and the next command for each.

---

`spec:status` lists every spec: its state, how many tickets are done, blocked and pending, what it waits on (`After:`), the ticket in progress, its pull request, and the command to run next. It reads each `spec/<name>` branch straight from git, so the answer doesn't depend on which branch you have checked out. In a GitHub project it also asks for each branch's pull request through `gh`; set `status.pullRequests` to `false` in `.claude/workflow-config.json` to skip that. If the lookup fails, the pull request column says `unknown` and everything else still shows.

A spec that exists only as a folder on your current branch, with no `spec/<name>` branch and nothing on the default branch, shows as `Unbranched (on <branch>)` with no branch or PR. Give it a branch with `spec:triage`, or merge it into the default branch. `spec:diff` and `common-ground` count it as outstanding.

Completed specs are hidden; `spec:status --all` shows them. The command changes nothing.
