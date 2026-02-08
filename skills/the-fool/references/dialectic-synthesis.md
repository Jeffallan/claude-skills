# Dialectic Synthesis

Hegelian dialectic with steel manning for constructing the strongest possible counter-argument and driving toward synthesis.

## Core Principle

The dialectic is not about winning. It is about producing a stronger position than either thesis or antithesis alone. The Fool's job is to argue the other side so well that the user is forced to either refine their position or acknowledge a genuine trade-off.

## Process

1. **Restate the thesis** — Steelman the user's position first
2. **Construct the antithesis** — Build the strongest opposing argument
3. **Present the clash** — Show where thesis and antithesis genuinely conflict
4. **Drive toward synthesis** — Propose a position that incorporates the best of both

## Steel Manning Technique

Steel manning is the opposite of straw manning. Restate the user's position in its strongest possible form before arguing against it.

### How to Steelman

| Step | Action | Example |
|------|--------|---------|
| 1. Identify the core claim | Strip away weak framing | "We should use microservices" → "Independent deployment and scaling of components will accelerate team velocity" |
| 2. Add the strongest evidence | Supply what the user implied | "...especially given 4 teams working on different release cycles" |
| 3. Acknowledge real benefits | Name what's genuinely good | "This would eliminate the current deploy queue bottleneck" |
| 4. Confirm with user | "Is this a fair restatement?" | Ensures you're attacking the real position |

### Steelman Checklist

- [ ] Have I made the position stronger, not weaker?
- [ ] Would the user recognize this as their view (or better)?
- [ ] Have I included the strongest evidence for their side?
- [ ] Am I attacking this version, not an easier one?

## Antithesis Construction

### Technique: Strongest Counter-Argument

Build the antithesis by asking: "If a smart, informed person disagreed, what would their best argument be?"

| Source of Counter-Arguments | Example |
|----------------------------|---------|
| Opposing trade-off | "Speed now vs. maintainability later" |
| Hidden cost | "The migration cost exceeds the projected savings for 18 months" |
| Alternative that solves the same problem | "A modular monolith gets 80% of the benefit at 20% of the cost" |
| Precedent from similar situations | "Company X tried this and reverted after 2 years" |
| Stakeholder the thesis doesn't serve | "The junior developers will struggle with the added complexity" |

### Reductio ad Absurdum (Supporting Technique)

Take the thesis to its logical extreme to reveal hidden limits.

| Thesis | Reductio | Reveals |
|--------|----------|---------|
| "We should optimize for developer experience" | "Then we should never ship to production, since bugs hurt DX" | DX must be balanced against delivery |
| "More tests are always better" | "Then we should have 100% coverage including getters/setters" | Test value has diminishing returns |
| "We should move fast" | "Then skip code review and testing" | Speed has a quality floor |

Use sparingly. Reductio highlights the boundary of a principle, not its invalidity.

## Synthesis Patterns

After presenting thesis and antithesis, propose a synthesis using one of these patterns.

### 1. Conditional Synthesis

"X is true **when** condition A holds; Y is true **when** condition B holds."

Example: "Microservices are right for the payment service (independent scaling, compliance boundary) but the admin dashboard should stay in the monolith (low traffic, fast iteration)."

### 2. Scope Partitioning

"Apply X to domain A and Y to domain B."

Example: "Use event sourcing for the audit trail (append-only, queryable history) but standard CRUD for user profiles (simple reads/writes)."

### 3. Temporal Synthesis

"Start with X, migrate to Y when trigger Z occurs."

Example: "Start with a monolith, extract services when team size exceeds 3 squads or deploy frequency hits weekly conflicts."

### 4. Risk Mitigation Synthesis

"Proceed with X but add safeguards from Y."

Example: "Adopt the new framework but keep the abstraction layer so we can swap back within 2 sprints."

### 5. Hybrid Extraction

"Take the strongest element from each side."

Example: "Use the microservices deployment model (independent containers) but keep a shared database with schema ownership (avoiding distributed data complexity)."

## Confidence Assessment

Rate the synthesis outcome.

| Level | Meaning | Action |
|-------|---------|--------|
| **HIGH** | Synthesis clearly stronger than either side alone | Proceed with synthesis |
| **MEDIUM** | Synthesis is plausible but untested | Identify the riskiest assumption and suggest an experiment |
| **LOW** | Both sides have strong, irreconcilable claims | Name the genuine trade-off; let the user decide based on priorities |
| **PIVOT** | The antithesis is stronger than the thesis | Recommend the user reconsider their original position |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| False synthesis | "Just do both!" without resolving the tension | Name the specific trade-off being resolved |
| Weak antithesis | Counter-argument is a strawman | Apply steel manning to the counter too |
| Thesis bias | Synthesis suspiciously close to original position | Check if antithesis was genuinely engaged |
| Complexity creep | Synthesis is more complex than either original | Simpler synthesis is usually better |
| Fence-sitting | "It depends" without specifying on what | Name the exact conditions for each path |

## Output Template

```markdown
## Thesis (Steelmanned)

[User's position restated in strongest form]

**Strongest evidence for:** [1-2 supporting points]

## Antithesis

[Strongest counter-argument]

**Strongest evidence for:** [1-2 supporting points]

## Points of Genuine Conflict

| Dimension | Thesis Says | Antithesis Says |
|-----------|------------|-----------------|
| [e.g., Speed] | [Position] | [Counter-position] |
| [e.g., Cost] | [Position] | [Counter-position] |

## Proposed Synthesis

**Pattern:** [Conditional / Scope / Temporal / Risk Mitigation / Hybrid]

[Concrete synthesis proposal]

**What this preserves from the thesis:** [specific elements]
**What this incorporates from the antithesis:** [specific elements]
**What this gives up:** [explicit trade-offs]

**Confidence:** HIGH / MEDIUM / LOW / PIVOT
**If MEDIUM:** Test [riskiest assumption] by [experiment]
```
