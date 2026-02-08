# Socratic Questioning

Structured question frameworks for exposing assumptions and deepening understanding.

## Core Principle

Socratic questioning does not argue. It asks. The goal is to help the user discover gaps in their own reasoning by surfacing what they have not examined. Every question should create a moment of "I hadn't thought about that."

## Question Categories

### 1. Definitional Questions

Challenge vague or overloaded terms.

| Pattern | Example |
|---------|---------|
| "When you say X, what specifically do you mean?" | "When you say 'scalable,' do you mean 10x users or 1000x?" |
| "How would you define X to someone unfamiliar?" | "How would you explain 'real-time' to a non-engineer?" |
| "Are there cases where X means something different?" | "Does 'fast' mean the same thing for API response and batch job?" |

### 2. Evidential Questions

Probe the basis for beliefs.

| Pattern | Example |
|---------|---------|
| "What evidence supports this?" | "What data shows users actually want this feature?" |
| "How do you know X is true?" | "How do you know the current system can't handle the load?" |
| "What would change your mind?" | "What metric would convince you this approach is wrong?" |
| "Is this based on data or intuition?" | "Is the 'users hate the current flow' claim from research or assumption?" |

### 3. Logical Questions

Test the reasoning chain.

| Pattern | Example |
|---------|---------|
| "Does X necessarily lead to Y?" | "Does adding caching necessarily improve user experience?" |
| "What assumptions connect X to Y?" | "What has to be true for microservices to improve velocity?" |
| "Could the opposite also be true?" | "Could a monolith actually ship faster in this case?" |
| "Are you conflating correlation with causation?" | "Did the refactor cause the improvement, or was it the new hire?" |

### 4. Perspective-Shifting Questions

Force consideration of other viewpoints.

| Pattern | Example |
|---------|---------|
| "How would [stakeholder] see this?" | "How would the on-call engineer feel about this architecture?" |
| "What would a skeptic say?" | "What would a senior engineer who prefers simplicity say?" |
| "What does this look like in 2 years?" | "Will this abstraction still make sense when the team doubles?" |
| "Who loses if this succeeds?" | "If we adopt this vendor, what capability do we give up?" |

### 5. Consequential Questions

Trace the implications.

| Pattern | Example |
|---------|---------|
| "What happens next?" | "After we migrate, what's the first thing that breaks?" |
| "What's the second-order effect?" | "If we hire contractors to speed up, what happens to team knowledge?" |
| "What's the cost of being wrong?" | "If this assumption is wrong, how bad is the recovery?" |
| "What becomes harder later?" | "What future feature becomes harder if we choose this schema?" |

## Assumption Detection Signals

Watch for language that hides assumptions.

| Signal Phrase | Hidden Assumption |
|---------------|-------------------|
| "Obviously..." | The speaker hasn't questioned this |
| "Everyone knows..." | Consensus hasn't been verified |
| "It just makes sense..." | The reasoning chain hasn't been articulated |
| "We always..." | Historical pattern assumed to be optimal |
| "There's no other way..." | Alternatives haven't been explored |
| "It's simple..." | Complexity has been underestimated |
| "Users want..." | User research may be absent or stale |
| "The standard approach is..." | Convention hasn't been validated for this context |

## Domain-Adapted Question Banks

### Technical Decisions

- What are you optimizing for? Are you sure that's the right dimension?
- What's the simplest version that tests the core assumption?
- What constraint are you treating as fixed that might actually be flexible?
- How would you build this if you had to ship in one week?
- What's the most expensive thing to change later?

### Business Decisions

- Who is the customer for this decision? Are you sure?
- What would make this a bad investment in hindsight?
- How does this compare to doing nothing?
- What's the opportunity cost of this choice?
- If a competitor made the opposite choice, would you be worried?

### Strategic Decisions

- What has to be true for this strategy to work?
- Which of those assumptions are you least confident about?
- What's the fastest way to test the riskiest assumption?
- How will you know if this is failing before it's too late?
- What's the exit strategy if this doesn't work?

## Output Template

```markdown
## Assumption Inventory

| # | Assumption | Type | Confidence |
|---|-----------|------|------------|
| 1 | [Stated or hidden assumption] | Stated / Unstated | High / Medium / Low |

## Probing Questions

### [Theme 1: e.g., "User Behavior"]
1. [Question targeting assumption #X]
2. [Follow-up question deepening the probe]

### [Theme 2: e.g., "Technical Feasibility"]
1. [Question targeting assumption #Y]
2. [Follow-up question]

### [Theme 3: e.g., "Business Viability"]
1. [Question targeting assumption #Z]
2. [Follow-up question]

## Suggested Experiments

| Assumption | Experiment | Effort | Signal |
|-----------|-----------|--------|--------|
| [Riskiest assumption] | [How to test it] | Low/Med/High | [What result means] |
```
