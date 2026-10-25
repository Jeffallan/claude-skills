# Recorded Evidence and memidex

Use this reference when: Explaining recorded outcomes, inspecting artifacts, tracing knowledge, or reviewing an outcome correction.

## Establish which run answers the question

Start with the requested run ID, or list completed runs when it is unknown:

```bash
npx agent-qa runs list --json
npx agent-qa runs list --test checkout --limit 20 --json
```

A title filter can return several tests. Match the target, test identity, completion time, and build information to the request.
Do not infer checkout coverage from a passing cart test or infer the current build's status from an older run.
An empty completed-run list means no matching completed record was returned.
It does not establish whether an asynchronous run is queued or active.
Check the relevant supported queue or returned stream when that distinction matters; do not start a replacement run by default.

The following commands use `RUN_ID`, `RECORD_ID`, and `ARTIFACT_SHA` as placeholders.
Replace them with identifiers returned by the supported readers; do not invent identifiers.

```bash
npx agent-qa digest RUN_ID --json
npx agent-qa runs overview RUN_ID --json
```

The digest is a top-level command.
The overview maps recorded tests, steps, and artifacts.
Use the overview's zero-based test and step indices when addressing evidence.
Read returned errors as errors, not as an empty successful result.

## Inspect only the relevant evidence

For a recorded first test and first step, these examples request structured documents:

```bash
npx agent-qa runs evidence RUN_ID --test 0 --step 0 --kind console --json
npx agent-qa runs evidence RUN_ID --test 0 --step 0 --kind network --json
```

Choose indices from the actual overview rather than copying `0` automatically.
Other supported document kinds include accessibility, ARIA, and variables; consult `runs evidence --help` for exact flags.
A missing artifact narrows what can be concluded. It does not justify reconstructing a screenshot or inventing a browser observation.
Export a recorded screenshot or recording through the artifact reader:

```bash
npx agent-qa runs evidence RUN_ID --screenshot ARTIFACT_SHA --out ./run-evidence.png
```

The output path must be new; the export command refuses to overwrite an existing file.
The `--screenshot` flag also accepts a recording's artifact SHA. Use an appropriate extension for the actual artifact.
Inspect the exported artifact before claiming what it shows.
Keep the artifact tied to its run, test, and step; a screenshot alone may not show the required final state.

## Interpret results without extending coverage

| Observation | Supported conclusion | What still needs evidence |
|-------------|----------------------|---------------------------|
| Test validates or dry run lists it | Configuration and selection checks succeeded | Actual application behavior |
| MCP returns a run acknowledgement | A run was acknowledged | Terminal status and test outcome |
| Matching completed test is recorded as passed | That recorded test passed in that run | Untested journeys or a different build |
| Test records a failed expected outcome | The run recorded that failure | Whether it is an application defect, stale expectation, or environment issue |
| No matching completed record is returned | Matching completed evidence is unavailable | Any claim that the requested journey passed |

Do not silently relabel `healed`, `timeout`, or `cancelled` outcomes as `passed`.
Preserve the tool's recorded verdict and explain any uncertainty about its interpretation.
Report application defects separately from provider authentication, unavailable browsers, device setup, and other execution failures.
For a read-only request, end with evidence and the remaining gap rather than initiating a new test or correction.

## Trace memory and self-improvement

memidex stores reviewable application knowledge, including facts, procedures, cautions, and policies.
agent-qa can use and refine that knowledge across runs; a memory change is not proof of a passing test.
Read the `AGENTS.md` policy in the project’s committed `agent-qa-knowledge` directory before changing knowledge files.
Use the recorded knowledge readers to distinguish what a run consumed from what it learned:

```bash
npx agent-qa runs knowledge RUN_ID --json
npx agent-qa knowledge inspect --json
npx agent-qa knowledge show RECORD_ID --json
```

Use the recorded brief trace when the question is why a particular step received a piece of knowledge:

```bash
npx agent-qa knowledge brief-why RUN_ID --step 0 --json
```

For a multi-test run, add the actual test ID using `--test` when needed.
Read provenance and gate decisions before treating a record as accepted or current.
Use documented knowledge operations and the repository's knowledge policy for authorized corrections.
Do not edit `.agent-qa/` databases or derived indexes to manufacture a result, erase a failure, or bypass a gate.

## Review an outcome correction

An outcome mark is a mutation, not an annotation-only read: it can apply an attributable correction.
First compare the expectation and recorded evidence and identify the exact test and step.
When MCP is connected, `agent_qa_preview_run_mark` previews the effect without writing.
Inspect the current schema and preview for the requested mark, such as `false-fail`, `false-pass`, or `confirmed-bug`.
A preview may refuse an ambiguous or unsupported correction; resolve that ambiguity rather than choosing a nearby step.
Apply `agent_qa_mark_run` or the supported CLI mark only when that correction is within the user's authorized task.
Record its actual receipt and report any refusal or incomplete effect.
Do not claim that a correction or learned record reran the application or proved a previously untested behavior.

## Use MCP equivalents when available

| Need | MCP tool name before any client namespace |
|------|------------------------------------------|
| Completed runs | `agent_qa_list_runs` |
| Run verdict and decisions | `agent_qa_get_run_digest` |
| Test, step, and artifact map | `agent_qa_get_run_overview` |
| Step evidence | `agent_qa_get_run_evidence` |
| Knowledge used and learned | `agent_qa_get_run_knowledge` |
| Proposed correction effects | `agent_qa_preview_run_mark` |

Discover actual tool availability and schemas on the connected server.
A tool error or missing reader is a limitation to report, not permission to inspect private storage internals.

## Report only what the evidence supports

Name the observed run, test, target, and relevant step when available.
Separate the recorded verdict, your interpretation, and any coverage gap.
Preserve configured secret placeholders; do not recover their original values for the report.
Review evidence before sharing it because arbitrary logs and screenshots can contain unmasked information.
Link local exported artifacts when useful, and describe any corrections actually applied with their receipts.
