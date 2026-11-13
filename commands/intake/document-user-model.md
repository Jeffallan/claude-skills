---
name: document-user-model
description: Generate an accurate, agent-readable model of the application's primary actor (representations, identity, lifecycle state machine, completeness rules, account lifecycle) by reverse-engineering the auth and profile layers.
argument-hint: "[directory]"
---

# intake:document-user-model

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce a primary-actor reference at `docs/domain/user-model.md` (configurable): a precise account of the
application's **principal entity**, the actor that authenticates, owns data, and drives the main flows, written
for an AI agent or engineer to rely on as the implementation contract. Cover the actor's representations, its
identity, the lifecycle states that gate what it can do, the completeness rules, and the account lifecycle. **An
application may have several actor types** (e.g. customer and vendor, rider and driver, patient and clinician);
document the primary one here and note any co-equal principals for a separate run. **Document only what the code
proves. Never invent a representation, field, state, or transition.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when the actor model, auth flow, or lifecycle
changes (this command is idempotent; it overwrites the document).

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the actor model from the auth, profile, and routing layers; infer
  representations, states, and gates from code.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **The project's language skill** for the actor's type system, chosen by stack, e.g. `fullstack-dev-skills:typescript-pro`,
  `fullstack-dev-skills:python-pro`, `fullstack-dev-skills:kotlin-specialist`, `fullstack-dev-skills:swift-expert`, `fullstack-dev-skills:csharp-developer`.
- **`fullstack-dev-skills:architecture-designer`**: produce the lifecycle state-machine diagram.

## Workflow

### Phase 1: Discover the primary actor
Identify the central domain entity: the one that logs in, owns records, and is referenced as the join key
elsewhere. In priority order:
1. The authentication / identity layer: who logs in and what stable identifier the system assigns (an auth
   provider subject ID, a session principal, a database primary key).
2. The stored representation(s) of the actor: a profile record, account row, or document.
3. Type / interface / model definitions that project the stored record into views (a public view others see, an
   own/editable view, the canonical stored shape, DTOs).
4. The routing / guard layer that gates behavior on actor state (auth presence, verification, completeness, role).

If the codebase has more than one co-equal principal, pick the primary actor for this document and list the others
to defer (see Failure conditions).

### Phase 2: Extract representations, identity, and rules
- **Representations:** the same stored record is often projected into multiple shapes. Capture each, where it is
  used, and which fields it carries versus omits. State whether the split is **enforced server-side** or is only a
  **client-side convention** (a frequent and dangerous mismatch).
- **Identity:** the stable key that identifies the actor and where it is assigned; that it is the join key across
  other entities; the authentication method(s) the code actually supports (e.g. password, OAuth/social, magic
  link, phone). Distinguish identity from mutable presentation fields (a display name is not a key).
- **Completeness / validation rules:** the gate(s) that decide whether an actor is "ready" (e.g. a
  profile-complete check), the exact conditions, **where each is enforced**, and any place it is **not** enforced.
  Note when the on-write validation is a stricter superset of the readiness gate.

### Phase 3: Diagram the lifecycle state machine
Identify the states the actor moves through (e.g. unauthenticated, unverified, incomplete, active, suspended,
deleted) and the runtime signals that define each. Produce a Mermaid `stateDiagram-v2` whose transitions are
labeled by trigger. Record, per transition, the mechanism and the **enforcement point**, and flag any gate that is
bypassable.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the chosen primary actor (and any co-actors
deferred), the list of representations, the identified states, and the output path. Do not write the document
until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write the document at the output path using the template below.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: which fields each representation carries, the identity key and where it is
assigned, the supported auth methods, every completeness condition and its enforcement point, every state and its
runtime condition, and every transition's trigger and mechanism. Re-trace the account-deletion cascade against the
teardown code. Ground any example in a real call site. Flag any documented boundary the code does not actually
enforce. Prefer "unknown / not enforced" over a guess.

## Output template

```markdown
---
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# <Actor> Model

<1-2 sentence overview: the primary actor, its representations, and that this documents its lifecycle.>

**Sources of truth:** <auth layer / type definitions / completeness gate / routing guard / deletion path files to trust over this doc>

## Representations
<table: representation -> type/shape, where used, fields carried vs omitted; mark enforced server-side vs client-side convention>

## Identity
<the stable key; how and where assigned; its use as the join key; supported authentication method(s); mutable presentation fields that are NOT identity>

## Lifecycle state machine
` ` `mermaid
stateDiagram-v2
  ...
` ` `
### States
<table: state -> runtime condition -> what it grants -> where defined>
### Transitions
<table: from -> to, trigger, mechanism / enforcement point>

## Completeness and validation rules
<the readiness gate(s): exact conditions, where enforced, where NOT enforced; how on-write validation differs from the gate>

## Account lifecycle
<creation, verification, suspension/reactivation if present, and deletion: what is purged, in what order, server-side vs client-side>

## Gotchas for implementers
<convention-vs-enforcement mismatches, gates the router does not check, legacy-document tolerance, identity-misuse pitfalls>
```

## Failure conditions

- **No identifiable actor or auth layer:** state that plainly and stop; do not invent an identity model.
- **Multiple co-equal principals:** document the primary actor, list the others, and note that the command should
  be re-run per actor; do not merge distinct actor models into one.
- **Representation and enforcement disagree** (e.g. a "private" view whose fields the access rules still expose):
  document **both** and flag the discrepancy; never present a client-side convention as access control.

## Output

A single document at the output path, plus a short summary: the actor documented, representations captured, the
count of states and transitions, and any discrepancies or unknowns surfaced for follow-up.
