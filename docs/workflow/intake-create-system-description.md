# intake:create-system-description

Write the baseline spec and a living system description from the intake docs, the spec index and every completed spec.

**Step:** system description (intake phase, last) · **Command file:** `commands/intake/create-system-description.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `--full` | flag | no | Rewrite the whole description instead of folding in only the specs it hasn't seen |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `system-description` | file | `docs/system-description.md` | Components, data flow, security, API surface, dependencies, operations and change management, with a change history |
| `baseline-spec` | file | `docs/specs/completed/baseline/overview.md` | The system as intake found it, written on the first run |

## How it runs

The first run writes the baseline spec, a completed spec named `baseline` whose `Feature areas:` line comes from the documentation phase, and regenerates the spec index. Later specs on the same areas find it through the index. It then writes the whole system description from the intake docs and any completed specs.

Each later run reads the description's Change history and folds in only the completed specs it doesn't list, changing just the sections they touch. `--full` rewrites everything. Every section names its sources, and open findings that affect a section appear in it by id.

`spec:complete` keeps the description current one spec at a time: in its completion commit, before the PR opens, it proposes updates for the finished spec and applies the ones the owner approves.

## Next steps

Intake is done when the docs, the tests and the findings tracker agree. Go to the [Discovery Phase](discovery-phase.md) or the [Spec Phase](spec-phase.md).
