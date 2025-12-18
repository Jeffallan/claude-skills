---
description: Generate an implementation plan from a planning document
argument-hint: <overview-doc-url>
---

# Generate Implementation Plan

**Overview Document:** $ARGUMENTS

---

## Phase 0: Context Retrieval

1. **Fetch the overview document** from parent: `{Overview_Document}`

2. **Extract from document:**
   - `{Epic_Key}` - The epic ticket key (e.g., MA-123)
   - `{Jira_Project}` - Link to the Jira project/board
   - Related ticket links

3. **FAILURE CONDITION - Missing Information:**

   If epic key or project cannot be determined:

   **STOP and prompt the user:**
   ```
   I was unable to extract required information from the overview document.

   Found: [list what was found]

   Please provide:
   1. Epic Key: [e.g., MA-123]
   2. Jira Project URL: [paste link]
   ```

   **DO NOT PROCEED** until confirmed.

4. **MANDATORY CHECKPOINT - Document Confirmation:**

   ```
   Please confirm the following before I proceed:

   Overview Document: {Overview_Document}
   Epic Key: {Epic_Key}
   Jira Project: {Jira_Project}

   Is this correct? (Yes / No / Correct)
   ```

   **DO NOT PROCEED** without explicit user confirmation.

---

## Phase 1: Discovery

1. **Read the overview document** for epic context, scope, and risk assessments
2. **Read all Jira tickets** linked to this epic for detailed requirements
3. **Explore the codebase** to understand:
   - File structure and naming conventions
   - Similar existing implementations to reference
   - Test patterns and fixtures available
   - API patterns and data models

---

## Phase 2: Ticket Refinement

Analyze existing tickets and prepare adjustments (see Ticket Management below).

**MANDATORY CHECKPOINT - Proposed Ticket Changes:**

Before making ANY ticket changes, present to user:

```
## Proposed Ticket Changes for {Epic_Key}

### New Tickets to Create
| Title | Description | Points | Justification |
|-------|-------------|--------|---------------|
| [title] | [brief desc] | [pts] | [why needed] |

### Tickets to Split
| Original | New Tickets | Reason |
|----------|-------------|--------|
| [KEY] | [list new] | [why split] |

### Story Point Updates
| Ticket | Current | Proposed | Reason |
|--------|---------|----------|--------|
| [KEY] | [old] | [new] | [justification] |

### Dependencies to Add
| Ticket | Blocked By | Reason |
|--------|------------|--------|
| [KEY] | [blocker] | [why] |

Proceed with these changes? (Yes / No / Modify)
```

- **Yes** → Make the changes and continue
- **No** → Skip ticket changes, proceed to Phase 3
- **Modify** → User provides adjustments, re-confirm

**DO NOT modify any Jira tickets** without explicit approval.

---

## Phase 3: Implementation Plan

Generate a detailed, agent-executable implementation plan (see structure below).

**MANDATORY CHECKPOINT - Plan Review:**

Before publishing, present the complete implementation plan to the user:

```
## Implementation Plan Preview for {Epic_Key}

[Full implementation plan content]

---

Review the plan above. Proceed to publish? (Yes / No / Modify)
```

- **Yes** → Continue to Phase 4
- **No** → Discard and ask what changes are needed
- **Modify** → User provides feedback, regenerate and re-confirm

**DO NOT PROCEED** to publishing without explicit approval.

---

## Phase 4: Publish

1. **MANDATORY CHECKPOINT - Parent Document Updates:**

   Before updating the parent planning document, present proposed changes:

   ```
   ## Proposed Updates to Overview Document

   I will add the following "Adjustments Section" to {Overview_Document}:

   [Show exact content to be added]

   Proceed with update? (Yes / No / Modify)
   ```

   **DO NOT UPDATE** the parent document without explicit approval.

2. Publish the implementation plan as a Confluence subpage (`{Implementation_Plan}`)

3. **Update all tickets with Implementation Plan link:**
   - After publishing, `{Implementation_Plan}` URL is now known
   - Update ALL epic tickets to replace placeholder with actual URL:
     ```
     Overview Document: {Overview_Document}
     Implementation Plan: {Implementation_Plan}
     ```
   - This ensures `/execute-ticket` can extract both links from any ticket

4. Update the parent planning document with approved adjustments

---

## Ticket Management

Before creating the implementation plan, analyze the existing tickets and adjust as needed.

### Ticket Description Format (MANDATORY)

**ALL tickets** (new and existing) MUST have these links at the TOP of their description:

```
Overview Document: {Overview_Document}
Implementation Plan: {Implementation_Plan}

---

[Rest of ticket description]
```

- **New tickets:** Add this header when creating
- **Existing tickets:** Update description to add this header if missing
- `{Implementation_Plan}` will be the URL of the subpage created in Phase 4

**Note:** Since the Implementation Plan doesn't exist yet during Phase 2, use a placeholder:
```
Implementation Plan: [To be added after plan is published]
```
Then update all tickets with the actual URL after Phase 4 publishing.

### Create New Tickets
- Identify gaps in coverage (missing functionality, edge cases, setup tasks)
- Create tickets for discovered technical dependencies
- Add tickets for required refactoring or tech debt that blocks implementation

### Split Large Tickets
- Any ticket estimated at >8 story points should be split
- Each ticket should represent a single, deliverable unit of work

### Add Story Points
Estimate and add story points to ALL tickets (new and existing):

| Points | Complexity | Example |
|--------|------------|---------|
| 1-2 | Simple, isolated change | Fix typo, update config, add simple validation |
| 3-5 | Moderate, few files | New API endpoint, component with tests |
| 8 | Complex, multiple components | Feature spanning frontend + backend |
| 13+ | Too large - must be split | Epic-level work |

### Link Dependencies
- Set "blocked by" relationships in Jira for all dependencies
- Ensure no circular dependencies exist

---

## Implementation Plan Structure

### Summary Section
- Total number of tasks (including any new tickets created)
- Overall complexity assessment (Low/Medium/High based on risk scores)
- Total story points
- Key dependencies overview
- Suggested execution order

### Task Breakdown
For **each Jira ticket**, create a task entry with:

#### Task Header
- Ticket key and title (e.g., "MA-124 - Add user authentication")
- Link to the Jira ticket
- Story points
- Risk level from the planning doc (Low/Medium/High)
- Dependencies (list any tickets that must be completed first)

#### Implementation Steps
Provide **detailed, agent-executable steps** including:
- Specific file paths to create or modify
- Code patterns to follow (reference existing codebase patterns)
- API endpoints to implement
- Database changes if any
- Configuration updates needed
- Follow existing conventions for naming, file structure, and architecture

Each step should be concrete enough that an AI coding agent can execute it directly without additional context.

#### Files to Modify
List all files that will be touched:
- `path/to/file.ts` - Brief description of changes

#### Tests to Write
Specify exactly what tests are needed:
- **Unit tests:** List specific functions/components to test
- **Integration tests:** List API endpoints or service interactions to test
- **E2E tests:** List user flows to test (if applicable)

#### Acceptance Criteria
Each task is complete when:
- [ ] All implementation steps are done
- [ ] Pre-commit hooks pass (linting, formatting, type checks)
- [ ] Pre-push hooks pass (tests, build)
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing (if applicable)
- [ ] E2E tests written and passing (if applicable)
- [ ] 90% branch coverage maintained
- [ ] All existing tests continue to pass
- [ ] Code reviewed and approved
- [ ] Jira ticket acceptance criteria met

---

### Execution Order
Provide a **topologically sorted** list of tasks based on dependencies:
1. Task A (no dependencies) - X points
2. Task B (depends on A) - X points
3. Task C (depends on A) - X points
4. Task D (depends on B, C) - X points

---

### Parallel Execution Strategy

Identify tickets that can be worked on **simultaneously** by independent agents:

#### Parallel Execution Waves
Group tickets into waves where all tickets in a wave can be executed concurrently:

```
Wave 1 (no dependencies - execute in parallel):
  - TICKET-101: [title] (3 pts) → frontend-developer
  - TICKET-102: [title] (5 pts) → backend-developer
  - TICKET-103: [title] (2 pts) → test-automator

Wave 2 (depends on Wave 1 - execute in parallel after Wave 1):
  - TICKET-104: [title] (5 pts) → fullstack-developer
  - TICKET-105: [title] (3 pts) → frontend-developer

Wave 3 (depends on Wave 2):
  - TICKET-106: [title] (8 pts) → fullstack-developer
```

#### Agent Specialization Recommendations
For each ticket, recommend the optimal agent type based on the work involved:

| Work Type | Recommended Agent |
|-----------|-------------------|
| Frontend UI/components | frontend-developer |
| API/backend services | backend-developer |
| Database changes | database-optimizer |
| Full-stack features | fullstack-developer |
| Test coverage | test-automator |
| Security-sensitive | security-auditor |
| Performance-critical | performance-engineer |

#### Coordination Notes
- Tickets in the same wave have no dependencies on each other
- Wave N+1 tickets depend on one or more Wave N tickets
- Independent agents can work simultaneously within each wave
- Synchronize and verify completion before starting next wave

---

## Parent Document Updates

After completing the implementation plan, update the original Confluence planning, `{Overview_Document}`,document with:

### Adjustments Section (add to planning doc)
- **Tickets Added:** List any new tickets created with justification
- **Tickets Split:** List any tickets that were split and why
- **Scope Changes:** Document any scope adjustments discovered
- **New Risks:** Add any new risks discovered during implementation planning
- **Revised Dependencies:** Update dependency graph if changed
- **Updated Estimates:** Revised total effort based on story points

---

## Output Location

Publish the implementation plan to Confluence as a subpage:
- Parent page: `{Overview_Document}`
- Subpage title: "{Epic_Key} Implementation Plan"

If the subpage already exists, update it. If you cannot create subpages, ask the user for an alternative location.

Also update the parent planning document at `{Overview_Document}` with the "Adjustments Section" content.

---

## Output

When complete, provide:
1. **Implementation Plan URL** (new subpage) - needed for ticket execution
2. **Updated Overview Document URL** (parent page)
3. **Summary of changes made** - tickets created, split, updated

---

## Agent Delegation

**Deep Exploration:** Thoroughly explore the codebase to understand:
- Current implementation patterns and conventions
- Affected components and their dependencies
- Existing test coverage and testing patterns

**Design Review:** Have the architectural approach reviewed for scalability,
maintainability, and alignment with existing patterns.

**Codebase Analysis:** Before proceeding, thoroughly explore the existing
codebase to understand current patterns, architecture, and conventions.

**Architecture Review:** Have the proposed structure reviewed for completeness
and proper organization.
