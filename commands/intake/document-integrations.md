---
name: document-integrations
description: Generate an accurate, agent-readable reference of every external service and SDK the project talks to (purpose, configuration, integration points, credentials, topology diagram) by reverse-engineering the codebase.
argument-hint: "[directory]"
---

# intake:document-integrations

**Argument:** `$ARGUMENTS`. Optional root directory to analyze (defaults to the project root).

Produce an external-integrations reference at `docs/architecture/external-integrations.md` (configurable): a precise
catalog of every external service, API, and third-party SDK the project depends on, written for an AI agent or
engineer to rely on as the implementation contract. Per integration, record what it is used for, where it is
initialized/configured, the in-code integration points, and the credentials/setup it needs. **Document only what the
code proves. Never invent an integration, endpoint, or credential. Never reproduce a secret value.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when an integration is added, removed, or
reconfigured (this command is idempotent; it overwrites the document).

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the dependency surface; infer which external services the code calls and where.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:cloud-architect`**: interpret cloud/provider SDKs, managed services, and runtime credential models (e.g.
  workload identity, instance/service-account credentials, secret managers).
- **`fullstack-dev-skills:api-designer`**: characterize each integration's API surface (REST/GraphQL/gRPC/SDK calls, webhooks, event
  triggers) and how the project consumes it.
- **The project's language/stack skill** for the SDKs in play: choose by stack, e.g. `fullstack-dev-skills:typescript-pro`,
  `fullstack-dev-skills:python-pro`, `fullstack-dev-skills:golang-pro`, `fullstack-dev-skills:java-architect`.

## Workflow

### Phase 1: Discover the integration surface
Identify every external dependency the code actually talks to, in priority order:
1. Dependency manifests (e.g. `package.json`, `requirements.txt`/`pyproject.toml`, `go.mod`, `pom.xml`/`build.gradle`,
   `Gemfile`, `*.csproj`): flag packages that are SDKs/clients for external services, not pure utilities.
2. Client/SDK initialization sites: where a client is constructed (`new XClient(...)`, `initializeApp(...)`,
   `createClient(...)`, connection strings, base-URL constants).
3. Configuration and wiring files (provider config, IaC, plugin/build config, MCP or tooling manifests) that name
   external projects, regions, endpoints, or hosts.
4. The call sites: where requests are sent, webhooks/callbacks are received, or event triggers fire.

Classify each integration by **side** (client/frontend, server/backend, build/CI, or developer tooling) and by
**direction** (the project calls out vs. the provider calls in via webhook/event/trigger). Distinguish runtime
integrations from build-time and developer-only tooling; note the latter as out-of-runtime.

### Phase 2: Extract per-integration detail
Per integration, capture:
- **Purpose**: what capability it provides and which app features depend on it.
- **SDK / package and version**: the exact dependency and pinned version from the manifest.
- **Where it is configured / initialized**: the file(s) and symbol(s) that construct the client and set options.
- **Integration points**: the concrete functions/handlers/triggers that read or write through it, with file
  pointers. Include event/webhook triggers and the data they carry.
- **Credentials / setup**: what auth material or config it requires and **where that material lives** (env var
  name, secret manager, runtime identity, gitignored config file). Name the mechanism; never print the value.
- **Behavior and failure mode**: relevant options actually set in code (timeouts, retries, regions, sampling,
  fail-open vs fail-closed), and what happens when the integration is unavailable.

### Phase 3: Diagram
Produce a Mermaid `flowchart` topology showing the app component(s), the external services/providers, and the edges
between them. Group nodes into subgraphs by boundary (e.g. client, backend/cloud project, third-party services).
Use solid edges for direct/synchronous SDK calls and dotted edges for asynchronous event/webhook triggers; label
edges with the trigger or call where it adds clarity. Omit developer-only tooling from the runtime topology (note it
separately).

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the list of integrations found (with side and
runtime-vs-tooling classification) and the output path. Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write the document at the output path using the template below.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: package names and versions, init sites, integration points, trigger
wiring, and the location (not the value) of each credential. Confirm no secret value is reproduced anywhere in the
doc. Ground any example in a real call site. Fix or remove anything not provable from the code. Prefer "unknown /
not configured in code" over a guess.

## Output template

```markdown
---
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# External Integrations

<1-2 sentence overview: what this catalogs and across which sides (client / server / build).>

**Sources of truth (read these if this doc and the code disagree):**
- <init/config files to trust over this doc, one per line with a one-line role>

> <cross-links (where they exist): configuration per environment, data model, authorization, API reference>

## Topology

` ` `mermaid
flowchart TB
  ...
` ` `

<one-line legend: solid = direct SDK call, dotted = event/webhook trigger; note any nodes intentionally omitted>

## Integration summary
| Integration | SDK / package | Side | Configured in | Credentials live in |
|---|---|---|---|---|

## <Integration name>
**What it is.** <purpose; which features depend on it; SDK + version>
**Where it is initialized / configured.** <file(s) and symbol(s); options actually set>
**Integration points.** <functions/handlers/triggers with file pointers; events/webhooks and their payload>
**Credentials / setup.** <what auth/config it needs and WHERE it lives, never the value; enablement steps>

<repeat per integration; group runtime integrations first, then build-time, then developer tooling>

## Gotchas for implementers
<trust boundaries, fail-open vs fail-closed behavior, things that silently no-op, config that invalidates tokens>
```

## Failure conditions

- **No external integrations found**: state that plainly and stop; do not fabricate services.
- **A dependency is declared but never initialized/called** (or vice versa): document the discrepancy; do not
  assume it is wired.
- **A secret value would be exposed**: never reproduce it. Record only the credential's name and storage location,
  and flag if a secret appears hardcoded in source so it can be rotated/moved.

## Output

A single document at the output path, plus a short summary: integrations cataloged (by side), the topology
rendered, and any discrepancies, fail-open behaviors, or unknowns surfaced for follow-up.
