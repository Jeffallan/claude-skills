# Hooks and Guard Commands

What each ticket-guard hook does, and the guard commands the ticket commands call. The guard ships with the plugin as one Python file, `runtime/guard.pyz`; every call is written `guard ...` and runs as `uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" ...`. uv supplies a Python 3.11 or later when the machine has none, and nothing is fetched from PyPI. Its state lives under the git directory, in `$(git rev-parse --git-dir)/ticket-guard/`, so nothing it writes there is committed and each worktree has its own. The one exception is the owner decision log, `decisions.jsonl`: `guard decisions export` copies a spec's decisions to its `review/` folder for git history, and on another clone the owner runs `guard decisions import` to add them to that clone's log. The gate reads only the local log.

## When to use this reference

- A hook denied an edit, asked for approval, or blocked a stop, and you need to know why.
- You are resuming a ticket and need the meaning of a marker field.
- You are checking which guard command a ticket step calls.

## When not to use it

- To decide what a ticket should do: the ticket's section of the plan decides that.
- To record an owner decision: `guard decide` and `guard decisions import` are attended only and never part of a ticket.

## The marker gate

Every hook runs the same shell test first:

```sh
m="$(git -C "${CLAUDE_PROJECT_DIR:-.}" rev-parse --absolute-git-dir 2>/dev/null)/ticket-guard/marker.json"
[ -f "$m" ] || exit 0
exec uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" hook <event>
```

A session with no ticket pays about 2 ms per hooked call for the file test (1.9 ms measured 2026-11-11); ticket work pays about 80 ms to start Python and the guard (median of 20 runs, 2026-11-12), with nothing fetched from the network. Outside a git repo the path doesn't exist and the hook exits 0.

The runtime then stands down (prints nothing, exits 0) when the marker belongs to another session, another branch, or the input is malformed. The first hook call after `guard marker start` claims the marker for its session; a new session re-claims it only through `ticket:execute`.

When `uv` is missing or can't get a Python 3.11 or later, the hook exits non-zero, Claude Code treats that as a non-blocking error, and the edit goes through. The boundary checks in `ticket:complete` still catch what the hook missed.

## Hooks

| Event | Matcher | What the runtime does |
|-------|---------|------------------------|
| `PreToolUse` | `Write`, `Edit`, `MultiEdit`, `NotebookEdit`, `Bash` | Claims the marker on first call. On an edit to a frozen RED test: goal mode denies it; attended mode asks and logs `amendment_requested`. In goal mode it also denies edits under `text.ticketsDir`. `Bash` is matched only so the claim happens early; Bash calls are never denied |
| `PostToolUse` | `Write`, `Edit`, `MultiEdit`, `NotebookEdit` | After an approved edit to a frozen RED test runs, logs `amendment_applied`. GREEN accepts a frozen test changed after RED only when such a record covers it, and the summary names the file |
| `Stop` | none | Goal mode only. Re-runs the latest GREEN command (else the RED one) and blocks the stop while it fails or a frozen test changed, naming the command and the log tail. It ignores `stop_hook_active`. After `guard.greenFailLimit` consecutive failures (default 3) it lets the stop through and records `green_failure`, so `ticket:complete` fails the ticket. A final message starting with `BLOCKED:` always passes |
| `SessionStart` | `compact` | Prints the ticket, the mode and the next step, so the session can continue after a compaction drops earlier context. It runs in every session start after a compaction, and costs a file check when no ticket is in progress |

All four hooks ship in the plugin's `hooks/hooks.json` (F11, 2026-11-11). They used to live in this skill's frontmatter, which registered them only once the skill was invoked, so a resumed session had no guard until its next ticket. Plugin hooks run in every session of every plugin user: with no marker each one costs one `git rev-parse` and a file test, about 1.9 ms per hooked call (measured 2026-11-11; a bare `bash -c true` is 0.8 ms).

## Marker fields

| Field | Meaning |
|-------|---------|
| `mode` | `goal` or `attended`, from `guard marker start --mode` |
| `spec`, `ticket`, `branch` | What is in progress, and where |
| `start_sha` | HEAD when the ticket started; everything after it belongs to the ticket |
| `session_id`, `claimed_at` | The claiming session |
| `green_failures` | Consecutive GREEN failures counted by the Stop hook |
| `blocked_at`, `blocked_stop` | Set when a final message started with `BLOCKED:` |

`guard marker status` prints the marker and warns when it is older than `guard.markerWarnHours` (default 24).

## Commands by ticket step

| Step | Command | Notes |
|------|---------|-------|
| Start | `guard marker start <spec> <ticket> --mode goal\|attended` | Refuses a dirty tree, except the spec's `implementation-plan.md`. Resumes the same ticket; refuses another ticket's marker |
| RED | `guard run red [--type test\|stand-in\|refactor] -- <command>` | RED only when the command fails, no non-test file changed since the start SHA, and the failure is not a collection or import error. `stand-in` needs only a failure; `refactor` needs the full suite passing and freezes every test file |
| GREEN | `guard run green -- <command>` | Records command, exit code, HEAD and log digest; refuses when a frozen test changed without an approved amendment |
| Block | `guard block <ticket> "<reason>" [--start <sha>] [--question "<text>"]` | On the marker's ticket: saves the patch and untracked files, restores the start SHA, writes the Blocked row, clears the marker. `--question` also appends a row to the plan's Open questions table (next number, the ticket, the question, `Asked by` the marker's mode or `attended` with no marker), so it lands in the same commit; refuses before changing anything when the plan has no Open questions table. Without a marker (a lost one): the same, from the start SHA of the ticket's last `marker_start` event or `--start`, logging `marker_clear` with `lost: true`. For a dependent with no evidence: writes only the row. Refuses when HEAD moved past the start SHA, and refuses `--start` while another ticket holds the marker |
| Re-run | `guard rerun` | Runs `verify` commands (else the last GREEN) on HEAD plus the uncommitted work in a temporary worktree. `--spec <name>` runs it for a spec-level recheck with no marker and records under `<name>-recheck` |
| RED replay | `guard red-replay` | Copies only the RED test files onto the start SHA and expects them to fail. Refactor tickets skip it |
| Tamper scan | `guard tamper-scan [--reason ID=TEXT ...]` | Flags deleted tests, added skips, changed snapshots, assertion-free tests. Exits 1 until each flag has a reason; goal mode ignores `--reason` |
| Docs affected | `guard docs-affected [--base <sha>] [--json]` | Lists docs under the docs root (`docsRoot`, default `docs`, the specs root excluded) that cite a symbol the diff touches as `` `path::symbol` `` or whose `sources:` globs match a file the diff adds, and the docs a changed doc names in its `related:` frontmatter, one hop. Each is `updated`, `checked` or `pending`. Default base: the ticket's start SHA |
| Docs checked | `guard docs-checked <doc> --reason "<why it still holds>"` | Records that an affected doc needs no change, with the run mode. Allowed in goal mode, because it never stands alone: `spec:review` lists every waiver, and `guard gate` refuses until its docs reviewer rules on each one |
| Docs waivers | `guard docs-waivers <spec> [--base <sha>]` | Writes `docs-waivers.md` in the spec's `review/` folder: the plan's waivers and every doc changed by three words or fewer, each for the docs reviewer to rule `holds` or `wrong` |
| Docs drift | `guard docs-drift [--json]` | Lists each doc whose code changed since its `verified:` commit (a cited symbol, or any file a `sources:` glob matches), in commits that didn't also update the doc, and each doc edited by a commit with no `Intake:` or `Ticket:` trailer |
| Docs check | `guard docs-check` | Exits 1 on a `related:` doc that is missing or doesn't link back, a citation whose file or symbol is gone, and a `verified:` that isn't a commit |
| Summary | `guard summary [--accept-lost-marker]` | Prints the Completion Status notes line, with the docs updated or checked; exits 1 listing missing evidence, including an affected doc still pending. `--accept-lost-marker` is attended only |
| Finish | `guard marker clear` | Called by `ticket:complete` after the commit |
| Owner decisions | `guard decisions export <spec>`, `guard decisions import <spec>` | Not a ticket step: `spec:review` and `spec:complete` call them. `export` overwrites the spec's `review/decisions.jsonl` with every local decision the gate reads for that spec, sorted by time. `import` is attended only and refuses in goal mode: it appends each exported record the local log lacks, tagged `imported_from`, and prints them |

Exit codes: 0 success, 1 refusal, 2 outside a git repo. Hooks always exit 0.

## Evidence record

`ticket-guard/evidence/<ticket>.jsonl` holds one JSON object per event: `marker_start`, `marker_claim`, `red`, `green`, `amendment_requested`, `amendment_applied`, `green_failure`, `blocked`, `marker_clear`, `docs_checked` and the boundary results. Logs of each run sit in `ticket-guard/logs/` with their sha256 in the record. `ticket:complete` copies the summary line into the plan; the record itself stays local and is never committed.

## Troubleshooting

| Symptom | Cause | What to do |
|---------|-------|------------|
| Every edit to a test is denied | The test was frozen by RED in goal mode | Fix the code, not the test. When the test itself is wrong, block the ticket |
| The stop keeps getting blocked | GREEN fails | Fix the failure; after the limit the stop is let through and the ticket fails at `ticket:complete`, so block it instead of looping |
| Hooks do nothing | No marker, another session's marker, or another branch | Run `guard marker status`; resume through `ticket:execute` |
| `guard summary` reports a lost marker | The marker vanished without `marker clear` | Goal mode: `guard block <ticket> "marker lost"`, which saves and restores without the marker. Attended: the owner may accept after the boundary checks pass |
| `uv` not found | uv isn't installed | Install uv; the config wizard checks for it |

## Related

- `test-master` for writing the RED tests the guard records.
- `debugging-wizard` when GREEN keeps failing and the cause isn't obvious.
