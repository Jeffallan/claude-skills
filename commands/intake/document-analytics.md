---
name: document-analytics
description: Generate an accurate, agent-readable product-analytics reference (telemetry setup, an event catalog, and identity wiring) by reverse-engineering the instrumentation from code.
argument-hint: "[directory]"
---

# intake:document-analytics

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce a product-analytics reference at `docs/operations/analytics-events.md` (configurable): the authoritative
catalog of every analytics/telemetry event the product emits, where each one fires, and the parameters it
carries. **Document only what the code proves. Never invent an event, parameter, or call site.**

This command covers **product analytics** (user-behavior events). It does not document crash/error telemetry or
metrics/tracing pipelines; note where those live and link them, but keep them out of the event catalog.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when instrumentation changes (this command is
idempotent; it overwrites the document).

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the instrumentation; find the event definitions and every emit call site.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:monitoring-expert`**: interpret the telemetry provider's setup, enablement gating, and identity model;
  reason about what is and is not actually delivered in each environment.
- **The project's frontend/backend skill** for the call-site language, chosen by stack, e.g. `fullstack-dev-skills:typescript-pro`,
  `fullstack-dev-skills:react-expert`, `fullstack-dev-skills:python-pro`, `fullstack-dev-skills:golang-pro`.

## Workflow

### Phase 1: Discover the telemetry layer
Identify the analytics provider and how events reach it, in priority order. The provider is generic: a
SaaS analytics SDK, a self-hosted product-analytics tool, a customer-data platform, a server-side tracking
library, or a thin in-house wrapper over any of these.

1. **The emit wrapper / client.** A central module that initializes the provider and exposes the function call
   sites use (e.g. a `track` / `logEvent` / `capture` helper). This is the contract; prefer it over scattered
   direct SDK calls.
2. **The event definition.** Any typed enum, union, constant set, or schema that enumerates allowed event
   names. If none exists, the set of distinct names passed at call sites is the de facto catalog.
3. **Enablement / gating.** Where the provider is turned on or off: platform/environment guards, consent or
   opt-out checks, sampling, lazy/optional SDK loading, and dev-vs-prod behavior.
4. **Identity wiring.** Where the user is identified and where user/group properties are set (typically an auth
   listener or session bootstrap).

Record the provider and the wrapper's API. They set the vocabulary for the rest of the doc.

### Phase 2: Extract the event catalog and identity model
Per event, capture from the code:

- **Event name:** exactly as sent.
- **When it fires:** the user action or system condition that triggers the emit, including branch conditions
  (e.g. an event that fires from two mutually exclusive paths with different params).
- **Params:** every parameter sent, its type, and its meaning; note defaults and any param hygiene the wrapper
  applies (e.g. dropping null/undefined, redaction, truncation).
- **Call site(s):** file and (where stable) line for each place the event is emitted.

On the identity side, capture each wrapper beyond `track`: user identify/reset, user/group property setters, and any
screen/page-view logging. Record the purpose of each and whether it is **actually called** and from where.

Cross-check the **definition against the call sites in both directions**:
- **Defined but never fired:** an event name in the enum/schema with no emit call site (dead definition).
- **Fired but undefined:** an emit call site whose name is not in the definition (untyped/ad-hoc event).

### Phase 3: MANDATORY CHECKPOINT, confirm scope before writing
Present the provider, the wrapper API, the full event list, the identity wrappers and their live/dead status,
and the output path. Do not write the document until the user confirms the catalog is complete. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write the document at the output path using the template below. Lead with setup/enablement, then the event
catalog table (one row per event), then the identity/user-properties section. Cite the source file (and line
where stable) for each event and wrapper.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: event names, fire conditions, param names and types, and call sites.
Confirm every defined event maps to at least one live call site and flag those that do not; confirm no emitted
name falls outside the definition and flag those that do. Verify each identity wrapper's live/dead status by
finding (or failing to find) its caller. Ground any example in a real call site. Fix or remove anything not
provable from the code. Prefer "unknown" over a guess.

## Output template

```markdown
---
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# Analytics Events

<1-2 sentence overview: the telemetry provider and what this catalogs.>

**Sources of truth (read these if this doc and the code disagree):**
- <the emit wrapper / analytics client module>
- <the event definition (enum / union / schema), if any>
- <the identify call site>

> <One line: where crash/error telemetry and metrics/tracing live, if separate, and a link. They are out of
> scope for this catalog.>

## Setup and enablement
<How the provider is loaded and initialized; the wrapper API; when it is enabled vs a no-op (platform,
environment, consent, sampling, optional SDK); whether emits are fire-and-forget; param hygiene applied.>

## Event catalog
<One row per event. Cross-checked against actual emit call sites. Treat the file path as canonical if line
numbers drift.>

| Event | When it fires | Params | Call site(s) |
|---|---|---|---|

<Summary line: how many defined events have a live call site; whether any emitted name is outside the
definition.>

## Identity, properties, and screen/page logging
<One row per identity wrapper. Record purpose and live/dead status with the call site (or "no call site").>

| Wrapper | Purpose | Status |
|---|---|---|

## Gotchas for implementers
<multi-path events to segment on, dead definitions vs ad-hoc events, environments where nothing is sent, dropped
params, swallowed errors, and the rule that the call site (not the definition) is the contract.>
```

## Failure conditions

- **No analytics instrumentation found:** state that plainly and stop; do not fabricate an event catalog.
- **No central wrapper or event definition** (only scattered direct SDK calls): build the catalog from the
  distinct emitted names and say there is no single source of truth, so the catalog is call-site-derived.
- **Definition and call sites disagree:** document **both** sides: list defined-but-never-fired events and
  fired-but-undefined events explicitly; do not silently reconcile them.

## Output

A single document at the output path, plus a short summary: events cataloged, identity wrappers documented
(live vs dead), and any defined-but-never-fired or fired-but-undefined events surfaced for follow-up.
