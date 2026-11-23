# spec:current and spec:diff eval

Scores one `spec:current` run, then the `spec:diff` run that follows it in the same clone, on a fixture whose system description, findings tracker and outstanding specs are known. `spec:current` folds completed specs into `docs/system-description.md` and compiles `docs/current-state.json`; it is scored on the repo after it. `spec:diff` prints a read-only plan; it is scored on its saved report and on the tree staying the same around it. `common-ground` checks the assumptions `spec:diff` lists against that state, and has its own eval (`../common-ground/EVAL.md`).

## What it checks

| Check | Passes when | Reads |
|-------|-------------|-------|
| `current-commits` | Each gold commit has a commit after the start whose subject matches, which carries the gold trailer line when one is given, and which touches only the gold files | `git log <start>..HEAD` |
| `description-folded` | The Change history has a row for the gold spec, and neither the `Last updated` SHA nor the `verified:` frontmatter is the old one | `docs/system-description.md` |
| `state-fresh` | The state matches the schema `guard current-state` writes (the runtime's own validator), and its `built_at.system_description` is not the old SHA and is the description's `Last updated` SHA | `docs/current-state.json` |
| `components` | The component count is in range; every `required` entry (a regex on name and does) matches a row, and every row it matches has an allowed status; every other `planned` row matches `planned_allowed`; every other row has the `others` status; no row a `forbidden` entry matches says what its `does_not` regex matches | `components` |
| `findings` | The finding ids are exactly the gold set | `findings` |
| `drift` | The drifted docs are exactly the gold set, and no `absent` doc is among them | `drift` |
| `diff-coverage` | The report has a `### <spec>` section for every gold spec and carries the gold banner | The saved `spec:diff` report |
| `diff-assumptions` | Every gold assumption matches a row of the Assumptions table with that Spec, its regex on the Assumption and Quoted from cells, its kind on Kind and its place on Checked against. Recall only: extra rows aren't scored | The saved report |
| `diff-overlaps` | Every gold overlap matches a row of the Overlaps table that names both specs | The saved report |
| `diff-changes` | Each spec's change table matches every gold `changes` regex and no `not_changed` regex | The saved report |
| `diff-read-only` | HEAD and `git status --short`, saved before and after `spec:diff`, are the same | The two saved files |

The assumption table is the `| ID | Spec | Kind | Assumption | Quoted from | Checked against |` table of `plugin/references/specs/assumptions.md`; when the report holds it twice, the last one counts. Each part scores only when its inputs are given (the repo, the report, the two saved files), so the total is out of the checks that ran. Row matching is case-insensitive; statuses compare exactly, as `guard current-state` writes them.

## Gold set

A JSON file, kept with the fixture in a private eval directory (`../README.md`):

```json
{
  "fixture_start": "<sha the run starts from>",
  "spec_current": {
    "commits": {
      "description": {"subject": "<regex>", "trailer": "<exact trailer line>", "files_only": ["docs/system-description.md"]},
      "state": {"subject": "<regex>", "files_only": ["docs/current-state.json"]}
    },
    "description": {"change_history_row": {"spec": "<spec>"}, "last_updated_not": "<sha>", "verified_not": "<sha>"},
    "current_state": {
      "built_at_system_description_not": "<sha>",
      "components": {
        "count": [2, 9],
        "required": [{"match": "<regex on name and does>", "status": ["wired"]}],
        "planned_allowed": "<regex a planned row must match>",
        "others": "wired",
        "forbidden": [{"match": "<regex on name and does>", "does_not": "<regex>"}]
      },
      "findings": {"ids": ["F-001"]},
      "drift": {"docs": ["docs/<doc>.md"], "absent": ["docs/<doc>.md"]}
    }
  },
  "spec_diff": {
    "specs": ["<spec>"],
    "banner": "<text the report must carry>",
    "writes_nothing": true,
    "assumptions": [{"spec": "<spec>", "match": "<regex>", "kind": "<regex>", "checked_against": "<regex>"}],
    "overlaps": [{"specs": ["<spec>", "<spec>"], "match": "<regex on the row>"}],
    "changes": {"<spec>": ["<regex>"]},
    "not_changed": {"<spec>": ["<regex>"]}
  }
}
```

## Running it

```bash
make eval-spec-current-diff EVAL=<eval directory> RUN=<run name>
make eval-spec-current-diff GOLD=<gold.json> REPO=<clone> START=<sha> DIFF_REPORT=<report.md> \
  DIFF_BEFORE=<before.txt> DIFF_AFTER=<after.txt>
```

`eval.json` names the gold file and `fixture_start`, and per run the `repo`, `diff_report`, `diff_before` and `diff_after`. Save the two tree snapshots around `spec:diff` with `git rev-parse HEAD; git status --short`. It prints one JSON result with `score`, `total` and each check. Exit 0 means every check passed, 1 means one failed, 2 means bad input (an unknown start SHA included).

`scripts/test-eval-loop.sh` (part of `make test`) checks the scorer on a synthetic run that matches its gold set and fails each check once.

## Limits

- `spec:current` is attended: the owner approves the proposed description changes, so a scored run scripts the answers, and the gold set must match them.
- The description's prose isn't judged; the compiled state stands in for section 2.
- The diagrams in the `spec:diff` report aren't scored.
