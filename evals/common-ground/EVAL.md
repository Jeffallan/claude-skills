# Common-ground eval

Scores one `common-ground` assumptions check against a fixture with a known current state and outstanding specs that carry seeded false assumptions. It measures whether the check catches each seeded conflict, flags nothing else, and names the spec that rests on each one.

## What it checks

| Check | Passes when | Reads |
|-------|-------------|-------|
| `conflict-recall` | Every gold conflict (a regex on the Assumption and Source cells) is matched by a `conflicts` row of its spec, and every gold `either` entry by a row of its spec that says `conflicts`, or whose verdict starts with `holds` and whose Assumption, Source or Fix cell matches the entry's `caveat` regex | The saved report |
| `no-false-flags` | Every `conflicts` row matches a gold conflict, `either` or `optional` entry of its spec | The saved report |
| `right-spec` | No gold conflict or `either` entry is missed on its spec while a `conflicts` row of another spec matches it: a flag names the spec that rests on it | The saved report |
| `holds-recognized` | Every gold hold (a regex on the Assumption and Source cells) is matched by a `holds` row of its spec, so a true assumption reported `unknown` fails. Passes when the gold set lists no holds | The saved report |
| `unknown-not-guessed` | Every gold unknown (a regex on the Assumption and Source cells) has a row of its spec, and no such row says `conflicts`: an assumption nothing settles is not guessed false. A missing row fails | The saved report |
| `no-spec-edits` | No file the run's commits touched is under `docs/specs/` or is `docs/current-state.json` | `git-files.txt` |
| `ground-file-valid` | `ground.index.json` parses as JSON and its `assumptions` count equals the number of assumption ids (`### A<n>:` headings) in `COMMON-GROUND.md` (`plugin/references/common-ground/file-management.md`) | `ground.index.json`, `COMMON-GROUND.md` |

`unknown-not-guessed` is skipped when the gold set has no `unknowns`; `no-spec-edits` and `ground-file-valid` are skipped when their run file is missing. A skipped check reports `"pass": null, "skipped": true` and counts toward neither `score` nor `total`, so runs saved before these checks keep their scores.

The report is the `| ID | Verdict | Spec | Assumption | Source | Fix |` table `common-ground` prints (`plugin/commands/common-ground.md`, "Spec Assumptions Check"). Save the command's final message as the run's report. When the run prints the table again (after an owner's answer), the last table counts. A Verdict in bold or code (`**conflicts**`) reads the same.

The run folder is the folder that holds the report. Besides the report, the operator's save step writes:

- `git-files.txt`: one path per line, every file the run's commits touched (`git diff --name-only <start>..HEAD`)
- `ground.index.json` and `COMMON-GROUND.md`: the ground files as the run left them

## Gold set

A JSON file, kept with the fixture in a private eval directory (`../README.md`):

```json
{"conflicts": [{"spec": "<spec>", "match": "<regex on the assumption or its source>"}],
 "holds": [{"spec": "<spec>", "match": "<regex>"}],
 "unknowns": [{"spec": "<spec>", "match": "<regex>"}],
 "either": [{"spec": "<spec>", "match": "<regex>", "caveat": "<regex>"}],
 "optional": [{"spec": "<spec>", "match": "<regex>"}]}
```

`either` is for an assumption a careful run may report either way: as a conflict, or as holding with a caveat that names what is missing. `holds-recognized` does not require an `either` entry.

`optional` is for a conflict that is true but not required: a `conflicts` row matching it is no false flag, and `conflict-recall` never requires it.

Every gold entry (conflicts, holds, unknowns, either, optional) matches only report rows whose Spec is the entry's spec, so a row whose text happens to match another spec's regex is no match for it. A `conflicts` row that matches no entry of its own spec is a false flag; it also fails `right-spec` when it matches a gold conflict the run missed on that conflict's spec.

The fixture's `docs/current-state.json` must be compiled by `spec:current` (`guard current-state`) before the run, so the check grounds itself on the state the gold set assumes.

## Running it

```bash
make eval-common-ground EVAL=<eval directory> RUN=<run name>
make eval-common-ground REPORT=<report.md> GOLD=<gold.json>
```

`eval.json` names the gold file and, per run, the `report`. It prints one JSON result with `score`, `total` and each check. Exit 0 means every check that ran passed, 1 means one failed, 2 means bad input.

`scripts/test-eval-loop.sh` (part of `make test`) checks the scorer on a matching report, on one with a missed conflict, a false flag and a wrong spec, and on a report printed twice whose last table holds a gold hold as `unknown`. For an `either` entry it checks that a `conflicts` row and a `holds` row naming the caveat pass, and that a `holds` row without it, an `unknown` row, a missing row and a row on another spec fail. It checks that a flag whose text matches another spec's gold regex is a false flag on its own spec and not a wrong spec, that a gold conflict flagged only on another spec fails `right-spec`, that a gold hold needs a row of its own spec, and that an `optional` entry clears a matching flag of its spec without being required. It also checks that each run-folder and unknowns check passes, fails, and is skipped when its gold key or file is absent.

Under an active goal, `common-ground` must end with `BLOCKED: common-ground needs the owner`, write nothing and ask nothing. Score such a run with `make eval-goal-guard DIR=<run folder> COMMAND=common-ground` (`../discovery/EVAL.md`, "Goal guard").
