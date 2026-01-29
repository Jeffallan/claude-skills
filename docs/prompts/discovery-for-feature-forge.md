# Multi-Agent Discovery Prompt for Feature Forge

> **Purpose:** Use this prompt to trigger parallel skill-invoked discovery across
> multiple domains before starting a Feature Forge specification workshop.
> The collected findings become input context for the Feature Forge interview,
> replacing guesswork with concrete technical evidence.

---

## Prompt

```
I need to define a new feature: [FEATURE DESCRIPTION].

Before we start the Feature Forge specification workshop, run parallel discovery
across the relevant domains to build technical context. Launch the following
Task subagents concurrently — each should invoke its respective skill and return
a focused summary:

1. **Architecture Discovery** — Launch a Task subagent (general-purpose) that invokes
   the `architecture-designer` skill to:
   - Identify which system components this feature touches
   - Map integration points and data flows
   - Flag architectural constraints or trade-offs
   - Recommend patterns that fit the existing system

2. **Security Discovery** — Launch a Task subagent (general-purpose) that invokes
   the `security-reviewer` skill to:
   - Identify authentication and authorization requirements
   - Flag data sensitivity concerns (PII, PCI, GDPR)
   - Surface OWASP-relevant risks for this feature type
   - Recommend security patterns and controls

3. **Codebase Discovery** — Launch a Task subagent (Explore) to:
   - Search for existing patterns, components, or utilities related to this feature
   - Identify code conventions and abstractions already in use
   - Find similar features that can serve as implementation templates
   - Note relevant test patterns and coverage expectations

4. **API/Integration Discovery** — Launch a Task subagent (general-purpose) that
   invokes the `api-designer` skill to:
   - Propose API surface area (endpoints, methods, payloads)
   - Identify existing API patterns to follow for consistency
   - Flag external service dependencies and rate limits
   - Recommend versioning and backwards-compatibility approach

Wait for all subagents to complete, then:

1. **Synthesize** — Combine the findings into a structured discovery summary with
   sections for: Architecture, Security, Codebase Patterns, and API Surface.
2. **Identify Decisions** — List the key decisions that emerged from discovery
   (e.g., "sync vs async processing", "new table vs extend existing").
   Present these as `AskUserQuestions` with structured options.
3. **Launch Feature Forge** — With the discovery context and user decisions in hand,
   invoke the `feature-forge` skill to begin the specification workshop. The interview
   should reference discovery findings rather than re-asking questions the subagents
   already answered.
```

---

## Usage

### Basic Invocation

Replace `[FEATURE DESCRIPTION]` with your feature summary:

```
I need to define a new feature: user-facing data export that supports CSV and JSON
formats with scheduled recurring exports.

Before we start the Feature Forge specification workshop, run parallel discovery...
```

### Customizing Discovery Agents

Not every feature needs all four discovery tracks. Tailor the subagent list:

| Feature Type | Recommended Agents |
|-------------|-------------------|
| New UI feature | Codebase + Architecture |
| New API endpoint | API/Integration + Security + Codebase |
| Data pipeline | Architecture + Security + Codebase |
| Auth/permissions | Security + Architecture + Codebase |
| Full-stack feature | All four agents |

### Expected Output Flow

```
User provides feature description
    │
    ├─→ [Parallel] Architecture Discovery ──→ Component map, constraints
    ├─→ [Parallel] Security Discovery ──────→ Auth reqs, data sensitivity
    ├─→ [Parallel] Codebase Discovery ──────→ Existing patterns, templates
    └─→ [Parallel] API Discovery ───────────→ Endpoint design, integrations
         │
         ▼
    Synthesized Discovery Summary
         │
         ▼
    AskUserQuestions: Key decisions from discovery
         │
         ▼
    Feature Forge Interview (informed by discovery context)
         │
         ▼
    EARS Specification Document
```

---

## Design Rationale

This prompt applies the **ReAct + Chain-of-Thought** pattern from prompt engineering:

- **ReAct:** Each subagent acts as a reasoning-action step — it invokes a skill (action),
  collects findings (observation), then feeds results forward.
- **Chain-of-Thought:** The synthesis step forces explicit reasoning about how discovery
  findings connect before entering the Feature Forge interview.
- **Structured Elicitation:** Key decisions surface as `AskUserQuestions` with options
  derived from technical evidence, not assumptions.

The parallel execution pattern reduces total discovery latency — all four agents run
concurrently rather than sequentially asking the user about each domain.
