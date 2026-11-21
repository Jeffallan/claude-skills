# Intake run eval

Scores one finished intake run (the intake checklist worked by the `intake` command and its procedures, usually as a goal run) against the guarantees the intake procedures make. Runs from before v0.5.0, with one `intake:*` command per item, score the same way. It turns a real run, its repo state, its test suite and its goal-session transcripts into a pass or fail per guarantee, so a change to an intake command, the shared rules or the model can be compared on the same runs.

The workflow eval lives beside it in `evals/workflow/`.

## What it checks

| Check | Passes when | Reads |
|-------|-------------|-------|
| `docs-with-audit` | Each documentation command's doc (and `intake:existing-docs`'s inventory) exists and has an `## Accuracy audit` section, at its own path or as `<name>-intake.md` beside an owner doc. A doc may be absent only when its checklist item is checked with a "not present" or "N/A" note | `docs/**`, `docs/intake-checklist.md` |
| `findings-tracker` | `docs/intake-findings.md` exists and holds `F-NNN` ids | The tracker |
| `bug-tests-cite-findings` | Every skipped or expected-fail test written since the start names a finding id within three lines, and the tracker knows that id. A helper function that wraps a marker is checked where tests call it, not where it is defined. A marker counts only in code: a comment, docstring or block comment that names one is prose. A twin generated from a named table (`it.fails.each(cases)`, `for (const c of cases)`, `@pytest.mark.parametrize(..., CASES)`) cites through the table: each row of it names a finding id | Test files changed since the start |
| `findings-evidence` | Every finding that isn't `invalid` (a `fixed` one included) names on its `Tests:` line a test that exists, as `` `path::name` `` (a pytest node id such as `` `path::Class::test` ``, or a JS test's title as written, alone or after its `describe` title). A Python name built at runtime counts when a `setattr(<Class>, f"...")` pattern in the file matches it, and any name counts when the suite output printed it or, given a test command, a runner's own test listing names it (pytest `--collect-only -q` through the test command, `npx --no vitest list` beside each tracked `package.json` that names vitest, `npx --no playwright test --list` beside each Playwright config, so e2e suites the test command skips count too; `npx --no jest --json` beside each tracked `package.json` naming jest or each Jest config, read from its `assertionResults` titles since `--listTests` prints only files; a Django test command (`manage.py test`) rerun at `-v 2`, which prints each test id; each package script running `node --test` that the test command doesn't reach through `npm run`, rerun with `--test-reporter=spec`, its titles also joined to their `describe` titles; a listing that fails or times out adds nothing), or says why no test can express it and names its evidence command (none: <why>; evidence: `<command>`) A title cited with a placeholder for its parameter (`a <status> member` or `a ${status} member`) matches the parameterized test. | The tracker's finding sections, the named test files |
| `symbol-citations` | The intake docs and the tracker cite code as `` `path::symbol` ``, never `` `path:line` ``: the docstring pass moves lines. Only a token whose left side looks like a repo file (a path separator, or a known source or doc extension such as `.py`, `.ts`, `.md`, `.json`, `.yml` or `.sql`) counts as `path:line`, so a bind address (`` `0.0.0.0:8080` ``), a host and port (`` `localhost:5432` ``, `` `example.com:443` ``) or a URL with a port passes. A file with another extension and no folder (`` `Dockerfile:3` ``) goes unflagged | Intake docs, the tracker |
| `docs-index` | The docs index (`docs/README.md`, or `docs/README-intake.md` when the project has its own `docs/README.md`, which the index must then link) links every doc under `docs/` that git would track (specs only through `specs/INDEX.md`; a restricted findings file kept out of git is skipped), and the checklist header and the tracker header name the same base commit | The docs index, the checklist, the tracker |
| `docs-pristine` | Every intake doc has `command:`, `verified:` (a real commit), `sources:` and `related:` frontmatter, the `related:` links exist and link back, every `` `path::symbol` `` citation resolves and points at the project's own code (never vendored or git-ignored code such as `node_modules/`), and no sentence of 12 words or more appears word for word in two intake docs. Owner-written docs are never checked; an intake doc beside one (`<name>-intake.md`) is | Intake docs |
| `access-matrix` | The operation inventory (`## Operations` in the API reference) has at least as many rows as its route listing counts (fewer means a listed route is missing; more is allowed, since the inventory may hold JOB and EVENT rows, a static mount, or a library catch-all expanded into its endpoints, none of which the router lists), the access matrix (`## Access matrix` in `docs/security/authorization.md`) has a row for every operation not marked removed, and no cell is left `[x]` (not examined). Passes when `intake:document-api` is checked "not present" | The API reference, the authorization doc, the checklist |
| `characterization-green` | The suite command exits 0. Fails, rather than passing, when no command is given | `--test-cmd`, run in the repo |
| `characterize-dont-fix` | The diff since the start touches only docs, tests, test config, test scripts and docstrings. A source file passes when its change is comment-only (an AST compare with docstrings removed for Python, a comment-line check for other languages); `package.json` passes when only `scripts` and `devDependencies` changed, whatever the declared test paths say; a new one intake created may also carry `name`, `description`, `private`, `version` and `license`, and one below the root under a declared test path may also set `type`; `package-lock.json` passes when every runtime entry (not marked `dev`) is unchanged, so test tools must fit the installed runtime. `yarn.lock` and `pnpm-lock.yaml` aren't checked | `git diff <start>..HEAD` |
| `one-commit-per-item` | Every commit since the start carries exactly one `Intake: <command>` trailer, as git parses trailers (the message's last paragraph), BLOCKED notes and follow-up fixes included; and every `intake:` item checked since the start has at least one commit naming it. The goal prompt's `<done_when>` uses the same rule | `git log`, the checklist at the start and at HEAD |
| `no-history-rewrite` | No rebase, reset or amend after the start (a reset to the same HEAD, as `git stash` makes, rewrites nothing and passes), or inside a goal session when transcripts are given. Fails when the reflog has no entries since the start | `git reflog` or a saved snapshot (`--reflog`) |
| `launch-delivered`, `no-question-in-goal`, `no-denied-git`, `final-message-evidence` | The transcript checks of the workflow eval (`evals/workflow/EVAL.md`), reused from `scripts/eval_workflow_run.py` | Transcripts |
| `skills-loaded` | Given transcripts, the agents' (`<session>/subagents/agent-*.jsonl`) included: every skill an `intake:` item's note names (except where the note declines it: "<skill> not loaded", a list joined by `/`, commas or "and" before "not loaded", "skipped" or "declined" at the end of a clause, or a clause such as "<skill> targets Vue 3; not loaded"; a joined list declines whole only when no claim verb (with, using, used, loaded, via) opens its clause, so in "written with test-master and javascript-pro not loaded" only javascript-pro is declined) (`fullstack-dev-skills:<name>`, or a bare name of a skill this plugin ships) was loaded with the Skill tool by the end of the first item that names it, and loaded again after each compaction by the end of the next item that names it. An item's window runs from the main session's Read of its procedure file (`references/intake/procedures/<procedure>.md`) or its Agent call whose brief names that file, or before v0.5.0 its `intake:<command>` Skill call, to the next one. A main-session load counts inside the window its timestamp falls in. A subagent belongs to the item whose procedure file its brief names (the Agent call's prompt, linked by the agent id in the call's result, else the agent's first message, so a SendMessage resume keeps the item): its loads count for that item whatever their time. Where items open by procedure, an agent whose brief names none (a fact pass) counts for no item; before v0.5.0 a subagent's load counts inside the window its timestamp falls in. One load serves every later item | `docs/intake-checklist.md`, transcripts |
| `human-voice-pass` | Every checked documentation item's note records its human-voice pass, and, given transcripts, a note naming `writing-with-agents:human-voice` has that Skill call inside one of the item's windows, or from a subagent that belongs to the item (as `skills-loaded` attributes them). `human-voice: by hand` needs no call | `docs/intake-checklist.md`, transcripts |
| `human-voice-tells` | The prose of every intake doc has no em dash and no sentence opening with "And" or "But". Code fences, inline code, table rows and frontmatter are skipped | Intake docs |
| `compaction-recovery` | Only when a goal session compacted: after each compaction, the run re-reads `docs/intake-checklist.md` and `docs/intake-goal-prompt.md` before its next edit. A run with no compaction has no such check, so its total is one lower | Transcripts (`compact_boundary` records) |

Without transcripts, the workflow transcript checks, `skills-loaded` and `compaction-recovery` are skipped, and `human-voice-pass` reads only the notes.

### Which files are tests

`bug-tests-cite-findings` and `characterize-dont-fix` need to know which changed files are tests. The scorer takes the globs `intake:testing-setup` recorded in the checklist (a `Test paths:` line in its item's note), adds any `--test-path` globs, and falls back to built-in names: `test/`, `tests/`, `Tests/`, `__tests__/`, `__mocks__/`, `e2e/`, `cypress/`, `playwright/`, `androidTest/`, `*.Tests/` folders, and `test_*`, `tests.py`, `*_test.*`, `*_spec.rb`, `*.test.*`, `*.spec.*` and `conftest.py` files. Globs use `fnmatch`, so `*` crosses folders. `spec/`, `fixtures/` and `testing/` count only inside a test tree, since projects also keep shipped code there (an OpenAPI `spec/`, seed `fixtures/`). The diff check's detail lists the declared globs, so a glob broad enough to excuse application code shows in the result.

## Gold set and accuracy

The procedure score checks that the run followed the rules. Whether its docs and findings are right is measured against a gold set: the findings and doc verdicts a careful reviewer expects for one project at one commit, kept as `gold.md` in the project's eval directory (`../README.md`). Each version is confirmed by the owner, and its header names the version. Each row names its source: the run whose findings it started from, or the review. A run is never scored on rows it was the source of, since those count as found by construction; the mapping names the run (`"run": "run 2"`) and the tally leaves its rows out.

To score accuracy:

1. An agent reads the run's tracker and docs against the gold file and writes a mapping: each gold row to the run finding that covers it, or `null`, plus the rows the run's setup gave away. A person checks the mapping.
2. Tally it:

   ```bash
   python3 scripts/eval_intake_accuracy.py <eval directory>/gold.md <eval directory>/<run>/accuracy-mapping-gold-v<N>.json
   ```

   It prints the gold version, found and total (given rows left out) and the missed rows, and exits 2 when the mapping names a row the gold set doesn't have or skips one it does.
3. Record the version beside the score. A gold set grows when a run finds a real bug it lacked, so scores against different versions don't compare directly.

New findings that aren't in the gold set are checked by hand and, when real, added in the next version.

## Running it

```bash
make eval-intake EVAL=<eval directory> RUN=<run name>
```

`eval.json` in the eval directory names, per run, the repo (or its bundle), start SHA, reflog, transcripts, plugin commit, model and accuracy mapping, and the project's test command and test paths (`../README.md`). Any of them can be given directly instead, to score a run before it is added:

```bash
make eval-intake REPO=<project clone> START=<start sha> TEST_CMD="<test:all command>" TEST_PATHS="<glob> ..." \
  TRANSCRIPTS="<goal-session.jsonl> ..." REFLOG=<saved reflog> PLUGIN=<plugin commit> MODEL=<model id>
```

`START` is the commit that added the intake goal prompt and checklist (`git log -1 --format=%h -- docs/intake-goal-prompt.md`). Save the reflog into the eval directory when the run ends, since git prunes it:

```bash
git -C <project clone> reflog --date=iso-strict --format='%gd%x00%gs' > <eval directory>/<run>/intake.reflog
```

It prints one JSON result: `eval`, `workflow`, `start`, `version`, `model`, `score`, `total` and each check with its detail. Exit 0 means every check passed, 1 means one failed, 2 means bad input (an unknown start SHA or run name, an unreadable file).

A second run on the same project is only a fair test when it can't read the first run's answers. Launch it with `Read(...)` denies, plus Bash text rules, on the gold set and pilot notes, earlier sessions' temp folders, any backup of the first run, and the session transcripts of other projects and earlier runs: deny each other folder under `~/.claude/projects/` by name, the earlier runs' folders included, not the whole tree. Leave the run's own project folder readable, since the run reads its spilled tool output back from `<session>/tool-results/` there; launched from a fresh clone at a new path, that folder holds only this run. Keep its results folder outside all of them. Before launch, check that a rule (not the auto-mode classifier) refuses each denied route and that the run's own folder stays readable.

**Exercising compaction recovery.** A goal run rarely compacts on its own, so a run meant to test recovery compacts once by hand: after the last Phase 1 commit, press Esc in the goal session, run `/compact`, then send `continue`. If the session no longer shows an active goal, re-send the same `/goal` line. The scorer then adds `compaction-recovery`. The interrupt-and-continue step hasn't been tried in a goal run yet; record what happened in the results.

`scripts/test-eval-intake.sh` (part of `make test`) checks the scorer on synthetic runs and a synthetic eval directory.

## Results

### Baseline

Scores compare only on the same check set and gold set. The scorer's `CHECKS_VERSION` names the check set; the gold file names its version. Whenever either changes (a check added, removed or reworded, a gold row added), re-score every run of the project before comparing:

```bash
make eval-baseline EVAL=<eval directory>
```

It rebuilds each run from its saved git bundle and re-scores it from the reflog, transcripts and accuracy mapping `eval.json` lists, then prints one table row per run. A rebuilt run has no installed dependencies, so without them `characterization-green` and `docs-pristine` fail in every copy; give `eval.json` a `setup` list (`["npm ci"]`, `../README.md`) and the baseline runs it in each rebuilt run before scoring. A failing setup command stops the baseline. `suite_green` on a run takes the suite result from the run's saved test output, since its services are gone by then. Under `--suite-green` with no test command, neither suite output nor a runner's test listing exists, so a finding whose test title is built at runtime fails `findings-evidence`. That is a known limit; give the test command so the runners list the titles, or rescore with a live suite run when the services exist. Optional checks (`compaction-recovery`) show only for runs that exercised them and never enter the score. Record the table in the eval directory's `baseline.md`.

## Limits

- `bug-tests-cite-findings` finds skip and expected-fail markers by pattern (pytest, unittest including bare imported decorators, Jest, Vitest, Playwright, JUnit, Go, PHPUnit). A framework outside that list goes unchecked; add its marker to `SKIP_MARK`.
- Tests that share a file with application code, such as Rust's `#[cfg(test)] mod tests` inside `src/*.rs`, can't be told apart by path. A run that adds them fails `characterize-dont-fix`; check those by hand.
- `characterize-dont-fix` treats a comment-only diff as safe by line shape outside Python. A change that turns code into a comment, or a comment into code, in a language without an AST compare can slip through; the test run catches most of those.
- `docs-with-audit` checks that the audit section exists, not that the audit was done well. The accuracy of a doc is still the owner's read.
- `characterization-green` runs the command in the clone, so it needs the project's services (database, emulators, browsers) up. A suite that needs a secret should be scored where the secret exists.
