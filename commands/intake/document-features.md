---
name: document-features
description: Generate an accurate, agent-readable feature catalog (what the application does today, grouped by area, with user-visible behavior and implementing files, plus the state machines of domain entities and the business invariants the features imply) by reverse-engineering the code's behavioral surfaces.
argument-hint: "[directory]"
---

# intake:document-features

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce a feature catalog at `docs/domain/features.md` (configurable): what the application **actually does today**,
grouped by functional area, each entry giving a one-line description, the user-visible behavior, and the files that
implement it. Written for an AI agent or engineer to use as the map from capability to code. **Document only
features present in the code; anything not in the code is not built. Never list aspirational or planned features.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit, the goal-run behavior, and the access-control contract this command feeds: the operation ids, the invariants, and the shape of "Transitions and blocking states". This command owns `## State machines` in that contract, and the project invariants from `INV-7` onward.

The document stays neutral: it describes what the code does. Where the code breaks an invariant from the contract or one this command records, or contradicts its own stated intent (a type, a comment, a test, another doc), append a finding to `docs/intake-findings.md` before writing the doc, and cite its id where the doc describes that behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when features are added or removed (a rerun edits the existing
document in place and keeps hand edits; see "Reruns" in `references/intake/rules.md`).

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer features from screens / routes / services / handlers; identify undocumented
  behavior.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:feature-forge`**: frame each capability in user-facing terms (what it does and the user-visible behavior),
  using a consistent requirements vocabulary.

## Workflow

### Phase 1: Discover the behavioral surfaces
Enumerate every place behavior is exposed, in priority order (the file types differ by stack):
1. **UI entry points:** screens / pages / routes / views (e.g. mobile screens, web pages, server-rendered views
   in a Next.js / Rails / Django / Spring app).
2. **Client write paths and the API / RPC handlers they call:** the actions that mutate state.
3. **Server-only / background features:** scheduled jobs, queue consumers, database/storage triggers, serverless
   functions, webhooks; behavior with no UI is still a feature.
4. **Reusable components / modules** that embody a discrete capability.

Group the discovered surfaces into functional **areas** by what the user is trying to accomplish (e.g. Account &
Auth, Profile, Discovery, Messaging, Notifications, Safety & Trust, Billing, Admin).

### Phase 2: Extract per-feature detail
Per feature, capture: a **one-line description** of what it does; the **user-visible behavior** (what the user
sees and triggers, and which states are handled: empty, loading, error); and the **exact files** that implement
it across UI, service, and server. Note cross-cutting behaviors (analytics events, guards, rate limits) where the
code shows them. Document only behavior the code proves.

### Phase 3: Map domain state machines and invariants
**Entities with a status.** Find every domain entity whose behavior depends on a stored state (orders, invoices,
subscriptions, bookings, payouts, tickets, documents under review): a status or state column, an enum, a set of
timestamps or booleans that together mean a state. The primary actor's states belong to `intake:document-user-model`;
link to them rather than repeating them.

**Derive transitions from the writers, not from the happy path.** For each state field, search for every place
that writes it and record each write as a transition. Cover every kind of writer:
- app code: handlers, services, model methods, serializers or forms that accept the field;
- library code, including the routes a library mounts (a payment or subscription library's webhooks, an admin
  site, a workflow or state-machine package): read the library's handlers for the version the lockfile pins;
- the admin site and any back-office or management command;
- background jobs, scheduled tasks and queue consumers (expiry, auto-cancel, retries);
- signals, hooks, callbacks and database triggers;
- migrations and data fixes that set the field.

For each transition, find the operation ids that reach it in the `## Operations` inventory of
`docs/architecture/api-reference.md`, and who may call them. A writer with no route gets `none` in Routes and names
its trigger. A route that reaches a writer but is missing from the inventory goes into `api-reference.md` in its
own commit ("Output layout" in `rules.md`). When the inventory doesn't exist yet, work from the code and add an
Open question saying so. Note each terminal or locked state (paid, cancelled, refunded, archived) and whether any
writer still changes the entity or its amounts once it is there.

A transition with no named actor allowed to make it, or a route that reaches a transition its actor list omits,
is an **INV-6** finding unless the doc cites evidence of intent. When intent can't be settled, add an Open
question with a draft answer.

**Project invariants.** Write down the rules the features imply that the default invariants don't cover: a
booking can't overlap another, a refund never exceeds the charge, a quantity is never negative, a price is set by
the server and never by the client, a discount applies once, a state can't be skipped. Number them `INV-7` onward,
stable across reruns. Each one cites the evidence that the project intends it (a validator, a constraint, a test,
a comment, a doc, a UI rule) and lists the operation ids that must uphold it. Record only invariants with such
evidence; a rule you merely expect goes to Open questions with a draft answer. Then check each invariant against
every operation that can break it, including concurrent requests, repeated requests and requests that skip a
step. A path that breaks it is a finding citing the invariant id. `intake:document-authorization` and
`intake:testing-owasp` test these invariants by id.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the area grouping, the feature count per area, the
entities with a status and their writer counts, the project invariants, the findings to append, and the output
path. Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Append the findings first, with the next free ids, then write the document at the output path using the template
below.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify each feature against the code: the named implementing files exist and contain the described behavior;
the user-visible behavior matches what the code does (including the empty/loading/error states claimed). Confirm
every summary-table row maps to a subsection and vice versa. Remove any feature you cannot point to in code.
For each state machine, re-run the writer search per state field and confirm every write site maps to a
transition row, each row's routes exist in the inventory, and its callers match the guard on that route. For each
project invariant, confirm the cited evidence exists and every breaking path is a finding id in the doc. Prefer
omission over invention.

## Output template

```markdown
---
command: intake:document-features
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# Features

<1-2 sentence overview: the application and that this catalogs only what the code does today.>

**Sources of truth:** <UI entry points / service write paths / server-only handlers / reusable components to trust over this doc>

## Summary
| Feature | Area | Key files |
|---|---|---|
| <feature> | <area> | `<path>` |

## <Area>
### <Feature>
<one-line: what it does>
<user-visible behavior: what the user sees and triggers, and the states handled>
Implemented in `<file>` (+ `<service>`, `<server handler>` where applicable).

## State machines
### <Entity>
State field(s): `<model>.<field>`; states: <list, terminal ones marked>

| From | To | Trigger | Routes | Who may call | Mechanism |
|------|----|---------|--------|--------------|-----------|
| <state> | <state> | <trigger> | <OP ids from ../architecture/api-reference.md, or none> | <principal and what it must hold> | `path::symbol` |

<one row per writer of a state field: app, library, admin, job, signal or hook, migration; finding ids where a row breaks INV-6>

## Project invariants
| Id | Invariant | Evidence of intent | Operations that must uphold it | Findings |
|----|-----------|--------------------|-------------------------------|----------|
| INV-7 | <rule> | `path::symbol` (validator, constraint, test, comment, doc) | <OP ids> | <F-ids or none> |

## Gotchas for implementers
<cross-cutting surprises: non-obvious enforcement points, async/eventually-consistent behavior, split responsibilities>
```

## Failure conditions

- **No discernible feature surface** (a library or SDK with no application): state that plainly and stop; do not
  invent product features.
- **A surface exists but its behavior is unreadable** (heavy dynamic dispatch, generated or obfuscated code):
  list the feature, mark its behavior **unverified**, and point to the entry file rather than guessing.
- **No domain entity has a status:** keep `## State machines` with one line saying so and the search that showed
  it; never invent states.

## Output

A single document at the output path, plus a short summary: features documented, areas covered, the state
machines and transitions recorded, the project invariants, the finding ids appended, and anything omitted as
unverifiable.
