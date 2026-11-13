# intake:document-config

Write a configuration reference (environment model, env vars vs hardcoded config, per-environment build/deploy profiles, local-dev quickstart), worked out from how the project is configured, built, and run.

**Step:** documentation (intake phase) · **Command file:** `commands/intake/document-config.md`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `configuration-doc` | file | docs/operations/configuration.md | Configuration reference. Covers the environment/config model, environment variables vs hardcoded config, per-environment build/deploy profiles, and a local-dev setup quickstart. |

## How it runs

The command reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
