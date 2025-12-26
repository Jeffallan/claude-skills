---
description: Create an epic planning document by analyzing Jira tickets and codebase
argument-hint: <epic-key>
---

# Epic Planning Document Generator

**Epic Key:** $ARGUMENTS

---

## Workflow Chain

This command creates a comprehensive planning document (Overview Document) for an epic:

```
/create-epic-plan <epic-key>     → Creates Overview Document (YOU ARE HERE)
         ↓
/create-implementation-plan <overview-doc-url>  → Creates Implementation Plan
         ↓
/execute-ticket <ticket-key>     → Executes individual tickets
```

---

## Phase 0: Context Retrieval

1. **Fetch the epic** from Jira using `{Epic_Key}`

2. **Extract from epic:**
   - `{Epic_Title}` - The epic title/name
   - `{Jira_Project}` - The Jira project URL
   - Linked tickets

3. **Determine Confluence location:**
   - Default: `/Epics/In Progress/{Epic_Key}/`
   - If location unclear, ask user

4. **FAILURE CONDITION - Missing Information:**

   If epic cannot be found or has no linked tickets:

   **STOP and prompt the user:**
   ```
   I was unable to retrieve epic {Epic_Key}.

   Issue: [epic not found / no linked tickets / access denied]

   Please provide:
   1. Confirm the epic key is correct
   2. Jira Project URL: [paste link]
   3. Confluence publish location: [paste link or confirm default]
   ```

   **DO NOT PROCEED** until confirmed.

5. **MANDATORY CHECKPOINT - Epic Confirmation:**

   ```
   Please confirm before I proceed:

   Epic Key: {Epic_Key}
   Epic Title: {Epic_Title}
   Linked Tickets: [count] tickets found
   Publish Location: [Confluence path]

   Is this correct? (Yes / No / Correct)
   ```

   **DO NOT PROCEED** without explicit user confirmation.

---

## Phase 1: Discovery

1. **Read all Jira tickets** linked to epic `{Epic_Key}`
   - Use JQL query: `Parent = {Epic_Key}` to find all child tickets
   - Extract acceptance criteria from each ticket
   - Identify ticket dependencies and relationships
   - Note any technical constraints mentioned

2. **Explore the codebase using parallel agents**

   Launch these agents **in parallel** to analyze different aspects of the codebase:

   | Agent | Task | Output for Section 11 |
   |-------|------|----------------------|
   | `Explore` | Find all files/modules affected by this epic based on ticket requirements | → Affected Modules |
   | `Explore` | Discover API patterns, middleware conventions, response formats | → Patterns Discovered (API) |
   | `Explore` | Discover component patterns, naming conventions, state management | → Patterns Discovered (Components) |
   | `Explore` | Find test file locations, testing framework, fixture patterns | → Test Locations & Conventions |
   | `Explore` | Find similar features that can serve as implementation references | → Reference Implementations |

   **Agent Prompts:**

   ```
   Agent 1 - Affected Modules:
   "Find all directories and files that will be affected by implementing [epic summary].
   List the key modules, their purposes, and how they relate to the epic requirements."

   Agent 2 - API Patterns:
   "Analyze the API layer in packages/server/. Document the route structure,
   middleware patterns, authentication approach, response formats, and error handling conventions."

   Agent 3 - Component Patterns:
   "Analyze the frontend components in packages/web/src/components/. Document naming
   conventions, folder structure, state management patterns, and common UI patterns used."

   Agent 4 - Test Patterns:
   "Analyze the test structure in tests/ and e2e/. Document the testing framework,
   file naming conventions, available test utilities, fixture patterns, and mock approaches."

   Agent 5 - Reference Implementations:
   "Find existing features similar to [epic summary] that can serve as templates.
   List the files and explain what patterns from each can be reused."
   ```

   **Wait for all agents to complete**, then synthesize findings into Section 11.

3. **Document unknowns:**
   - Missing information or ambiguous requirements
   - Technical decisions that need architectural input
   - Integration points that need clarification

---

## Phase 2: Planning Document Creation

Create a comprehensive planning document with these sections:

### 1. Epic Overview
- **Purpose:** What problem does this epic solve?
- **User Value:** How does this improve the user experience?
- **Scope:** What is included/excluded from this epic?
- **Key Stakeholders:** Who is impacted by this work?

### 2. Epic Goals & Success Metrics
- **Primary Goal:** Main objective of this epic
- **Success Metrics:** How will we measure success?
- **KPIs:** Quantifiable outcomes (if applicable)

### 3. Requirements Summary
- **Functional Requirements:** What the system must do
- **Non-Functional Requirements:** Performance, security, accessibility, etc.
- **Business Rules:** Constraints and validation rules
- **Edge Cases:** Error handling and boundary conditions

### 4. Technical Change Overview
List all technical changes with risk assessment. For each change:

| Component | Type | Description | Risk Score | Dependencies |
|-----------|------|-------------|------------|--------------|
| [file/component] | [New/Enhancement/Refactor/Fix] | [summary] | [Low/Med/High] | [blockers] |

### 5. Impact Analysis
- **Codebase Impact:** Files, components, APIs affected
- **Data Model Changes:** Database migrations required
- **API Changes:** New endpoints, modified contracts, breaking changes
- **UI/UX Changes:** New screens, modified flows
- **Migration Strategy:** How will existing users/data transition?
- **Rollback Plan:** How can this be safely reverted?
- **Tradeoffs:** What compromises are being made and why?

### 6. Testing Strategy
- **Unit Testing:** Coverage targets (aim for 90% branch coverage)
- **Integration Testing:** Cross-component interactions
- **API Testing:** Endpoint validation and error handling
- **Test Data:** Fixtures and mock data requirements
- **Coverage Goals:** Specific areas requiring high coverage

### 7. User Behavior Testing
- **E2E Scenarios:** Critical user journeys to validate
- **Acceptance Test Cases:** Scenarios derived from requirements
- **User Flows:** Step-by-step validation paths
- **Regression Testing:** Existing flows that must not break

### 8. Implementation Notes
- **Patterns to Follow:** Existing code patterns to replicate
- **Architecture Decisions:** Key technical choices and rationale
- **Technical Debt:** Known shortcuts or future improvements
- **Security Considerations:** Authentication, authorization, data protection

### 9. Acceptance Criteria
Definition of done for this epic:
- [ ] All functional requirements implemented
- [ ] Test coverage meets targets (90% branch coverage)
- [ ] Documentation updated
- [ ] Security review completed (if applicable)
- [ ] Performance benchmarks met (if applicable)
- [ ] Accessibility standards met (if applicable)

### 10. Open Questions & Risks
- **Blockers:** Items preventing progress
- **Unknowns:** Information still needed
- **Assumptions:** Things we're assuming to be true
- **Risks:** Potential issues and mitigation strategies

### 11. Codebase Analysis

Capture findings from codebase exploration to inform the implementation plan:

**Affected Modules:**
- List directories and modules that will be modified
- Example: `packages/server/routes/` - API endpoints affected

**Patterns Discovered:**
- API conventions (route structure, middleware patterns, response formats)
- Test patterns (framework, file locations, fixture patterns)
- Component patterns (naming, structure, state management)
- Database patterns (query patterns, transaction handling)

**Reference Implementations:**
- Similar features that can serve as templates
- Example: "See `packages/web/src/components/events/` for CRUD component patterns"

**Test Locations & Conventions:**
- Unit tests: `tests/unit/` - pattern: `[feature].test.ts`
- Integration tests: `tests/integration/` - pattern: `[endpoint].test.ts`
- E2E tests: `e2e/` - pattern: `[flow].spec.ts`
- Test utilities available: List helpers, fixtures, mocks

### 12. Linked Tickets

**Epic:** [{Epic_Key}]({Epic_URL}) - {Epic_Title}
**Jira Project:** [{Jira_Project}]({Jira_Project_URL})

| Key | Summary | Type | Story Points |
|-----|---------|------|--------------|
| [TICKET-123](url) | Ticket summary | Task/Bug/Story | X |

*Use JQL `Parent = {Epic_Key}` to fetch current ticket list.*

---

## Risk Assessment Framework

Evaluate each technical change across 7 dimensions (score 1-3 each):

| Dimension | Low (1) | Medium (2) | High (3) |
|-----------|---------|------------|----------|
| **Scope** | ≤3 files, isolated change | 4-10 files, single feature | 10+ files, cross-cutting |
| **Dependencies** | All prerequisites exist | Some foundation work needed | Requires significant groundwork |
| **Blocking Factor** | Independent work | Soft dependency for 1-2 tickets | Hard blocker for multiple streams |
| **Stability** | Well-defined, existing patterns | Some unknowns, new patterns | Novel approach, high uncertainty |
| **UX Impact** | Backend/internal only | Secondary flows affected | Core user journey affected |
| **Testing Complexity** | Simple assertions, existing fixtures | New mocks/fixtures needed, async flows | Complex integration, E2E required, hard to isolate |
| **Reversibility** | Easily reverted, no data changes | Moderate effort to rollback | Database migrations, breaking API changes, one-way door |

**Risk Levels:**
- **7-11 (Low):** Proceed with standard implementation
- **12-16 (Medium):** Incremental delivery, extra code review
- **17-21 (High):** Spike/POC first, decompose further, architectural review required

---

## Phase 3: Review & Publish

**MANDATORY CHECKPOINT - Document Review:**

Before publishing, present the complete planning document to the user:

```
## Planning Document Preview for {Epic_Key}

[Full planning document content]

---

Gaps/Unknowns Identified:
- [List any missing information]
- [Technical decisions needing input]
- [High-risk changes requiring spikes]

Ready to publish this planning document to Confluence? (Yes / No / Modify)
```

- **Yes** → Publish to Confluence
- **No** → Ask what changes are needed
- **Modify** → User provides feedback, regenerate and re-confirm

**DO NOT PUBLISH** without explicit user approval.

---

## Phase 4: Publish & Output

1. Publish to Confluence at: `/epics/In Progress/{Epic_Key}/`
   - Page title: "{Epic_Key} {Epic_Title}"

2. Verify the document was published successfully

3. Get the published document URL (`{Overview_Document}`)

---

## Failure Conditions

| Condition | Action |
|-----------|--------|
| Epic key not found | Error message, ask user to verify epic key |
| No linked tickets | Warn user, ask if they want to continue with minimal document |
| Confluence location invalid | Ask user for correct location |
| Missing Jira/Confluence access | Provide instructions for credential setup |
| Codebase exploration inconclusive | Document unknowns, proceed with available information |

---

## Output

**When complete, you MUST provide:**

```
## Epic Planning Complete!

**Overview Document:** {Overview_Document}

### Summary
- Epic: {Epic_Key} - {Epic_Title}
- Tickets Analyzed: [count]
- Technical Changes: [count]
- Risk Profile: [X low, Y medium, Z high]
- Test Coverage Target: 90% branch coverage

### Open Questions
1. [Question needing clarification]
2. [Technical decision needing input]

### Next Step
Run the following command to generate the implementation plan:

/create-implementation-plan {Overview_Document}
```

**CRITICAL:** The Overview Document URL is required for the next step in the workflow chain.

---

## Agent Delegation

**Before creating the planning document:**

- **Codebase Analysis:** Thoroughly explore existing patterns, architecture, and conventions
- **Architecture Review:** Have proposed structure reviewed for completeness
- **Deep Exploration:** Understand current implementation, affected components, dependencies, and test coverage
- **Design Review:** Validate approach for scalability, maintainability, and alignment with existing patterns
