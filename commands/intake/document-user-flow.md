---
name: document-user-flow
description: Generate an accurate, agent-readable user-flow reference (routes, entry points, end-to-end journeys with per-journey flowcharts) by reverse-engineering the project's routing and navigation layer.
argument-hint: "[directory]"
---

# intake:document-user-flow

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce a user-flow reference at `docs/flows/user-flow.md` (configurable): a precise map of how a person moves
through the application, from the entry point through every navigation transition to the terminal screens, written
for an AI agent or engineer to rely on as the navigation and screen-to-service wiring contract. **Document only what
the routes and handlers prove. Never invent a screen, transition, or guard.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when routes or navigation flows change (a rerun edits the existing
document in place and keeps hand edits; see "Reruns" in `references/intake/rules.md`).

## Skills to invoke

- **`fullstack-dev-skills:spec-miner`**: reverse-engineer the routing layer, navigation transitions, and handler wiring from code; trace
  journeys through an undocumented app.
- **`fullstack-dev-skills:code-documenter`**: structure, format, and validate the output document.
- **`fullstack-dev-skills:architecture-designer`**: produce the per-journey flowcharts (and the routing-model diagram, if access control is
  non-trivial).
- **The project's framework / navigation skill** for the routing layer; choose by stack, e.g. `fullstack-dev-skills:react-native-expert`
  or `fullstack-dev-skills:flutter-expert` (mobile navigation stacks/tabs), `fullstack-dev-skills:nextjs-developer`, `fullstack-dev-skills:react-expert`, `fullstack-dev-skills:vue-expert`, or
  `fullstack-dev-skills:angular-architect` (web/SPA routers), `fullstack-dev-skills:django-expert`, `fullstack-dev-skills:rails-expert`, or `fullstack-dev-skills:laravel-specialist` (server-side route
  tables and controllers).

## Workflow

### Phase 1: Discover routes and entry points
Identify how the app defines navigable destinations and how a user arrives at them, in priority order:
1. The route / navigation manifest, i.e. the app's routing/navigation layer. This varies by stack: a file-based route
   tree (a screens/pages directory), a central route table or router config, server-side route definitions
   (controllers, URL maps), or a navigation graph/stack declaration.
2. The root layout / app shell and any access guards that decide which destination mounts (redirect logic, route
   guards, middleware, interceptors, conditional initial routes).
3. Entry points beyond the main UI: deep links / universal links, push or email links, OAuth callbacks, share
   targets, and the default / index route.
4. The handlers wired to each route: the screen / page / controller it mounts and the services or actions it calls.

Record the routing technology and its vocabulary (screens/stacks/tabs vs pages/layouts vs controllers/views/URL
patterns). It sets the terms used throughout the document.

### Phase 2: Trace journeys
Group the routes into the handful of end-to-end journeys a real user follows (e.g. onboarding/authentication, the
core/primary loop, a secondary workflow, notifications and deep linking, account or safety actions). Per journey,
walk the code path from the entry route through every navigation transition to the terminal screen. Per step,
capture: the concrete route or screen, the user action or event that triggers the transition, the handler/service
called, the data read or written, and the resulting navigation (push / replace / redirect / back). Note any guard
that can divert the flow (incomplete state, missing permission, error branch).

### Phase 3: Diagram
Per journey, produce a Mermaid `flowchart` of its routes and the transitions between them: label edges with the
triggering action and label nodes with the real route path or handler. If access control is non-trivial, add one
top-level flowchart for the routing/guard model.

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the routing technology, the list of journeys (each
with its entry route), and the output path. Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 4: Write
Write the document at the output path using the template below.

### Phase 5: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify every claim against the code: route paths, the action that triggers each transition, the handler/service
invoked, the navigation call used (push vs replace vs redirect vs back), and every guard condition. Ground each step
and edge label in a real route or call site. Confirm each Mermaid diagram parses. Fix or remove anything not provable
from the code. Prefer "unknown / not wired" over a guess.

## Output template

```markdown
---
command: intake:document-user-flow
verified: <short SHA of HEAD when the accuracy audit ran>
sources: [<globs of the code this doc describes>]
related: [<docs this one depends on or that depend on it, paths under docs/>]
---
# User Flows

<1-2 sentence overview: what this maps and that every journey is grounded in the real routing layer.>

**Sources of truth:** <root layout/guard, route/screen files, and the services they call to trust over this doc>

## Routing model   <!-- include only if access control / guards are non-trivial -->
<how the router decides what mounts: guards, redirects, middleware; a state table if it helps>
` ` `mermaid
flowchart TD
  Start["app entry / index route"] --> Guard{"access guard?"}
  Guard -->|"signed out"| AuthEntry["/auth entry route"]
  Guard -->|"signed in"| AppEntry["primary app route"]
` ` `

## <N>. <Journey name>   <!-- e.g. 1. Onboarding and authentication -->
<1-2 sentence scope: which routes it covers and where it starts and ends.>

### <sub-step group>   <!-- optional grouping within a longer journey -->
1. On <route/screen>, <user action or event> triggers <handler/service>, which <reads/writes data>, then <navigation>.
2. ...

` ` `mermaid
flowchart TD
  Entry["/entry-route"] -->|"user action"| Next["/next-route"]
  Next --> Decision{"guard or branch?"}
  Decision -->|"condition A"| PathA["/route-a"]
  Decision -->|"condition B"| PathB["/route-b"]
` ` `

## Gotchas for implementers
<guard vs screen-level navigation, deterministic ids, one-shot vs live data, deep-link reachability, best-effort steps>
```

## Failure conditions

- **No routing/navigation layer found** (a single-screen app, or a pure library/API/CLI with no user-facing
  navigation): state that plainly and stop; do not invent journeys. An API-only project defers to the API or
  integration docs instead.
- **A journey cannot be traced end to end** (a dead-end route, an orphaned screen, or a transition wired to a missing
  handler): document the journey up to the break and flag the gap; do not fabricate the missing transition.
- **A transition in the UI and the code disagree** (e.g. a button that appears to navigate but whose handler is a
  no-op): document what the code actually does and flag the discrepancy; do not silently pick the apparent behavior.

## Output

A single document at the output path, plus a short summary: journeys documented, routes covered, entry points
(including deep links) mapped, and any dead-ends, orphaned routes, or unknowns surfaced for follow-up.
