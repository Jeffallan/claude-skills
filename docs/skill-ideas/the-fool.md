# Plan: `the-fool` Skill

## Summary

Create a domain-agnostic critical reasoning skill with 5 modes, rooted in the archetype of the Fool — the one who speaks truth to power. Uses `AskUserQuestions` for mode selection. Invoked organically mid-conversation with "play the fool" as mandatory trigger.

## File Structure

```
skills/the-fool/
  SKILL.md                              (~95 lines)
  references/
    socratic-questioning.md             (~150 lines)
    dialectic-synthesis.md              (~150 lines)
    pre-mortem-analysis.md              (~200 lines)
    red-team-adversarial.md             (~150 lines)
    evidence-audit.md                   (~150 lines)
    mode-selection-guide.md             (~100 lines)
```

## SKILL.md Design

### Frontmatter

```yaml
---
name: the-fool
description: Use when challenging ideas, plans, decisions, or proposals using structured critical reasoning. Invoke to play the fool, devil's advocate, pre-mortem, red team, or evidence audit.
triggers:
  - play the fool
  - devil's advocate
  - challenge this
  - stress test
  - poke holes
  - what could go wrong
  - red team
  - pre-mortem
  - test my assumptions
role: expert
scope: review
output-format: report
---
```

### Role Definition

The Fool — the court jester who alone could speak truth to the king. Not naive but strategically unbound by convention, hierarchy, or politeness. Applies structured critical reasoning across 5 modes to stress-test any idea, plan, or decision.

### When to Use

- Stress-testing a plan, architecture, or strategy before committing
- Challenging technology, vendor, or approach choices
- Evaluating business proposals, value propositions, or strategies
- Red-teaming a design before implementation
- Auditing whether evidence actually supports a conclusion
- Finding blind spots and unstated assumptions

### Core Workflow (5 steps)

1. **Identify (Thesis)** — Extract the user's position from conversation context. Restate it as a steelmanned thesis for confirmation.
2. **Select (Method)** — Use `AskUserQuestions` to let the user choose a reasoning mode, or auto-recommend based on context signals.
3. **Challenge (Antithesis)** — Apply the selected mode's method. Load the corresponding reference file for deep guidance.
4. **Engage (Dialogue)** — Present findings. Ask the user to respond to the strongest 2-3 points before proceeding.
5. **Synthesize (Resolution)** — Integrate insights into a strengthened position. Offer to run a second pass with a different mode.

### 5 Reasoning Modes

| Mode | Method | Output |
|------|--------|--------|
| Expose My Assumptions | Socratic questioning | Probing questions grouped by theme |
| Argue the Other Side | Hegelian dialectic + steel manning | Counter-argument and synthesis proposal |
| Find the Failure Modes | Pre-mortem + second-order thinking | Ranked failure narratives with mitigations |
| Attack This | Red teaming | Adversary profile, attack vectors, defenses |
| Test the Evidence | Falsificationism + evidence weighting | Claims audited with falsification criteria |

### AskUserQuestions Integration

**Mode Selection Question:**
```
Header: "Challenge Mode"
Question: "How should I challenge this?"

Options:
1. "Expose my assumptions" — Ask me the hard questions I haven't asked myself
2. "Argue the other side" — Build the strongest counter-argument and drive toward synthesis
3. "Find the failure modes" — Assume this fails and tell me why
4. "Attack this" — Think like an adversary looking for weaknesses
5. "You choose" — Recommend the best approach based on context
```

If "You choose" is selected, skill analyzes context signals and recommends 1-2 modes with rationale, then confirms with a follow-up AskUserQuestions.

### Reference Routing Table

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Socratic questioning | `references/socratic-questioning.md` | "Expose my assumptions" mode selected |
| Dialectic & synthesis | `references/dialectic-synthesis.md` | "Argue the other side" mode selected |
| Pre-mortem analysis | `references/pre-mortem-analysis.md` | "Find the failure modes" mode selected |
| Red team adversarial | `references/red-team-adversarial.md` | "Attack this" mode selected |
| Evidence audit | `references/evidence-audit.md` | "Test the evidence" mode selected |
| Mode selection guide | `references/mode-selection-guide.md` | "You choose" selected, or skill needs to auto-recommend |

### Constraints

**MUST DO:**
- Steelman the thesis before challenging it (restate in strongest form)
- Use `AskUserQuestions` for mode selection — never assume which mode
- Ground challenges in specific, concrete reasoning (not vague "what ifs")
- Maintain intellectual honesty — concede points that hold up
- Drive toward synthesis or actionable output (never leave the user with just objections)
- Adapt challenge depth to the domain and stakes
- Limit challenges to 3-5 strongest points (depth over breadth)
- Ask user to engage before synthesizing

**MUST NOT DO:**
- Strawman the user's position
- Generate challenges for the sake of disagreement
- Be nihilistic or purely destructive
- Stack minor objections to create false impression of weakness
- Skip synthesis (never leave the user with just a pile of problems)
- Override domain expertise with generic skepticism
- Output mode selection as plain text when `AskUserQuestions` can provide structured options

### Related Skills
- **Common Ground** — Surface hidden assumptions (use *before* the-fool)
- **Architecture Designer** — Document refined decisions as ADRs (use *after* the-fool)
- **Code Reviewer** — Structured critique of implementations (tactical counterpart)
- **Feature Forge** — Requirements elicitation (challenge specs *after* forging)

## Reference File Designs

### 1. `references/socratic-questioning.md` (~150 lines)

Structured question frameworks for exposing assumptions:
- Question categories: definitional, evidential, logical, perspective-shifting, consequential
- Domain-adapted question banks (technical, business, strategic)
- Detection signals for unstated assumptions ("obviously", "everyone knows", "it just makes sense")
- Output template: Assumption Inventory + Probing Questions grouped by theme + Suggested Experiments

### 2. `references/dialectic-synthesis.md` (~150 lines)

Hegelian dialectic with steel manning:
- How to construct a proper antithesis (not a strawman)
- Steel manning technique: strengthen the opposing position before arguing it
- Reductio ad absurdum as a supporting technique
- Synthesis patterns: conditional, scope partitioning, temporal, risk mitigation, hybrid extraction
- Synthesis quality checklist and anti-patterns
- Confidence assessment: HIGH / MEDIUM / LOW / PIVOT
- Output template: Thesis Restated + Antithesis Argued + Synthesis Proposed

### 3. `references/pre-mortem-analysis.md` (~200 lines)

Pre-mortem with second-order thinking:
- How to run a pre-mortem (assume failure, explain why)
- Failure narrative construction (specific > generic)
- Second-order consequence chains (first → second → third order effects)
- Inversion technique ("what guarantees failure?")
- Domain-specific failure patterns: technical (scaling, integration, migration), business (adoption, competition, timing), process (timeline, dependencies, stakeholders)
- Output template: Failure Narratives (ranked) + Early Warning Signs + Mitigations

### 4. `references/red-team-adversarial.md` (~150 lines)

Adversarial thinking and red teaming:
- Adversary persona construction (competitor, attacker, disgruntled user, regulator)
- Attack vector identification by domain
- Perverse incentive detection ("how will people game this?")
- Competitive response analysis
- Output template: Adversary Profile + Attack Vectors (ranked by likelihood x impact) + Defenses

### 5. `references/evidence-audit.md` (~150 lines)

Falsificationism and evidence quality:
- Popper's key question: "What would disprove this?"
- Claim extraction from proposals
- Falsification criteria design
- Evidence quality assessment (sample size, representativeness, recency, relevance)
- Cognitive biases in evidence evaluation (confirmation, survivorship, anchoring, availability)
- Competing explanations (abductive reasoning)
- Output template: Claims Extracted + Falsification Criteria + Evidence Quality + Alternative Explanations

### 6. `references/mode-selection-guide.md` (~100 lines)

Context signals for auto-recommending modes:
- Signal-to-mode mapping table (user phrases → recommended mode)
- Decision type mapping (trade-offs → dialectic, execution plans → pre-mortem, etc.)
- Domain mapping (security → red team, data claims → evidence audit, etc.)
- Multi-mode sequencing recommendations (e.g., "Socratic first, then dialectic")

## Updates to Existing Files

### SKILLS_GUIDE.md
- Add to **Workflow** category (or new **Critical Thinking** category):
  `The Fool — Challenge ideas and decisions with 5 structured reasoning modes`
- Add **Critical Thinking** decision tree:
  - Surface Assumptions → Common Ground
  - Challenge Decisions → The Fool
  - Evaluate Code → Code Reviewer
  - Audit Security → Security Reviewer
- Add **Decision Validation** workflow:
  1. Common Ground (surface assumptions)
  2. The Fool (stress-test the decision)
  3. Architecture Designer (document refined decision)

## Implementation Order

1. Create `skills/the-fool/SKILL.md`
2. Create `skills/the-fool/references/mode-selection-guide.md`
3. Create `skills/the-fool/references/socratic-questioning.md`
4. Create `skills/the-fool/references/dialectic-synthesis.md`
5. Create `skills/the-fool/references/pre-mortem-analysis.md`
6. Create `skills/the-fool/references/red-team-adversarial.md`
7. Create `skills/the-fool/references/evidence-audit.md`
8. Update `SKILLS_GUIDE.md` with new skill entry

## Verification

1. `python scripts/validate-skills.py --skill the-fool` — verify YAML, description format, references
2. `python scripts/update-docs.py --check` — verify counts are in sync
3. Manually verify trigger phrases match natural invocation patterns
4. Review each reference file stays within 100-600 line bounds

## Key Files to Reference During Implementation
- `skills/feature-forge/SKILL.md` — AskUserQuestions integration pattern
- `skills/feature-forge/references/interview-questions.md` — Structured question flow examples
- `skills/code-reviewer/SKILL.md` — Review-scope skill with routing table
- `commands/common-ground/COMMAND.md` — Interactive multi-phase dialogue pattern
- `SKILLS_GUIDE.md` — Category placement and decision tree format
