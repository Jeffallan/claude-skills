# Evals

Each eval scores finished runs of a claude-skills workflow against the guarantees its commands make, so a change to a command, the runtime or the model can be compared on the same runs.

| Eval | What it scores | Scorer |
|------|----------------|--------|
| [Workflow](workflow/EVAL.md) | One spec run, `spec:triage` to `spec:complete` | `scripts/eval_workflow_run.py` |
| [Intake](intake/EVAL.md) | One intake run of the checklist, its accuracy against a gold set, and its [severity agreement](intake/SEVERITY.md) | `scripts/eval_intake_run.py`, `eval_intake_accuracy.py`, `eval_intake_baseline.py`, `eval_intake_severity.py` |
| [Discovery](discovery/EVAL.md) | One discovery topic, `discovery:create` to `discovery:approve`: routing, blocking decisions and created tickets | `scripts/eval_discovery_run.py` |
| [Common-ground](common-ground/EVAL.md) | One `common-ground` assumptions check: seeded false assumptions caught, no false flags, the right spec named, true ones held | `scripts/eval_common_ground_run.py` |
| [spec:current and spec:diff](spec-current-diff/EVAL.md) | One `spec:current` run (its commits, the folded description, `docs/current-state.json`) and the `spec:diff` after it (assumptions, overlaps, changes, read-only) | `scripts/eval_spec_current_diff_run.py` |
| [spec:complete docs](spec-complete-docs/EVAL.md) | One `spec:complete` run's docs duties: the system description sections and Change history row, and docs:verify's stale-claim flags | `scripts/eval_spec_complete_docs_run.py` |

## Coverage

Every command the plugin ships (`plugin/commands/workflow-manifest.yaml`) and what checks it. `scripts/test-eval-loop.sh` fails when a manifest command has no row here. A smoke test checks the command's text or the runtime it calls without running an agent; an eval scores a real run.

| Command | Eval | Scorer | Smoke test | Docs page |
|---------|------|--------|------------|-----------|
| `intake` | [Intake](intake/EVAL.md) | `eval_intake_run.py`, `eval_intake_accuracy.py`, `eval_intake_baseline.py` | `test-command-rules.sh`, `test-eval-intake.sh` | [intake-phase](../docs/workflow/intake-phase.md) |
| `discovery:create` | [Discovery](discovery/EVAL.md) (routing, decisions) | `eval_discovery_run.py` | `test-command-rules.sh` | [discovery-create](../docs/workflow/discovery-create.md) |
| `discovery:approve` | [Discovery](discovery/EVAL.md) (created tickets) | `eval_discovery_run.py` | `test-command-rules.sh` | [discovery-approve](../docs/workflow/discovery-approve.md) |
| `spec:triage` | **gap**: only through the [Workflow](workflow/EVAL.md) run it starts | **gap** | `test-command-rules.sh` | [spec-triage](../docs/workflow/spec-triage.md) |
| `spec:create` | **gap**: only through the [Workflow](workflow/EVAL.md) run its plan drives | **gap** | `test-command-rules.sh`, `test-launch-command.sh` | [spec-create](../docs/workflow/spec-create.md) |
| `spec:review` | [Workflow](workflow/EVAL.md) (`fix-tickets`) | `eval_workflow_run.py` | `test-command-rules.sh`, `test-review-wiring.sh` | [spec-review](../docs/workflow/spec-review.md) |
| `spec:complete` | [spec:complete docs](spec-complete-docs/EVAL.md); [Workflow](workflow/EVAL.md) (ticket outcomes) | `eval_spec_complete_docs_run.py`, `eval_workflow_run.py` | `test-command-rules.sh` | [spec-complete](../docs/workflow/spec-complete.md) |
| `spec:status` | **gap** | **gap** | `test-command-rules.sh`, `runtime/tests/test_guard_spec_status.py` | [spec-status](../docs/workflow/spec-status.md) |
| `spec:current` | [spec:current and spec:diff](spec-current-diff/EVAL.md) | `eval_spec_current_diff_run.py` | `runtime/tests/test_guard_current_state.py` | [spec-current](../docs/workflow/spec-current.md) |
| `spec:diff` | [spec:current and spec:diff](spec-current-diff/EVAL.md) | `eval_spec_current_diff_run.py` | `test-command-rules.sh` | [spec-diff](../docs/workflow/spec-diff.md) |
| `ticket:execute` | [Workflow](workflow/EVAL.md) (`one-commit-per-ticket`, `red-before-green`) | `eval_workflow_run.py` | `test-command-rules.sh` | [ticket-execute](../docs/workflow/ticket-execute.md) |
| `ticket:complete` | [Workflow](workflow/EVAL.md) (`gold-outcomes`) | `eval_workflow_run.py` | `test-command-rules.sh` | [ticket-complete](../docs/workflow/ticket-complete.md) |
| `common-ground` | [Common-ground](common-ground/EVAL.md) (the Spec Assumptions Check only) | `eval_common_ground_run.py` | `test-command-rules.sh` | [common-ground](../docs/workflow/common-ground.md) |

Gaps: `spec:status` has no eval; `spec:triage` and `spec:create` are scored only by the outcome of the run they set up, so a bad grouping or plan shows as a failed ticket, not as its own check. `common-ground`'s Surface and Adjust modes have no eval. Scorers live in `scripts/`; smoke tests are in `scripts/` unless a path says otherwise.

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
  "setup": ["npm ci"],
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
| `setup` | intake | Optional. Shell commands the baseline runs, in order, in each run it rebuilds from its bundle before scoring, since a rebuilt run has no installed dependencies (`["npm ci"]`). A run may override it; a failing command stops the baseline. Without it the suite runs as the bundle left it |
| `run` | both | The name `RUN=` selects |
| `repo` | both | The clone to score, only while it still sits at the run's end; drop it once the clone moves on (a Phase 4 branch), and the run scores from `bundle` and `branch`, as the baseline always does |
| `spec` | workflow | The spec the run executed |
| `start` | intake | The commit that added the goal prompt and checklist |
| `plugin`, `model` | both | Recorded in the result |
| `reflog`, `transcripts` | both | Saved when the run ended, since git prunes the reflog and transcripts stay on the machine that ran them. `transcripts` lists the goal session and every agent transcript under `<session>/subagents/`; the scorer tells them apart by `isSidechain` |
| `suite_green` | intake | Take the suite result from the run's saved test output (its services are gone) |
| `accuracy` | intake | The run's mapping onto the gold set |

## Running

```bash
make eval-intake EVAL=<eval directory> RUN=<run name>
make eval-baseline EVAL=<eval directory>
make eval-workflow EVAL=<eval directory> RUN=<run name>
make eval-discovery EVAL=<eval directory> RUN=<run name>
make eval-common-ground EVAL=<eval directory> RUN=<run name>
make eval-spec-current-diff EVAL=<eval directory> RUN=<run name>
make eval-spec-complete-docs EVAL=<eval directory> RUN=<run name>
```

`eval-baseline` writes its table into the eval directory's `baseline.md`; `PRINT=1` prints it instead.

A flag given on the command line (`REPO=`, `START=`, `TRANSCRIPTS=` and the rest) overrides the value in `eval.json`.

## What stays local

Some files stay on your machine even when the results repo is private. List them in its `.gitignore`: details of security findings the project hasn't fixed, raw transcripts (push redacted copies instead), and repo bundles. Before each push, check the files for tokens and environment dumps, since a goal run's shell commands can capture them.
