# Context Optimization Strategies

## 1. Context Compaction
- **Goal**: Reduce token usage without losing semantic meaning.
- **Techniques**:
  - **Whitespace Removal**: Remove excessive newlines/spaces (minor gain).
  - **Syntax Stripping**: Remove comments or non-essential code structure in large files.
  - **Data Formatting**: Convert verbose JSON to compact YAML or CSV.

## 2. KV-Cache Optimization
- **Concept**: Reuse computed key-value pairs for static context (System Prompt, Few-Shots).
- **Strategy**: Keep the prefix of the prompt constant across requests.
  - **Static Prefix**: System Instructions + Standard Examples.
  - **Dynamic Suffix**: History + User Query.

## 3. Observation Masking (for Agents)
- **Problem**: Tool outputs can be huge (e.g., `ls -R`).
- **Solution**:
  - Truncate output (e.g., `head -n 20`).
  - Summarize output (e.g., "Found 50 files, mainly .py").
  - Use specific tools (e.g., `grep` instead of `cat`).

## 4. Optimization Checklist
- [ ] Are JSON keys descriptive but short?
- [ ] Is the system prompt free of redundant instructions?
- [ ] Are we sending the entire file when only a function is needed?
