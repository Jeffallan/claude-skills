# intake:existing-docs

List the docs a project already has, map them to the intake doc set, and check their claims against the code.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/existing-docs.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `existing-docs-inventory` | file | docs/intake-existing-docs.md | Every doc the project already had, the intake topics it covers, and its claims checked against the code, each wrong claim a finding. |

## How it runs

It runs first in the documentation step, before the docstrings. It lists your docs (README, `docs/`, ADRs, runbooks), maps each one to the intake topics it covers, and checks its claims against the code. A claim the code contradicts becomes a finding in `docs/intake-findings.md`. A claim no code can settle is listed as unverified.

Intake never edits your docs. Later intake commands link to a doc of yours that already covers their topic and write only what it lacks. When one of your docs sits at an intake doc's path, the intake doc goes beside it as `<name>-intake.md`. The intake docs index lists your docs too, marked as owner-written. When you already have a `docs/README.md`, the index is `docs/README-intake.md`.

On a project with no docs, the inventory says so and every intake topic gets its own doc. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
