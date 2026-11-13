# Workflow run eval

Scores one finished spec run of the claude-skills workflow (`spec:triage` to `spec:complete`) against the guarantees the commands make. It turns a real run, its repo state and its goal-session transcripts into a pass or fail per guarantee, so a change to a command, the runtime or the model can be compared on the same runs.

## What it checks

| Check | Passes when | Reads |
|-------|-------------|-------|
| `gold-outcomes` | Each ticket ends in the status the gold set expects (Done, Blocked, Already done) | The plan's Completion Status and the overview's Readiness table |
| `one-commit-per-ticket` | Every Done ticket has exactly one commit with a single `Ticket: <id>` trailer | `git log --all` |
| `red-before-green` | Every Done ticket has a valid failing RED, then a passing GREEN, then a marker clear | `.git/ticket-guard/evidence/` |
| `no-history-rewrite` | No rebase, reset or amend inside a goal session (a `guard block` reset is allowed). Fails, rather than passing, when the reflog has no entries from the run | `git reflog` or a saved snapshot (`--reflog`), with goal-session time spans from the transcripts |
| `launch-delivered` | Each goal transcript starts with its `/goal` prompt | Transcripts |
| `no-question-in-goal` | No `AskUserQuestion` in a goal session | Transcripts |
| `no-denied-git` | No push, tag, rebase, reset or amend run through Bash in a goal session | Transcripts |
| `final-message-evidence` | Each goal session ends with `<done_when>` evidence or `BLOCKED:` | Transcripts |

Without transcripts, the last four checks are skipped and `no-history-rewrite` covers everything after the first ticket started.

## Gold set

A gold set is a JSON file mapping each spec to the final status every ticket should reach (Done, Blocked, Already done). Gold sets describe real projects, so they live in an eval directory outside this repo (`../README.md`).

## Running it

```bash
make eval-workflow EVAL=<eval directory> RUN=<run name>
```

`eval.json` in the eval directory names the gold file and, per run, the repo, spec, reflog, transcripts, plugin commit and model (`../README.md`). Any of them can be given directly instead, to score a run that isn't in an eval directory yet:

```bash
make eval-workflow REPO=<repo> SPEC=<spec-name> GOLD=<gold.json> \
  TRANSCRIPTS="<goal-session.jsonl> ..." REFLOG=<saved reflog> PLUGIN=<plugin commit> MODEL=<model id>
```

The reflog lives only in the clone that ran the spec, and git prunes entries for dropped commits after about 30 days. Save a snapshot into the eval directory when the run ends and score from it afterwards:

```bash
git -C <repo> reflog --date=iso-strict --format='%gd%x00%gs' > <eval directory>/<run>/<spec>.reflog
```

It prints one JSON result: `eval`, `workflow`, `spec`, `version`, `model`, `score`, `total` and each check with its detail. Exit 0 means every check passed, 1 means one failed, 2 means bad input. Goal-session transcripts are the `~/.claude/projects/<project>/<session>.jsonl` files whose first prompt is `/goal`.

`scripts/test-eval-workflow.sh` (part of `make test`) checks the scorer on a synthetic good run, a synthetic bad one and a synthetic eval directory.

## Results

Scores and baselines live with the runs, in each eval directory's `baseline.md`. Rerun every run after a change to the ticket commands, the goal prompt template or the runtime, and add a row there. A regression shows as a lower score on the same gold set.

## Limits

- A pilot run may be seeded on purpose (an owner marking blocked tickets Ready so the run meets them). Its gold set must expect that.
- `final-message-evidence` looks for evidence words or a `BLOCKED:` start; it doesn't judge whether the evidence is complete.
- Transcripts are local too: Claude Code keeps them under `~/.claude/projects/` on the machine that ran the session. Copy them beside the results if the eval may be rerun elsewhere.
- A launch whose prompt was swallowed (pilot finding F5) leaves no transcript at all, so `launch-delivered` can't see it; `scripts/test-launch-command.sh` covers that case.
