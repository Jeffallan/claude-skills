---
description: Execute a Jira ticket following its implementation plan
argument-hint: <ticket-key>
---

# Ticket Execution Workflow

**Target Ticket:** $ARGUMENTS

---

## Phase 0: Context Retrieval

1. **Fetch the Jira ticket** using `{Target_Ticket}`

2. **Extract from ticket description:**
   - `{Overview_Document}` - Link to the planning/overview document
   - `{Implementation_Plan}` - Link to the implementation plan document

3. **FAILURE CONDITION - Missing or Unclear Links:**

   If links cannot be found, are ambiguous, or you are unsure which links are correct:

   **STOP and prompt the user:**
   ```
   I was unable to confidently identify the required documents from ticket {Target_Ticket}.

   Found links: [list any links found, or "None"]

   Please provide:
   1. Overview Document URL: [paste link]
   2. Implementation Plan URL: [paste link]
   ```

   **DO NOT PROCEED** until both URLs are confirmed.

4. **MANDATORY CHECKPOINT - Document Confirmation:**

   Before proceeding to Phase 1, you MUST confirm with the user:

   ```
   Please confirm these are the correct documents for {Target_Ticket}:

   Overview Document: {Overview_Document}
   Implementation Plan: {Implementation_Plan}

   Proceed with these documents? (Yes / No / Correct)
   ```

   - **Yes** → Continue to Phase 1
   - **No** → Ask user to provide correct URLs
   - **Correct** → User provides corrected URLs, then re-confirm

   **DO NOT PROCEED** to Phase 1 without explicit user confirmation.

---

## Phase 1: Preparation

1. **Read the overview document** (`{Overview_Document}`) for epic context and requirements
2. **Read the implementation plan** (`{Implementation_Plan}`) for detailed execution steps
3. **Locate ticket `{Target_Ticket}`** in the implementation plan
4. **Explore the codebase** for relevant patterns before starting
5. **Check for parallel execution opportunities** (see below)

---

## Parallel Execution Check

After reading the implementation plan, check for a **Parallel Execution Strategy** section:

1. **If parallel waves are defined:**
   - Identify the current wave (first wave with incomplete tickets)
   - All tickets in the same wave can be executed **simultaneously**
   - Consider delegating wave tickets to specialized agents in parallel:
     - Frontend work → frontend-developer agent
     - Backend work → backend-developer agent
     - Database work → database-optimizer agent
     - Test coverage → test-automator agent
   - Present the parallel execution opportunity to the user for approval

2. **Parallel execution prompt to user:**
   ```
   The implementation plan defines parallel execution waves.

   Current Wave: [N]
   Tickets ready for parallel execution:
   - TICKET-101: [title] → recommended: [agent-type]
   - TICKET-102: [title] → recommended: [agent-type]
   - TICKET-103: [title] → recommended: [agent-type]

   Options:
   A) Execute all wave tickets in parallel (spawn multiple agents)
   B) Execute tickets sequentially (one at a time)
   C) Select specific tickets to parallelize

   Which approach? [A/B/C]
   ```

3. **If user approves parallel execution:**
   - Launch specialized agents concurrently for each ticket
   - Each agent works independently on their assigned ticket
   - Coordinate completion before advancing to next wave

---

## Phase 2: Implementation

6. **CHECKPOINT:** Confirm ticket selection and approach with user
7. Update Jira status to "In Progress"
8. Execute implementation steps from the plan
9. Write required tests (unit, integration, E2E as needed)
10. Verify all acceptance criteria are met

---

## Phase 3: Completion

11. Present implementation summary and commit message for user review

**Note:** The user will handle git commit and PR creation.

---

## User Checkpoints

**STOP and check in with the user at these points:**

1. **Before starting:** Confirm ticket selection and planned approach
2. **On deviation:** Stop and get approval (see Deviation Handling)
3. **On blocker:** Report the issue and wait for guidance
4. **When complete:** Present commit message and summary for user review

---

## Execution Checklist

### Before Starting
- [ ] Read the ticket's section in the implementation plan
- [ ] Verify all blocking tickets are complete (check Jira status)
- [ ] **CHECKPOINT:** Confirm ticket and approach with user
- [ ] Move ticket to "In Progress" in Jira

### During Implementation
- [ ] Follow implementation steps exactly as documented in the plan
- [ ] Reference existing codebase patterns
- [ ] Create/modify files as specified
- [ ] Write all required tests:
  - Unit tests for new functions/components
  - Integration tests for API/service interactions
  - E2E tests for user flows (if applicable)

### Before Marking Complete
- [ ] Pre-commit hooks pass (linting, formatting, type checks)
- [ ] Pre-push hooks pass (tests, build)
- [ ] All new tests written and passing
- [ ] All existing tests continue to pass
- [ ] 90% branch coverage maintained
- [ ] All Jira ticket acceptance criteria met

### Completion
- [ ] Present commit message and implementation summary for user review

---

## Suggested Commit Message Format

When implementation is complete, present this for user review:

```
{Target_Ticket}: Brief summary of changes

- Change 1 description
- Change 2 description
- Change 3 description
```

---

## Deviation Handling

If the implementation plan needs to be deviated from:

1. **STOP** - Do not proceed with the deviation without approval

2. **Report** - Clearly explain:
   - What the planned approach was
   - What deviation is needed
   - Why the deviation is necessary
   - Impact of the deviation

3. **Present options:**
   - **Proceed** with deviation (will be documented)
   - **Modify** the approach (suggest alternatives)
   - **Pause** and update implementation plan first

4. **WAIT** for user feedback before continuing

5. **Document** the approved deviation in the completion summary

---

## Follow-up Ticket Management

If follow-up work is discovered during implementation:

1. **Draft the ticket:**
   ```
   Title: [Clear, actionable title]
   Description: [What needs to be done and why]
   Acceptance Criteria:
   - [ ] Criterion 1
   - [ ] Criterion 2
   Story Points: [Estimate]
   Related Ticket: {Target_Ticket}
   ```

2. **Recommend placement:**
   - **Backlog** - Low priority, not time-sensitive
   - **Epic** - Related to current epic, schedule during planning
   - **Current Sprint** - Blocking or urgent, needs immediate attention
   - **Future Sprint** - Important but not urgent, schedule next

3. **Prompt user:**
   "I've identified follow-up work needed. Here's the draft ticket:
   [ticket details]

   Recommended placement: [placement]

   Do you approve? (Yes / No / Modify)"

4. **WAIT for approval** before creating the ticket in Jira

---

## Output

When complete, provide a summary:

```markdown
## Ticket Completion Summary

### Ticket
- **Key:** {Target_Ticket}
- **Title:** [Title]

### Suggested Commit Message
[Formatted commit message]

### Changes Made
- [List of changes]

### Files Modified/Created
- `path/to/file.ts` - Description of changes

### Tests Added
- `path/to/test.spec.ts` - What it tests

### Deviations from Implementation Plan
- [Any approved deviations with justification, or "None"]

### Follow-up Tickets Created
- [TICKET-KEY] - [Title] (Placement: [where])
- Or "None"
```

---

## Agent Delegation

**Pre-Implementation Exploration:** Before writing code, explore:
- File structure and naming conventions
- Similar existing implementations to reference
- Test patterns and fixtures available
- API patterns and data models

**Code Quality:** Have implementations reviewed for quality, patterns,
and potential issues before committing.

**Testing:** Delegate test creation to ensure comprehensive coverage.

**Test Strategy:** Design comprehensive test coverage including:
- Unit tests for business logic
- Integration tests for API/service interactions
- E2E tests for critical user journeys

**Quality Validation:** Have test coverage and quality reviewed.

**Code Review:** Have code reviewed for:
- Quality and adherence to patterns
- Security vulnerabilities
- Performance implications

**Security Analysis:** For sensitive changes, analyze security implications.

**Root Cause Analysis:** For issues, systematically investigate:
- Error patterns and stack traces
- Recent changes that may have introduced bugs
- Environmental factors

**Performance Investigation:** For performance issues, profile and analyze
bottlenecks systematically.
