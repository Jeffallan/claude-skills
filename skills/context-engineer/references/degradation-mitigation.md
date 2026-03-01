# Context Degradation Mitigation

## 1. Degradation Patterns

### 1.1 Lost-in-the-Middle
- **Symptom**: Agent ignores instructions in the middle of long context.
- **Fix**: Move critical instructions to the end (recency bias) or beginning (primacy bias).
- **Example**:
  ```python
  # Bad
  system_prompt + long_history + user_query

  # Good
  system_prompt + long_history + reminder_of_instructions + user_query
  ```

### 1.2 Context Poisoning
- **Symptom**: Irrelevant or conflicting information from previous turns confuses the agent.
- **Fix**: Explicitly invalidate outdated information.
- **Example**: "Ignore the previous constraint about X; focus only on Y."

### 1.3 Distraction/Dilution
- **Symptom**: Too much irrelevant detail reduces reasoning quality.
- **Fix**: Filter context to only relevant retrieval results or summarized history.

## 2. Mitigation Strategies

### 2.1 Four-Bucket Approach
1. **Critical Instructions**: Always present (System Prompt).
2. **Immediate Context**: Last 3-5 turns (Verbatim).
3. **Relevant History**: Retrieved via semantic search (RAG).
4. **Archived History**: Summarized or discarded.

### 2.2 Periodic Refocusing
- **Action**: Every 5-10 turns, ask the user to confirm the current goal.
- **Prompt**: "Just to ensure I'm on track, we are currently working on [Goal]. Is this correct?"

## 3. Degradation Metrics
- **Recall Rate**: Can the agent retrieve a specific fact from the middle of the context?
- **Instruction Adherence**: Does the agent still follow negative constraints (e.g., "no code") after 20 turns?
