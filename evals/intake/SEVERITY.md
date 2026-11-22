# Severity scoring

Read this when you compare an intake run's severities with a gold set. It covers the inputs, the scale, miss classes, metrics and gates. How to rate a finding is in the plugin's `references/intake/findings.md`, "Severity". Every example here is synthetic; no gold row or real project appears in this file, and none should be added.

## Inputs

- The gold file. Its Findings table has a `Severity` column (and `Area` and `Source`, as for accuracy).
- The run's accuracy mapping (`EVAL.md`, "Gold set and accuracy"). Each gold row it matches to a run finding is scored; null rows, given rows and rows the run was the source of are left out, as the accuracy tally leaves them out. A docs-only `(d)` match has no rating, so it is listed apart and not scored.
- The run's `docs/intake-findings.md` at the scored commit. Each finding section's `- **Severity:**` line gives the run's level.

## Running it

```bash
python3 scripts/eval_intake_severity.py <gold.md> <mapping.json> <intake-findings.md> --plugin <sha>
python3 scripts/eval_intake_severity.py --pool <eval directory> [<eval directory> ...]
```

One run prints its summary table, each miss and the unmatched findings. `--pool` scores every run in each directory's `eval.json` that has an `accuracy` mapping, reading the tracker from the run's `bundle` at `scored_at`, then prints the pooled metrics with the calibration gates. `--json` prints the same as JSON. Gates are advisory: the exit code is 0 unless `--gate` is given and a gate fails (1). Bad input exits 2.

## Levels

Critical scores 4, High 3, Medium 2, Low 1. Runs from before the plugin's scale gained Critical could not use it. For a run whose scale has no Critical, a run High against a gold Critical is a scale match: exact in the normalized score, one under in the raw score, and listed with the class `scale`. Both exact scores are reported; every other metric uses the normalized score.

Whether a run's scale had Critical comes from, in order:

1. `--critical` or `--no-critical` on the command line, or `"critical": true` or `false` on the run's entry in `eval.json`.
2. The run's `plugin` commit: Critical existed when that commit's `references/intake/findings.md` names it. A suffix such as `3671e13-noskills` is dropped. `--plugin-repo` points at another claude-skills clone.
3. Otherwise the run is assumed to predate Critical, and the report says so.

## Gold cell markers

The `Severity` cell holds one level, with two optional markers:

| Cell | Meaning |
|------|---------|
| `High (floor)` | Gold is High because of sensitive data of other accounts or a role gain. A run rated lower is a floor miss |
| `Medium or Low (contested)` | Reviewers still split after discussion. The run is exact when it picks either level, and the row stays out of the floor gate |

## Each matched finding

The scorer records the run level, the gold level, the signed error (run minus gold, normalized) and whether the run's `Severity:` line names a rubric row and an adjustment, as in `Medium (orders). Row: High, keeps access after removal; one lower, staff only`. Each raw miss gets one class:

| Class | When |
|-------|------|
| `scale` | Exact only on the normalized score (see Levels) |
| `contested` | The gold row is contested and the run picked neither level |
| `floor` | The gold row is a floor and the run is lower |
| `unexplained` | The `Severity:` line names no rubric row |
| `misapplied` | The line names a row, and the level still differs from gold. Whether the named row fits the gold facts is the reviewer's call |

Run findings with no gold match are counted by level, so over-rating outside gold stays visible. They are not scored for agreement.

## Metrics

| Metric | Meaning |
|--------|---------|
| Exact, raw and normalized | Share of matched findings at the gold level |
| Within one | Share at most one level off |
| Mean signed error | Run minus gold; negative means under-rating |
| Over-rated, under-rated | Counts by direction |
| Misses of two or more | Count |
| Floor and unexplained misses | Counts by class |
| Severity lines naming a row | Lines with `Row: <level>, <row>; <adjustment>` out of matched findings |
| Linear- and quadratic-weighted kappa | Cohen's kappa on the fixed four-level scale |
| Gwet's AC2, linear | Agreement that holds up when one level dominates, where kappa drops toward zero |
| Recall per level | Per gold level, the share the run rated exactly |
| Confusion matrix | Gold level by run level, raw, in the JSON output |

A single run has too few findings for kappa or AC2 to mean much; they are printed but not gated. Pool runs and projects for those.

## Gates

Starting values, to tune after three runs on the new rubric.

| Gate | Per run | Pooled |
|------|---------|--------|
| Floor misses | 0 | 0 |
| Misses of two or more | 0 | at most 2% |
| Exact, normalized | at least 80% | at least 70% |
| Within one | 100% | at least 95% |
| Mean signed error | within 0.2 of zero | within 0.15 of zero |
| Over-rated, under-rated | not gated | each at most 15% |
| Linear-weighted kappa | not gated | at least 0.70 |
| Gwet's AC2, linear | not gated | at least 0.70 |
| Recall per level | not gated | at least 0.60 for each level |
| Unexplained misses | report-only | report-only |
| Severity lines naming a row | report-only | report-only |

The last two stay report-only until runs use the rubric's `Row:` line; runs from before it name no row, so every non-scale miss is unexplained.

## Not scored yet

- Re-rates: whether a later item that shows more or less reach changed the finding's `Severity:` line in its own commit. Check those by hand from the tracker history.
- A bootstrap interval on kappa, and the comparison with the human-human kappa of the gold version. Both need a pooled calibration set.

## Report

Write no security detail and no gold text when you record results: ids, levels, area and class only, as the scorer prints them.
