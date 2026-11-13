---
name: document-security
description: "Generate an accurate, agent-readable security-mechanisms reference (defense layers, authentication/verification gates, input validation, rate limiting, content moderation, secrets/attestation status, abuse controls, deny-by-default) by reverse-engineering what the code actually enforces."
argument-hint: "[directory]"
---

# intake:document-security

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce a security-mechanisms reference at `docs/security/security.md` (configurable): a precise map of the
controls that protect the system, written for an AI agent or engineer to rely on as the implementation
contract. This is a **documentation** command, not a security audit. Describe each mechanism **as it is
actually implemented** (what enforces it, where, and whether it is authoritative). Do not hunt for, rank, or
speculate about vulnerabilities, and do not invent a control the code does not contain.

This document covers the *mechanisms* (what enforces safety and where). The question of *who may read or write
each resource* (the access matrix) belongs in the companion authorization document produced by
`intake:document-authorization`. Cross-link the two rather than duplicating.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when the security surface changes (new auth
flow, new validation layer, a moderation or rate-limit change). This command is idempotent and overwrites the
document.

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the existing enforcement code; infer the layers and
  where each control lives.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:security-reviewer`**: use its knowledge of control categories to confirm the
  inventory is complete (auth, validation, rate limiting, moderation, attestation, abuse controls,
  default-deny). Use it to enumerate *what to look for*, not to file findings against the project.
- **`fullstack-dev-skills:secure-code-guardian`**: interpret how each mechanism is implemented (token checks,
  parameterized queries, input validation, header policies) so the description is technically precise.

## Workflow

### Discover: locate the enforcement points
Identify where security is enforced, in priority order. The right places vary by stack.

1. **Authoritative, synchronous gates.** Whatever decides a request before it commits: API middleware or
   guards, authentication and session checks, database-side access rules (for example row-level security
   policies or declarative database rules), framework authorization decorators, input-validation schemas.
2. **Asynchronous or out-of-band enforcement.** Background workers, queue consumers, database triggers,
   serverless functions, or scheduled jobs that enforce limits or scrub content *after* a write.
3. **Privileged server paths.** Code that runs with elevated credentials and bypasses the normal request
   guards (admin/service-role keys, internal-only endpoints, cascade or cleanup jobs), and the framework's admin
   site: every model it registers and which fields its list and detail views show (tokens, password hashes,
   personal data).
4. **Client- or edge-side gates.** Navigation guards, UI checks, gateway/WAF/CDN rules. Note these explicitly
   as **UX-only and non-authoritative** unless a server layer also enforces them.

Record the request topology in one or two sentences: is there an application server in the path, a
direct-to-database client, an API gateway, a backend-for-frontend? This sets which layer is authoritative.

### Extract: describe each mechanism as implemented
Walk these categories and document each one that exists. Mark any that does not exist "not present". Ground
every claim in a file and, where useful, a line reference or symbol name.

- **Authentication and verification gates.** How a caller is identified and what must be true before they may
  act (signed-in checks, email/phone verification, MFA, token or claim requirements). State which checks are
  authoritative versus UX-only and where each lives.
- **Input and field validation.** The schemas or rule helpers that constrain request shape (lengths, ranges,
  formats, enums and allow-lists, immutability), where they run (client, server, database), and whether the
  same rule is duplicated across layers (note any requirement to keep, say, a rules file in sync with language
  constants).
- **Rate limiting and quota.** The limits, windows, where counters live, and whether enforcement is
  synchronous (rejected before commit) or eventual (created then reverted). Capture the exact constants.
- **Content moderation.** Automated screening of user content (text, image, file): the trigger, the detection
  service or model, thresholds and categories, the action on rejection, and the fail-open versus fail-closed
  behavior when the detector errors.
- **Secrets and attestation status.** How secrets and credentials are supplied (environment variables, a
  secret manager, build config) without listing values, and the status of any app-attestation or bot-defense
  layer (platform device-integrity APIs, CAPTCHA, device check). If a control is scaffolded but disabled, say
  so plainly and point at the commented or unwired code.
- **Abuse controls.** Report, block, mute, ban, takedown, and similar trust-and-safety paths: the client write
  path and the server enforcement behind it, plus any side effects (for example, a block that also
  unmatches/unfollows).
- **Deny-by-default.** The catch-all posture: a default-deny rule, a closed allow-list, or fail-closed
  middleware that blocks any path not explicitly permitted. Identify the resources that depend on it (anything
  reachable only by privileged server code).

### MANDATORY CHECKPOINT: confirm scope before writing
Present the request topology, the list of mechanisms found (and the categories marked "not present"), the
authoritative-versus-UX split, and the output path. Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Write: produce the document
Write the document at the output path using the template below. Lead with the defense-layers overview table,
then one section per mechanism. Keep each section grounded in code; prefer a small "where / authoritative? /
enforced when" framing over prose. Add a "Gotchas for implementers" section for asynchronous enforcement,
fail-open behavior, UX-only gates, and cross-layer sync requirements.

### Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: which layer is authoritative, the exact limits and thresholds, whether
enforcement is synchronous or eventual, fail-open versus fail-closed, and the disabled or scaffolded status of
any control. Confirm each file and line pointer still resolves. Fix or remove anything not provable from the
code. Prefer "not enforced", "scaffolded", or "unknown" over a confident guess. Re-confirm this is a
description of mechanisms, not a list of weaknesses.

## Output template

```markdown
---
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# Security Mechanisms

<1-2 sentence overview: the request topology and that this documents the *mechanisms*, not the access matrix.>

**Sources of truth (read these if this doc and the code disagree):**
- <authoritative rules / middleware file>: synchronous access control and validation.
- <async enforcement file>: rate limiting, moderation, privileged cascades.
- <client/edge gate file>: UX-level gate (non-authoritative).
- <secrets / attestation config file>: credential supply and attestation status.

> Related: the [authorization model](./authorization.md) (the per-resource access matrix) and the
> [data model](../architecture/data-model.md) (shapes and field constraints).

## Defense layers at a glance
| Layer | Where | Authoritative? | Enforced |
|---|---|---|---|
| <mechanism> | <file / component> | <yes / UX-only / async> | <when it runs> |

## Authentication and verification gates
<who is identified, what must be true to act; authoritative versus UX-only; file pointers>

## Input and field validation
<the validating schemas/rules, where they run, cross-layer duplication and sync requirements>

## Rate limiting and quota
<limits, windows, counter location, synchronous versus eventual; exact constants>

## Content moderation
<trigger, detector, thresholds/categories, action on rejection, fail-open versus fail-closed>

## Secrets and attestation
<how secrets are supplied (no values); attestation/bot-defense status, including scaffolded-but-disabled>

## Abuse controls
<report / block / etc.: client path, server enforcement, side effects>

## Deny-by-default
<the catch-all posture and the resources that depend on it (server-only or internal)>

## Gotchas for implementers
<asynchronous enforcement, fail-open behavior, UX-only gates, cross-layer sync requirements>
```

## Failure conditions

- **No enforcement code found.** State that plainly and stop; do not invent controls the project does not
  have.
- **A control is scaffolded but disabled.** Document it as disabled with a pointer to the unwired code; do not
  present it as active.
- **Layers disagree** (for example a client gate with no server backstop, or a rule that contradicts the code
  path). Document **both** and flag the discrepancy; do not silently pick one.
- **Scope creep into auditing.** If you find yourself rating severity or recommending fixes, stop; that is a
  separate security-review task. Document the mechanism as built.

## Output

A single document at the output path, plus a short summary: mechanisms documented, categories marked "not
present", the authoritative-versus-UX split, and any disabled controls or cross-layer discrepancies surfaced
for follow-up.
