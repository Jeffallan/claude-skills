# Context Fundamentals

## 1. The Context Budget
- **Concept**: Context window is a scarce resource (attention budget).
- **Rule**: Every token consumes attention. Irrelevant tokens degrade performance.
- **Metric**: Signal-to-Noise Ratio (SNR). High SNR = Better Reasoning.

## 2. Context Components
1. **System Prompt**: Identity, permanent rules, output format.
2. **Few-Shot Examples**: Demonstrations of desired behavior.
3. **Conversation History**: Short-term memory (user interactions).
4. **Retrieved Context (RAG)**: Long-term memory or external knowledge.

## 3. Structuring Context
- **XML Tagging**: Use tags to delineate sections.
  ```xml
  <documents>
    <doc id="1">...</doc>
  </documents>
  <instructions>...</instructions>
  <history>...</history>
  ```
- **Order Matters**:
  1. System Instructions
  2. Reference Material (RAG)
  3. Few-Shot Examples
  4. Conversation History
  5. User Query

## 4. Progressive Disclosure
- **Principle**: Don't dump all information at once.
- **Implementation**:
  - Step 1: High-level summary.
  - Step 2: Drill down into specific sections based on user intent.
