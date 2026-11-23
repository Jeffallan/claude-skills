# intake:document-api

**Options:** what follows the procedure name in `intake <procedure> ...`, passed on in the brief: an optional root directory to analyze (defaults to the project root).

Produce an API reference at `docs/architecture/api-reference.md` (configurable): the authoritative contract for
every operation the backend exposes. An operation is anything a caller or event can invoke and the backend
runs: an HTTP route, a GraphQL resolver, an RPC method, a message/queue consumer, or a serverless function
bound to a platform event (timer, storage, database change, webhook). **Document only what the code proves.
Never invent a route, parameter, status code, or side effect.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/access-control.md` before the first phase. The first two set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior. The third defines the operation inventory this command owns ("Operation inventory"): the `## Operations` table every later access-control doc and test cites by id.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when the API surface changes (a rerun edits the existing document in place and keeps hand edits; see "Reruns" in `references/intake/rules.md`).

## Skills to load

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the backend; enumerate handlers and infer their contracts from code.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:api-designer`**: apply consistent vocabulary for routes, methods, request/response shapes, and errors;
  classify each operation by its API style.
- **`fullstack-dev-skills:secure-code-guardian`**: read each operation's authentication and authorization boundary accurately, and
  flag operations that run with elevated privilege or no caller check.
- **The project's backend skill** for the runtime in use, chosen by stack, e.g. `fullstack-dev-skills:fastapi-expert`,
  `fullstack-dev-skills:nestjs-expert`, `fullstack-dev-skills:golang-pro`, `fullstack-dev-skills:java-architect`, `fullstack-dev-skills:rails-expert`, `fullstack-dev-skills:graphql-architect`.

## Workflow

### Phase 1: Discover the backend API surface
Find every entry point a caller or event can reach, in priority order. The surface may mix several styles in
one codebase; cover all of them.

1. **Route/handler registration.** Router files, controller/decorator annotations, framework route tables, an
   API gateway or serverless manifest (e.g. an OpenAPI/Swagger spec, a `serverless.yml`/IaC function block, a
   `routes` module, controller classes).
2. **GraphQL schema and resolvers.** The SDL/type definitions and the resolver map (Query, Mutation,
   Subscription, field resolvers).
3. **RPC service definitions.** Protobuf/gRPC service blocks, tRPC routers, or other RPC method registries.
4. **Event-triggered and serverless functions.** Handlers bound to a platform event rather than a caller route:
   timers/cron, queue or stream consumers, storage-object events, database-change triggers, pub/sub topics,
   inbound webhooks.
5. **The resolved route table.** Run the router's own listing command against the configured application
   (a route-listing CLI task, a URL resolver dump, the OpenAPI schema the framework generates at runtime) and
   keep its output. It is the inventory's source, because libraries mount routes no app file declares: an auth
   library's account endpoints, an admin site, health or debug views, a GraphQL endpoint, an older API version
   still mounted. Never build the inventory only from the routes the app's code declares. Record the exact
   command and the number of routes it lists.
6. **The deployment/runtime config** so the doc records the runtime, entry module, and how the surface is
   deployed.

Record the API style or styles present. They set the vocabulary: routes/methods/status codes for REST,
operations and the schema for GraphQL, methods and messages for RPC, trigger/resource for event-driven
functions.

### Phase 2: Extract each operation's contract
Per operation, capture from the code:

- **Trigger / route / method:** the HTTP method plus path, the GraphQL operation name, the RPC method, or the
  event binding and resource it fires on.
- **Request / event shape:** path/query params, headers, request body schema, GraphQL arguments and variables,
  RPC message fields, or the event payload fields the handler actually reads (note which it ignores).
- **Behavior:** the ordered steps the handler performs, including the helpers it calls and any non-obvious
  control flow (early returns, no-ops, fail-open vs fail-closed).
- **Side effects:** every write or external action: data-store mutations, cascade deletes, file/blob
  operations, outbound calls (push/email/queue/third-party), and emitted events.
- **Response / errors:** the success shape and status, plus every error the handler raises or returns
  (status code or error type, condition, and whether it is surfaced to the caller or swallowed).
- **Source:** `app`, `library: <name>` or `framework`, from where the handler is defined.
- **Authentication and permission (resolved):** what actually runs for this operation, after decorators,
  class attributes, router or middleware defaults and the library's own defaults are applied, together with the
  setting or default that produced it. A library default the project never set is written as such,
  "(library default)". Note any privilege the runtime itself holds (e.g. an admin/service identity that bypasses
  normal access rules). Ownership and per-principal rules belong to the authorization doc; link it rather than
  re-deriving them here.

Also collect any **shared constants and policy values** (rate limits, timeouts, thresholds, pagination
defaults) and the **non-exported helpers** that operations depend on; document each helper inline at its first
use rather than as a standalone operation.

### Phase 3: MANDATORY CHECKPOINT, confirm scope before writing
Present the API style or styles detected, the route listing command and its count, the full list of operations
(grouped by style and by source), and the output path.
Do not write the document until the user confirms the list is complete and nothing internal-only is being
exposed by mistake. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write the document at the output path using the template below. Lead with the `## Operations` inventory, then one
detail entry per operation. Cite each handler as `path::symbol` so the doc stays verifiable.

The inventory follows "Operation inventory" in `references/intake/access-control.md`:

- One row per method and path, library and framework routes included. Non-CRUD operations (custom actions,
  account endpoints, exports, bulk, webhooks, sockets) are rows like any other. A non-HTTP operation gets a row
  too, with its kind in `Method` (`QUERY`, `MUTATION`, `RPC`, `EVENT`) and its operation name or binding in `Path`.
- Ids are `OP-` plus a three-digit number. On a rerun, keep every existing id with its operation, append new
  operations with the next free id, and never reuse an id. A route that is gone keeps its row, marked removed,
  so citations elsewhere still resolve.
- Write the listing command, its route count and the short SHA it ran at above the table, and record the same
  command and count in the item's checklist note.

Docs describe what the code does, neutrally. Where the resolved permission breaks an access invariant
(`references/intake/access-control.md`, "Access invariants") or contradicts stated intent (a comment, a test,
another doc, a setting the project chose), append a finding to the tracker before writing the doc, and cite its id
in the detail entry. A library default nobody chose that lets anonymous callers change state is such a case:
"the library does it by default" is not evidence of intent.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: route/method/trigger, request/event fields, status codes and error
types, side effects, and the resolved permission. Re-run the listing command and compare its count with the
`## Operations` row count (removed rows aside). Every listed route has a row, and every row has a detail entry; a
difference is fixed before committing, or explained in the `## Accuracy audit` section when the two can't match
(a route the listing collapses, an event handler the router never lists). Ground any example request/response in a real
handler. Fix or remove anything not provable from the code. Prefer "unknown / not enforced" over a guess, and
flag any operation whose contract the code leaves ambiguous.

## Output template

```markdown
---
command: intake:document-api
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# API Reference

<1-2 sentence overview: which API style or styles the backend uses and what this documents.>

**Sources of truth (read these if this doc and the code disagree):**
- <router / schema / resolver / handler files>
- <runtime + dependency manifest>
- <client/consumer call sites for non-HTTP operations>

## Runtime
| Property | Value | Source |
|---|---|---|
| API style(s) | <REST / GraphQL / RPC / event-driven> | <path::symbol> |
| Runtime | <language + version> | <path::symbol> |
| Entry module | <path> | <path::symbol> |
| Deploy | <command or pipeline> | <path::symbol> |

## Operations

Route listing: `<command>` (<N> routes at <short sha>).

| Id | Method | Path | Source | Handler | Authentication | Permission (resolved) |
|----|--------|------|--------|---------|----------------|------------------------|
| OP-001 | <method> | <path> | <app / library: name / framework> | `<path::symbol>` | <scheme or none> | <permission> (<setting or library default>) |

## Shared policy constants   <!-- include only if any exist -->
| Constant | Value | Meaning |
|---|---|---|

## Operation details
### OP-001 `<operation name>`
<API style + binding>: <HTTP method + path / GraphQL operation / RPC method / event + resource> (`<path::symbol>`)

- **Triggers when:** <caller action or platform event; link the originating call site if non-HTTP>
- **Request / event read:** <params, body, args, or payload fields actually consumed>
- **Steps:** <ordered behavior, including helpers and control flow>
- **Returns:** <success shape + status/code>
- **Side effects:** <data writes, cascades, files, outbound calls, emitted events>
- **Errors:** <each error: status/type, condition, surfaced vs swallowed>
- **Auth:** <resolved authentication and permission with their source; elevated runtime privilege; link the authorization doc; finding ids>

## Gotchas for implementers
<async side effects, fail-open vs fail-closed handlers, non-transactional multi-step writes, operations that
run with elevated privilege, defined-but-unregistered or registered-but-dead handlers, path/shape mismatches>
```

## Failure conditions

- **No backend API surface found:** state that plainly and stop; do not fabricate routes or handlers.
- **The route listing command can't run** (the app won't boot here, a missing secret): build the inventory from the
  route configuration and the libraries' URL modules, write "Route listing: not run (<reason>)" above the table, and
  add an Open question. Never present a hand-built list as the resolved table.
- **Multiple API styles in one codebase:** document each style in its own section of the summary table and
  operation list; do not force them into one shape.
- **Schema/spec and implementation disagree** (e.g. an OpenAPI spec or GraphQL SDL that drifts from the
  handlers): document the **implemented** behavior, cite the discrepancy, and do not silently trust the spec.

## Output

A single document at the output path, plus a short summary: the listing command and its count, operations
documented (by style and source), new and removed ids on a rerun, shared constants captured, finding ids raised,
and any discrepancies, dead handlers, or unknowns surfaced for follow-up.
