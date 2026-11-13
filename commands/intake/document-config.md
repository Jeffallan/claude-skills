---
name: document-config
description: Generate an accurate, agent-readable configuration reference (environment model, env vars vs hardcoded config, per-environment build/deploy profiles, local-dev quickstart) by reverse-engineering how the project is configured, built, and run.
argument-hint: "[directory]"
---

# intake:document-config

**Argument:** `$ARGUMENTS`. Optional root directory to analyze (defaults to the project root).

Produce a configuration reference at `docs/operations/configuration.md` (configurable): a precise account of how the
project is configured, built, and run across environments, written for an AI agent or engineer to rely on as the
implementation contract. **Document only what the code and config prove. Never invent a variable, default, or
profile. Never reproduce a secret value.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. The first two set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior. The third defines the two sections this command owns ("Library security settings"): `## Library security settings` and `## Security settings: test versus deployed`.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when configuration, build profiles, or the
environment model change (a rerun edits the existing document in place and keeps hand edits; see "Reruns" in `references/intake/rules.md`).

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer how config flows through the code; find where settings are read and defaulted.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:cloud-architect`**: interpret per-environment topology, managed-service config, and runtime credential models.
- **`fullstack-dev-skills:devops-engineer`**: characterize build/deploy profiles, CI/CD wiring, container/runtime config, and scripts.
- **The project's language/stack skill** for the config idioms in play: choose by stack, e.g. `fullstack-dev-skills:typescript-pro`,
  `fullstack-dev-skills:python-pro`, `fullstack-dev-skills:golang-pro`, `fullstack-dev-skills:java-architect`.

## Workflow

### Phase 1: Discover the configuration surface
Identify where and how the project is configured, in priority order:
1. Environment/config inputs: `.env*` files and templates, `process.env`/`os.environ`/equivalent reads, settings
   modules, config files (`*.yaml`/`*.toml`/`*.json`/`*.ini`), and any config-loading/validation layer.
2. Hardcoded/compile-time config: constants and object literals in source that carry endpoints, project ids,
   feature flags, or keys (note these explicitly; they are config even without env indirection).
3. Build/deploy config: build tool and bundler config, CI/CD pipelines, container/orchestration manifests, IaC,
   and any per-environment profile definitions.
4. Scripts: package/run scripts and Makefile/justfile targets for start, build, test, lint, and deploy.

Determine the **environment model**: how the project distinguishes environments (dev/staging/prod), what selects the
active one (an env var, a build profile, a runtime flag, a per-environment project/account), and whether there is a
real per-environment split or a single target with a runtime switch.

### Phase 2: Extract the config model
Capture:
- **Settings catalog**: each meaningful setting: its name, what it controls, where it is read, its default (if
  any), and whether it is required. Separate **env-var-driven** settings from **hardcoded/compile-time** config and
  say which is which.
- **Secrets handling**: which settings are secrets and **where they live** (env var name, secret manager, CI
  secret, gitignored file). Name the mechanism and the storage location; never print the value. Flag any secret that
  appears hardcoded in source.
- **Per-environment build/deploy profiles**: each profile/target, what differs between them (distribution, runtime,
  flags, auto-increment, etc.), and how one is selected.
- **Scripts**: the canonical commands to start, build, test, lint, and deploy, with their purpose.
- **Library security settings**: for each auth, admin and API library the project installs (an auth or account
  library, a token or session library, an admin site, an API framework, a CORS or rate-limit package), every
  setting that bears on security, with its effective value and the source of that value
  (`<settings file>::<NAME>`, an env var, or "library default"). Read the library's own defaults in the installed
  package, not from memory, and list the defaults the project never set: who may register, whether accounts
  activate by link, which permission and authentication classes apply when a view names none, token lifetime and
  rotation, which routes the library mounts, throttles, password rules.
- **Security settings, test versus deployed**: the settings the test configuration resolves next to the ones the
  deployed configuration resolves, for each security control: debug mode, CORS origins, allowed hosts, throttles
  and rate limits, cookie flags (secure, httponly, samesite), CSRF, password validators and hashers, the email
  backend, HTTPS redirects and HSTS, session lifetime. Read both from the settings the test runner actually loads
  and the settings the deploy config selects. Mark each row that differs, and say which tests that difference
  leaves unproven.

### Phase 3: Assemble the local-dev quickstart
From the above, derive the minimal ordered steps to get a working local environment: install dependencies, supply
required config/secrets (by name and source, never value), choose a runtime, and run any build/deploy step needed
for the chosen feature set. Note anything that silently no-ops or behaves differently locally vs. in a full build.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the environment model, the count of settings
(env-driven vs hardcoded), the build/deploy profiles found, the security-relevant libraries found, the test and
deployed settings modules being compared, and the output path. Do not write the document until the
user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write the document at the output path using the template below.

Docs describe what the configuration does, neutrally. A setting whose effective value breaks an access invariant
(`references/intake/access-control.md`, "Access invariants") or contradicts stated intent (a comment, a test,
another doc) is a finding: append it to the tracker before writing the doc, and cite its id in the row. A
security-relevant default nobody chose that weakens a control is a finding too, because "the library does it by
default" is not evidence of intent. A deployed setting that turns a control off is also a finding. A control the test settings
turn off is not a finding by itself; record it in the test-versus-deployed table so the testing commands know
which tests need the deployed value.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code/config: setting names, defaults, required-vs-optional status, the file each is
read in, profile differences, script commands, and each library setting's effective value against the installed
library's default and the project's override. Confirm both security tables come from the settings modules the
test runner and the deploy config actually load. Confirm no secret value is reproduced anywhere in the doc, and
that each secret's storage location is named correctly. Ground any example in a real file. Fix or remove anything not
provable. Prefer "unknown / not defaulted in code" over a guess.

## Output template

```markdown
---
command: intake:document-config
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# Configuration

<1-2 sentence overview: how the project is configured, built, and run, and what this documents.>

**Sources of truth (read these if this doc and the code disagree):**
- <config/build/script files to trust over this doc, one per line with a one-line role>

> <cross-links (where they exist): external integrations, authorization, any existing setup runbook>

## Environment model
<how environments are distinguished and selected; single target vs real split; the deciding flag/profile/account>

| Concern | How environment is determined | File |
|---|---|---|

> <Undetermined / not defaulted in code: settings with no in-code default; secrets supplied out-of-band>

## Settings
<env-var-driven settings vs hardcoded/compile-time config, clearly separated>

| Setting | Controls | Source (env / hardcoded) | Default | Required | Read in |
|---|---|---|---|---|---|

## Secrets
<which settings are secrets and WHERE each lives, never the value; flag any hardcoded secret>

## Build / deploy profiles
<each profile/target, what differs, and how it is selected>

| Profile | Selected by | Differences | Notes |
|---|---|---|---|

## Library security settings
<one subsection per auth, admin and API library; every security-relevant setting, defaults the project never set included>

### <library name> <version>
| Setting | Effective value | Source | Notes |
|---|---|---|---|
| <NAME> | <value, never a secret> | <`settings file::NAME` / env var / library default> | <what it controls; finding id> |

## Security settings: test versus deployed
Test settings: `<module or file>`. Deployed settings: `<module or file>`, selected by <flag or profile>.

| Setting | Test value | Deployed value | Differs | Effect on tests |
|---|---|---|---|---|
| <debug / CORS / allowed hosts / throttles / cookie flags / password rules / email backend / ...> | <value> | <value> | <yes / no> | <which control the tests don't exercise; finding id> |

## Scripts
| Script | Command | Purpose |
|---|---|---|

## Local dev setup
1. <install dependencies>
2. <supply required config/secrets by name and source, never value>
3. <choose a runtime>
4. <any build/deploy step needed for the chosen feature set>

## Gotchas for implementers
<no-env-indirection traps, single-project assumptions, load-bearing flags, config that invalidates state>
```

## Failure conditions

- **No configuration surface found**: state that plainly and stop; do not fabricate variables or profiles.
- **Config sources disagree** (e.g. a default in code vs a different value in a committed config file): document
  **both** and flag the discrepancy; do not silently pick one.
- **No deployed settings in the repo** (they live in a platform console or secret store): fill the deployed column
  with "not in repo" and add an Open question naming the settings whose deployed value the owner must confirm.
- **A secret value would be exposed**: never reproduce it. Record only the name and storage location, and flag a
  hardcoded secret for rotation/relocation.

## Output

A single document at the output path, plus a short summary: the environment model, settings cataloged (env-driven vs
hardcoded), build/deploy profiles, the local-dev quickstart, the security-relevant libraries and settings listed,
the security settings that differ between test and deployed, finding ids raised, and any discrepancies, hardcoded
secrets, or unknowns surfaced for follow-up.
