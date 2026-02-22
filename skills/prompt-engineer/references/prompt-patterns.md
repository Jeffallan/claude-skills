# Prompt Patterns

---

## Pattern Selection Guide

```
                        ┌─────────────────────────────────────┐
                        │        TASK CHARACTERISTICS         │
                        └─────────────────────────────────────┘
                                         │
           ┌─────────────────────────────┼─────────────────────────────┐
           │                             │                             │
    Simple, Common              Requires Reasoning            Requires Actions
           │                             │                             │
           ▼                             ▼                             ▼
    ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
    │  Zero-Shot  │              │    CoT or   │              │    ReAct    │
    │             │              │  Few-Shot   │              │             │
    └─────────────┘              └─────────────┘              └─────────────┘
```

| Pattern | Best For | Token Cost | Reliability |
|---------|----------|------------|-------------|
| Zero-shot | Simple, well-defined tasks | Low | Medium |
| Few-shot | Tasks needing format guidance | Medium | High |
| Chain-of-Thought | Reasoning, math, logic | Medium-High | High |
| ReAct | Multi-step tasks with tools | High | Very High |
| Tree-of-Thoughts | Complex problem solving | Very High | Very High |

---

## Zero-Shot Prompting

**When to use:** Simple classification, extraction, formatting, or generation tasks where the model has strong prior knowledge.

**When NOT to use:** Complex reasoning, domain-specific formats, or tasks requiring specific output structure.

### Basic Structure

```
<role>You are a [specific role with relevant expertise].</role>

<task>
[Clear, specific instruction]
</task>

<constraints>
- [Constraint 1]
- [Constraint 2]
</constraints>

<input>
{user_content}
</input>

<output_format>
[Expected format description]
</output_format>
```

### Example: Sentiment Classification

```
You are a sentiment analysis expert.

Classify the following customer review as POSITIVE, NEGATIVE, or NEUTRAL.
Respond with only the classification label.

Review: "{review_text}"

Classification:
```

### Example: Entity Extraction

```
Extract all company names mentioned in the following text.
Return them as a JSON array of strings.
If no companies are mentioned, return an empty array.

Text: "{input_text}"

Companies:
```

### Zero-Shot Best Practices

1. **Be specific about the task** - Avoid ambiguous instructions
2. **Specify output format** - Tell the model exactly what to return
3. **Include constraints** - What NOT to do is as important as what to do
4. **Use role priming** - "You are an expert..." improves quality

---

## Few-Shot Prompting

**When to use:** Tasks needing specific output format, domain-specific reasoning, or consistent style.

**When NOT to use:** Simple tasks where examples add unnecessary tokens, or when examples might constrain creativity.

### Basic Structure

```
<task>
[Task description]
</task>

<examples>
Input: [example 1 input]
Output: [example 1 output]

Input: [example 2 input]
Output: [example 2 output]

Input: [example 3 input]
Output: [example 3 output]
</examples>

<input>
{actual_input}
</input>

Output:
```

### Example: Code Review Comments

```
Generate a constructive code review comment for the given code issue.

Example 1:
Issue: Variable named 'x' in a function calculating total price
Comment: Consider renaming 'x' to 'totalPrice' or 'priceSum' to improve readability. Descriptive variable names help future maintainers understand the code's intent without needing to trace through the logic.

Example 2:
Issue: SQL query built with string concatenation using user input
Comment: This code is vulnerable to SQL injection attacks. Consider using parameterized queries or an ORM to safely handle user input. For example: `cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))`

Example 3:
Issue: Catch block that silently swallows exceptions
Comment: Empty catch blocks can hide bugs and make debugging difficult. Consider logging the exception or, if the exception is truly expected, add a comment explaining why it's safe to ignore.

Issue: {code_issue}
Comment:
```

### Few-Shot Selection Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| Diverse | Cover different cases/categories | Classification, categorization |
| Similar | Match examples to input type | Consistent formatting |
| Increasing complexity | Start simple, build up | Complex reasoning tasks |
| Edge cases | Include boundary cases | Robust handling |

### Example Selection Guidelines

1. **Match the distribution** - Examples should represent real inputs
2. **3-5 examples typically optimal** - Balance between guidance and token cost
3. **Order matters** - Recent examples have more influence
4. **Include edge cases** - Show how to handle unusual inputs
5. **Keep format consistent** - All examples should follow the same structure

### Dynamic Few-Shot Selection

```python
def select_examples(query: str, example_pool: list, k: int = 3) -> list:
    """Select most relevant examples using embedding similarity."""
    query_embedding = embed(query)

    scored = []
    for example in example_pool:
        score = cosine_similarity(query_embedding, example.embedding)
        scored.append((score, example))

    # Return top-k most similar examples
    scored.sort(reverse=True)
    return [ex for _, ex in scored[:k]]
```

---

## Chain-of-Thought (CoT) Prompting

**When to use:** Math problems, logical reasoning, multi-step analysis, debugging, planning.

**When NOT to use:** Simple factual recall, creative generation, or tasks where reasoning steps aren't helpful.

### Zero-Shot CoT

Simply add "Let's think step by step" or similar phrase:

```
Solve the following problem step by step:

{problem}

Let's work through this systematically:
```

### Structured CoT

```
Analyze the following problem and solve it step by step.

Problem: {problem}

## Step 1: Understand the problem
[What are we trying to find?]

## Step 2: Identify relevant information
[What data do we have?]

## Step 3: Plan the approach
[What method will we use?]

## Step 4: Execute the solution
[Work through the calculations/logic]

## Step 5: Verify the answer
[Check if the answer makes sense]

Final Answer:
```

### Example: Debugging with CoT

````
Debug the following code by analyzing it step by step.

Code:
```python
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)
```

Error: ZeroDivisionError when called with empty list

## Analysis

### Step 1: Trace the execution path
Let me trace what happens when `numbers = []`:
1. `total = 0` - total is initialized to 0
2. `for num in numbers:` - loop doesn't execute (empty list)
3. `return total / len(numbers)` - returns `0 / 0`

### Step 2: Identify the root cause
The function doesn't handle the edge case of an empty list.
`len([])` returns 0, causing division by zero.

### Step 3: Propose fix
Add a check for empty input before division.

### Fixed Code:
```python
def calculate_average(numbers):
    if not numbers:
        return 0  # or raise ValueError("Cannot average empty list")
    total = sum(numbers)
    return total / len(numbers)
```
````

### CoT Variants

| Variant | Technique | Use Case |
|---------|-----------|----------|
| Zero-shot CoT | "Think step by step" | Quick reasoning tasks |
| Manual CoT | Explicit step examples | Complex domain problems |
| Self-consistency | Generate multiple paths, vote | High-stakes decisions |
| Least-to-most | Decompose into subproblems | Complex multi-part problems |

---

## ReAct Pattern (Reasoning + Acting)

**When to use:** Tasks requiring external tools, information retrieval, or iterative problem solving.

**When NOT to use:** Pure text generation, simple Q&A, or tasks with no action component.

### ReAct Structure

```
You are an assistant that solves problems by thinking and taking actions.

Available tools:
- search(query): Search the web for information
- calculate(expression): Evaluate a mathematical expression
- lookup(term): Look up a definition or fact

Respond in this format:
Thought: [Your reasoning about what to do next]
Action: [tool_name(parameters)]
Observation: [Result from the tool - provided by system]
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to answer.
Answer: [Final answer]

Question: {user_question}
```

### Example: ReAct for Research

```
Question: What is the current market cap of the company that created ChatGPT?

Thought: I need to find out which company created ChatGPT, then look up their market cap.
Action: search("company that created ChatGPT")
Observation: ChatGPT was created by OpenAI, an AI research company.

Thought: Now I need to find OpenAI's current market cap.
Action: search("OpenAI market cap 2025")
Observation: OpenAI's valuation reached $157 billion in 2024 after their latest funding round.

Thought: I now have the information needed to answer.
Answer: ChatGPT was created by OpenAI, which has a valuation of approximately $157 billion (as of their 2024 funding round). Note: OpenAI is a private company, so this is a valuation rather than a public market cap.
```

### ReAct Implementation Pattern

```python
def react_loop(question: str, tools: dict, max_iterations: int = 10) -> str:
    """Execute a ReAct reasoning loop."""
    context = f"Question: {question}\n\n"

    for i in range(max_iterations):
        # Get next thought and action from LLM
        response = llm.complete(REACT_PROMPT + context)

        # Parse thought and action
        thought, action = parse_react_response(response)
        context += f"Thought: {thought}\n"

        if action.startswith("Answer:"):
            return action.replace("Answer:", "").strip()

        # Execute action and get observation
        tool_name, params = parse_action(action)
        observation = tools[tool_name](*params)

        context += f"Action: {action}\n"
        context += f"Observation: {observation}\n\n"

    return "Max iterations reached without answer."
```

---

## Tree-of-Thoughts (ToT)

**When to use:** Complex problems requiring exploration of multiple solution paths, creative problem solving, strategic planning.

**When NOT to use:** Simple tasks, time-sensitive operations, or when token budget is limited.

### ToT Structure

```
Problem: {complex_problem}

## Generate Candidate Approaches

### Approach A: [First strategy]
- Pros: [advantages]
- Cons: [disadvantages]
- Estimated success: [low/medium/high]

### Approach B: [Second strategy]
- Pros: [advantages]
- Cons: [disadvantages]
- Estimated success: [low/medium/high]

### Approach C: [Third strategy]
- Pros: [advantages]
- Cons: [disadvantages]
- Estimated success: [low/medium/high]

## Evaluate and Select

Based on the analysis, Approach [X] is most promising because [reasoning].

## Execute Selected Approach

[Detailed execution of chosen approach]

## Verify Solution

[Check if solution meets requirements]
```

### ToT for Code Architecture

```
Design a caching system for a high-traffic API endpoint.

## Candidate Architectures

### Option A: In-Memory Cache (Redis)
Thought: Use Redis for distributed caching
Evaluation:
- Latency: ~1ms (excellent)
- Scalability: Horizontal scaling supported
- Complexity: Low - well-established pattern
- Risk: Cache invalidation complexity
Score: 8/10

### Option B: CDN Edge Caching
Thought: Cache at CDN level for static/semi-static content
Evaluation:
- Latency: ~10-50ms (good)
- Scalability: Excellent - distributed globally
- Complexity: Medium - cache headers management
- Risk: Stale content for dynamic data
Score: 6/10

### Option C: Multi-Layer Cache
Thought: Combine L1 (local) + L2 (Redis) + L3 (CDN)
Evaluation:
- Latency: <1ms for hot data
- Scalability: Excellent
- Complexity: High - multiple invalidation points
- Risk: Consistency challenges
Score: 7/10

## Decision
Option A (Redis) selected for initial implementation:
- Lowest complexity for team's current expertise
- Sufficient performance for projected load
- Clear upgrade path to Option C if needed

## Implementation Plan
[Detailed implementation steps...]
```

---

## Pattern Comparison Quick Reference

```
┌────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│    Pattern     │   Tokens     │  Complexity  │  Reliability │   Best For   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│   Zero-shot    │     Low      │     Low      │    Medium    │ Simple tasks │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│   Few-shot     │    Medium    │    Medium    │     High     │Format/style  │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│      CoT       │    Medium    │    Medium    │     High     │  Reasoning   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│     ReAct      │     High     │     High     │  Very High   │ Tool usage   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│      ToT       │  Very High   │  Very High   │  Very High   │Complex solve │
└────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

---

## Combining Patterns

Patterns can be combined for more powerful prompts:

### Few-Shot + CoT

```
Solve math word problems by showing your work.

Example 1:
Problem: If a train travels 60 mph for 2.5 hours, how far does it go?
Solution:
- Distance = Speed × Time
- Distance = 60 mph × 2.5 hours
- Distance = 150 miles
Answer: 150 miles

Example 2:
Problem: A store has a 20% off sale. If an item costs $45, what's the sale price?
Solution:
- Discount = Original × Discount Rate
- Discount = $45 × 0.20 = $9
- Sale Price = Original - Discount
- Sale Price = $45 - $9 = $36
Answer: $36

Problem: {new_problem}
Solution:
```

### ReAct + CoT

```
Thought: Let me break this down step by step.
First, I need to understand what information I'm looking for...
[reasoning]
Based on this analysis, I should search for...
Action: search("specific query based on reasoning")
```

---

## Related Skills

- **RAG Architect** - Retrieval patterns for grounding prompts
- **Fine-Tuning Expert** - When prompting isn't enough
- **LLM Architect** - System-level prompt orchestration
