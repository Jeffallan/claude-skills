# intake:document-config

Write a configuration reference (environment model, env vars vs hardcoded config, per-environment build/deploy profiles, local-dev quickstart), worked out from how the project is configured, built, and run.

**Step:** documentation (intake phase) · **Procedure file:** `references/intake/procedures/document-config.md` · **Run:** `intake document-config`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to analyze. Defaults to the project root. |

## Outputs

| Name | Type | Path | Description |
|------|------|------|-------------|
| `configuration-doc` | file | docs/operations/configuration.md | Configuration reference. Covers the environment/config model, environment variables vs hardcoded config, per-environment build/deploy profiles, a local-dev setup quickstart, `## Library security settings` (each auth, admin and API library's security-relevant settings with effective value and source, defaults the project never set included), and `## Security settings: test versus deployed`. |

## How it runs

The procedure reads the code, stops at a checkpoint to confirm scope, writes its document, then runs an accuracy audit against the code, because agents read the result as the implementation contract. In an attended run the agent stops at the checkpoint so you can confirm or correct the scope; in a goal run it records the scope as a draft in the checklist note and goes on (see the [intake phase](intake-phase.md)).

Two sections cover security. `## Library security settings` lists each auth, admin and API library's security settings with their effective values and where each value comes from, including defaults you never set. `## Security settings: test versus deployed` puts the test and deployed values side by side for controls such as debug mode, CORS, allowed hosts, throttles, cookie flags, password rules and the email backend. A default nobody chose that weakens a control goes into the findings tracker.

Run it after `intake:document-codebase`. A rerun edits what it owns in place and keeps your hand edits. In a goal run it never asks a question; see the [intake phase](intake-phase.md).
