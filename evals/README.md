# Evals

Each eval scores finished runs of a claude-skills workflow against the guarantees its commands make, so a change to a command, the runtime or the model can be compared on the same runs.

| Eval | What it scores | Scorer |
|------|----------------|--------|
| [Workflow](workflow/EVAL.md) | One spec run, `spec:triage` to `spec:complete` | `scripts/eval_workflow_run.py` |
| [Intake](intake/EVAL.md) | One intake run of the checklist, and its accuracy against a gold set | `scripts/eval_intake_run.py`, `eval_intake_accuracy.py`, `eval_intake_baseline.py` |

This repo holds the scorers, their tests and the check definitions. It never holds eval data: gold sets, run bundles, transcripts and scores describe real projects and stay in a private results repo.

## Eval directories

Every scorer reads its inputs from an eval directory you point it at: one folder per eval and project, laid out as `<results repo>/<eval>/<project>/`.

```
<eval>/<project>/
├── eval.json        # the project, the gold file and every run
├── gold.md          # intake: expected findings and doc verdicts (gold.json for the workflow eval)
├── baseline.md      # the score table and history, re-scored whenever the checks or the gold set change
└── <run>/           # one folder per run: bundle, reflog, transcripts, accuracy mapping, test output
```

`eval.json` names everything else, with paths relative to the directory (absolute and `~` paths also work):

```json
{
  "eval": "intake",
  "project": "<name>",
  "gold": "gold.md",
  "test_cmd": "<test:all command>",
  "test_paths": ["<glob>"],
  "runs": [
    {
      "run": "run 1",
      "repo": "<live clone, while it exists>",
      "bundle": "run1/repo.bundle",
      "branch": "<intake branch>",
      "start": "<start sha>",
      "plugin": "<plugin commit>",
      "model": "<model id>",
      "reflog": "run1/intake.reflog",
      "transcripts": ["run1/<session>.jsonl"],
      "suite_green": true,
      "accuracy": "run1/accuracy-mapping-gold-v1.json"
    }
  ]
}
```

| Key | Eval | Meaning |
|-----|------|---------|
| `gold` | both | The gold file |
| `test_cmd`, `test_paths` | intake | The project's characterization suite and its test globs; a run may override either |
| `run` | both | The name `RUN=` selects |
| `repo` | both | The clone to score, only while it still sits at the run's end; drop it once the clone moves on (a Phase 4 branch), and the run scores from `bundle` and `branch`, as the baseline always does |
| `spec` | workflow | The spec the run executed |
| `start` | intake | The commit that added the goal prompt and checklist |
| `plugin`, `model` | both | Recorded in the result |
| `reflog`, `transcripts` | both | Saved when the run ended, since git prunes the reflog and transcripts stay on the machine that ran them |
| `suite_green` | intake | Take the suite result from the run's saved test output (its services are gone) |
| `accuracy` | intake | The run's mapping onto the gold set |

## Running

```bash
make eval-intake EVAL=<eval directory> RUN=<run name>
make eval-baseline EVAL=<eval directory>
make eval-workflow EVAL=<eval directory> RUN=<run name>
```

A flag given on the command line (`REPO=`, `START=`, `TRANSCRIPTS=` and the rest) overrides the value in `eval.json`.

## What stays local

Some files stay on your machine even when the results repo is private. List them in its `.gitignore`: details of security findings the project hasn't fixed, raw transcripts (push redacted copies instead), and repo bundles. Before each push, check the files for tokens and environment dumps, since a goal run's shell commands can capture them.
