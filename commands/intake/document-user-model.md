---
name: document-user-model
description: Generate an accurate, agent-readable model of the application's primary actor (representations, identity, lifecycle state machine with every transition's routes and callers, blocking states, completeness rules, account lifecycle) by reverse-engineering the auth and profile layers.
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

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit, the goal-run behavior, and the access-control contract this command feeds: the operation ids, the invariants, and the shape of "Transitions and blocking states". This command owns `## Lifecycle state machine` and `## Blocking states` in that contract.

The document stays neutral: it describes what the code does. Where the code breaks an invariant from the contract, or contradicts its own stated intent (a type, a comment, a test, another doc), append a finding to `docs/intake-findings.md` before writing the doc, and cite its id where the doc describes that behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when the actor model, auth flow, or lifecycle
changes (a rerun edits the existing document in place and keeps hand edits; see "Reruns" in `references/intake/rules.md`).

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

### Phase 3: Derive the lifecycle state machine and blocking states
Identify the states the actor moves through (e.g. unauthenticated, unverified, incomplete, active, suspended,
deleted) and the stored fields and runtime signals that define each (an active flag, a status column, a
verification timestamp, a deletion marker). The `Flags` column of `docs/architecture/data-model.md` names the
security-relevant fields; start there.

**Derive transitions from the writers, not from the happy path.** For each state field, search for every place
that writes it and record each write as a transition. Cover every kind of writer:
- app code: handlers, services, model methods, serializers or forms that accept the field;
- library code, including the routes a library mounts (account activation, password reset, email confirmation,
  social login, an admin site): read the library's handlers for the version the lockfile pins;
- the admin site and any back-office or management command;
- background jobs, scheduled tasks and queue consumers;
- signals, hooks, callbacks and database triggers;
- migrations and data fixes that set the field.

A route that writes the field through a library is a transition even when no app code names it. For each
transition, find the operation ids that reach it in the `## Operations` inventory of
`docs/architecture/api-reference.md`, and who may call them (the principal, plus what they must hold: a session,
an emailed link, a staff flag). A writer with no route (a job, a migration, a signal) gets `none` in Routes and
names its trigger. A route that reaches a writer but is missing from the inventory goes into `api-reference.md`
in its own commit ("Output layout" in `rules.md`). When the inventory doesn't exist yet, work from the code and
add an Open question saying so.

**Blocking states.** A blocking state is one the code or its intent says should stop the actor (deactivated,
unverified, suspended, banned, deleted, locked). For each one, record:
- the operations still allowed in it, by operation id, and the check that allows or refuses them (or that no
  check exists);
- every way out of it: each transition leaving the state, with its routes and who may call them;
- the credentials that survive entering it: sessions, access and refresh tokens, API keys, password-reset,
  activation, invite and email-change links. A credential survives when the system still accepts it after the
  state change; check both the code that runs on entry (does it revoke anything?) and the code that runs on
  each later request (does authentication check the state?).

Record the findings as you go, under the contract's invariants:
- A self-service way out of a blocking state, or a credential that survives entering it, is an **INV-2**
  finding unless the doc cites evidence of intent (a comment, a test, a doc, a setting the project chose).
  "The library does it by default" is not evidence of intent.
- A transition with no named actor allowed to make it, or a route that reaches a transition its actor list
  omits, is an **INV-6** finding.
- When intent can't be settled either way, add an Open question with a draft answer instead.

Produce a Mermaid `stateDiagram-v2` whose transitions are labeled by trigger, and record per transition the
mechanism and the **enforcement point**.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the chosen primary actor (and any co-actors
deferred), the list of representations, the state fields with their writer counts, the identified states (blocking
ones marked), the findings to append, and the output path. Do not write the document until the user confirms. In a
goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Append the findings first, with the next free ids, then write the document at the output path using the template
below. Each blocking state named here becomes a principal column in the access matrix
(`intake:document-authorization`), so use one stable name per state.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: which fields each representation carries, the identity key and where it is
assigned, the supported auth methods, every completeness condition and its enforcement point, every state and its
runtime condition, and every transition's trigger and mechanism. Re-run the writer search for each state field
and confirm every write site maps to a transition row; confirm each row's routes exist in the inventory and its
callers match the guard on that route. For each blocking state, re-check the allowed operations, the ways out and
the surviving credentials against the code. Confirm every INV-2 or INV-6 break is either a finding id in the doc
or carries cited evidence of intent. Re-trace the account-deletion cascade against the teardown code. Ground any example in a real call site. Flag any documented boundary the code does not actually
enforce. Prefer "unknown / not enforced" over a guess.

## Output template

```markdown
---
command: intake:document-user-model
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
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
| From | To | Trigger | Routes | Who may call | Mechanism |
|------|----|---------|--------|--------------|-----------|
| <state> | <state> | <trigger> | <OP ids from ../architecture/api-reference.md, or none> | <principal and what it must hold> | `path::symbol` |

<one row per writer of a state field: app, library, admin, job, signal or hook, migration; finding ids where a row breaks INV-6>

## Blocking states
### <state>
- **Operations still allowed:** <OP ids, and the check that allows them or "no check">
- **Ways out:** <each transition leaving the state: routes, who may call, finding id or cited intent>
- **Credentials that survive entry:** <each credential type, survives or revoked, by `path::symbol`; finding id or cited intent>

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
count of states, transitions (with the writers searched per state field) and blocking states, the finding ids
appended, and any discrepancies or unknowns surfaced for follow-up.
