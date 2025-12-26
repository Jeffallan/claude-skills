---
description: Generate an implementation plan from a planning document
argument-hint: <overview-doc-url>
---

# Generate Implementation Plan

**Overview Document:** $ARGUMENTS

---

## Overview

This workflow creates two outputs:
1. **Implementation Plan (Confluence)** - Coordination dashboard for tracking execution
2. **Updated Jira Tickets** - Self-contained with full implementation details

---

## Phase 0: Context Retrieval

1. **Fetch the overview document** from `{Overview_Document}`

2. **Extract:**
   - `{Epic_Key}` - The epic ticket key (e.g., CC-123)
   - `{Jira_Project}` - Link to the Jira project/board
   - Related ticket links

3. **FAILURE CONDITION:** If epic key or project cannot be determined, prompt user for missing info.

4. **CHECKPOINT:** Confirm epic key and project before proceeding.

---

## Phase 1: Discovery

1. **Read the overview document** for epic context, scope, and requirements
2. **Fetch all Jira tickets** linked to this epic
3. **Explore the codebase** for patterns relevant to the tickets

**Codebase Exploration Focus:**
- Affected files/modules per ticket
- API patterns (routes, middleware, response formats)
- Component patterns (naming, state management)
- Test patterns (locations, fixtures, mocks)
- Reference implementations

---

## Phase 2: Ticket Refinement

Analyze existing tickets and prepare adjustments:

- **Create new tickets** for gaps (missing functionality, dependencies)
- **Split large tickets** (>8 story points)
- **Add story points** to all tickets
- **Link dependencies** (blocked-by relationships)

**CHECKPOINT:** Present proposed ticket changes and get approval before modifying Jira.

---

## Phase 3: Generate Implementation Plan

Create a **lightweight coordination document** in Confluence.

### Implementation Plan Structure

```markdown
# {Epic_Key} Implementation Plan

## Summary

| Metric | Value |
|--------|-------|
| **Epic** | [{Epic_Key}](link) |
| **Total Tickets** | X |
| **Total Story Points** | X |
| **Overall Complexity** | Low/Medium/High |
| **Execution Waves** | X |
| **Key Dependencies** | Brief summary |

---

## Completion Status

| Ticket | Status | Completed Date | Notes |
|--------|--------|----------------|-------|
| [CC-XXX](link) | Pending | - | - |
| [CC-YYY](link) | Pending | - | - |

---

## Execution Order (Topologically Sorted)

| # | Ticket | Summary | Points | Risk | Dependencies | Status |
|---|--------|---------|--------|------|--------------|--------|
| 1 | [CC-XXX](link) | Title | 2 | Low | None | Pending |
| 2 | [CC-YYY](link) | Title | 3 | Low | CC-XXX | Pending |

---

## Parallel Execution Strategy

### Wave 1: [Name] (X pts) - Execute in Parallel

| Ticket | Summary | Points | Agent | Status |
|--------|---------|--------|-------|--------|
| CC-XXX | Title | 2 | frontend-developer | Pending |
| CC-YYY | Title | 3 | backend-developer | Pending |

### Wave 2: [Name] (X pts) - After Wave 1

| Ticket | Summary | Points | Agent | Status |
|--------|---------|--------|-------|--------|
| CC-ZZZ | Title | 5 | fullstack-developer | Pending |

**Note:** [Any blocking dependencies or coordination notes]

---

## Agent Recommendations

| Work Type | Recommended Agent |
|-----------|-------------------|
| Frontend UI/components | frontend-developer |
| API/backend services | backend-developer |
| Database changes | database-optimizer |
| Full-stack features | fullstack-developer |
| Test coverage | test-automator |

---

## Document Links

- **Overview Document:** [link]
- **Epic:** [link]
```

**CHECKPOINT:** Present plan preview and get approval before publishing.

---

## Phase 4: Update Jira Tickets

After publishing the implementation plan, update **each ticket** with full implementation details.

### Ticket Description Template

Each ticket must be **self-contained** with everything needed to execute:

```markdown
Overview Document: {Overview_Document_URL}
Implementation Plan: {Implementation_Plan_URL}

## Summary

[Brief description of what this ticket accomplishes]

## Implementation Steps

1. **[Step title]**
   - Specific action with file path
   - Code snippet if applicable
   ```typescript
   // Example code
   ```

2. **[Step title]**
   - Specific action
   - Details

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `path/to/file.ts` | Modify | What changes |
| `path/to/new.ts` | Create | What it does |

## Tests

### File: `tests/unit/feature.test.ts`

```typescript
// Complete, copy-paste ready test code
import { ... } from '...';

describe('Feature', () => {
  beforeEach(() => {
    // setup
  });

  test('should do X', () => {
    // test implementation
  });
});
```

## Acceptance Criteria

- [ ] Implementation step 1 complete
- [ ] Implementation step 2 complete
- [ ] All tests passing
- [ ] No TypeScript errors (`npm run check`)
- [ ] Linting passes (`npm run lint`)
```

### Why Self-Contained Tickets

- `/execute-ticket` can run with just the ticket (no external doc fetching required)
- All context in one place
- Reduces token usage during execution
- Enables parallel agent execution

---

## Phase 5: Update Overview Document

Add an **Adjustments Section** to the overview document:

```markdown
## Implementation Plan Adjustments

**Plan Created:** [date]
**Implementation Plan:** [link]

### Tickets Added
- [CC-XXX] - [title] - [justification]

### Tickets Split
- [CC-YYY] split into [CC-YYY1], [CC-YYY2] - [reason]

### Story Points Updated
- [CC-ZZZ]: X → Y points - [reason]

### New Dependencies
- [CC-AAA] blocked by [CC-BBB] - [reason]
```

**CHECKPOINT:** Present proposed updates and get approval before modifying.

---

## Output

When complete, provide:

```
## Implementation Plan Created

**Implementation Plan:** [Confluence URL]
**Overview Document:** [Updated URL]

### Summary
- Tickets in epic: X
- Total story points: X
- Execution waves: X

### Changes Made
- Tickets created: [list]
- Tickets updated: [list]
- Story points added: [list]

### Next Steps
1. Review the implementation plan
2. Run `/execute-ticket <ticket-key>` to begin work
```

---

## Checkpoints Summary

| Phase | Checkpoint | Action |
|-------|------------|--------|
| 0 | Document confirmation | Confirm epic key and project |
| 2 | Ticket changes | Approve new/split/updated tickets |
| 3 | Plan preview | Approve before publishing |
| 5 | Overview updates | Approve adjustments section |

**Never modify Jira or Confluence without explicit user approval.**
