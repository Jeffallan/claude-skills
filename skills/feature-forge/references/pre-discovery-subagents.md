# Pre-Discovery with Subagents

For features spanning multiple domains (auth, database, UI, etc.) that need front-loaded technical context before the Feature Forge interview.

## Overview

For features spanning multiple domains, you can accelerate discovery by launching Task subagents with relevant skills BEFORE starting the Feature Forge interview. This front-loads technical context so the interview focuses on decisions rather than exploration.

## When to Use

- Feature touches 3+ distinct system layers (e.g., auth, database, UI)
- Codebase is unfamiliar or underdocumented
- You need concrete technical facts before asking requirements questions
- Stakeholder time is limited and you want to minimize back-and-forth

## When NOT to Use

- Feature is well-scoped to a single domain
- You already have deep codebase knowledge
- Requirements are purely business/UX (no technical exploration needed)

## Pattern

```
1. Identify domains the feature touches
2. Launch parallel Task subagents with relevant skills:
   - Architecture Designer → existing patterns and constraints
   - Framework Expert → current implementation details
   - Security Reviewer → security requirements and risks
3. Collect findings from all subagents
4. Begin Feature Forge interview with technical context loaded
5. Focus interview on decisions, trade-offs, and requirements
```

## Example

For a "user profile with avatar upload" feature:

```
Task subagent 1 (Architecture Designer):
  "Analyze the current user model, storage patterns, and image handling in this codebase"

Task subagent 2 (Security Reviewer):
  "What security concerns exist for file upload in this stack?"

Task subagent 3 (Framework Expert):
  "How does this project handle API endpoints and file storage?"
```

Results feed into the Feature Forge interview, so questions like "Where should we store avatars?" come with context about existing patterns.

## Integration with Interview Questions

See `interview-questions.md` for the full multi-agent discovery pattern and how subagent findings map to interview categories.
