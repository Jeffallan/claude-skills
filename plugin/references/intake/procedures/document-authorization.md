# intake:document-authorization

**Options:** what follows the procedure name in `intake <procedure> ...`, passed on in the brief: an optional root directory to analyze (defaults to the project root).

Produce an authorization reference at `docs/security/authorization.md` (configurable): a precise statement of
*which principal may do what to each object, through which operation*, written for an AI agent or engineer to
rely on as the implementation contract. Document the access rules **exactly as the code enforces them**, and do
not invent a role, claim, or rule the code does not contain. The prose stays neutral. Where enforcement breaks
an access invariant or contradicts stated intent, that place goes to the findings tracker as a finding (or an
Open question when intent can't be settled), and the doc cites its id.

This document owns the join: the access invariants, the access matrix and the channels per protected object.
It cites the facts other docs own (operation ids from the API reference, states from the user model and the
features doc, token properties from the security doc) and never restates them. The *mechanisms* behind the
matrix (verification gates, validation, rate limiting, tokens) belong in the companion security document
produced by `intake:document-security`.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit, the goal-run behavior, and the shape of the principals, invariants, matrix, channels and second pass this command writes.

## When to use

Run once during intake, after `intake:document-api`, `intake:document-user-model`, `intake:document-features`
and `intake:document-security`: the matrix joins their output. Re-run when access rules change (a new route, a
new role or claim, a changed ownership predicate, a new account state). A rerun edits the existing document in
place and keeps hand edits ("Reruns" in `references/intake/rules.md`); operation ids stay stable.

## Skills to load

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the existing access-control code and infer the model
  from how decisions are actually made.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:secure-code-guardian`**: interpret authorization primitives (token claims, ownership
  checks, policy predicates, ACL lookups, queryset scoping) so each matrix cell is technically precise.
- **`fullstack-dev-skills:security-reviewer`**: classify the model (RBAC, ABAC, ReBAC, ACL), check each cell
  against the invariants, and write the findings for cells that break one.

## Workflow

### Read the inputs
Read the docs the matrix joins, each by the section the contract names ("Who owns what" in
`access-control.md`):

- the operation inventory, `## Operations` in `docs/architecture/api-reference.md`;
- the actor states, `## Lifecycle state machine` and `## Blocking states` in `docs/domain/user-model.md`;
- the domain state machines and any stated business rules in `docs/domain/features.md`;
- the token properties, `## Tokens` in `docs/security/security.md`;
- the security-relevant fields, the `Flags` column in `docs/architecture/data-model.md`.

When one is missing, work from the code alone and add an Open question naming the missing doc ("In a goal run"
in `rules.md`). Without the inventory, take the rows from the framework's resolved route table as the contract's
"Operation inventory" describes, label them by method and path, and say in the Open question that the rows
carry no operation ids yet.

### Discover: detect the authorization model (do NOT assume RBAC)
Determine how the codebase actually decides access before documenting anything. Inspect the decision sites
(middleware, guards, decorators, permission classes, policy files, queryset or repository scoping, database
access rules such as row-level security policies, ACL tables) and classify the model.

- **RBAC (role-based).** Decisions read a role or permission (for example `role == "admin"` or
  `hasPermission(...)`), often from a token claim, a join table, or a user field.
- **ABAC (attribute-based).** Decisions evaluate attributes of the subject, resource, action, or environment
  (for example department, tenant, status, time) against a policy.
- **Ownership or relationship-based (ReBAC).** Decisions compare the caller's identifier against a field on the
  resource (`ownerId == caller`, `caller in members`) or against a deterministic resource ID; there is no
  notion of role.
- **ACL (access-control list).** Explicit per-resource grant entries (a stored list of who may do what for each
  resource).
- **A mix.** Most real systems combine these (for example ownership by default with role overrides for an admin
  tier). Document the actual combination and which dimension wins when they overlap.

State the model in one or two sentences. **If there is no role system, say so explicitly** ("there is no
role-based access control; access is decided by ownership and participation") so downstream agents do not assume
a role path that does not exist. If a privileged server context (admin or service-role credentials) bypasses
the rules entirely, note that this is *bypass*, not an elevated role.

### Extract: identity, principals, invariants, and the guard chain per operation
- **Identity and claims basis.** Identify the principal (authenticated user, service account, anonymous) and
  the subject identifier used in decisions (user ID, tenant ID). List exactly which token claims or session
  fields the rules read, and which they pointedly do not.
- **Helper and primitive inventory.** Catalogue the reusable predicates the access rules are composed from (for
  example `isSignedIn()`, `isOwner(x)`, `isMember(list)`, `hasRole(r)`, a policy function, an ACL lookup) with
  each one's definition and meaning. Helpers that govern *document shape* (field validation) rather than
  *authority* belong in the security doc, not here.
- **Principals.** The matrix columns, built as "Principals" in the contract describes: `anonymous`,
  `authenticated`, `owner`, one per role the code checks, and one per blocking state the user model lists, even
  a state the code never checks. Note what credentials each blocking-state column holds.
- **Invariants.** INV-1 to INV-6 from the contract (source "intake default"), plus the project invariants
  `features.md` numbers in `## Project invariants` (`INV-7` onward), cited by id. An access-only invariant
  the code states and `features.md` lacks continues that numbering, citing the code, test, comment or doc
  that states it.
  For every place the code departs from an invariant on purpose, find the intent evidence the contract accepts
  (a comment, a test, a doc, a setting the project chose). A library default is not intent.
- **Guard chain per operation.** For every inventory operation, the checks that actually run, in order:
  authentication, the resolved permission (library defaults included), the object-level check, list scoping,
  the fields the operation accepts, and what each blocking state's old credentials meet on the way in. Use the
  literal predicate from the code, not a paraphrase.
- **Protected objects and their channels.** For each object a principal may own or be denied, every channel
  that returns or changes it and the indirect leaks, as "Channels per protected object" in the contract lists.
- **Server-only and internal resources.** Resources with no client access, written exclusively by privileged
  server code, and the rule or default-deny that enforces this.
- **Default rule.** The catch-all for any operation or resource not explicitly declared (default-deny is the
  safe norm; document whatever it actually is).

### MANDATORY CHECKPOINT: confirm scope before writing
Present the detected model (and the combination and precedence if mixed), the identity and claims basis, the
principal columns, the project invariants with their sources, the operation count from the inventory (the
matrix row count), the protected objects for the channels section, any missing input doc, and the output path.
Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in
`references/intake/rules.md`.

### Write: produce the document
Write the document at the output path using the template below.

1. Fill the matrix: one row per inventory operation, one column per principal, each cell holding the outcome
   and `[x]` ("Access matrix" in the contract). Fill `Fields written` and `List scope`.
2. Check every cell, and every channel, against every invariant. A cell that breaks one with cited intent
   evidence goes in the deviations table under `## Access invariants`. A cell that breaks one without intent
   evidence is a finding: append it to `docs/intake-findings.md` before the doc cites it, in the form
   "Findings from the matrix" in the contract describes (operation ids, principal column, invariant, one
   finding per root cause), and put its id after the cell's status. When intent can't be settled either way,
   add an Open question with a draft answer and cite it in the cell note. No deviating cell stays silent.
3. Write the channels section the same way: each channel's operation ids, whether the ownership rule holds on
   it, and a finding id where it does not.
4. Add a "Gotchas for implementers" section for where authority is decided (for example by a membership array
   versus the resource ID) and for privileged operations that live outside the rules layer.

### Independent second pass
After the matrix is written, run the second pass described in "An independent second pass" in the contract. A
pass that reviews a finished matrix tends to agree with it, so this one derives the cells itself from code that
carries no finding ids.

1. Build a clean copy of the code. Find the commit before the docstring pass, the parent of the first commit
   with the trailer `Intake: intake:document-codebase` (HEAD when there is none), and extract it to a scratch
   folder outside the repo: `git archive <commit> | tar -x -C <scratch>`. Its comments name no findings.
2. Split the inventory into batches of about 60 operations. An agent can't start agents, so return the batches
   to the intake command and stop: for each batch its rows of the inventory (id, method, path, source), plus the
   principal columns, the invariants, the clean copy's path and the installed source of any library that mounts
   routes. The intake command starts one fresh `code-reader` per batch, all in one message, with only that, never the matrix, the
   findings tracker or the intake branch, and asks it for the outcome of every cell in its batch with the code it
   relied on, and for a separate list of any other defect it noticed. It resumes you with their reports.
3. Compare the returned cells with the matrix. Wording that differs but means the same outcome is not a disagreement.
   For each real disagreement, check the code and probe the running app; correct the cell the matrix got wrong,
   and file a deviation not yet filed as a finding (or add its rows to the finding with the same root cause).
4. Probe each defect on its other list the same way and file the ones that hold.
5. Delete the scratch copy. Record in the checklist note: `second pass: <C> cells derived, <D> disagreements,
   <M> matrix cells corrected, <O> other defects reported, <K> new findings`.

### Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`):
wording only, never a claim. Then audit:

- The matrix row count equals the inventory's operation count, and every principal column is present.
- Every cell's outcome matches the code's guard chain for that operation and principal, library defaults
  included.
- Every cell that breaks an invariant carries a finding id or an Open question, and every deviation listed
  under `## Access invariants` cites its intent evidence.
- Every project invariant cites its source, and every channel's operation ids exist in the inventory.
- The model classification matches every decision site (a single role check anywhere means the model is not
  pure ownership), and every `path::symbol` citation resolves.

Fix or remove anything not provable from the code. Prefer "denied", "server-only", or "unknown" over a guess.

## Output template

```markdown
---
command: intake:document-authorization
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [architecture/api-reference.md, domain/user-model.md, domain/features.md, security/security.md, <others>]
---
# Authorization and Access Control

<1-2 sentence overview: who may do what, through which operation, and the model in one line.>

The authorization model is **<RBAC / ABAC / ownership-based / ACL / the actual mix>**. <One or two sentences
on how decisions are made and which dimension wins when they overlap.>

> <If applicable, the explicit negative statement, for example "There is no role-based access control: no
> roles, no admin tier, no privilege claims. Access is decided by ownership and participation.">

**Sources of truth (read these if this doc and the code disagree):**
- <authoritative access-control file>: the access definition for every operation.
- <privileged server file>: operations that bypass the rules layer under elevated credentials.

> Related: the [operation inventory](../architecture/api-reference.md#operations), the
> [blocking states](../domain/user-model.md#blocking-states), the [security mechanisms](./security.md) and the
> [data model](../architecture/data-model.md).

## Identity model
<the principal, the subject identifier, and exactly which claims/fields decisions read>

## Authorization primitives
| Helper / primitive | Definition | Meaning |
|---|---|---|
| <name> | `<path::symbol>` | <what it asserts> |

## Principals
| Column | Who | Credentials held |
|---|---|---|
| anonymous | no credentials | none |
| <blocking state> | an account in `<state>` ([user model](../domain/user-model.md#blocking-states)) | <the session, token or key it held before entering the state> |

## Access invariants
| Id | Invariant | Source |
|---|---|---|
| INV-1 ... INV-6 | <the defaults from the intake access-control contract> | intake default |
| INV-7 | <project rule> | `<path::symbol>` or <doc> |

Deviations with intent evidence:

| Invariant | Operations | Principal | Intent evidence |
|---|---|---|---|
| <INV-n> | <OP ids> | <column> | `<path::symbol>`, <test, comment, doc or chosen setting> |

## Access matrix
Rows: <N> operations from the [inventory](../architecture/api-reference.md#operations) (all of them). Cells:
expected outcome, then status.

| Op | anonymous | authenticated | owner | <role> | <blocking state> | Fields written | List scope |
|----|-----------|---------------|-------|--------|------------------|----------------|------------|
| OP-<nnn> | <outcome> [x] | <outcome> [x] | <outcome> [x] F-<nnn> | ... | ... | <fields> | <scope> |

<row notes: protected fields an operation should never accept, `n/a` reasons, Open question references>

## Channels per protected object
### <object>
| Channel | Operations | Ownership rule holds? |
|---|---|---|
| <detail, list, search, filter, ordering, nested include, export, file URL, bulk, socket, webhook, job, older version> | <OP ids> | <yes / no: F-<nnn>> |

Indirect leaks: <filtering or ordering on unreadable fields; 403 versus 404 or error text revealing existence>

## Server-only and internal resources
<resources with no client access, written only by privileged server code, and what enforces that>

## Default rule
<the catch-all posture for undeclared operations and resources>

## Gotchas for implementers
<where authority is actually decided; privileged operations outside the rules layer; mixed-model precedence>
```

## Failure conditions

- **No access-control code found.** State that plainly, fill every cell from what does run (often `allow`), and
  check those cells against the invariants like any other. Do not fabricate a model.
- **Misclassifying the model.** Do not default to RBAC. If decisions never read a role, the model is not RBAC;
  document what the code does. If even one decision reads a role or claim, the model includes that dimension;
  say so and document the combination.
- **Rules and code disagree** (for example a declarative policy that the application path contradicts).
  Document **both**, flag the discrepancy and add a finding; do not silently pick one.
- **A matrix shorter than the inventory.** Every operation gets a row, a library's routes included. A row you
  can't fill holds `[x]` with the reason in its note; it is never dropped.
- **A library default read as intent.** A default the project never set is not evidence of intent. The cell
  stays a deviation until a comment, test, doc or chosen setting says otherwise.
- **Auditing in the doc's voice.** Documenting stays neutral: no severity, no "should" in the doc. Every cell
  that breaks an invariant without intent evidence still becomes a finding or an Open question; the finding
  carries the severity and the recommendation, and the doc cites its id.

## Output

A single document at the output path, plus a short summary: the detected model, the principal columns, the
matrix row count against the inventory count, the project invariants, the findings and Open questions raised
from deviating cells and channels, the second pass's counts, and any rule/code discrepancies.
