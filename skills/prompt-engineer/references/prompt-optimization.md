# Prompt Optimization

---

## The Optimization Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROMPT OPTIMIZATION CYCLE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐        │
│    │ Baseline │────▶│  Measure │────▶│ Diagnose │────▶│  Change  │        │
│    │  Prompt  │     │ Results  │     │  Issues  │     │   One    │        │
│    └──────────┘     └──────────┘     └──────────┘     └────┬─────┘        │
│         ▲                                                   │              │
│         │                                                   │              │
│         └───────────────────────────────────────────────────┘              │
│                           (Iterate until target met)                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **CRITICAL RULE: Change one variable at a time.** Multiple simultaneous changes make it impossible to identify what worked.

---

## Establishing a Baseline

Before optimizing, establish clear metrics and baseline performance.

### Baseline Checklist

```markdown
## Prompt Baseline Document

### Prompt Version: v1.0.0
### Date: YYYY-MM-DD
### Model: claude-opus-4-5-20251101

### Task Definition
[What should the prompt accomplish?]

### Success Criteria
- Primary metric: [e.g., accuracy >= 95%]
- Secondary metrics: [e.g., latency < 2s, cost < $0.01/request]

### Test Set
- Size: [number of test cases]
- Source: [how test cases were collected]
- Categories: [breakdown by type/difficulty]

### Baseline Results
| Metric | Value | Target |
|--------|-------|--------|
| Accuracy | 82% | 95% |
| Avg latency | 1.8s | <2s |
| Avg tokens | 450 | <300 |
| Cost/request | $0.015 | <$0.01 |
```

### Creating a Representative Test Set

```python
def create_test_set(task_type: str, size: int = 100) -> list:
    """Create a diverse test set for prompt evaluation."""
    test_cases = []

    # Include different categories
    categories = {
        "typical": 0.60,      # Common cases (60%)
        "edge_case": 0.20,    # Boundary conditions (20%)
        "adversarial": 0.10,  # Tricky inputs (10%)
        "malformed": 0.10,    # Invalid/unusual inputs (10%)
    }

    for category, proportion in categories.items():
        count = int(size * proportion)
        test_cases.extend(generate_cases(task_type, category, count))

    return test_cases
```

---

## Diagnostic Framework

When prompts underperform, diagnose the root cause before changing anything.

### Failure Category Analysis

| Failure Type | Symptoms | Common Causes |
|--------------|----------|---------------|
| **Format errors** | Wrong structure, missing fields | Unclear format spec, no examples |
| **Hallucinations** | Made-up facts, wrong answers | Lack of grounding, vague instructions |
| **Inconsistency** | Same input, different outputs | Ambiguous instructions, high temperature |
| **Over-verbosity** | Too much explanation | No length constraints, wrong audience |
| **Under-performance** | Low accuracy across board | Wrong pattern choice, insufficient context |
| **Edge case failures** | Breaks on unusual inputs | Missing constraint handling |

### Diagnostic Questions

```markdown
## Prompt Diagnostic Checklist

### 1. Instruction Clarity
- [ ] Is the task unambiguously defined?
- [ ] Are constraints explicit?
- [ ] Is the output format specified?

### 2. Context Sufficiency
- [ ] Does the model have all needed information?
- [ ] Are examples representative of real inputs?
- [ ] Is domain knowledge assumed correctly?

### 3. Edge Case Coverage
- [ ] Empty inputs?
- [ ] Maximum length inputs?
- [ ] Invalid/malformed inputs?
- [ ] Ambiguous cases?

### 4. Instruction Conflicts
- [ ] Do any instructions contradict each other?
- [ ] Do examples match the instructions?
- [ ] Are constraints achievable together?
```

### Error Analysis Template

```python
def analyze_failures(results: list) -> dict:
    """Categorize and analyze prompt failures."""
    analysis = {
        "total": len(results),
        "passed": 0,
        "failed": 0,
        "failure_categories": {},
        "examples": []
    }

    for result in results:
        if result["passed"]:
            analysis["passed"] += 1
        else:
            analysis["failed"] += 1
            category = categorize_failure(result)
            analysis["failure_categories"][category] = \
                analysis["failure_categories"].get(category, 0) + 1

            # Keep first 3 examples per category
            if len([e for e in analysis["examples"] if e["category"] == category]) < 3:
                analysis["examples"].append({
                    "category": category,
                    "input": result["input"],
                    "expected": result["expected"],
                    "actual": result["actual"],
                    "hypothesis": generate_hypothesis(result)
                })

    return analysis
```

---

## Optimization Techniques

### Technique 1: Instruction Refinement

**Problem:** Vague or ambiguous instructions leading to inconsistent outputs.

**Before:**
```
Summarize this article.

{article}
```

**After:**
```
Summarize the following article in exactly 2-3 sentences.
Focus on the main conclusion and key supporting evidence.
Do not include quotes or specific numbers unless essential.
Write for a general audience with no assumed domain knowledge.

Article:
{article}

Summary:
```

### Technique 2: Constraint Tightening

**Problem:** Outputs that are technically correct but don't meet practical needs.

**Before:**
```
Extract the email addresses from this text.

{text}
```

**After:**
```
Extract all valid email addresses from the following text.

Requirements:
- Return as a JSON array of strings
- Return empty array [] if no emails found
- Only include properly formatted emails (user@domain.tld)
- Deduplicate - each email appears once
- Sort alphabetically

Text:
{text}

Emails:
```

### Technique 3: Example Calibration

**Problem:** Few-shot examples that don't match real-world input distribution.

```python
def calibrate_examples(example_pool: list, real_inputs: list, k: int = 5) -> list:
    """Select examples that match the distribution of real inputs."""
    # Cluster real inputs
    real_clusters = cluster_by_embedding(real_inputs, n_clusters=k)

    # For each cluster, find best matching example
    calibrated = []
    for cluster_center in real_clusters:
        best_match = max(
            example_pool,
            key=lambda ex: cosine_similarity(embed(ex["input"]), cluster_center)
        )
        calibrated.append(best_match)

    return calibrated
```

### Technique 4: Output Scaffolding

**Problem:** Model produces correct content but wrong structure.

**Before:**
```
Analyze this code for security issues.
```

**After:**
```
Analyze this code for security issues using the following structure:

## Summary
[One sentence overview]

## Issues Found
For each issue:
- **Severity:** [Critical/High/Medium/Low]
- **Location:** [file:line or function name]
- **Description:** [What's wrong]
- **Fix:** [How to remediate]

## Recommendation
[Overall assessment and priority order for fixes]

Code:
{code}
```

---

## Token Optimization

### Token Reduction Strategies

| Strategy | Savings | Risk | When to Use |
|----------|---------|------|-------------|
| Remove redundant instructions | 10-20% | Low | Always |
| Shorten examples | 20-40% | Medium | Token-constrained |
| Use abbreviations/symbols | 5-15% | Medium | Technical audiences |
| Compress context | 30-50% | High | Very long inputs |
| Switch to zero-shot | 40-60% | High | Simple tasks |

### Before/After: Token Reduction

**Before (180 tokens):**
```
You are a helpful assistant that specializes in analyzing customer feedback
and extracting sentiment information. Your task is to read the customer
review provided below and determine whether the overall sentiment expressed
in the review is positive, negative, or neutral. Please respond with exactly
one word: either "positive", "negative", or "neutral". Do not include any
other text, explanations, or formatting in your response.

Customer Review:
{review}

Sentiment:
```

**After (45 tokens):**
```
Classify sentiment as: positive, negative, or neutral.
Reply with one word only.

Review: {review}

Sentiment:
```

### Measuring Token Impact

```python
import tiktoken

def compare_token_usage(prompt_v1: str, prompt_v2: str, model: str = "gpt-4") -> dict:
    """Compare token usage between two prompt versions."""
    enc = tiktoken.encoding_for_model(model)

    v1_tokens = len(enc.encode(prompt_v1))
    v2_tokens = len(enc.encode(prompt_v2))

    return {
        "v1_tokens": v1_tokens,
        "v2_tokens": v2_tokens,
        "difference": v1_tokens - v2_tokens,
        "reduction_pct": ((v1_tokens - v2_tokens) / v1_tokens) * 100,
        "cost_impact": estimate_cost_savings(v1_tokens, v2_tokens, model)
    }
```

### Context Compression Techniques

```python
def compress_context(text: str, target_ratio: float = 0.5) -> str:
    """Compress context while preserving key information."""

    # Strategy 1: Extractive summarization
    key_sentences = extract_key_sentences(text, ratio=target_ratio)

    # Strategy 2: Remove redundancy
    deduplicated = remove_redundant_info(key_sentences)

    # Strategy 3: Use LLM for compression
    compressed = llm.complete(f"""
    Compress the following text to {int(target_ratio * 100)}% of its length.
    Preserve all facts, numbers, and key details.
    Remove only redundant or low-information content.

    Text: {deduplicated}

    Compressed:
    """)

    return compressed
```

---

## A/B Testing Framework

### Test Design

```python
class PromptABTest:
    """Framework for A/B testing prompt variants."""

    def __init__(self, prompt_a: str, prompt_b: str, test_cases: list):
        self.prompt_a = prompt_a
        self.prompt_b = prompt_b
        self.test_cases = test_cases
        self.results = {"a": [], "b": []}

    def run(self, sample_size: int = 100) -> dict:
        """Run A/B test with randomized assignment."""
        import random

        for test_case in random.sample(self.test_cases, sample_size):
            # Randomize order to avoid position bias
            if random.random() < 0.5:
                result_a = self.evaluate(self.prompt_a, test_case)
                result_b = self.evaluate(self.prompt_b, test_case)
            else:
                result_b = self.evaluate(self.prompt_b, test_case)
                result_a = self.evaluate(self.prompt_a, test_case)

            self.results["a"].append(result_a)
            self.results["b"].append(result_b)

        return self.analyze_results()

    def analyze_results(self) -> dict:
        """Statistical analysis of A/B test results."""
        from scipy import stats

        scores_a = [r["score"] for r in self.results["a"]]
        scores_b = [r["score"] for r in self.results["b"]]

        t_stat, p_value = stats.ttest_ind(scores_a, scores_b)

        return {
            "prompt_a_mean": sum(scores_a) / len(scores_a),
            "prompt_b_mean": sum(scores_b) / len(scores_b),
            "p_value": p_value,
            "significant": p_value < 0.05,
            "winner": "a" if sum(scores_a) > sum(scores_b) else "b",
            "confidence": 1 - p_value
        }
```

### Minimum Sample Size Calculation

```python
def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    significance_level: float = 0.05,
    power: float = 0.80
) -> int:
    """Calculate required sample size for detecting a given effect."""
    from scipy import stats

    # Effect size (Cohen's h for proportions)
    p1 = baseline_rate
    p2 = baseline_rate + minimum_detectable_effect
    h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))

    # Required sample size per group
    z_alpha = stats.norm.ppf(1 - significance_level / 2)
    z_beta = stats.norm.ppf(power)

    n = 2 * ((z_alpha + z_beta) / h) ** 2

    return math.ceil(n)

# Example: Detect 5% improvement from 80% baseline
# sample_size = calculate_sample_size(0.80, 0.05)  # ~783 per group
```

---

## Version Control for Prompts

### Prompt Versioning Schema

```yaml
# prompt_registry.yaml
prompts:
  sentiment_classifier:
    current: v2.1.0
    versions:
      v1.0.0:
        file: prompts/sentiment/v1.0.0.txt
        date: 2024-01-15
        metrics:
          accuracy: 0.82
          latency_p50: 1.2s
        status: deprecated

      v2.0.0:
        file: prompts/sentiment/v2.0.0.txt
        date: 2024-02-01
        metrics:
          accuracy: 0.89
          latency_p50: 1.1s
        changes:
          - Added few-shot examples
          - Tightened output format
        status: deprecated

      v2.1.0:
        file: prompts/sentiment/v2.1.0.txt
        date: 2024-02-15
        metrics:
          accuracy: 0.94
          latency_p50: 1.0s
        changes:
          - Optimized examples for edge cases
          - Reduced token count by 30%
        status: production
```

### Change Documentation Template

```markdown
## Prompt Change Record

### Version: v2.0.0 -> v2.1.0
### Date: 2024-02-15
### Author: [name]

### Problem Statement
Accuracy dropped to 85% on sarcastic reviews (edge case category).

### Hypothesis
Current examples don't include sarcastic tone, causing misclassification.

### Changes Made
1. Added 2 sarcastic review examples
2. Added instruction: "Consider tone and context, not just words"
3. Removed verbose instruction paragraph (token optimization)

### Test Results
| Metric | v2.0.0 | v2.1.0 | Change |
|--------|--------|--------|--------|
| Overall accuracy | 89% | 94% | +5% |
| Sarcasm accuracy | 62% | 91% | +29% |
| Tokens | 156 | 109 | -30% |

### Rollback Plan
Revert to v2.0.0 if accuracy drops below 90% in production.
```

---

## Common Optimization Mistakes

| Mistake | Why It's Wrong | Better Approach |
|---------|----------------|-----------------|
| Multiple changes at once | Can't identify what worked | One change per iteration |
| Testing on training examples | Overfitting to test set | Hold out validation set |
| Optimizing for edge cases first | May hurt common case | Fix common cases first |
| Ignoring latency/cost | Production constraints matter | Track all metrics |
| No baseline measurement | Can't prove improvement | Always measure first |
| Skipping failure analysis | Symptoms vs. root cause | Diagnose before changing |

---

## Optimization Decision Tree

```
                    ┌──────────────────────────┐
                    │   Prompt Underperforms   │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  What's the failure mode? │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
  Format Issues            Wrong Content           Inconsistent
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ Add output    │      │ Improve       │      │ Add examples  │
│ scaffolding   │      │ instructions  │      │ Lower temp    │
│ Add examples  │      │ Add context   │      │ Add constraints│
└───────────────┘      │ Use CoT       │      └───────────────┘
                       └───────────────┘
```

---

## Related Skills

- **Evaluation Frameworks** - Measuring prompt performance systematically
- **Fine-Tuning Expert** - When optimization hits limits
- **Cost Engineer** - Token and latency optimization at scale
