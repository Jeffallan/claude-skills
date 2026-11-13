# Intake Rules

The rules every `intake:*` command shares: where the output goes, how a documentation command checks scope and audits its document, how a testing command proves its tests run, and how both behave in a goal run. Each command reads this file before its first phase. Findings and the tests that pin them follow `references/intake/findings.md`.

## Output layout

Documentation commands write one document each under `docs/`, grouped by category. Testing commands write into the project's existing test tree; they never create a parallel one.

```
docs/
├── README.md                         # intake:create-onboarding, links every doc below
├── intake-findings.md                # the findings tracker, every command appends
├── intake-existing-docs.md           # intake:existing-docs, the docs the project already had
├── system-description.md             # intake:create-system-description
├── architecture/
│   ├── data-model.md                 # intake:document-data-model
│   ├── file-tree.md                  # intake:document-file-tree
│   ├── external-integrations.md      # intake:document-integrations
│   └── api-reference.md              # intake:document-api
├── domain/
│   ├── user-model.md                 # intake:document-user-model
│   ├── features.md                   # intake:document-features
│   └── glossary.md                   # intake:document-glossary
├── security/
│   ├── security.md                   # intake:document-security
│   └── authorization.md              # intake:document-authorization
├── flows/
│   └── user-flow.md                  # intake:document-user-flow
├── operations/
│   ├── configuration.md              # intake:document-config
│   └── analytics-events.md           # intake:document-analytics
└── specs/completed/baseline/
    └── overview.md                   # the baseline spec, see intake:create-system-description
```

- The five categories are `docs/architecture/` (how it is built), `docs/domain/` (what it does), `docs/security/`, `docs/flows/` (user journeys) and `docs/operations/` (how it runs).
- Cross-link sibling docs with relative paths (`../security/authorization.md`).
- Each command owns its file and overwrites it on a rerun. The findings tracker is the exception: commands only append to it.
- Once `docs/README.md` exists, a command that writes a new doc adds it to the README's index in the same commit (`intake:create-system-description` adds `system-description.md` and `specs/`).
- A later command that proves an earlier doc wrong, incomplete or stale corrects it in its own commit: a doc saying a test "will" pin a behavior that is now pinned, a finding called "suspected" that a test confirmed, the test trees `intake:testing-setup` adds go into `file-tree.md`, an account path a testing command finds goes into `user-model.md` and `security.md`. Keep the doc's structure and add a dated line to its `## Accuracy audit` naming what changed and why. A doc that stops matching the code is worse than no doc.

## Existing docs

Docs the project had before intake are the owner's. Intake never edits them. `intake:existing-docs` lists them in `docs/intake-existing-docs.md` and checks their claims against the code:

- A claim the code contradicts is a finding with its evidence (the doc and the symbol), like any other bug.
- A claim no code can settle ("deploys take five minutes") is marked unverified in the inventory, never a finding.
- A topic an existing doc covers fully is linked from the intake doc for that topic, not repeated. A topic it covers in part or not at all is written by the intake command, as usual.
- When an owner doc sits at an intake doc's path, the intake doc goes beside it as `<name>-intake.md`, and each lists the other in `related:`.

`docs/README.md` lists the owner docs too, marking each "owner-written" with its open finding ids.

## Doc frontmatter and citations

Every intake doc starts with frontmatter naming the docs to check when it changes. List the docs that state facts this one depends on, or that depend on it, as paths under `docs/`, and keep each link two-way:

```markdown
---
related: [security/authorization.md, architecture/api-reference.md]
---
```

Cite code by symbol: `` `app/billing/services.py::round_minutes` ``, `` `app/models.py::Profile.save` `` for a method, the key name for configuration. Never cite `path:line`: `intake:document-codebase` and every later docstring move lines, so a line number goes stale before the run ends. After a ticket workflow adopts these docs, `ticket:execute` finds the docs a change affects through these citations and `related:` links.

Check both before committing a doc:

```bash
uv run -q --no-project --python ">=3.11" "${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz" docs-check
```

It reports a `related:` doc that is missing or doesn't link back, and a citation whose file or symbol is gone. Fix what it lists in intake docs; an owner doc it lists goes in the inventory instead.

## What intake may change

Intake changes docs, tests, test configuration and docstrings. Nothing else.

| May change | Never changes |
|------------|---------------|
| Files under `docs/` | Application code, other than comments and docstrings |
| Test files, fixtures and helpers | Dependencies the application ships with |
| Test runner config, test scripts in the package manifest, dev-only test dependencies | Build, deploy or runtime config |
| Comments and docstrings | Database schemas or migrations |

A command that finds it can't test something without changing application code records a finding and leaves the code alone. `intake:testing-setup` may add a test-only hook (an environment flag the test config sets) only when the code has no seam at all, and records it as a finding so the owner sees it.

### A red baseline

When the existing suite fails before intake starts, find out why before any other testing work. `intake:testing-setup` owns this.

- **The test code is stale**: a factory, fixture or helper under the test tree no longer matches the code (a field moved to another model, an import was renamed). That is test infrastructure, so repair it, record a finding naming the commit that broke it, and let the repaired tests characterize the code like any others.
- **The application misbehaves**: the test is right and the code is wrong. Keep the test, mark it expected-fail with a new finding id, and add a passing characterization test beside it.
- **The environment won't build**: a dependency that no longer installs, an image that fails to build. Build config is outside intake, so work around it outside the repo (a scratch image, a pinned tool), record a finding, and name the workaround in the test command you report.

Never leave the suite red. The goal run's `<done_when>` and the intake eval's `characterization-green` both need the test command to exit 0 at the end; neither compares before and after.

## Checkpoint

Every command stops once before it writes: the documentation commands after discovery, the testing commands after designing their cases. The checkpoint shows the scope (what was found, what will be written, where) so a wrong scope costs nothing.

Attended, the command presents the scope and waits for the owner. It writes nothing until the owner confirms or corrects it.

## Human-voice pass

Every documentation command gives its document's prose a human-voice pass after writing it and before the accuracy audit: people read these docs too. When the `writing-with-agents:human-voice` command is available, run it in embedded mode on the prose; otherwise remove the usual tells by hand (no em dashes, no sentences opening with "And" or "But", no "not just X, but Y" shapes, no filler). Leave code, commands, paths, identifiers, tables of facts, frontmatter and `path::symbol` citations exactly as they are. The pass may change wording, never a claim; the audit below then re-checks every claim against the code. Record it in the item's checklist note as `human-voice: writing-with-agents:human-voice` or `human-voice: by hand`; the intake eval checks that note, and that a note naming the command loaded it.

## Accuracy audit

Every documentation command ends with an audit, because agents read its document as the implementation contract. After writing and the human-voice pass, re-read each claim against the code: names, types, paths, constraints, defaults, call sites. Then:

- Fix or remove any claim the code doesn't prove. Prefer "unknown" or "not enforced" over a guess.
- Ground every example in a real call site, and cite it as `path::symbol`.
- Keep each fact in one doc. Read the docs already written for anything this one restates: the doc that owns the topic keeps the fact, and this one links to it. A sentence repeated word for word across docs fails the eval, and a fact kept in six docs needs six edits when it changes.
- When two sources disagree (a type and a rule, a doc and the code), keep both in the document, flag the discrepancy and add a finding.
- End the document with an `## Accuracy audit` section: the date, the commit, what was checked and how, and the finding ids it raised. The eval looks for this section.

## Run and verify

Every testing command ends by running what it wrote, because its output is code that must execute.

- Run the suite with the project's own script and capture fresh output in the summary: the command, the pass, fail and skip counts, and the exit code.
- Every characterization test passes. Every intended-behavior test is skipped or expected-fail and names its finding id.
- Update the tracker in the same commit as the tests: a Test coverage row per finding, the finding's `Tests:` line, and its text when the test confirmed or disproved it (`references/intake/findings.md`, "Every finding has evidence").
- Seed related records so their ids differ across tables (user 1 owns profile 7). A fresh database often numbers everything from 1, so code that uses one table's id for another passes by coincidence.
- A deny or error-path test asserts the specific denial or error, never just "it threw". A test that passes because something unrelated failed is a false pass.
- Keep the type checker and linter as clean as they were before the run.
- A layer that can't run here (no emulator, no browser, a missing secret) is reported as blocked with the reason. It never counts as passing.
- `intake:testing-setup` proves each layer with a smoke test before any other testing command writes a real test.

## In a goal run

Intake commands run unattended inside a `/goal` run, under the rules in `references/specs/unattended.md` that apply to ticket commands. Two rules change for intake:

- **Never call `AskUserQuestion`.** The checkpoint becomes a draft: the command writes the scope it would have shown in its checklist note and continues with it. It never stops the run to wait. A routine scope confirmation is not a question. Add an Open questions row to `docs/intake-findings.md`, with a draft decision, only when the owner could reasonably choose differently and the choice changes what gets written: a layer skipped, a surface left out, a contradiction picked one way.
- **Never block on a missing document.** A command whose input doc is absent works from the code alone and adds an Open question saying so.

The rest holds unchanged: no tracker writes, no history rewrites, subagents only read, every edit in the main session. A command that can't finish (a layer won't run, the project won't build) records why in its summary and the Open questions, and the run moves to the next command. Only a stop the goal prompt lists ends the run with `BLOCKED:`.

## Skills

Each command names its skills by exact name. The language and framework skill is chosen by detection: read the package manifest and lockfile, the framework config and the test config, then pick the matching `fullstack-dev-skills:` skill. A stack with no matching skill gets none, and the command says so rather than borrowing a neighbor's.
