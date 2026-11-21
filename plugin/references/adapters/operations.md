# Adapter Operations and Workflow Config

Every workflow command reaches the tracker and the code host through the operations below, never through a tracker-specific step written into the command. Each tracker has its own file in this folder that maps every operation to a real call. A command reads `.claude/workflow-config.json` first, then loads only the file for the configured tracker.

| Tracker value | Adapter file |
|---------------|--------------|
| `jira` | `references/adapters/jira.md` |
| `github-issues` | `references/adapters/github-issues.md` |
| `github-projects` | `references/adapters/github-projects.md` (plus `github-issues.md`) |
| `linear` | `references/adapters/linear.md` |
| `text` | `references/adapters/text.md` |

PR operations go through the code-host adapter, `references/adapters/code-host-github.md`, the only host in v0.5.0.

## Vocabulary

- **Ticket:** one unit of work in the tracker (a Jira issue, a GitHub issue, a Linear issue, a text file).
- **Group:** the tracker object that holds a spec's tickets (a Jira Epic, a parent spec issue, a Linear project). Its title is the spec name, unchanged.
- **Spec line:** `Spec: <spec-name>` appended to each ticket body by `spec:triage`, so every command finds a ticket's spec the same way in every tracker. A ticket's spec is its last `Spec:` line.
- **Released line:** `Released from <spec-name>: <reason>` appended by `spec:complete` to a ticket it hands back to the backlog. A Released line after the last `Spec:` line means the ticket is in no spec.

## Tracker operations

The adapter-operations names in each command's YAML definition use the IDs in the first column.

| ID | Operation | Input | Returns | Required |
|----|-----------|-------|---------|----------|
| `create` | Create a ticket | title, body, optional group | ticket ID | Yes |
| `read` | Read a ticket | ticket ID | title, body, status, labels, group, links, last update | Yes |
| `list-spec-tickets` | List a spec's tickets | group ID | ticket IDs with status | Yes |
| `link` | Link a ticket to a group | ticket ID, group ID | nothing | Yes |
| `unlink` | Remove a ticket from its group | ticket ID, group ID | nothing | Yes |
| `update` | Update a ticket: append text, or set one field such as points | ticket ID, text or field and value | nothing | Yes |
| `comment` | Comment on a ticket | ticket ID, text | comment ID | Yes |
| `close` | Close a ticket as completed | ticket ID | final status | Yes |
| `reopen` | Reopen a closed ticket | ticket ID | status | Text: yes. Others: optional |
| `ensure-group` | Find the group by exact spec name, or create it | spec name | group ID | Yes (a no-op for a text convention that groups by the `Spec:` line) |
| `link-groups` | Mark one group blocked by another (`After:`) | blocked group, blocking group | nothing | Best effort: report when unsupported |
| `list-ungrouped` | List open tickets in no group, within the repo scope | none | ticket IDs | Optional: without it, list open tickets and drop those in a group |

### Rules for every adapter

- **Append, never rewrite.** `update` adds text to the end of a ticket body. Existing text stays as it was.
- **Exact names.** `ensure-group` matches the spec name exactly, after a tracker search that is always fuzzy. When two groups share the name, it refuses and names both; the owner resolves it.
- **Close each ticket, then the group.** Closing a group closes nothing else in any tracker.
- **No status moves.** There is no "set status" operation. Only `spec:complete` closes or reopens tickets.
- **Neutral commit trailer.** Commits reference tickets as `Ticket: <id>`. Never put a Linear issue ID or a Jira `#transition` token in a commit message or branch name; tracker integrations act on those.
- **Repo scope.** Reads that list tickets (`list-ungrouped`, triage queries) apply the tracker's `repoScope` filter, so a shared tracker never pulls in another repo's tickets.
- **Writes are attended.** Goal runs never call a write operation. Every write raises the shared "ask" permission rule, and the owner approves it.

## Code-host operations

| ID | Operation | Used by |
|----|-----------|---------|
| `open-pr` | Push the spec branch, then open the spec PR or reuse the open one | `spec:complete` |
| `read-pr-feedback` | Read reviews, change requests and unresolved threads, with each author's write access | `spec:complete` |
| `reply-resolve` | Post an approved reply, resolve a thread | `spec:complete` |
| `check-pr` | CI status, approvals, change requests, unresolved threads | `spec:complete` |
| `merge-pr` | Merge the spec PR | `spec:complete`, on the owner's yes |

With `codeHost.type` set to anything but `github`, `spec:complete` stops before the PR step, prints the manual steps (push, open the PR with the generated body, merge), and closes the tickets after the owner says the merge is done.

## `.claude/workflow-config.json`

Nested per tracker. Only the chosen tracker's block is required; every other key has the default shown.

```json
{
  "version": 1,
  "tracker": "github-issues",
  "specsRoot": "docs/specs",
  "github": { "repo": "owner/repo", "project": "https://github.com/orgs/owner/projects/7" },
  "jira": { "site": "example.atlassian.net", "project": "KEY", "repoScope": { "component": "web-app" } },
  "linear": { "team": "ENG", "repoScope": { "label": "web-app" } },
  "text": { "instructions": "tiki --help", "ticketsDir": "tickets" },
  "codeHost": { "type": "github" },
  "triage": { "staleDays": 30, "warnAboveTickets": 10 },
  "setup": ["npm ci"],
  "status": { "pullRequests": true },
  "verify": ["npm test", "npm run lint"],
  "goal": { "batchSize": 3, "deny": ["mcp__linear__save_issue"], "allow": ["Skill(fullstack-dev-skills:ticket-guard)"], "permissionMode": "auto", "extraArgs": [] },
  "guard": { "markerWarnHours": 24, "greenFailLimit": 3, "testPatterns": ["tests/**", "**/*.test.ts"] }
}
```

| Key | Meaning | Default |
|-----|---------|---------|
| `version` | Config format version | `1` |
| `tracker` | `jira`, `github-issues`, `github-projects`, `linear` or `text` | None; required |
| `specsRoot` | Folder holding `todo/`, `completed/` and `INDEX.md` | `docs/specs` |
| `github.repo` | `owner/repo` | The `origin` remote |
| `github.project` | Project owner plus number (`owner/7`) or the project URL; never a title | Required for `github-projects` |
| `jira.site`, `jira.project` | Site host and project key | Required for `jira` |
| `jira.repoScope` | `{"component": "<name>"}` or `{"label": "<name>"}`: only tickets matching it belong to this repo | Required for `jira` |
| `linear.team` | Team key | Required for `linear` |
| `linear.repoScope` | `{"label": "<name>"}`, or `{}` when the team holds only this repo's tickets | Required for `linear` |
| `text.instructions` | A CLI help command, a skill name, or a markdown file in the repo that describes the ticket convention | Required for `text` |
| `text.ticketsDir` | Folder holding text tickets; goal runs may not edit it | Required for `text` |
| `codeHost.type` | `github`, or `none` for manual PR steps | `github` when `origin` is on github.com, else `none` |
| `triage.staleDays` | Flag tickets with no update for this many days | `30` |
| `triage.warnAboveTickets` | Warn and suggest a split above this many tickets in one spec | `10` |
| `status.pullRequests` | Whether `spec:status` asks the code host for each spec branch's PR. When the lookup fails, the PR column says `unknown` and the rest still prints | `true` for a GitHub code host, else `false` |
| `setup` | Commands that prepare a fresh checkout (install dependencies) before any verify command runs in it: `spec:create`'s check run and the guard's clean re-run and RED replay worktrees. A failing setup command fails the check, naming the command | `[]` |
| `verify` | Verification commands every ticket and goal run reruns | `[]` (the commands then use the plan's) |
| `goal.batchSize` | Tickets per next-batch run | `3` |
| `goal.deny` | Extra tool names denied in goal runs: the tracker MCP server's write tools | `[]` |
| `goal.permissionMode` | Permission mode `guard run-batches` passes on every headless call; without one, a headless session has every edit refused | `auto` |
| `goal.extraArgs` | Arguments passed as-is on every headless call, such as `["--plugin-dir", "<build>"]` | `[]` |
| `goal.allow` | Tools `guard run-batches` allows on every headless call; a list here replaces the default | `["Skill(fullstack-dev-skills:ticket-guard)"]` |
| `guard.markerWarnHours` | Warn when a ticket marker is older than this | `24` |
| `guard.greenFailLimit` | Consecutive GREEN failures the goal-mode Stop hook blocks before letting the stop through | `3` |
| `guard.testPatterns` | Glob patterns for test files, replacing the runtime's default convention | Runtime default |

The config never holds credentials. Tokens stay in the tool that uses them (`gh auth`, the MCP server's login, environment variables).

## Config wizard

Every attended command that needs the config and finds none runs this wizard before anything else.

**Unattended guard first.** When a goal is active, write nothing. Print the proposed config (detected values, with the questions still open) and end with `BLOCKED: no workflow config`. When `AskUserQuestion` is unavailable and no goal is active, take the wrong-session stop in `references/specs/unattended.md` instead. There is no silent default tracker.

1. **Check the runtime.** Run `uv --version`. When it fails, tell the owner to install uv (`https://docs.astral.sh/uv/`) and stop: the bundled guard runs through `uv run`, which also supplies Python 3.11 or later when the machine lacks it.
2. **Detect signals.** The tracker recommendation comes only from the repo:
   - An existing config: `.claude/workflow-config.json` on another branch (`git log --all -1 --format=%h -- .claude/workflow-config.json`): recommend its tracker and block.
   - A text-ticket tool in the repo (a `tickets/` folder, a ticket CLI on `PATH` that the repo's docs name, a skill that manages tickets): recommend `text`.
   - The `origin` remote (`git remote get-url origin`) on github.com: recommend `github-issues`, and `codeHost.type: "github"`.
   - Issue keys such as `ABC-123` in recent commit subjects or branch names (`git log -50 --format=%s`, `git branch -a`): a Jira or Linear project. Offer both, naming the key, and recommend neither.
   - A Jira, Atlassian or Linear MCP server among the session's tools: list that tracker as available, never the recommendation on its own. A connected server belongs to the session's account, not to this repo, and picking it would create real tickets there.
   - No repo signal: mark no tracker "(Recommended)".
   - Test and lint commands in the project's manifests or Makefile: recommend them for `verify`.
   - A dependency install the checks need in a fresh checkout (`npm ci` beside a `package-lock.json`, `uv sync` beside a `uv.lock`): recommend it for `setup`.
   - Files the guard would treat as tests that aren't (a `spec/` folder of product docs or schemas, a `*.spec.json` or `*.test.json` data file; see the naming gotcha in `docs/TRACKER_SETUP.md`): recommend `guard.testPatterns` listing the real test paths.
3. **Ask, one question at a time,** with `AskUserQuestion`, putting the detected value first and marked "(Recommended)" (for the tracker, only a repo signal from step 2 earns that mark): the tracker; then that tracker's block; then `verify`; then `setup` and `guard.testPatterns` when step 2 found a reason for them. Test patterns are settled here, attended, because a goal run may not narrow them later: auto mode refuses that as weakening a safeguard.
   - Jira: site and project key, then the repo scope. Propose a component when the project has components whose name matches the repo, else a label equal to the repo name.
   - Linear: team, then the repo scope. Propose a label equal to the repo name, or `{}` when the team's issues all belong to this repo.
   - GitHub Projects: the project URL or owner plus number. Then run `gh auth status`; when the `project` scope is missing, tell the owner to run `gh auth refresh -s project`.
   - Text: where the convention is described (`text.instructions`) and the tickets folder.
4. **Show the file and write it on approval.** Write `.claude/workflow-config.json`, then continue the command that called the wizard. Remind the owner to commit the file with the next spec commit.

## When not to use these operations

- Reading a ticket's text for a goal run: the run reads the plan, never the tracker, so it can resume without tracker access.
- Discovery topics and spec files: they are local files under `specsRoot`, never tracker objects.
