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

## Why discovery comes fAPIs take wildly different shapes. A checklist that silently assumes "REST + ORM + JWT login" will run to completion and produce a confident-looking report while missing the entire attack surface of anything that doesn't fit that mold. Spend one pass understanding what's in front of you before applying any checklist below. Every step is conditional on Step 0 — skip parts that don't apply, and say so explicitly.

## Step 0: Discover the shape of the system

Read the entry point(s) and top-level directory structure, and answer:
- Transport protocols: HTTP, gRPC, WebSocket, raw TCP/UDP, message-queue consumers — list every one, a codebase often runs several at once.
- Data stores: relational/ORM, document/NoSQL, key-value, time-series, in-memory cache, event log — note which data lives where.
- Auth mechanism(s): session/token, JWT, OAuth2, API key, mTLS, HMAC-signed payloads, device identifiers, or none.
- Config/secrets source: env vars, config file, secrets manager, or hardcoded in source/deploy filesStep 1: Structural separation

Check for a clean split between the transport layer (routes/handlers/consumers, whatever Step 0 found), business logic, and storage access.

## Step 2: Data layer — branch by store type

Relational: keys, foreign keys/cardinality, indexes, migration drift. NoSQL: partition/sort key design, app-side joins, TTL. Cache: expiry policy, stale-data risk. Event-driven: consumer idempotency, ordering, dead-letter handling.

## Step 3: Auth & authorization — branch by mechanism

Confirm public endpoints are public on purpose, protected ones actually enforce auth (not just import a library), privileged actions check roles specifically, and non-HTTP mechanisms genuinely reject invalid identities.

## Step 4: Secrets & configuration hygiene

Search the repo and deploy/CI files for hardcoded credentials, keys, and passwords. Confirm secrets come from env vars/secrets managers, and `.gitignore` excludes local secret files. Flag anything found with an exact file:line reference.

## Step ransport & network checks

CORS/origin validation, TLS termination point, rate limiting, input validation before queries/shell/file paths.

## Step 6: Dynamic verification — only if a live instance is reachable

If you can run it: hit health/protected endpoints (HTTP), connect with/without a token (WebSocket), call with grpcurl (gRPC), send malformed/valid frames (raw TCP), or publish a duplicate message and check idempotency (queues). If no live environment exists, say so and skip to Step 7.

## Step 7: Report the findings

Always use this template:

# API Audit — [project name]
## System shape
## Findings (by severity: Critical/High/Medium/Low/Info, each with file:line, why it matters, fix)
## Not testable
## Coverage
