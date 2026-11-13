# spec:status

See where every spec stands, and the next command for each.

---

`spec:status` lists every spec: its state, how many tickets are done, blocked and pending, what it waits on (`After:`), the ticket in progress, its pull request, and the command to run next. It reads each `spec/<name>` branch straight from git, so the answer doesn't depend on which branch you have checked out. In a GitHub project it also asks for each branch's pull request through `gh`; set `status.pullRequests` to `false` in `.claude/workflow-config.json` to skip that. If the lookup fails, the pull request column says `unknown` and everything else still shows.

Completed specs are hidden; `spec:status --all` shows them. The command changes nothing.
