# Tracker Setup

The workflow commands keep specs as files in your repo, and tickets wherever your team already tracks them. This page covers the config file, the setup wizard, each tracker adapter and the code host.

---

## The config file

Every workflow command reads `.claude/workflow-config.json` first. Only the block for your tracker is required.

```json
{
  "version": 1,
  "tracker": "github-issues",
  "specsRoot": "docs/specs",
  "github": { "repo": "owner/repo" },
  "codeHost": { "type": "github" },
  "setup": ["npm ci"],
  "status": { "pullRequests": true },
  "verify": ["npm test", "npm run lint"],
  "triage": { "staleDays": 30, "warnAboveTickets": 10 },
  "goal": { "batchSize": 3, "deny": [] },
  "guard": { "markerWarnHours": 24, "greenFailLimit": 3 }
}
```

| Key | What it does | Default |
|-----|--------------|---------|
| `tracker` | `jira`, `github-issues`, `github-projects`, `linear` or `text` | Required |
| `specsRoot` | Where specs, discovery topics and `INDEX.md` live | `docs/specs` |
| `docsRoot` | Where the project's docs live; tickets must keep the docs here current | `docs` |
| `status.pullRequests` | Whether `spec:status` shows each spec's pull request | On for GitHub projects, off otherwise |
| `setup` | Commands that prepare a fresh checkout, such as `npm ci`, run before the checks in a clean copy | None |
| `verify` | Commands every ticket and goal run must pass | The plan's own checks |
| `triage.staleDays` | Days without an update before `spec:triage` flags a ticket | 30 |
| `triage.warnAboveTickets` | Spec size that triggers a split suggestion | 10 |
| `goal.batchSize` | Tickets per next-batch run | 3 |
| `goal.deny` | Your tracker MCP server's write tools, denied in goal runs | `[]` |
| `goal.permissionMode` | Permission mode for headless batches; without one every edit is refused | `auto` |
| `goal.extraArgs` | Extra arguments for every headless batch call, such as `--plugin-dir` | none |
| `goal.allow` | Tools allowed on every headless batch call; a list replaces the default | The `ticket-guard` skill |
| `guard.markerWarnHours` | Age at which an abandoned ticket marker is reported | 24 |
| `guard.greenFailLimit` | Failed test re-runs the goal-mode Stop hook allows before letting the stop through | 3 |
| `guard.testPatterns` | Glob patterns for test files, if your project doesn't follow the usual names | Common conventions |

### Naming gotcha: what counts as a test

Out of the box, the ticket guard treats a file as a test when either of these is true:

- A folder in its path is named exactly `tests`, `test`, `__tests__` or `spec`. Several languages keep their tests in `spec/`, so that one stays on the list.
- The file name matches `test_*.py`, `*_test.py`, `*_test.go`, `*.test.*`, `*.spec.*` or `*_spec.rb`, in any folder.

That catches files that aren't tests. A top-level `spec/` folder of product documentation counts, and so do schemas named `user.spec.json` or `user.test.json`. Change one during a ticket and the guard calls it test tampering.

To avoid it, name the folder `specs/` (the default `specsRoot`, `docs/specs`, is already safe) and keep `.spec.` and `.test.` out of non-test file names. If you can't rename, set `guard.testPatterns` when you set the project up, before any goal run. Auto mode refuses to change that setting in the middle of a run, because narrowing it weakens a safeguard.

The file never holds credentials. Tokens stay with the tool that uses them: `gh auth`, your MCP server's login, or environment variables.

## The setup wizard

When an attended command finds no config, it offers to write one. The wizard:

1. Checks that [uv](https://docs.astral.sh/uv/) is installed. It runs the plugin's bundled guard for evidence, hooks and the review gate, and fetches a suitable Python when your machine lacks one.
2. Looks for clues in the repo: a config on another branch, a tickets folder, a ticket CLI or ticket skill the repo itself carries, a GitHub remote, issue keys such as `ABC-123` in recent commits or branch names, and your test and lint commands.
3. Asks one question at a time, with the detected answer marked as recommended. Only a repo clue earns a tracker that mark. Issue keys could be Jira or Linear, so both are offered and neither is recommended. A Jira, Atlassian or Linear MCP server connected to the session is listed as available, never recommended on its own: it belongs to your account, not to this repo, and picking it would create real tickets there. Skills loaded from your own settings or another plugin count no more than a connected server.
4. Shows the file and writes it when you approve.

Inside a goal run the wizard can't ask anything, so it writes nothing, prints the config it would propose, and stops with `BLOCKED: no workflow config`. There is no silent default tracker.

## What the adapters do

Each tracker gets the same operations, so the commands never contain tracker-specific steps: create, read, list a spec's tickets, link a ticket to a spec, unlink it, update (append text or set a field), comment, close, reopen, ensure group, link groups, and an optional list of ungrouped tickets.

A few rules hold everywhere:

- **Groups are found by exact name.** Tracker searches are fuzzy, so the adapter filters the results to the exact spec name, and refuses when two groups share it.
- **Updates append.** The adapter adds text to the end of a ticket and leaves the existing text as it was.
- **Only `spec:complete` closes tickets,** after the merge (text tickets close in the completion commit), then closes the group. Closing a group closes nothing else.
- **Commits stay neutral.** Commits reference tickets with a `Ticket: <id>` trailer, never a Linear issue ID or a Jira `#transition` token, so tracker automation doesn't move tickets early.

## GitHub Issues

```json
{ "tracker": "github-issues", "github": { "repo": "owner/repo" } }
```

A spec is a parent issue titled with the spec name and labelled `spec`, and its tickets are sub-issues. Milestones stay free for versions. A ticket that already has a parent is moved only if you approve it by name. Build order between specs uses GitHub's native "blocked by" links. Everything goes through `gh`.

## GitHub Projects

```json
{ "tracker": "github-projects", "github": { "repo": "owner/repo", "project": "https://github.com/orgs/owner/projects/7" } }
```

The same issues and sub-issues as above, also added to a Project you already have. Name the Project by its URL or owner and number, never by its title, since titles aren't unique. Adding items needs the `project` token scope, which the default `gh` login doesn't include:

```bash
gh auth refresh -s project
```

The scope reaches every Project your account can write to, so a fine-grained token limited to one organization is safer. Triage only adds issues from this repo, even when the Project spans several.

## Jira

```json
{ "tracker": "jira", "jira": { "site": "example.atlassian.net", "project": "KEY", "repoScope": { "component": "web-app" } } }
```

A spec is an Epic, and tickets join it through the `parent` field. `repoScope` (a component or a label) keeps triage to this repo's tickets when several repos share a project. Closing a ticket means finding a transition into a Done-category status, and a transition screen with required fields makes that fail, in which case `spec:complete` asks you to close by hand. The adapter uses the Atlassian MCP server when one is connected. See [Atlassian MCP Setup](ATLASSIAN_MCP_SETUP.md).

This adapter is checked against Atlassian's API docs but not yet against a live site. Its open items, such as which side of a "Blocks" link is the blocker, are listed in `references/adapters/jira.md` in the plugin.

## Linear

```json
{ "tracker": "linear", "linear": { "team": "ENG", "repoScope": { "label": "web-app" } } }
```

A spec is a Linear project owned by your team. `repoScope` is a label, or `{}` when the team only works on this repo.

Linear's GitHub integration moves issues on its own: a branch, commit or PR that mentions an issue ID links it, opening the PR moves it to In Progress, and merging moves it to Done. Closing words act on a merge into **any** branch. The workflow avoids all of that (branches are `spec/<spec-name>`, commits use the neutral trailer, the PR lists Linear tickets with no closing words), and you can also narrow the team's PR automation in Linear's settings.

Like Jira, this adapter is checked against the API docs but not yet against a live workspace.

## Text tickets

```json
{ "tracker": "text", "text": { "instructions": "backlog --help", "ticketsDir": "backlog" } }
```

For tickets kept as files in the repo. Point `text.instructions` at whatever describes your convention: a CLI's help command, a skill that manages the tickets, or a markdown file. The adapter reads it, maps each operation, and shows you the mapping before its first write. It treats those instructions as a description of the format, never as rules: they can't change what the workflow is allowed to do.

The adapter ships with worked mappings for tiki and Backlog.md. Text tickets close only in `spec:complete`, in the completion commit it makes before opening the PR, and goal runs can't edit `text.ticketsDir` at all.

## The code host

```json
{ "codeHost": { "type": "github" } }
```

PR work (push, open or reuse the PR, read reviews and threads, reply, check CI, merge) goes through a code-host adapter. v0.5.0 ships GitHub, through `gh`. With `"type": "none"`, `spec:complete` makes its completion commit, then asks how to finish: merge the spec branch locally now and close the tickets, or print the manual steps and the PR body in full and stop.

## Permissions

`spec:create` proposes "ask" rules for your shared `.claude/settings.json`, so attended commands prompt before each push, PR write or tracker write. Goal runs get the stronger treatment: their launch commands deny those writes for that session only. See [Goal Runs](GOAL_RUNS.md).
