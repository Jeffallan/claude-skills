# intake:create-system-description

Write the baseline spec and a living system description from the intake docs, the spec index and every completed spec.

**Step:** system description (intake phase, last) · **Command file:** `commands/intake/create-system-description.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `--full` | flag | no | Rewrite the whole description instead of folding in only the specs it hasn't seen |
| `--roadmap` | flag | no | Write only the planned architecture view from the specs not yet completed |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `system-description` | file | `docs/system-description.md` | Components, data flow, security, API surface, dependencies, operations and change management, with a change history |
| `baseline-spec` | file | `docs/specs/completed/baseline/overview.md` | The system as intake found it, written on the first run |
| `architecture-roadmap` | file | `docs/architecture-roadmap.md` | With `--roadmap`: current and target component diagrams and one row per outstanding spec |

## How it runs

The first run writes the baseline spec, a completed spec named `baseline` whose `Feature areas:` line comes from the documentation phase, and regenerates the spec index. Later specs on the same areas find it through the index. It then writes the whole system description from the intake docs and any completed specs.

A project that started from discovery and never ran intake has no intake docs. There the baseline names the discovery topics, records no intake findings and takes its feature areas from the completed specs. The description comes from the completed specs and the code; the discovery outputs are plans, so a claim from them is stated only when the code or a completed spec confirms it.

Each later run reads the description's Change history and folds in only the completed specs it doesn't list, changing just the sections they touch. `--full` rewrites everything. Every section names its sources, and open findings that affect a section appear in it by id.

`--roadmap` writes `docs/architecture-roadmap.md` instead and touches nothing else. It sets the current component diagram from the system description beside a target diagram built from every spec `guard spec-status` lists as not yet completed, with a table of what each one adds, changes or removes. The page is marked as a plan, carries no `sources:` or `related:` frontmatter so no ticket's docs check ever lists it, and is never a source for the description. It refuses until `docs/system-description.md` exists.

`spec:complete` keeps the description current one spec at a time: in its completion commit, before the PR opens, it proposes updates for the finished spec and applies the ones the owner approves.

## Next steps

Intake is done when the docs, the tests and the findings tracker agree. Go to the [Discovery Phase](discovery-phase.md) or the [Spec Phase](spec-phase.md).
