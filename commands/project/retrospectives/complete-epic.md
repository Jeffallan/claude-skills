---
description: Complete an epic after all tickets are executed, generate report, and close in Jira
argument-hint: <epic-key>
---

# Complete Epic Workflow

**Epic Key:** $ARGUMENTS

---

## Workflow Chain

This command completes an epic after all tickets have been executed:

```
/create-epic-plan <epic-key>     → Creates Overview Document
         ↓
/create-implementation-plan <overview-doc-url>  → Creates Implementation Plan
         ↓
/execute-ticket <ticket-key>     → Executes individual tickets
         ↓
/complete-epic <epic-key>        → Completes epic (YOU ARE HERE)
         ↓
/complete-sprint <sprint-folder> → Sprint retrospective
```

---

## Phase 0: Context Retrieval

1. **Fetch the epic** from Jira using `{Epic_Key}`

2. **Extract from epic:**
   - `{Epic_Title}` - The epic title/name
   - `{Jira_Project}` - The Jira project URL
   - All linked tickets
   - Epic status

3. **Locate documentation:**
   - Find Overview Document in Confluence at `/Epics/In Progress/{Epic_Key}/`
   - Find Implementation Plan (subpage of Overview Document)

4. **FAILURE CONDITION - Missing Documentation:**

   If documentation cannot be found:

   **STOP and prompt the user:**
   ```
   I was unable to locate the required documents for epic {Epic_Key}.

   Please provide:
   1. Overview Document URL: [paste link]
   2. Implementation Plan URL: [paste link]
   ```

   **DO NOT PROCEED** until confirmed.

5. **MANDATORY CHECKPOINT - Epic Completion Readiness:**

   ```
   Please confirm the following before proceeding with epic completion:

   Epic: {Epic_Key} - {Epic_Title}
   Total Tickets: [count]
   Completed Tickets: [count]
   In Progress: [count]
   Blocked: [count]

   Overview Document: {Overview_Document}
   Implementation Plan: {Implementation_Plan}

   Are all tickets complete and ready to close this epic? (Yes / No / Review)
   ```

   - **Yes** → Continue to Phase 1
   - **No** → List incomplete tickets and exit
   - **Review** → Show detailed ticket status breakdown

   **DO NOT PROCEED** if there are incomplete tickets without explicit user override.

---

## Phase 1: Verification

1. **Verify all tickets are complete:**
   - Check Jira status for each ticket in the epic
   - Identify any tickets not in "Done" status
   - Check for any blocking issues or unresolved dependencies

2. **FAILURE CONDITION - Incomplete Tickets:**

   If any tickets are not complete:

   **STOP and report:**
   ```
   Epic {Epic_Key} has incomplete tickets:

   In Progress:
   - [TICKET-KEY]: [Title] - Status: [status]

   Blocked:
   - [TICKET-KEY]: [Title] - Blocker: [reason]

   To Do:
   - [TICKET-KEY]: [Title]

   Options:
   A) Complete remaining tickets first
   B) Move incomplete tickets to backlog and close epic
   C) Extend epic deadline and keep open

   What would you like to do? [A/B/C]
   ```

   **DO NOT PROCEED** without user decision.

3. **Review implementation quality:**
   - Check that all PRs related to epic tickets are merged
   - Verify test coverage meets 90% target
   - Review any documented deviations or technical debt

---

## Phase 2: Epic Completion Report

Generate a comprehensive epic completion report with these sections:

### 1. Epic Summary
- **Epic:** {Epic_Key} - {Epic_Title}
- **Duration:** Start date → Completion date
- **Total Story Points:** Planned vs. Actual
- **Tickets Completed:** [count]
- **Team Members:** List of contributors

### 2. Objectives & Outcomes
- **Original Goals:** (from Overview Document)
- **Success Metrics:** (from Overview Document)
- **Outcomes Achieved:**
  - Goal 1: [Met/Partially Met/Not Met] - [explanation]
  - Goal 2: [Met/Partially Met/Not Met] - [explanation]
- **Business Impact:** Quantifiable results (users affected, performance improvements, etc.)

### 3. Ticket Breakdown
| Ticket | Title | Points | Completed | Deviations |
|--------|-------|--------|-----------|------------|
| [KEY] | [title] | [pts] | [date] | [any deviations] |

**Summary:**
- Total tickets: [count]
- Average cycle time: [days]
- Tickets with deviations: [count]
- Follow-up tickets created: [count]

### 4. Technical Deliverables
- **Files Created:** [count] files
  - Major components: [list key files]
- **Files Modified:** [count] files
  - Major changes: [list significant modifications]
- **Lines of Code:** +[additions] / -[deletions]
- **Test Coverage:**
  - Unit tests: [count] tests, [%] coverage
  - Integration tests: [count] tests
  - E2E tests: [count] tests
  - Overall coverage: [%] (target: 90%)

### 5. Architecture & Design Decisions
- **Key Architectural Patterns Used:**
  - [Pattern 1]: [explanation and files affected]
  - [Pattern 2]: [explanation and files affected]
- **Design Tradeoffs:**
  - [Decision 1]: [what was chosen vs. alternatives, rationale]
  - [Decision 2]: [what was chosen vs. alternatives, rationale]
- **Reusable Components Created:** [list components that can be reused in future work]

### 6. Quality Metrics
- **Code Review:**
  - PRs created: [count]
  - Average review time: [hours/days]
  - Revision rounds: [average]
- **Bug Tracking:**
  - Bugs found during development: [count]
  - Bugs found in production: [count]
  - Critical issues: [count]
- **Pre-commit/Pre-push Hooks:**
  - Pass rate: [%]
  - Common failures: [list patterns]

### 7. Technical Debt & Follow-up
- **Technical Debt Incurred:**
  - [Item 1]: [description, why it was necessary, remediation plan]
  - [Item 2]: [description, why it was necessary, remediation plan]
- **Follow-up Tickets Created:**
  - [TICKET-KEY]: [Title] - [Priority] - [Sprint placement]
- **Refactoring Opportunities:** [areas identified for future improvement]
- **Performance Optimizations:** [areas that could be optimized]

### 8. Testing & Quality Assurance
- **Test Strategy Effectiveness:**
  - Did tests catch issues early? [Yes/No - examples]
  - Edge cases covered: [list critical edge cases tested]
  - Regression tests added: [count]
- **Quality Issues:**
  - Issues missed by tests: [count and examples]
  - Improvements needed: [suggestions for future testing]

### 9. Documentation Delivered
- **Confluence Pages:**
  - Overview Document: {Overview_Document}
  - Implementation Plan: {Implementation_Plan}
  - [Other docs created]
- **Code Documentation:**
  - JSDoc coverage: [%]
  - README updates: [list files]
  - API documentation: [endpoints documented]
- **Runbook Updates:** [operational documentation added]

### 10. Lessons Learned
#### What Went Well
- [Success 1]: [detailed description with examples]
- [Success 2]: [detailed description with examples]
- [Success 3]: [detailed description with examples]

#### What Could Be Improved
- [Challenge 1]: [description, impact, how it could be avoided]
- [Challenge 2]: [description, impact, how it could be avoided]
- [Challenge 3]: [description, impact, how it could be avoided]

#### Process Improvements
- [Improvement 1]: [specific recommendation]
- [Improvement 2]: [specific recommendation]
- [Improvement 3]: [specific recommendation]

### 11. Risk Assessment Review
Compare planned risks (from Overview Document) with actual outcomes:

| Risk | Planned Level | Actual Impact | Mitigation Effectiveness |
|------|--------------|---------------|-------------------------|
| [Risk 1] | [Low/Med/High] | [description] | [Effective/Partial/Ineffective] |

**Unexpected Risks Encountered:**
- [Risk]: [description and how it was handled]

### 12. Recommendations for Future Epics
- **Planning Phase:**
  - [Recommendation 1]
  - [Recommendation 2]
- **Implementation Phase:**
  - [Recommendation 1]
  - [Recommendation 2]
- **Testing Phase:**
  - [Recommendation 1]
  - [Recommendation 2]

---

## Phase 3: Documentation Updates

**MANDATORY CHECKPOINT - Documentation Updates:**

Before updating documentation, present proposed changes:

```
## Proposed Documentation Updates

### 1. Overview Document Updates
I will add the following "Completion Report" section to {Overview_Document}:

[Show exact content to be added]

### 2. Move to Complete Folder
I will move the epic documentation from:
  FROM: /Epics/In Progress/{Epic_Key}/
  TO: /Epics/Complete/Sprint [N]/{Epic_Key}/

### 3. Update All Ticket Links
I will update all [count] tickets to point to the new location.

Proceed with these updates? (Yes / No / Modify)
```

**DO NOT UPDATE** documentation without explicit approval.

---

## Phase 4: Publish & Close

1. **Publish Epic Completion Report:**
   - Add as a new section to the Overview Document
   - Create a standalone "Completion Report" subpage (optional)

2. **Move documentation to complete:**
   - Move from `/Epics/In Progress/{Epic_Key}/` to `/Epics/Complete/Sprint [N]/{Epic_Key}/`
   - Update all internal links to reflect new location

3. **Update all tickets:**
   - Add completion date
   - Update documentation links to new location
   - Add link to completion report

4. **MANDATORY CHECKPOINT - Close Epic in Jira:**

   ```
   Ready to close epic {Epic_Key} in Jira?

   This will:
   - Set epic status to "Done"
   - Update resolution to "Completed"
   - Add completion comment with report link

   Proceed? (Yes / No)
   ```

   **DO NOT CLOSE** the epic without explicit approval.

5. **Close epic in Jira:**
   - Set status to "Done"
   - Add resolution: "Completed"
   - Add comment with link to completion report

6. **Generate sprint folder reference:**
   - Determine which sprint this epic belongs to
   - Note the sprint folder path for future retrospective

---

## Phase 5: Knowledge Transfer

1. **Identify reusable patterns:**
   - Document any new patterns that should be used in future work
   - Update AGENTS.md if new coding standards were established
   - Update CLAUDE.md if new commands or workflows were created

2. **Share key learnings:**
   - Technical insights that benefit other team members
   - Process improvements that should be adopted
   - Tools or techniques that proved valuable

3. **Update team documentation:**
   - Architecture decision records (ADRs)
   - Design pattern library
   - Best practices guide

---

## Failure Conditions

| Condition | Action |
|-----------|--------|
| Epic not found | Error message, ask user to verify epic key |
| Incomplete tickets exist | Report incomplete tickets, wait for user decision |
| Documentation not found | Ask user for document locations |
| Cannot move Confluence pages | Ask user to move manually, provide instructions |
| Cannot close epic in Jira | Report error, provide manual instructions |
| Missing git history/PRs | Generate report with available data, note gaps |

---

## Output

**When complete, you MUST provide:**

```
## Epic Completion Successful!

**Epic:** {Epic_Key} - {Epic_Title}

### Summary
- Total Story Points: [planned] → [actual]
- Total Tickets: [count] completed
- Duration: [start date] → [end date] ([X] days)
- Test Coverage: [%] (target: 90%)
- Follow-up Tickets: [count] created

### Documentation
- **Completion Report:** {Completion_Report_URL}
- **Overview Document:** {Overview_Document} (updated)
- **Implementation Plan:** {Implementation_Plan}
- **New Location:** /Epics/Complete/Sprint [N]/{Epic_Key}/

### Key Deliverables
- [count] files created
- [count] files modified
- [count] unit tests added
- [count] integration tests added
- [count] E2E tests added

### Technical Debt
- [count] items identified (see completion report)
- [count] follow-up tickets created

### Lessons Learned (Top 3)
1. [Lesson 1]
2. [Lesson 2]
3. [Lesson 3]

### Next Steps
- Review follow-up tickets: [list tickets with links]
- Sprint folder ready for retrospective: /Epics/Complete/Sprint [N]/
- Run `/complete-sprint [N]` when sprint is complete
```

**CRITICAL:** The sprint folder location is needed for sprint retrospective.

---

## Agent Delegation

**Data Analysis:** Analyze git history, PR data, and test coverage systematically.

**Documentation Review:** Review completion report for completeness and accuracy.

**Quality Assessment:** Evaluate test coverage, code quality, and technical debt objectively.

**Knowledge Extraction:** Identify patterns, learnings, and recommendations from the epic execution.

**Process Analysis:** Evaluate workflow efficiency and identify improvement opportunities.
