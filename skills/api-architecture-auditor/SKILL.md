---
name: api-architecture-auditor
description: Audits any API or backend codebase — REST, GraphQL, gRPC, WebSocket, raw TCP/UDP protocol servers, or message-queue-driven services — for architectural separation, data-layer integrity, authentication/authorization coverage, secrets hygiene, and live runtime behavior. Use this whenever the user asks to review, audit, assess, or check the security/architecture/quality of an API, backend, server, or microservice codebase — even if they don't say "API" explicitly (e.g. "review this backend," "is this service secure," "check this codebase before we ship it," "audit my server's endpoints"). Do not assume the target is REST-over-HTTP with a relational database; discover the actual shape of the system first.
license: MIT
metadata:
  domain: security-and-architecture
  role: auditor
  scope: analysis
  output-format: report
---

# API Architecture & Security Auditor

## Why discovery comes first

APIs take wildly different shapes. An HTTP+JSON CRUD service backed by Postgres looks nothing like a fleet of raw-TCP device-protocol handlers writing to DynamoDB and a time-series store, which looks nothing like a gRPC microservice mesh authenticated by mTLS. A checklist that silently assumes "REST + ORM + JWT login" will run to completion and produce a confident-looking report — while missing the entire attack surface and architecture of anything that doesn't fit that mold.

So before applying any checklist, spend one pass understanding what's actually in front of you. Every step below is conditional on what you find in Step 0 — skip the parts that don't apply, and say explicitly that you skipped them and why, rather than silently ignoring them or forcing a fit.

## Step 0: Discover the shape of the system

Read the entry point(s) (main function, server bootstrap, routing setup) and the top-level directory structure, and answer:

- **Transport protocols.** What does this system actually expose, and on what ports/routes? A single codebase can run several transports at once (e.g. an HTTP health endpoint alongside a WebSocket server and several raw TCP listeners) — list every one you find, don't stop at the first.
- **Data stores.** What backs persistence, and what kind is each — relational/ORM, document/NoSQL, key-value, time-series, in-memory cache, event log? Note which data lives in which store; systems commonly split "live state" from "history" across two different technologies.
- **Auth mechanism(s).** Session/token, JWT, OAuth2, API key, mTLS/client certificate, HMAC-signed payloads, a device identifier such as an IMEI or serial number, or genuinely none (common for internal-only services). Don't assume a login flow exists just because most tutorials have one.
- **Configuration and secrets.** Where do credentials and connection strings come from — environment variables, a config file, a secrets manager, or (worth checking explicitly) hardcoded directly in source or in a committed deploy/compose file?

Write these findings down explicitly before continuing. They determine which parts of Steps 1–6 apply.

## Step 1: Structural & architectural separation

Check for a clean separation between the layer that talks to the outside world, the layer that holds business logic, and the layer that touches storage — but interpret "the outside world" using whatever Step 0 found. For an HTTP service that's routes/controllers; for a socket server it's the protocol frame decoder and connection handlers; for a queue-driven service it's the message consumer. Confirm the business logic doesn't know or care which transport invoked it, and that storage access is isolated behind a repository/service layer rather than scattered through handler code.

## Step 2: Data layer review — branch by store type

Apply the check that matches each store found in Step 0, not a single relational template:

- **Relational (SQL/ORM):** primary keys and audit metadata (created/updated/deleted timestamps), foreign keys and whether cardinality (1:1, 1:N, N:N) matches the real-world relationship, indexes on frequently-queried columns, and whether migrations match the live schema.
- **Document/NoSQL:** partition/sort key design and whether it matches actual query patterns, whether "relationships" are resolved in application code rather than the database, TTL and versioning behavior.
- **Key-value / cache:** expiry policy, what happens on a cache miss, and whether stale cached data could be served as if it were live.
- **Event-sourced / message-driven:** whether consumers are idempotent (does replaying the same message twice double-apply an effect?), ordering guarantees, and dead-letter/retry handling.

## Step 3: Authentication & authorization — branch by mechanism

Whatever Step 0 found, confirm:

- Public endpoints/handlers are public on purpose — list them and ask whether each one should really have no auth.
- Protected endpoints actually enforce the mechanism in practice, not just that a security library is imported somewhere in the project.
- Privileged or write operations enforce role/permission checks specifically, not just "any authenticated user."
- For non-HTTP mechanisms — device serials, HMAC signatures, mutual TLS — confirm an unknown or invalid identity is actually rejected. The equivalent of a 401 here might be "connection closed," "message silently dropped," or "handshake never completes" — find out which, and confirm it happens.

## Step 4: Secrets & configuration hygiene

This is consistently the highest-value, easiest-to-verify finding in real audits: a single search can catch a live cloud credential sitting in a file that's already committed to version control.

- Search the repo and any compose/deploy/CI files for patterns like cloud access-key prefixes, `api_key=`, `password=`, private-key headers, or connection strings with embedded credentials.
- Confirm secrets are actually sourced from environment variables or a secrets manager rather than literals, even where the code appears to reference an env var name — check that no fallback default hardcodes a real-looking value.
- Check that `.gitignore` actually excludes local secret files.
- Flag anything found with an exact file and line reference so it can be rotated immediately — this is often the single most actionable line in the whole report.

## Step 5: Transport & network-level checks

- CORS or WebSocket origin validation — is it actually restrictive, or does it unconditionally allow every origin?
- Where is TLS terminated — by the app itself, by a proxy in front of it, or nowhere?
- Is there rate limiting or throttling on public or expensive endpoints?
- Is input validated before it reaches a query, shell command, or file path?

## Step 6: Dynamic verification — only if a live instance is reachable

Static review tells you what the code says it does; running it tells you what it actually does. But not every audit has a runnable environment, valid credentials, or reachable network on hand. If none of that is available, say so explicitly and move to Step 7 rather than guessing at behavior you can't observe.

If you can run it, test whatever mechanisms Step 0 identified:

- **HTTP:** request the health endpoint (expect success), request a protected route with no credentials (expect a rejection), then authenticate and retry (expect success), and confirm relational responses return populated related data rather than bare foreign keys.
- **WebSocket:** connect without a token (expect rejection or immediate close), then with a valid token, and confirm an origin check genuinely rejects an unexpected `Origin` header rather than accepting everything.
- **gRPC:** use a generic client (e.g. grpcurl) or the service's own client the same way — unauthenticated call should fail, authenticated call should succeed.
- **Raw TCP/UDP protocol servers:** open a raw socket and send a malformed or unrecognized frame (the server should reject or disconnect, not hang or crash); then send a valid handshake/login frame and confirm the expected acknowledgement.
- **Message-queue-triggered logic:** publish a test message and confirm it's consumed idempotently — publishing the same message twice shouldn't double-apply its effect.

## Step 7: Report the findings

Always structure the output this way, regardless of what kind of system was audited — this keeps reports comparable across completely different codebases:

```markdown
# API Audit — [project name]

## System shape
[what Step 0 found: transports, stores, auth mechanisms, config/secrets source]

## Findings
[grouped by severity — Critical / High / Medium / Low / Info — each with file:line,
what's wrong, why it matters, and a suggested fix]

## Not testable
[which dynamic checks were skipped, and why — e.g. no live environment, no seeded credentials]

## Coverage
[which of Steps 1–6 applied to this system, which were skipped as not applicable, and why]
```

The "Coverage" section matters as much as the findings — it tells the reader whether a quiet section means "nothing wrong here" or "this system doesn't have that kind of component at all."
