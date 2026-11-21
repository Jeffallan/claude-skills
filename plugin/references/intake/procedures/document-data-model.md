# intake:document-data-model

**Options:** what follows the procedure name in `intake <procedure> ...`, passed on in the brief: an optional root directory to analyze (defaults to the project root).

Produce a data-model reference at `docs/architecture/data-model.md` (configurable): a precise map of how the
project persists data, written for an AI agent or engineer to rely on as the implementation contract. **Document
only what the code proves. Never invent a field, constraint, or relationship.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. The first two set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior. The third names what this command owns for the access matrix ("Who owns what"): the `Flags` column of each entity table.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when the schema changes (a rerun edits the existing document in place and keeps hand edits; see "Reruns" in `references/intake/rules.md`).

## Skills to load

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the existing persistence layer; infer entities and relationships from code.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **The project's language/data skill** for the schema's type system: choose by stack, e.g. `fullstack-dev-skills:typescript-pro`,
  `fullstack-dev-skills:python-pro`, `fullstack-dev-skills:sql-pro`, `fullstack-dev-skills:postgres-pro`, `fullstack-dev-skills:django-expert`, the ORM's skill.
- **`fullstack-dev-skills:architecture-designer`**: produce the entity-relationship diagram.

## Workflow

### Phase 1: Discover the persistence layer
Identify where and how data is stored, in priority order:
1. Schema / migration files (SQL DDL, `schema.prisma`, ORM model classes, migrations).
2. Type/interface definitions describing stored shapes (a domain types module).
3. Access/security rules that enumerate stores and validate fields (e.g. Firestore `*.rules`, Postgres RLS).
4. The data-access layer (repositories / services / DAOs) for how records are written and how IDs are formed.

Record the storage technology (relational, document, key-value, graph). It sets the vocabulary: tables/rows vs
collections/documents.

### Phase 2: Extract entities and fields
Per entity: its identifier / primary key and **ID convention**, every field with its type, and the
**constraints actually enforced** (validation, nullability, ranges, enums, immutability). If the code distinguishes
**stored shapes** from **view models / DTOs**, capture both and the mapping between them.

Mark the fields the access matrix and the state machines depend on, in a `Flags` column. A field may carry several
flags:

- `state`: a field that holds a lifecycle or status value (a status enum, an active, verified or locked flag, a
  soft-delete or archived timestamp, an expiry stamp).
- `owner`: a key that ties the record to the account or tenant it belongs to (an owner, creator, user, account,
  organization or tenant foreign key).
- `privilege`: a field that grants rights (a role, a staff or admin flag, a permission set, a group membership, a
  plan or tier that unlocks features).
- `money`: an amount, price, balance, credit, quantity or count whose value a caller could profit from changing.

Flag by what the field does, not by its name: a `level` integer that gates admin pages is `privilege`. Note in the
row which code writes each flagged field (the serializer, form or handler that accepts it, a signal, a job), so
later commands can check whether a caller can set it.

### Phase 3: Extract relationships and integrity rules
Foreign keys / references and cardinality, join or lookup patterns, cascade behavior (e.g. delete cascades),
uniqueness guarantees (including those enforced by deterministic IDs), and denormalized/duplicated fields together
with their canonical source.

### Phase 4: Diagram
Produce a Mermaid `erDiagram` of entities, key attributes, and relationships with cardinality.

### Phase 5: Enumerations and validation
Collect enums / allowed-value sets, where each is defined, and where it is re-validated (application code vs
database/rules). Summarize field-level constraints.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the storage technology, the entity list, the
flagged fields, and the output path. Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 6: Write
Write the document at the output path using the template below.

Docs describe the schema neutrally. Where enforcement breaks an access invariant (`references/intake/access-control.md`,
"Access invariants") or contradicts stated intent (a type, a comment, a test, another doc), append a finding to the
tracker before writing the doc, and cite its id in the field's Notes. A flagged field that a write path accepts from
the caller with no check is such a case, and so is a constraint the type promises but the store never enforces.

### Phase 7: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: field names and types, enforced constraints, ID conventions, relationships,
cascade behavior, and every flag (search the models again for state, ownership, privilege and money fields left
unflagged). Ground any example in a real call site. Fix or remove anything not provable from the code.
Prefer "unknown / not enforced" over a guess.

## Output template

```markdown
---
command: intake:document-data-model
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# Data Model

<1-2 sentence overview: the storage technology and what this documents.>

**Sources of truth:** <schema / types / rules / data-access files to trust over this doc>

## Entity relationship diagram
` ` `mermaid
erDiagram
  ...
` ` `

## View models vs stored shapes   <!-- include only if the project distinguishes them -->
<mapping table: stored shape -> view model(s), with notes>

## Entities
### <entity / table / collection> (`<id convention>`)
<purpose; what writes it; one-line access pointer to the authorization doc>
| Field | Type | Constraint | Flags | Notes |
|---|---|---|---|---|
| <name> | <type> | <enforced constraint> | <state / owner / privilege / money, or blank> | <who writes it; finding id> |

## Enumerations
<type -> allowed values; where defined and where re-validated>

## Relationships and integrity rules
<FKs, cardinality, cascade behavior, uniqueness, denormalized fields + canonical source>

## Gotchas for implementers
<query patterns, server-only/internal stores, sync requirements, async side effects>
```

## Failure conditions

- **No persistence layer found**: state that plainly and stop; do not fabricate a schema.
- **Schema and code disagree** (e.g. type definitions vs database rules): document **both** and flag the
  discrepancy; do not silently pick one.

## Output

A single document at the output path, plus a short summary: entities documented, relationships captured, flagged
fields by flag, finding ids raised, and any discrepancies or unknowns surfaced for follow-up.
