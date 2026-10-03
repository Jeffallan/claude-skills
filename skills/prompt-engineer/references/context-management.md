# Context Management

<!-- Content adapted from PR #168 (context-engineer skill) by Genius-apple (https://github.com/Genius-apple). -->
<!-- Original submission: https://github.com/Jeffallan/claude-skills/pull/168 -->

---

## When to Use This Reference

- Designing system prompts for complex agents with large context windows
- Debugging agents that ignore instructions or hallucinate mid-conversation
- Optimizing token usage for cost or latency in long-running sessions
- Structuring conversation history and RAG retrieval for maximum signal
- Evaluating retrieval quality impact on reasoning

---

## The Context Budget

The context window is a scarce resource — an **attention budget**. Every token consumes attention capacity. Irrelevant tokens actively degrade performance.

**Key metric:** Signal-to-Noise Ratio (SNR). Higher SNR = better reasoning quality.

### Context Components

| Component | Purpose | Persistence |
|-----------|---------|-------------|
| **System Prompt** | Identity, permanent rules, output format | Static across session |
| **Few-Shot Examples** | Demonstrations of desired behavior | Static or semi-static |
| **Conversation History** | Short-term memory (user interactions) | Grows per turn |
| **Retrieved Context (RAG)** | Long-term memory or external knowledge | Dynamic per query |

### Structuring Context with XML Tags

Use explicit delimiters to separate context types. This helps the model distinguish instructions from data:

```xml
<instructions>
  You are an expert code reviewer...
</instructions>
<documents>
  <doc id="1" source="auth.py">...</doc>
  <doc id="2" source="models.py">...</doc>
</documents>
<history>
  ...recent conversation turns...
</history>
<query>
  ...current user message...
</query>
```

### Recommended Ordering

1. System Instructions (highest primacy bias)
2. Reference Material (RAG documents)
3. Few-Shot Examples
4. Conversation History
5. User Query (highest recency bias)

---

## Context Degradation Patterns

### Lost-in-the-Middle

**Symptom:** Agent ignores instructions or facts placed in the middle of long context.

**Cause:** LLMs exhibit primacy bias (strong attention to the start) and recency bias (strong attention to the end). Content in the middle receives less attention.

**Mitigation:** Move critical instructions to the beginning (system prompt) or repeat them near the end, just before the user query:

```python
# Vulnerable to lost-in-the-middle
prompt = system_prompt + long_history + user_query

# Mitigated: critical instructions repeated near the end
prompt = system_prompt + long_history + instruction_reminder + user_query
```

### Context Poisoning

**Symptom:** Irrelevant or conflicting information from previous turns confuses the agent, producing contradictory or stale outputs.

**Mitigation:**
- Explicitly invalidate outdated information: *"Ignore the previous constraint about X; focus only on Y."*
- When context shifts significantly, insert a clear boundary marker
- Summarize and replace older turns rather than accumulating verbatim history

### Distraction / Dilution

**Symptom:** Too much irrelevant detail reduces reasoning quality, even when the answer exists in context.

**Mitigation:**
- Filter RAG results to only highly relevant documents
- Summarize verbose tool outputs before injecting into context
- Remove redundant or low-information turns from history

---

## The Four-Bucket Approach

A tiered strategy for managing context across long sessions:

| Bucket | Content | Treatment |
|--------|---------|-----------|
| **1. Critical Instructions** | System prompt, core constraints | Always present, verbatim |
| **2. Immediate Context** | Last 3-5 conversation turns | Verbatim, always included |
| **3. Relevant History** | Semantically matched past context | Retrieved via search (RAG) |
| **4. Archived History** | Everything else | Summarized or discarded |

This prevents unbounded context growth while preserving the most important information. As conversation length increases, content migrates from Bucket 2 to Bucket 3 or 4.

---

## Optimization Strategies

### Context Compaction

Reduce token usage without losing semantic meaning:

| Technique | Token Savings | Risk |
|-----------|--------------|------|
| Whitespace removal | Minor (1-5%) | Low |
| Comment/syntax stripping | Moderate (10-20%) | Low for data, higher for code |
| Format conversion (verbose JSON to compact YAML/CSV) | Moderate (15-30%) | Medium — verify parsability |
| Extractive summarization of history | High (30-50%) | Medium — potential information loss |

### KV-Cache Optimization

Reuse computed key-value pairs for static context by keeping the prompt prefix constant across requests:

- **Static Prefix:** System instructions + standard few-shot examples (unchanged between requests)
- **Dynamic Suffix:** Conversation history + user query (changes each turn)

This allows the model's KV-cache to skip recomputation of the static prefix, reducing latency and cost for APIs that support prompt caching.

### Observation Masking (for Agents)

Tool outputs can be disproportionately large relative to their information content:

| Problem | Solution |
|---------|----------|
| Huge tool output (e.g., full directory listing) | Truncate to first N lines |
| Verbose structured data | Summarize: *"Found 50 files, mainly .py"* |
| Reading entire files | Use targeted tools (grep, symbol lookup) instead of cat |
| Raw API responses | Extract only the fields needed for the current task |

---

## Periodic Refocusing

In long conversations (10+ turns), instruction adherence naturally degrades. Counter this with periodic refocusing:

- Every 5-10 turns, restate the current goal or constraints
- Use explicit checkpoints: *"To confirm, we are currently working on [Goal]. Is this correct?"*
- After major context shifts, insert a summary of the new direction

---

## Degradation Metrics

Measure context management effectiveness with:

| Metric | What It Tests | How to Measure |
|--------|---------------|----------------|
| **Recall Rate** | Can the agent retrieve a specific fact from mid-context? | Insert known facts at various positions, query for them |
| **Instruction Adherence** | Does the agent follow constraints after many turns? | Test negative constraints (e.g., "no code") at turn 5, 10, 20 |
| **SNR Impact** | Does adding context improve or degrade output quality? | Compare accuracy with/without additional context |

---

## Optimization Checklist

- [ ] Are JSON keys descriptive but short?
- [ ] Is the system prompt free of redundant instructions?
- [ ] Are you sending entire files when only a function is needed?
- [ ] Are critical instructions placed at the start and/or end of context?
- [ ] Is conversation history summarized beyond the immediate window?
- [ ] Are RAG results filtered for relevance before injection?
- [ ] Is the prompt prefix stable to enable KV-cache reuse?

---

## When Not to Use This Reference

- For prompt pattern selection (zero-shot, few-shot, CoT) — see `prompt-patterns.md`
- For token counting and A/B testing mechanics — see `prompt-optimization.md`
- For system prompt structure and persona design — see `system-prompts.md`
- For structured output schemas — see `structured-outputs.md`

---

## Related Skills

- **RAG Architect** — Vector search, chunking, and retrieval pipeline design
- **Architecture Designer** — System-level context flow in multi-agent architectures
- **Debugging Wizard** — Diagnosing agent behavior failures that may be context-related
