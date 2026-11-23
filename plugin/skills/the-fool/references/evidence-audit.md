# Evidence Audit

Falsificationism and evidence quality assessment for auditing whether claims are actually supported by evidence.

## Core Principle

Karl Popper's key insight: a claim is only meaningful if you can specify what would disprove it. The Evidence Audit mode extracts claims from proposals, designs falsification criteria, assesses evidence quality, and surfaces competing explanations. The goal is not to disprove — it is to determine whether the evidence actually supports the conclusion.

## Process

1. **Extract claims** — Identify the specific claims being made
2. **Design falsification criteria** — For each claim, specify what would disprove it
3. **Assess evidence quality** — Evaluate the evidence supporting each claim
4. **Identify cognitive biases** — Check for systematic errors in reasoning
5. **Surface competing explanations** — Find alternative explanations for the same evidence

## Claim Extraction

Proposals contain claims — often implicit. Extract them before evaluating.

### Types of Claims

| Type | Example | Hidden In |
|------|---------|-----------|
| **Causal** | "X causes Y" | "Our refactor improved performance" |
| **Predictive** | "X will happen" | "Users will adopt this feature" |
| **Comparative** | "X is better than Y" | "React is the better choice for us" |
| **Existential** | "X exists/doesn't exist" | "There's no alternative that meets our needs" |
| **Universal** | "X is always true" | "Microservices always improve team velocity" |
| **Quantitative** | "X is N" | "This will save 200 hours per quarter" |

### Extraction Method

For each statement in the proposal:
1. Is this a claim or a definition?
2. If a claim, what type?
3. What evidence is cited (or implied)?
4. What would make this claim false?

### Example Extraction

```
Statement: "Based on our pilot, migrating to Kubernetes will reduce deployment time by 60%."

Claims extracted:
1. The pilot results are representative of production (Predictive)
2. Kubernetes is the cause of the deployment time reduction (Causal)
3. The 60% reduction will persist at scale (Quantitative)
```

## Falsification Criteria

For each claim, design a test that would disprove it.

| Claim | Falsification Criterion | Test |
|-------|------------------------|------|
| "Users want feature X" | Fewer than 10% of users engage with X within 30 days | Feature flag, measure adoption |
| "This will scale to 100K users" | Response time exceeds 500ms at 50K users | Load test at target scale |
| "Migration will take 3 months" | More than 2 unknown-unknowns discovered in month 1 | Track surprise count during initial phase |
| "Framework X is faster" | Benchmark shows less than 5% difference | Controlled benchmark on representative workload |
| "This will reduce costs" | Total cost of ownership exceeds current cost within 12 months | TCO analysis including migration, training, operations |

### Unfalsifiable Claims (Red Flag)

Some claims cannot be falsified. These are red flags.

| Pattern | Example | Problem |
|---------|---------|---------|
| Vague outcome | "This will improve things" | No measurable criterion |
| Moving goalposts | "It'll work eventually" | No time boundary |
| Circular reasoning | "This is the best because it's what experts recommend" | Evidence is the claim restated |
| Unfalsifiable hedge | "This might help in some cases" | True by definition |

When you encounter unfalsifiable claims, ask: "What specific, measurable outcome would tell us this worked or didn't work?"

## Evidence Quality Assessment

Not all evidence is equal. Assess each piece of evidence on these dimensions.

### Evidence Quality Matrix

| Dimension | Strong | Weak |
|-----------|--------|------|
| **Sample size** | Large, representative sample | Single case, anecdote |
| **Recency** | Current data (within 12 months) | Outdated (2+ years) |
| **Relevance** | Same domain, same scale | Different domain or scale |
| **Independence** | Multiple independent sources | Single source or vendor-provided |
| **Methodology** | Controlled, reproducible | Ad hoc, unreproducible |
| **Specificity** | Precise metrics and conditions | Vague or qualitative |

### Evidence Grading Scale

| Grade | Description | Reliability |
|-------|-------------|------------|
| **A** | Controlled experiment, large sample, reproducible | High confidence |
| **B** | Observational data, reasonable sample, consistent with other evidence | Moderate confidence |
| **C** | Case study, small sample, or single source | Low confidence — needs corroboration |
| **D** | Anecdote, opinion, or vendor marketing material | Insufficient — do not base decisions on this alone |
| **F** | No evidence cited | Claim is unsupported |

### Common Weak Evidence Patterns

| Pattern | Example | Why It's Weak |
|---------|---------|---------------|
| Survivorship bias | "Companies using X are successful" | Ignores companies using X that failed |
| Cherry-picked metrics | "Response time improved 40%" | Other metrics (error rate, throughput) may have worsened |
| Vendor benchmarks | "Our tool is 3x faster" | Benchmarks optimized for vendor's strengths |
| Appeal to authority | "Google does it this way" | Google's constraints are not your constraints |
| Anchoring | "Industry average is X, we're at Y" | The average may not be the right benchmark |

## Cognitive Bias Awareness

Check for these biases in the reasoning chain.

| Bias | Description | Detection Signal |
|------|-------------|-----------------|
| **Confirmation bias** | Seeking evidence that confirms existing belief | Only positive evidence cited; no counter-evidence considered |
| **Survivorship bias** | Focusing on successes, ignoring failures | "All the successful companies do X" |
| **Anchoring** | Over-relying on first piece of information | First estimate unchanged despite new data |
| **Sunk cost fallacy** | Continuing because of past investment | "We've already spent 6 months on this" as justification |
| **Availability heuristic** | Overweighting recent or vivid examples | Decision based on one memorable incident |
| **Bandwagon effect** | "Everyone is doing it" | Trend adoption without fitness assessment |
| **Dunning-Kruger** | Overconfidence in unfamiliar domain | Confident claims about areas outside expertise |
| **Status quo bias** | Preferring current state despite evidence for change | "It's always been this way" |

## Competing Explanations (Abductive Reasoning)

For every conclusion, ask: "What else could explain this evidence?"

### Method

1. State the evidence
2. State the proposed explanation
3. Generate 2-3 alternative explanations
4. Compare explanatory power

### Example

```
Evidence: "Deployment failures dropped 50% after adopting tool X."

Proposed explanation: Tool X is better than the old tool.

Alternative explanations:
1. The team also started doing more code review in the same period
2. A particularly error-prone service was retired last month
3. The team gained experience that would have improved results with any tool
```

## Output Template

```markdown
## Evidence Audit: [Proposal/Decision]

### Claims Extracted

| # | Claim | Type | Evidence Cited |
|---|-------|------|---------------|
| 1 | [Specific claim] | Causal/Predictive/etc. | [What evidence supports it] |
| 2 | [Specific claim] | Causal/Predictive/etc. | [What evidence supports it] |
| 3 | [Specific claim] | Causal/Predictive/etc. | [What evidence supports it] |

### Falsification Criteria

| Claim | What Would Disprove It | How to Test |
|-------|----------------------|-------------|
| #1 | [Specific criterion] | [Concrete test] |
| #2 | [Specific criterion] | [Concrete test] |

### Evidence Quality

| Claim | Evidence Grade | Key Weakness |
|-------|--------------|--------------|
| #1 | A/B/C/D/F | [Primary concern] |
| #2 | A/B/C/D/F | [Primary concern] |

### Bias Check

| Bias Detected | Where | Impact |
|--------------|-------|--------|
| [Bias name] | Claim #X | [How it affects the conclusion] |

### Competing Explanations

| Evidence | Proposed Explanation | Alternative Explanations |
|----------|---------------------|------------------------|
| [Data point] | [Original claim] | 1. [Alternative] 2. [Alternative] |

### Verdict

**Overall evidence strength:** Strong / Moderate / Weak / Insufficient

**Recommendations:**
1. [Specific action to strengthen the weakest claim]
2. [Specific action to test the riskiest assumption]
```
