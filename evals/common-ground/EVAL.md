# Common-ground eval

Scores one `common-ground` assumptions check against a fixture with a known current state and outstanding specs that carry seeded false assumptions. It measures whether the check catches each seeded conflict, flags nothing else, and names the spec that rests on each one.

## What it checks

| Check | Passes when | Reads |
|-------|-------------|-------|
| `conflict-recall` | Every gold conflict (a regex on the Assumption and Source cells) is matched by a `conflicts` row | The saved report |
| `no-false-flags` | Every `conflicts` row matches a gold conflict | The saved report |
| `right-spec` | Every row that matches a gold conflict names the gold spec | The saved report |

The report is the `| ID | Verdict | Spec | Assumption | Source | Fix |` table `common-ground` prints (`plugin/commands/common-ground.md`, "Spec Assumptions Check"). Save the command's final message as the run's report.

## Gold set

A JSON file, kept with the fixture in a private eval directory (`../README.md`):

```json
{"conflicts": [{"spec": "<spec>", "match": "<regex on the assumption or its source>"}]}
```

The fixture's `docs/current-state.json` must be compiled by `spec:current` (`guard current-state`) before the run, so the check grounds itself on the state the gold set assumes.

## Running it

```bash
make eval-common-ground EVAL=<eval directory> RUN=<run name>
make eval-common-ground REPORT=<report.md> GOLD=<gold.json>
```

`eval.json` names the gold file and, per run, the `report`. It prints one JSON result with `score`, `total` and each check. Exit 0 means every check passed, 1 means one failed, 2 means bad input.

`scripts/test-eval-loop.sh` (part of `make test`) checks the scorer on a matching report and on one with a missed conflict, a false flag and a wrong spec.
