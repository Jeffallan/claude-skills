---
name: document-features
description: Generate an accurate, agent-readable feature catalog (what the application does today, grouped by area, with user-visible behavior and implementing files) by reverse-engineering the code's behavioral surfaces.
argument-hint: "[directory]"
---

# intake:document-features

**Argument:** `$ARGUMENTS` is an optional root directory to analyze (defaults to the project root).

Produce a feature catalog at `docs/domain/features.md` (configurable): what the application **actually does today**,
grouped by functional area, each entry giving a one-line description, the user-visible behavior, and the files that
implement it. Written for an AI agent or engineer to use as the map from capability to code. **Document only
features present in the code; anything not in the code is not built. Never list aspirational or planned features.**

Read `${CLAUDE_PLUGIN_ROOT}/references/intake/rules.md` and `${CLAUDE_PLUGIN_ROOT}/references/intake/findings.md` before the first phase. They set the output layout, the findings tracker, the checkpoint, the accuracy audit and the goal-run behavior.

## When to use

Run once during intake, after `intake:document-codebase`. Re-run when features are added or removed (this command
is idempotent; it overwrites the document).

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

**MANDATORY CHECKPOINT: confirm scope before writing.** Present the area grouping, the feature count per area, and
the output path. Do not write the document until the user confirms. In a goal run, follow the checkpoint rule in `references/intake/rules.md`.

### Phase 3: Write
Write the document at the output path using the template below.

### Phase 4: Accuracy audit (required; the output is agent-facing)
First give the document's prose its human-voice pass ("Human-voice pass" in `references/intake/rules.md`): wording only, never a claim. Then audit:
Re-verify each feature against the code: the named implementing files exist and contain the described behavior;
the user-visible behavior matches what the code does (including the empty/loading/error states claimed). Confirm
every summary-table row maps to a subsection and vice versa. Remove any feature you cannot point to in code.
Prefer omission over invention.

## Output template

```markdown
---
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

## Gotchas for implementers
<cross-cutting surprises: non-obvious enforcement points, async/eventually-consistent behavior, split responsibilities>
```

## Failure conditions

- **No discernible feature surface** (a library or SDK with no application): state that plainly and stop; do not
  invent product features.
- **A surface exists but its behavior is unreadable** (heavy dynamic dispatch, generated or obfuscated code):
  list the feature, mark its behavior **unverified**, and point to the entry file rather than guessing.

## Output

A single document at the output path, plus a short summary: features documented, areas covered, and anything
omitted as unverifiable.
