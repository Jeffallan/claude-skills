---
name: document-security
description: "Generate an accurate, agent-readable security-mechanisms reference (defense layers, authentication/verification gates, tokens and their properties, input validation, rate limiting, content moderation, secrets/attestation status, abuse controls, deny-by-default) by reverse-engineering what the code actually enforces."
argument-hint: "[directory]"
---

# intake:document-security

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce a security-mechanisms reference at `docs/security/security.md` (configurable): a precise map of the
controls that protect the system, written for an AI agent or engineer to rely on as the implementation
contract. Describe each mechanism **as it is actually implemented** (what enforces it, where, and whether it is
authoritative), and do not invent a control the code does not contain. The prose stays neutral. Where a
mechanism breaks an access invariant ("Access invariants" in `access-control.md`) or contradicts stated intent
(a comment, a type, a test, another doc), that place goes to the findings tracker as a finding, or an Open
question when intent can't be settled, and the doc cites its id.

This document covers the *mechanisms* (what enforces safety and where) and owns `## Tokens`: every token the
system issues and its properties. The question of *who may do what through each operation* (the access matrix)
belongs in the companion authorization document produced by `intake:document-authorization`, which cites this
doc's token rows. Cross-link the two rather than duplicating.

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit, the goal-run behavior, the access invariants, and the token properties this command documents ("Tokens" in `access-control.md`).

## When to use

Run once during intake, after `intake:document-codebase` and `intake:document-user-model` (token voiding is
checked against the user model's blocking states). Re-run when the security surface changes (new auth flow, a
new token type, a new validation layer, a moderation or rate-limit change). When the user model is missing,
work from the code and add an Open question naming it ("In a goal run" in `rules.md`). A rerun edits the existing document in place and keeps hand edits ("Reruns" in `references/intake/rules.md`).

## Skills to load

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the existing enforcement code; infer the layers and
  where each control lives.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:security-reviewer`**: check the inventory against its control categories (auth,
  tokens, validation, rate limiting, moderation, attestation, abuse controls, default-deny), and write the
  findings for a token property or control that is missing without intent evidence.
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
every claim in code, cited as `path::symbol` ("Doc frontmatter and citations" in `rules.md`).

- **Authentication and verification gates.** How a caller is identified and what must be true before they may
  act (signed-in checks, email/phone verification, MFA, token or claim requirements). State which checks are
  authoritative versus UX-only and where each lives.
- **Tokens.** Every token type the system issues, the library's included: session, access and refresh, API
  key, password reset, activation or email verification, invite, email change, magic link, and any other signed
  link or code. Find them by listing every place that creates a token, signs a value or mails a link. For each,
  record with a `path::symbol` citation: expiry (and its value), single use, bound to one user, bound to one
  purpose, and voided by which state changes: password change, each blocking state in the user model
  (deactivation, suspension, deletion), logout, role change. A property that doesn't apply to the token's kind
  (single use on a session) is `n/a` with the reason. A property the token lacks without intent evidence (a
  comment, a test, a doc, a setting the project chose; a library default is not intent) is a finding.
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
token types found and where each is issued, the authoritative-versus-UX split, and the output path. Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Write: produce the document
Write the document at the output path using the template below. Lead with the defense-layers overview table,
then one section per mechanism. Keep each section grounded in code; prefer a small "where / authoritative? /
enforced when" framing over prose. Write `## Tokens` as one row per token type. Before the doc cites a finding,
append it to `docs/intake-findings.md` with the next free id. Add a "Gotchas for implementers" section for
asynchronous enforcement, fail-open behavior, UX-only gates, and cross-layer sync requirements.

### Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: which layer is authoritative, the exact limits and thresholds, whether
enforcement is synchronous or eventual, fail-open versus fail-closed, and the disabled or scaffolded status of
any control. For every token, re-check each property against its issuing and validating code, and confirm
every `no` without intent evidence carries a finding id. Confirm each `path::symbol` citation still resolves.
Fix or remove anything not provable from the code. Prefer "not enforced", "scaffolded", or "unknown" over a
confident guess. Keep the prose descriptive: a weakness appears as the behavior plus its finding id, never as a
recommendation.

## Output template

```markdown
---
command: intake:document-security
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# Security Mechanisms

<1-2 sentence overview: the request topology and that this documents the *mechanisms*, not the access matrix.>

**Sources of truth (read these if this doc and the code disagree):**
- <authoritative rules / middleware file>: synchronous access control and validation.
- <async enforcement file>: rate limiting, moderation, privileged cascades.
- <client/edge gate file>: UX-level gate (non-authoritative).
- <secrets / attestation config file>: credential supply and attestation status.
- <token issuing and validating files>: every token type and its properties.

> Related: the [authorization model](./authorization.md) (the per-resource access matrix) and the
> [data model](../architecture/data-model.md) (shapes and field constraints).

## Defense layers at a glance
| Layer | Where | Authoritative? | Enforced |
|---|---|---|---|
| <mechanism> | <file / component> | <yes / UX-only / async> | <when it runs> |

## Authentication and verification gates
<who is identified, what must be true to act; authoritative versus UX-only; file pointers>

## Tokens
<every token type the system issues; `n/a` with a reason where a property doesn't apply to the kind>

| Token | Issued by | Expiry | Single use | Bound to user | Bound to purpose | Voided by | Finding |
|---|---|---|---|---|---|---|---|
| <type> | `<path::symbol>` | <value> (`<path::symbol>`) | <yes / no / n/a> (`<path::symbol>`) | <yes / no> | <yes / no> | <password change: yes / no; each blocking state: yes / no; logout: yes / no; role change: yes / no> | <F-nnn or none> |

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
  path). Document **both**, flag the discrepancy and add a finding; do not silently pick one.
- **A token property left blank.** Every token row has a value for every property, `unknown` included. A
  property the token lacks without intent evidence is a finding, never an empty cell.
- **Auditing in the doc's voice.** Documenting stays neutral: no severity, no "should" in the doc. A mechanism
  that breaks an invariant or contradicts stated intent still becomes a finding or an Open question; the
  finding carries the severity and the recommendation, and the doc cites its id.

## Output

A single document at the output path, plus a short summary: mechanisms documented, categories marked "not
present", the token types and their missing properties, the authoritative-versus-UX split, any disabled
controls or cross-layer discrepancies, and the finding ids and Open questions raised.
