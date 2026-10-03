# Assumption Classification

> Reference for: Common Ground
> Load when: Classifying assumptions, determining type or tier

---

## Assumption Types

Types indicate **how** an assumption was derived. Types are immutable once set (audit trail).

### stated

Direct user statements captured from conversation.

- **Evidence:** Explicit quote from user
- **Confidence:** High
- **Markers:** User said, user requested, user specified
- **Example:** "Use TypeScript for all new code" - user explicitly stated this

### inferred

Logical conclusions derived from code patterns, configuration, or context.

- **Evidence:** Code analysis, config files, project structure
- **Confidence:** Medium-High
- **Markers:** Config shows, code uses, pattern observed
- **Example:** "Project uses ESLint with Airbnb config" - inferred from .eslintrc.js

### assumed

Best-practice defaults applied without explicit confirmation.

- **Evidence:** Industry standards, common patterns
- **Confidence:** Medium
- **Markers:** Best practice, common convention, typically
- **Example:** "Tests should have >80% coverage" - assumed based on industry standard

### uncertain

Gaps or ambiguities requiring clarification before proceeding.

- **Evidence:** None, conflicting, or incomplete
- **Confidence:** Low
- **Markers:** Unknown, unclear, conflicting signals
- **Example:** "Legacy browser support required?" - no browserslist found, unclear requirement

---

## Assumption Tiers

Tiers indicate **confidence level** and how Claude should act on assumptions. Users can change tiers freely.

### ESTABLISHED (High Confidence)

User-validated facts that can be treated as premises.

- **Action:** Act confidently without re-asking
- **When to use:**
  - User explicitly validated the assumption
  - Verified through direct observation
  - Documented in project configuration
- **Example:** "TypeScript strict mode enabled" validated by user AND tsconfig.json

### WORKING (Medium Confidence)

Reasonable inferences that should be used but surfaced if contradicted.

- **Action:** Use as basis for work, but flag if contradicted
- **When to use:**
  - Inferred from code/config patterns
  - User confirmed informally ("yeah, that's right")
  - No contradicting evidence found
- **Example:** "No class components" - no classes found in codebase

### OPEN (Low Confidence)

Unvalidated assumptions requiring user input before acting.

- **Action:** Ask before making decisions based on this
- **When to use:**
  - Uncertain type assumptions
  - Conflicting signals observed
  - High-impact assumption without validation
- **Example:** "SSR required?" - could be SPA or SSR, architecture depends on answer

---

## Tier Transitions

| From | To | Trigger |
|------|-----|---------|
| OPEN | WORKING | User confirms informally in conversation |
| WORKING | ESTABLISHED | User explicitly validates ("yes, that's correct") |
| ESTABLISHED | WORKING | User says "usually but..." or exception noted |
| WORKING | OPEN | Contradiction found in code/config |
| Any | Archived | Superseded by new information |

---

## Classification Process

When identifying assumptions, follow this process:

### Step 1: Identify Source

| Source | Typical Type | Typical Tier |
|--------|-------------|--------------|
| User statement | stated | ESTABLISHED |
| Config file | inferred | WORKING |
| Code pattern | inferred | WORKING |
| Convention | assumed | WORKING |
| Unknown/gap | uncertain | OPEN |

### Step 2: Assess Evidence Strength

| Evidence | Tier Adjustment |
|----------|----------------|
| Explicit user confirmation | -> ESTABLISHED |
| Multiple corroborating sources | -> WORKING |
| Single source, no contradictions | -> WORKING |
| No evidence or conflicting | -> OPEN |

### Step 3: Consider Impact

High-impact assumptions (architecture, security, data handling) should start at OPEN unless strongly evidenced.

---

## Classification Examples

### Architecture & Tech Stack

| Assumption | Type | Tier | Reasoning |
|------------|------|------|-----------|
| "Uses TypeScript" | inferred | WORKING | tsconfig.json present |
| "React 18 with hooks" | inferred | WORKING | package.json shows react@18 |
| "No server-side rendering" | inferred | OPEN | High impact, needs validation |
| "Monorepo structure" | inferred | WORKING | Multiple packages/ dirs |

### Coding Standards

| Assumption | Type | Tier | Reasoning |
|------------|------|------|-----------|
| "ESLint Airbnb config" | inferred | WORKING | .eslintrc extends airbnb |
| "Prettier for formatting" | inferred | WORKING | .prettierrc present |
| "2-space indentation" | inferred | ESTABLISHED | Consistent across all files |
| "Prefer named exports" | assumed | WORKING | Convention, not enforced |

### Testing

| Assumption | Type | Tier | Reasoning |
|------------|------|------|-----------|
| "Jest for unit tests" | inferred | WORKING | jest.config.js present |
| "80% coverage target" | assumed | OPEN | No config found, assumed |
| "Integration tests required" | uncertain | OPEN | Unknown requirement |

### User Preferences

| Assumption | Type | Tier | Reasoning |
|------------|------|------|-----------|
| "Prefers verbose explanations" | stated | ESTABLISHED | User said "explain thoroughly" |
| "Wants minimal changes" | inferred | WORKING | User often requests targeted fixes |
| "Likes TypeScript annotations" | assumed | WORKING | Convention, not stated |

---

## User-Added Assumptions

When users add new assumptions via "Other", they specify both tier and type:

**Format:** `{assumption text} [tier] [type]`

**Examples:**
- "Must work offline [ESTABLISHED] [stated]" - user explicitly stating a requirement
- "Prefer functional style [WORKING] [stated]" - user preference

If type not specified, default to `[stated]` since user is directly adding it.
If tier not specified, default to `WORKING`.
