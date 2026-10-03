# Mode Selection Guide

How to recommend the right reasoning mode when the user selects "You choose" or when auto-recommending.

## Signal-to-Mode Mapping

Analyze the user's language and context to identify which mode fits best.

| User Signal | Recommended Mode | Rationale |
|-------------|-----------------|-----------|
| "Is this the right approach?" | Socratic Questioning | Exploring assumptions, not yet committed |
| "I'm about to commit to X" | Dialectic Synthesis | Needs strongest counter-argument before committing |
| "What could go wrong?" | Pre-mortem Analysis | Explicitly asking about failure modes |
| "Is this secure/safe?" | Red Team | Security and adversarial framing |
| "The data shows that..." | Evidence Audit | Claims based on evidence need falsification |
| "Everyone agrees that..." | Socratic Questioning | Consensus signals unexamined assumptions |
| "We chose X over Y" | Dialectic Synthesis | Trade-off decision benefits from strongest counter |
| "This will definitely work" | Pre-mortem Analysis | Overconfidence signals need for failure imagination |
| "No one would ever..." | Red Team | Assumptions about adversary behavior |
| "Studies show..." | Evidence Audit | Cited evidence needs quality assessment |

## Decision Type Mapping

| Decision Type | Primary Mode | Secondary Mode |
|---------------|-------------|----------------|
| Technology choice | Dialectic Synthesis | Pre-mortem Analysis |
| Architecture decision | Pre-mortem Analysis | Red Team |
| Business strategy | Dialectic Synthesis | Evidence Audit |
| Security design | Red Team | Pre-mortem Analysis |
| Data-driven conclusion | Evidence Audit | Socratic Questioning |
| Process/workflow design | Pre-mortem Analysis | Socratic Questioning |
| Hiring/team decision | Socratic Questioning | Dialectic Synthesis |
| Vendor selection | Pre-mortem Analysis | Dialectic Synthesis |
| Trade-off resolution | Dialectic Synthesis | Socratic Questioning |
| Risk assessment | Red Team | Pre-mortem Analysis |

## Domain Mapping

| Domain | Default Mode | Why |
|--------|-------------|-----|
| Security | Red Team | Adversarial thinking is native to the domain |
| Infrastructure | Pre-mortem Analysis | Failure modes are the primary concern |
| Data/Analytics | Evidence Audit | Claims require evidence scrutiny |
| Product/UX | Socratic Questioning | Assumptions about users need surfacing |
| Business | Dialectic Synthesis | Strategy benefits from strongest counter |
| Architecture | Pre-mortem Analysis | Systems fail at integration points |
| Legal/Compliance | Evidence Audit | Claims must withstand scrutiny |

## Multi-Mode Sequencing

Some situations benefit from running 2 modes in sequence.

### Recommended Sequences

| Sequence | When to Use |
|----------|-------------|
| Socratic → Dialectic | User has an untested idea. Surface assumptions first, then argue the counter. |
| Pre-mortem → Red Team | High-stakes system launch. Find internal failures, then external attacks. |
| Evidence Audit → Socratic | Data-driven proposal. Audit the evidence, then question the interpretation. |
| Dialectic → Pre-mortem | Strategic decision. Argue the counter, then stress-test the surviving position. |

### When to Suggest Multi-Mode

Recommend a second pass when:
- The first mode reveals a category of risk the user hadn't considered
- The thesis survives the first challenge largely intact (it may need harder testing)
- The domain spans two mapping categories (e.g., a security architecture decision)

### When NOT to Suggest Multi-Mode

- The user's question is narrow and specific
- The first mode already surfaced actionable changes
- The user signals they want to move on

## Auto-Recommendation Format

When presenting the recommendation, use this structure:

```
Based on [specific context signal], I recommend **[Mode Name]** because [1-sentence rationale].

[If a secondary mode is relevant:]
After that, a follow-up with **[Secondary Mode]** would [1-sentence benefit].
```

Then confirm with `AskUserQuestion`:
- Option 1: Recommended mode (with "(Recommended)" label)
- Option 2: Secondary mode if applicable
- Option 3: "Let me pick" — return to the full mode selection

## Edge Cases

- **Vague context**: Default to Socratic Questioning — it surfaces what matters
- **Multiple concerns**: Recommend Pre-mortem Analysis — it covers breadth naturally
- **User is emotional/frustrated**: Default to Dialectic Synthesis — steel manning validates their position before challenging it
- **Technical vs business split**: Match the mode to which side the user emphasizes
