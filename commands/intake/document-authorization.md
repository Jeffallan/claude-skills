---
name: document-authorization
description: "Generate an accurate, agent-readable authorization reference by first detecting the project's real authorization model (RBAC, ABAC, ownership/relationship-based, ACL, or a mix) and then documenting the identity/claims basis, the helper/primitive inventory, and a per-resource access matrix grounded in code."
argument-hint: "[directory]"
---

# intake:document-authorization

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce an authorization reference at `docs/security/authorization.md` (configurable): a precise statement of
*who may read and write each resource*, written for an AI agent or engineer to rely on as the implementation
contract. This is a **documentation** command, not a security audit. Document the access rules **exactly as the
code enforces them**. Do not hunt for privilege-escalation bugs, and do not invent a role, claim, or rule the
code does not contain.

This document covers *who may do what* (the access matrix). The *mechanisms* that back it (verification gates,
validation, rate limiting, moderation) belong in the companion security document produced by
`intake:document-security`. Cross-link rather than duplicate.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when access rules change (a new resource, a
new role/claim, a changed ownership predicate). This command is idempotent and overwrites the document.

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the existing access-control code and infer the model
  from how decisions are actually made.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:secure-code-guardian`**: interpret authorization primitives (token claims, ownership
  checks, policy predicates, ACL lookups) so each matrix cell is technically precise.
- **`fullstack-dev-skills:security-reviewer`**: use its model vocabulary (RBAC, ABAC, ReBAC, ACL) to classify
  the model correctly and to confirm no resource is missed. Use it to classify, not to file findings.

## Workflow

### Discover: detect the authorization model (do NOT assume RBAC)
**This is the critical first step.** Determine how the codebase actually decides access before documenting
anything. Inspect the decision sites (middleware, guards, decorators, policy files, database access rules such
as row-level security policies, ACL tables) and classify the model.

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

### Extract: identity basis, primitives, and per-resource rules
- **Identity and claims basis.** Identify the principal (authenticated user, service account, anonymous) and
  the subject identifier used in decisions (user ID, tenant ID). List exactly which token claims or session
  fields the rules read, and which they pointedly do not.
- **Helper and primitive inventory.** Catalogue the reusable predicates the access rules are composed from (for
  example `isSignedIn()`, `isOwner(x)`, `isMember(list)`, `hasRole(r)`, a policy function, an ACL lookup) with
  each one's definition and meaning. Note distinctly any helpers that govern *document shape* (field
  validation) rather than *authority*; those belong in the security doc, not here.
- **Per-resource rules.** For every resource, table, collection, or route, capture the exact condition for
  **read, create, update, delete** (or the verbs the system uses). Use the literal predicate from the code, not
  a paraphrase. Mark actions that no client may perform as `false` or denied, and note where they happen
  instead (for example server-only).
- **Server-only and internal resources.** List resources with no client access, written exclusively by
  privileged server code, and the rule or default-deny that enforces this.
- **Default rule.** The catch-all for any resource not explicitly declared (default-deny is the safe norm;
  document whatever it actually is).

### MANDATORY CHECKPOINT: confirm scope before writing
Present the detected model (and the combination and precedence if mixed), the identity and claims basis, the
resource list to be put in the matrix, the server-only resources, and the output path. Do not write the
document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Write: produce the document
Write the document at the output path using the template below. Lead with the model statement and the identity
basis, then the primitive inventory, then the access matrix (one row per resource), then server-only resources
and the default rule. Quote the real conditions in matrix cells. Add a "Gotchas for implementers" section for
where authority is decided (for example by a membership array versus the resource ID) and for privileged
operations that live outside the rules layer.

### Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every matrix cell against the code: the exact predicate for each verb on each resource, the claims
actually read, and the default rule. Confirm the model classification matches every decision site (a single
role check anywhere means the model is not pure ownership). Confirm each file and line pointer resolves. Fix or
remove anything not provable from the code. Prefer "denied", "server-only", or "unknown" over a guess.

## Output template

```markdown
---
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# Authorization and Access Control

<1-2 sentence overview: that this documents the per-resource access matrix, and the model in one line.>

The authorization model is **<RBAC / ABAC / ownership-based / ACL / the actual mix>**. <One or two sentences
on how decisions are made and which dimension wins when they overlap.>

> <If applicable, the explicit negative statement, for example "There is no role-based access control: no
> roles, no admin tier, no privilege claims. Access is decided by ownership and participation.">

**Sources of truth (read these if this doc and the code disagree):**
- <authoritative access-control file>: the complete access definition for every resource.
- <privileged server file>: operations that bypass the rules layer under elevated credentials.

> Related: the [security mechanisms](./security.md) and the [data model](../architecture/data-model.md).

## Identity model
<the principal, the subject identifier, and exactly which claims/fields decisions read>

## Authorization primitives
| Helper / primitive | Definition | Meaning |
|---|---|---|
| <name> | <code> | <what it asserts> |

## Access matrix
<conditions are the literal predicates from the code; `false` means no client may ever do it>

| Resource | Read | Create | Update | Delete |
|---|---|---|---|---|
| <resource> (`<location>`) | <condition> | <condition> | <condition> | <condition> |

<notes on specific rows where the predicate needs explanation>

## Server-only and internal resources
<resources with no client access, written only by privileged server code, and what enforces that>

## Default rule
<the catch-all posture for undeclared resources>

## Gotchas for implementers
<where authority is actually decided; privileged operations outside the rules layer; mixed-model precedence>
```

## Failure conditions

- **No access-control code found.** State that plainly and stop; do not fabricate a model or matrix.
- **Misclassifying the model.** Do not default to RBAC. If decisions never read a role, the model is not RBAC;
  document what the code does. If even one decision reads a role or claim, the model includes that dimension;
  say so and document the combination.
- **Rules and code disagree** (for example a declarative policy that the application path contradicts).
  Document **both** and flag the discrepancy; do not silently pick one.
- **Scope creep into auditing.** If you find yourself rating severity or recommending tightening, stop; that is
  a separate security-review task. Document the rule as built.

## Output

A single document at the output path, plus a short summary: the detected model, resources in the matrix,
server-only resources, the default rule, and any model ambiguities or rule/code discrepancies surfaced for
follow-up.
