---
description: Generate comprehensive sprint retrospective from completed epics
argument-hint: <sprint-number-or-folder-path>
---

# Sprint Retrospective Generator

**Sprint:** $ARGUMENTS

---

## Workflow Chain

This command generates a comprehensive retrospective after all sprint epics are complete:

```
/create-epic-plan <epic-key>     → Creates Overview Document
         ↓
/create-implementation-plan <overview-doc-url>  → Creates Implementation Plan
         ↓
/execute-ticket <ticket-key>     → Executes individual tickets
         ↓
/complete-epic <epic-key>        → Completes epic
         ↓
/complete-sprint <sprint-folder> → Sprint retrospective (YOU ARE HERE)
```

---

## Phase 0: Context Retrieval

1. **Determine sprint identifier:**
   - If `$ARGUMENTS` is a number (e.g., "1", "2"): Sprint [N]
   - If `$ARGUMENTS` is a path: Use as Confluence folder path
   - Default folder: `/Epics/Complete/Sprint [N]/`

2. **Locate all epic documents:**
   - Scan folder: `/Epics/Complete/Sprint [N]/`
   - Find all Overview Documents
   - Find all Implementation Plans
   - Find all Completion Reports

3. **FAILURE CONDITION - No Documents Found:**

   If no epic documents found in the sprint folder:

   **STOP and prompt the user:**
   ```
   I was unable to locate any completed epics in Sprint $ARGUMENTS.

   Searched location: [folder path]

   Please provide:
   1. Sprint number or folder path: [correct value]
   2. Confluence folder containing completed epics: [paste link]
   ```

   **DO NOT PROCEED** until confirmed.

4. **MANDATORY CHECKPOINT - Sprint Document Confirmation:**

   ```
   Please confirm the following before generating retrospective:

   Sprint: $ARGUMENTS
   Folder: [Confluence folder path]

   Epics Found:
   - {Epic_Key_1}: {Epic_Title_1} ([X] tickets, [Y] points)
   - {Epic_Key_2}: {Epic_Title_2} ([X] tickets, [Y] points)
   - ...

   Total: [count] epics, [total tickets] tickets, [total points] story points

   Is this the correct sprint to analyze? (Yes / No / Correct)
   ```

   **DO NOT PROCEED** without explicit user confirmation.

---

## Phase 1: Document Collection & Analysis

1. **Read all documents in parallel:**
   - Load all Overview Documents
   - Load all Implementation Plans
   - Load all Completion Reports
   - Load all related Jira tickets

2. **Extract key data points:**
   - Sprint goals (from epic summaries)
   - Story points: planned vs. completed
   - Ticket counts and statuses
   - Cycle times and completion dates
   - Test coverage metrics
   - Bug counts and patterns
   - Technical debt items
   - Follow-up tickets created
   - Team members involved

3. **Cross-reference data:**
   - Verify consistency across documents
   - Identify gaps or discrepancies
   - Flag incomplete or missing information

---

## Phase 2: Parallel Review Tracks

Execute these review tracks **simultaneously** (parallel analysis):

### Track 1 - Engineering Excellence
**Focus:** Code quality patterns and technical execution

**Analyze:**
- **Code Quality Patterns:** Common patterns used across epics
- **Anti-Patterns Observed:** Problems that appeared multiple times
- **Technical Debt:**
  - Debt introduced: [count items] from [epics]
  - Debt resolved: [count items]
  - Net change: [+/-]
- **Architecture Decisions:**
  - Key decisions made: [list with rationale]
  - Impact across codebase: [description]
- **Performance:**
  - Bottlenecks identified: [list]
  - Optimizations made: [list]
- **Dependency Management:**
  - New dependencies added: [count and justification]
  - Dependency conflicts: [count and resolution]
- **Build/Deployment:**
  - CI/CD pipeline changes: [description]
  - Build time trends: [analysis]

### Track 2 - Quality Assurance
**Focus:** Testing effectiveness and quality metrics

**Analyze:**
- **Test Coverage:**
  - Start of sprint: [%]
  - End of sprint: [%]
  - Coverage by epic: [breakdown]
  - Target met: [Yes/No - 90% target]
- **Testing Gaps:** Areas with insufficient coverage
- **Bug Patterns:**
  - Total bugs found: [count]
  - Bugs by severity: [critical/high/medium/low]
  - Root causes: [common patterns]
  - Bugs escaped to production: [count]
- **Regression Issues:**
  - Regressions introduced: [count]
  - Tests added to prevent: [count]
- **Test Automation:**
  - New automated tests: [count]
  - Test execution time: [trend analysis]
  - Flaky tests: [count and fixes]
- **Edge Cases:**
  - Critical edge cases discovered: [list]
  - Edge cases not caught by initial planning: [list]

### Track 3 - Security & Compliance
**Focus:** Security posture and compliance adherence

**Analyze:**
- **Security Vulnerabilities:**
  - Vulnerabilities found: [count by severity]
  - Vulnerabilities fixed: [count]
  - Outstanding: [count]
- **Authentication/Authorization:**
  - Auth changes made: [description]
  - Security issues found: [list]
  - IDOR vulnerabilities: [count and fixes]
- **Data Privacy:**
  - PII handling: [assessment]
  - Privacy concerns raised: [list]
  - GDPR/compliance considerations: [notes]
- **Compliance Requirements:**
  - Requirements met: [list]
  - Requirements missed: [list]
  - Compliance debt: [items]
- **Security Best Practices:**
  - Practices followed: [list]
  - Practices violated: [list with remediation]
  - Security reviews conducted: [count]

### Track 4 - Product & UX
**Focus:** Feature delivery and user experience

**Analyze:**
- **Feature Completeness:**
  - Features fully delivered: [count]
  - Features partially delivered: [count]
  - Features cut: [count with rationale]
- **Acceptance Criteria:**
  - Criteria met: [%]
  - Criteria requiring follow-up: [list]
- **User Story Quality:**
  - Well-defined stories: [%]
  - Stories requiring significant clarification: [count]
  - Improvement recommendations: [list]
- **UX/UI Consistency:**
  - Design system adherence: [assessment]
  - Inconsistencies found: [list]
  - New UI patterns created: [list]
- **Accessibility:**
  - WCAG compliance: [level achieved]
  - Accessibility issues: [count]
  - Improvements made: [list]
- **User Feedback:**
  - Feedback integrated: [examples]
  - Feedback deferred: [examples with reasons]
- **Scope Creep:**
  - Instances: [count]
  - Impact: [story points added]
  - Management: [how it was handled]

### Track 5 - DevOps & Infrastructure
**Focus:** Operations, infrastructure, and deployment

**Analyze:**
- **CI/CD Pipeline:**
  - Pipeline stability: [%]
  - Build failures: [count and causes]
  - Average build time: [minutes]
  - Deployment frequency: [count]
- **Environment Configuration:**
  - Config changes: [count]
  - Config issues: [count and resolution]
  - Environment drift: [assessment]
- **Database Migrations:**
  - Migrations created: [count]
  - Migration issues: [count]
  - Rollback scenarios tested: [Yes/No]
- **Docker/Container Management:**
  - Container updates: [count]
  - Container issues: [count]
  - Image size optimization: [changes]
- **Monitoring & Logging:**
  - New monitoring added: [description]
  - Logging effectiveness: [assessment]
  - Incidents detected: [count]
  - Alert noise: [assessment]
- **Performance Metrics:**
  - API response times: [trend]
  - Database query performance: [trend]
  - Resource utilization: [analysis]

### Track 6 - Process & Collaboration
**Focus:** Team dynamics and workflow effectiveness

**Analyze:**
- **Estimation Accuracy:**
  - Planned points: [total]
  - Actual points: [total]
  - Variance: [%]
  - Accuracy by epic: [breakdown]
  - Patterns in over/under-estimation: [analysis]
- **Sprint Planning:**
  - Planning session effectiveness: [assessment]
  - Requirements clarity: [score]
  - Dependency identification: [completeness]
- **Blocker Resolution:**
  - Total blockers: [count]
  - Average resolution time: [days/hours]
  - Blocker categories: [breakdown]
  - Prevention opportunities: [list]
- **Documentation Quality:**
  - Documentation created: [count pages]
  - Documentation updated: [count pages]
  - Doc clarity: [assessment]
  - Missing documentation: [gaps identified]
- **Cross-Team Dependencies:**
  - Dependencies identified: [count]
  - Dependencies resolved: [count]
  - Dependencies causing delays: [count]
  - Coordination effectiveness: [assessment]
- **Communication:**
  - Standups: [effectiveness assessment]
  - PR review turnaround: [average time]
  - Communication breakdowns: [count and impact]
  - Improvement areas: [list]
- **Parallel Execution:**
  - Epics executed in parallel: [count]
  - Parallel execution effectiveness: [assessment]
  - Conflicts/merge issues: [count]
  - Coordination overhead: [assessment]

---

## Phase 3: Synthesis & Report Generation

Combine insights from all tracks into a unified retrospective.

### Report Structure

# Sprint $ARGUMENTS Retrospective

## Executive Summary

### Sprint Overview
- **Duration:** [start date] → [end date] ([X] days)
- **Epics Completed:** [count]
- **Total Tickets:** [count]
- **Total Story Points:** [planned] → [actual] ([variance %])

### Sprint Goals
1. [Goal 1]: [Met/Partially Met/Not Met]
2. [Goal 2]: [Met/Partially Met/Not Met]
3. [Goal 3]: [Met/Partially Met/Not Met]

### Key Metrics
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Velocity** | [points] | [points] | [↑/↓/→] |
| **Completion Rate** | [%] | [%] | [↑/↓/→] |
| **Test Coverage** | 90% | [%] | [✓/✗] |
| **Bug Count** | [target] | [actual] | [↑/↓/→] |
| **Cycle Time** | [days] | [days] | [↑/↓/→] |

### Top 3 Wins
1. **[Win 1]:** [Detailed description with specific examples from epics]
2. **[Win 2]:** [Detailed description with specific examples from epics]
3. **[Win 3]:** [Detailed description with specific examples from epics]

### Top 3 Challenges
1. **[Challenge 1]:** [Detailed description, impact, and affected epics]
2. **[Challenge 2]:** [Detailed description, impact, and affected epics]
3. **[Challenge 3]:** [Detailed description, impact, and affected epics]

---

## Epic Breakdown

### Completed Epics
| Epic | Tickets | Points | Duration | Coverage | Status |
|------|---------|--------|----------|----------|--------|
| [{Epic_Key}]({Overview_Document}) | [count] | [pts] | [days] | [%] | [notes] |

### Epic Highlights
For each epic:
- **[{Epic_Key}]:** {Epic_Title}
  - **Objective:** [brief description]
  - **Outcome:** [Met/Exceeded/Partial]
  - **Key Deliverables:** [list 2-3 major items]
  - **Challenges:** [1-2 key challenges]
  - **Technical Debt:** [items introduced]
  - **Follow-up:** [tickets created]

---

## What Went Well

Group by track, with **specific examples** from epics:

### Engineering Excellence
- **[Success 1]:** [Description with epic references]
  - Example: In {Epic_Key}, [specific detail]
  - Impact: [quantifiable outcome]
- **[Success 2]:** [Description with epic references]
  - Example: In {Epic_Key}, [specific detail]
  - Impact: [quantifiable outcome]

### Quality Assurance
- **[Success 1]:** [Description with epic references]
- **[Success 2]:** [Description with epic references]

### Security & Compliance
- **[Success 1]:** [Description with epic references]
- **[Success 2]:** [Description with epic references]

### Product & UX
- **[Success 1]:** [Description with epic references]
- **[Success 2]:** [Description with epic references]

### DevOps & Infrastructure
- **[Success 1]:** [Description with epic references]
- **[Success 2]:** [Description with epic references]

### Process & Collaboration
- **[Success 1]:** [Description with epic references]
- **[Success 2]:** [Description with epic references]

---

## What Needs Improvement

Group by track, with **impact assessment**:

### Engineering Excellence
- **[Issue 1]:** [Description]
  - **Affected Epics:** [{Epic_Key_1}], [{Epic_Key_2}]
  - **Impact:** [High/Medium/Low]
  - **Impact Details:** [quantifiable impact, e.g., "Added 3 days to timeline"]
  - **Root Cause:** [analysis]
  - **Recommendation:** [specific action]

### Quality Assurance
- **[Issue 1]:** [Description with impact assessment]
- **[Issue 2]:** [Description with impact assessment]

### Security & Compliance
- **[Issue 1]:** [Description with impact assessment]
- **[Issue 2]:** [Description with impact assessment]

### Product & UX
- **[Issue 1]:** [Description with impact assessment]
- **[Issue 2]:** [Description with impact assessment]

### DevOps & Infrastructure
- **[Issue 1]:** [Description with impact assessment]
- **[Issue 2]:** [Description with impact assessment]

### Process & Collaboration
- **[Issue 1]:** [Description with impact assessment]
- **[Issue 2]:** [Description with impact assessment]

---

## Action Items

**Prioritized, specific, assignable recommendations with success criteria:**

### Critical (Address Next Sprint)
1. **[Action 1]:**
   - **Category:** [Engineering/QA/Security/Product/DevOps/Process]
   - **Description:** [Clear, actionable description]
   - **Owner:** [Recommended owner/team]
   - **Success Criteria:** [Measurable outcome]
   - **Effort:** [Story points or time estimate]
   - **Related Issues:** [Link to specific problems from "What Needs Improvement"]

2. **[Action 2]:**
   - [Same structure]

### High Priority (Within 2-3 Sprints)
1. **[Action]:** [Same structure]

### Medium Priority (Nice to Have)
1. **[Action]:** [Same structure]

### Deferred (Revisit Later)
1. **[Action]:** [Same structure with deferral reason]

---

## Patterns & Insights

### Technical Patterns to Replicate
- **[Pattern 1]:** [Description]
  - **Where Used:** {Epic_Key} - [specific files/components]
  - **Benefits:** [what made it successful]
  - **Recommendation:** [how to apply elsewhere]

### Anti-Patterns to Avoid
- **[Anti-Pattern 1]:** [Description]
  - **Where Observed:** {Epic_Key} - [specific examples]
  - **Problems Caused:** [impact]
  - **Prevention:** [how to avoid in future]

### Process Improvements
- **[Improvement 1]:** [Specific recommendation]
  - **Current State:** [how it works now]
  - **Proposed State:** [how it should work]
  - **Expected Benefit:** [quantifiable improvement]

### Tool/Workflow Recommendations
- **[Recommendation 1]:** [Tool or workflow suggestion]
  - **Problem It Solves:** [specific pain point]
  - **Implementation:** [how to adopt]
  - **Expected ROI:** [time saved, quality improved, etc.]

---

## Metrics Dashboard

### Sprint Velocity
- **Planned Velocity:** [points]
- **Actual Velocity:** [points]
- **Variance:** [+/- points] ([%])
- **Trend:** [comparison to previous sprints]

### Story Points Analysis
| Epic | Planned | Actual | Variance | Reason for Variance |
|------|---------|--------|----------|-------------------|
| [{Epic_Key}] | [pts] | [pts] | [+/-] | [explanation] |
| **Total** | **[pts]** | **[pts]** | **[+/-]** | |

### Bug Metrics
- **Bugs Introduced:** [count]
  - By epic: [breakdown]
  - By severity: [critical/high/medium/low]
- **Bugs Resolved:** [count]
- **Net Change:** [+/- count]
- **Escaped to Production:** [count]
- **Average Resolution Time:** [hours/days]

### Cycle Time Analysis
- **Average Cycle Time:** [days from start to completion]
- **Cycle Time by Epic:**
  - {Epic_Key}: [days] ([comparison to estimate])
- **Bottlenecks Identified:** [list stages with delays]

### Code Review Metrics
- **PRs Created:** [count]
- **Average Review Time:** [hours/days]
- **PRs with > 1 Revision:** [count] ([%])
- **Average Revisions per PR:** [number]
- **Review Feedback Quality:** [assessment]

### Test Coverage Metrics
- **Sprint Start Coverage:** [%]
- **Sprint End Coverage:** [%]
- **Coverage Change:** [+/- %]
- **Coverage by Epic:** [breakdown]
- **Target Met:** [Yes/No - 90% target]

### Technical Debt Metrics
- **Debt Items at Sprint Start:** [count]
- **Debt Introduced:** [count]
- **Debt Resolved:** [count]
- **Net Change:** [+/- count]
- **Debt by Category:** [breakdown]

---

## Knowledge Transfer

### New Skills/Technologies Adopted
- **[Skill/Tech 1]:** [Description]
  - **Adopted in:** {Epic_Key}
  - **Team Members Trained:** [count/names]
  - **Proficiency Level:** [Beginner/Intermediate/Advanced]
  - **Resources Used:** [documentation, tutorials, etc.]

### Documentation Created
- **Confluence Pages:** [count] pages
  - Epic Overview Documents: [count]
  - Implementation Plans: [count]
  - Completion Reports: [count]
  - Technical guides: [count]
- **Code Documentation:**
  - JSDoc coverage: [%]
  - README updates: [count]
  - API documentation: [endpoints documented]
- **Runbooks:** [count] operational docs created

### Reusable Components/Patterns
- **[Component 1]:** [Description and location]
  - **Use Cases:** [where it can be reused]
  - **Documentation:** [link to docs]
- **[Pattern 1]:** [Description]
  - **Use Cases:** [where it should be applied]
  - **Examples:** [epic references]

### Training Needs Identified
- **[Skill 1]:** [Team members needing training]
  - **Priority:** [High/Medium/Low]
  - **Recommended Resources:** [courses, docs, mentors]
- **[Skill 2]:** [Team members needing training]

---

## Systemic Issues Requiring Immediate Attention

**Issues that appeared across multiple epics or threaten future sprint success:**

### Issue 1: [Title]
- **Category:** [Engineering/QA/Security/Product/DevOps/Process]
- **Severity:** [Critical/High/Medium]
- **Frequency:** Appeared in [count] epics: [{Epic_Key_1}], [{Epic_Key_2}]
- **Description:** [Detailed description of the systemic problem]
- **Impact:** [Quantifiable impact on velocity, quality, or team morale]
- **Root Cause:** [Deep analysis of underlying cause]
- **Immediate Actions:** [Short-term mitigation]
- **Long-Term Solution:** [Strategic fix]
- **Owner:** [Recommended owner/team]
- **Timeline:** [Urgency and deadline]

### Issue 2: [Title]
[Same structure]

---

## Sprint Retrospective Meeting Notes

**For discussion in retrospective meeting:**

### Discussion Topics
1. **[Topic 1]:** [Question or topic for team discussion]
   - Context: [brief background]
   - Data: [relevant metrics or examples]

2. **[Topic 2]:** [Question or topic for team discussion]

### Team Feedback Requested
- **[Question 1]:** [Open-ended question for team input]
- **[Question 2]:** [Open-ended question for team input]

### Experiments for Next Sprint
- **[Experiment 1]:** [Process or technical experiment to try]
  - **Hypothesis:** [What we expect to happen]
  - **Success Criteria:** [How we'll measure success]
  - **Duration:** [How long to run experiment]

---

## Appendix: Epic References

### Epic Documents
- **{Epic_Key_1}:** {Epic_Title_1}
  - Overview: {Overview_Document_1}
  - Implementation Plan: {Implementation_Plan_1}
  - Completion Report: {Completion_Report_1}

### Follow-up Tickets Created
- **[TICKET-KEY]:** [Title]
  - Created by: {Epic_Key}
  - Priority: [High/Medium/Low]
  - Sprint Placement: [Sprint N / Backlog]

### External References
- Sprint Planning Document: [link]
- Sprint Demo Recording: [link]
- Team Capacity Planning: [link]

---

## Phase 4: Review & Publish

**MANDATORY CHECKPOINT - Retrospective Review:**

Before publishing, present the complete retrospective to the user:

```
## Sprint Retrospective Preview for Sprint $ARGUMENTS

[Full retrospective content]

---

Summary Statistics:
- Epics Analyzed: [count]
- Total Data Points: [count]
- Action Items: [count]
- Systemic Issues: [count]

Ready to publish this retrospective? (Yes / No / Modify)
```

- **Yes** → Continue to Phase 5
- **No** → Ask what changes are needed
- **Modify** → User provides feedback, regenerate and re-confirm

**DO NOT PUBLISH** without explicit user approval.

---

## Phase 5: Publish & Share

1. **Publish to Confluence:**
   - Location: `/Retrospectives/Sprint $ARGUMENTS/`
   - Page title: "Sprint $ARGUMENTS Retrospective"

2. **Create action item tracking:**
   - Optional: Create Jira tickets for action items
   - Link action items to retrospective document

3. **Generate distribution summary:**
   - Key findings for leadership
   - Action items requiring executive approval
   - Team announcements

4. **Verify publication:**
   - Confirm document is accessible
   - Get published document URL

---

## Failure Conditions

| Condition | Action |
|-----------|--------|
| No epics found in sprint folder | Error message, ask user to verify sprint number/folder |
| Incomplete epic documentation | Generate retrospective with available data, note gaps |
| Cannot access Confluence | Ask user for alternative location |
| Data inconsistencies across documents | Flag inconsistencies, proceed with best available data |
| Missing metrics/data | Document gaps, generate retrospective with available info |

---

## Output

**When complete, you MUST provide:**

```
## Sprint Retrospective Complete!

**Sprint:** $ARGUMENTS
**Retrospective Document:** {Retrospective_URL}

### Sprint Summary
- **Duration:** [start date] → [end date] ([X] days)
- **Epics Completed:** [count]
- **Total Story Points:** [planned] → [actual] ([variance %])
- **Velocity:** [points]
- **Test Coverage:** [%] (target: 90%)

### Key Findings
- **Top Win:** [Most significant success]
- **Top Challenge:** [Most significant challenge]
- **Critical Issues:** [count] systemic issues requiring immediate attention

### Action Items
- **Critical Priority:** [count] items
- **High Priority:** [count] items
- **Medium Priority:** [count] items
- **Deferred:** [count] items

### Metrics Highlights
- **Velocity Trend:** [↑/↓/→] [comparison to previous sprints]
- **Bug Count:** [count] ([↑/↓/→] from previous sprint)
- **Cycle Time:** [days] average ([↑/↓/→] from previous sprint)
- **Coverage Change:** [+/- %]

### Immediate Actions Required
1. [Action 1] - Owner: [owner] - Deadline: [date]
2. [Action 2] - Owner: [owner] - Deadline: [date]
3. [Action 3] - Owner: [owner] - Deadline: [date]

### Next Sprint Recommendations
- [Recommendation 1]
- [Recommendation 2]
- [Recommendation 3]
```

---

## Agent Delegation

**Parallel Document Analysis:** Use parallel processing to analyze multiple epic documents simultaneously for efficiency.

**Data Synthesis:** Systematically combine insights from multiple sources to identify patterns and trends.

**Statistical Analysis:** Analyze metrics and trends across the sprint for data-driven insights.

**Pattern Recognition:** Identify recurring issues, successes, and opportunities across epics.

**Root Cause Analysis:** Dig deep into systemic issues to identify underlying causes.

**Recommendation Generation:** Generate specific, actionable recommendations based on data and patterns.

**Quality Review:** Review retrospective for completeness, accuracy, and actionability before presenting to user.
