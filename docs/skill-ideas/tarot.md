# Tarot-Inspired Skill Ideas

High-level concepts mapping tarot archetypes to agent behaviors. Each archetype provides a memorable invocation pattern and a distinct cognitive mode.

---

## The Fool (In Progress)

**Archetype:** The court jester who speaks truth to power.

**Purpose:** Domain-agnostic critical reasoning with 5 modes — Socratic questioning, Hegelian dialectic, pre-mortem, red teaming, and evidence audit. Uses `AskUserQuestions` for mode selection.

**Trigger:** "play the fool", "devil's advocate", "challenge this"

**Status:** Full plan at `docs/skill-ideas/the-fool.md`

---

## The Hermit

**Archetype:** The seeker who withdraws to understand before acting.

**Purpose:** Deep research and reflection. When you need to step back from implementation and truly understand something first. Systematic codebase archaeology, reading documentation thoroughly, tracing data flows end-to-end. The opposite of "let me just try something."

**Trigger:** "I need to understand this before touching it"

**Gap filled:** No existing skill enforces a read-only investigation phase before action. Debugging-wizard investigates bugs; The Hermit investigates *systems* — how they work, why they were built this way, what the original authors intended.

**Possible modes:**
- Trace a data flow end-to-end
- Map the dependency graph of a concept
- Reconstruct the decision history (git archaeology)
- Build a mental model before proposing changes

---

## The Tower

**Archetype:** Lightning strikes — the old structure falls so something better can rise.

**Purpose:** Controlled demolition and rebuild. When something is fundamentally broken and incremental fixes won't work. Guides tearing down and rebuilding: legacy system replacement, major refactors, ripping out a bad abstraction.

**Trigger:** "this needs to be torn down and rebuilt"

**Gap filled:** Legacy-modernizer focuses on incremental migration (strangler fig). The Tower is for when incremental isn't viable — you need a clean break with a structured rebuild plan.

**Possible modes:**
- Blast radius assessment (what breaks if we remove this?)
- Parallel build strategy (new system alongside old)
- Cut-over planning (the moment of switch)
- Rollback design (if the new thing fails)

---

## The Wheel of Fortune

**Archetype:** The turning wheel — fate, chance, and multiple possible futures.

**Purpose:** Scenario planning under genuine uncertainty. Not "what could go wrong" (that's The Fool's pre-mortem) but mapping multiple possible futures and building strategies robust across them. Decision-making when you genuinely don't know which way things will go.

**Trigger:** "we don't know which way this will go"

**Gap filled:** No existing skill handles multi-scenario planning. Architecture-designer evaluates trade-offs for a known context; The Wheel of Fortune plans for unknown contexts.

**Possible modes:**
- Scenario generation (3-4 plausible futures)
- Strategy robustness testing (does this plan work across scenarios?)
- Optionality analysis (which choice preserves the most future options?)
- Trigger identification (what signals tell us which scenario is unfolding?)

---

## The Magician

**Archetype:** Manifestation — turning idea into reality with the tools at hand.

**Purpose:** Rapid prototyping and proof of concept. Takes an idea and manifests the simplest possible working version to test feasibility. Ruthlessly YAGNI. "Show me the smallest thing that proves this works."

**Trigger:** "can we even do this?", "prove this works"

**Gap filled:** Feature-forge defines requirements; The Magician skips requirements and builds the thinnest possible slice to answer a feasibility question. Complements feature-forge — use The Magician to validate assumptions *before* writing specs.

**Possible modes:**
- Feasibility spike (can the technology do this at all?)
- Integration probe (can these two systems talk to each other?)
- Performance experiment (will this approach scale?)
- UX sketch (does this interaction model make sense?)

---

## The High Priestess

**Archetype:** Intuition and hidden knowledge — seeing what others miss.

**Purpose:** Pattern recognition and intuition translation. When something "feels wrong" but you can't articulate why. Translates gut feelings into concrete technical concerns. Examines code smells, architectural drift, naming inconsistencies — the subtle signals that something is off.

**Trigger:** "something about this doesn't feel right"

**Gap filled:** Code-reviewer checks against known standards. The High Priestess investigates the *unnamed* — the patterns that don't match, the drift from original intent, the subtle wrongness that no linter catches.

**Possible modes:**
- Code smell archaeology (what changed and when did it start drifting?)
- Naming analysis (do the names still match what the code does?)
- Architectural consistency (does this component belong here?)
- Implicit contract detection (what undocumented assumptions does this code rely on?)

---

## The Star

**Archetype:** The guiding light — hope, purpose, and true north.

**Purpose:** North star alignment. When you're deep in implementation weeds and need to reconnect with the original vision. Checks current work against stated goals, user needs, and project values. Detects scope creep, gold plating, and mission drift.

**Trigger:** "are we still building the right thing?"

**Gap filled:** No existing skill checks alignment between work-in-progress and original intent. Feature-forge defines the target; The Star checks whether you're still pointed at it.

**Possible modes:**
- Goal alignment audit (does this PR serve the stated objective?)
- Scope creep detection (what got added that wasn't in the spec?)
- User value check (does the end user actually benefit from this work?)
- Simplification pass (what can be removed and still deliver the value?)

---

## Death

**Archetype:** Transformation — endings that enable new beginnings.

**Purpose:** Graceful deprecation and migration. Not destruction (that's The Tower) but *transition*. Guides sunsetting features, migrating users, deprecation timelines, and backward compatibility strategies. The art of ending things well.

**Trigger:** "we need to retire this"

**Gap filled:** Overlaps with legacy-modernizer but with a different focus. Legacy-modernizer transforms old into new; Death manages the *ending* — communication, migration paths, timeline, and the social/organizational aspects of removing something people depend on.

**Possible modes:**
- Impact assessment (who uses this and how?)
- Migration path design (where do users go instead?)
- Deprecation timeline (warnings, soft removal, hard removal)
- Tombstone documentation (why was this removed, and what replaced it?)

---

## The Emperor

**Archetype:** Order, structure, authority — the rules of the realm.

**Purpose:** Governance and standards enforcement. Audits a codebase or project against its own stated standards. Checks that conventions are followed, ADRs are respected, and architectural boundaries aren't violated. Not inventing rules — enforcing the ones already committed to.

**Trigger:** "are we following our own rules?"

**Gap filled:** Overlaps with code-reviewer but scoped differently. Code-reviewer evaluates individual PRs; The Emperor evaluates systemic compliance across the whole project. Checks ADRs, CONTRIBUTING.md, architectural decision records, and stated conventions.

**Possible modes:**
- Convention audit (are naming patterns, file structures consistent?)
- ADR compliance (are architectural decisions being followed?)
- Boundary check (are module boundaries respected?)
- Drift detection (where has the codebase diverged from stated standards?)

---

## Overlap Analysis

| Skill | Overlaps With | Distinction |
|-------|--------------|-------------|
| The Fool | Common Ground, Code Reviewer | Multi-mode critical reasoning vs. assumption surfacing vs. code-level review |
| The Hermit | Spec Miner, Debugging Wizard | Understanding systems vs. extracting specs vs. finding bugs |
| The Tower | Legacy Modernizer | Clean break rebuild vs. incremental migration |
| The Wheel of Fortune | Architecture Designer | Unknown futures vs. known trade-offs |
| The Magician | Feature Forge | Feasibility proof vs. requirements definition |
| The High Priestess | Code Reviewer | Unnamed intuitions vs. known standards |
| The Star | Feature Forge | Alignment check vs. initial specification |
| Death | Legacy Modernizer | Graceful ending vs. transformation |
| The Emperor | Code Reviewer | Systemic compliance vs. individual PR review |

**Strongest unique concepts** (no significant overlap): The Hermit, The Wheel of Fortune, The High Priestess, The Star

**Interesting but overlapping** (need clear boundary with existing skills): The Tower, Death, The Emperor, The Magician
