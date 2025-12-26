---
description: Create a discovery document for research/customer discovery epics
argument-hint: <epic-key>
---

# Epic Discovery Document Generator

**Epic Key:** $ARGUMENTS

---

## Workflow Chain

This command creates a discovery document for research and customer discovery epics:

```
/create-epic-discovery <epic-key>  → Creates Discovery Document (YOU ARE HERE)
         ↓
[Manual research, interviews, experiments]
         ↓
/synthesize-discovery <doc-urls...>  → Synthesizes findings into actionable tickets
         ↓
Creates tickets in target implementation epics
```

---

## Phase 0: Context Retrieval

1. **Fetch the epic** from Jira using `{Epic_Key}`

2. **Extract from epic:**
   - `{Epic_Title}` - The epic title/name
   - `{Jira_Project}` - The Jira project URL
   - Linked tickets

3. **Determine Confluence location:**
   - Default: `/Epics/Discovery/{Epic_Key}/`
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

## Phase 1: Question Extraction

1. **Read all Jira tickets** linked to epic `{Epic_Key}`
   - Use JQL query: `Parent = {Epic_Key}` to find all child tickets
   - Extract acceptance criteria from each ticket
   - Identify ticket dependencies and relationships
   - Note any technical constraints mentioned
   - Extract explicit questions from ticket descriptions
   - Identify implicit questions from ambiguous requirements
   - Note assumptions that need validation
   - Catalog unknowns and uncertainties

2. **Categorize questions** into themes:
   - Customer/User Discovery (who, what problems, what workflows)
   - Technical Feasibility (can we build it, how complex)
   - Business Viability (is it worth it, what's the ROI)
   - Integration Points (external systems, APIs, data sources)
   - Scope Boundaries (what's in, what's out)

3. **Identify research methods** needed for each question:
   - User interviews
   - Data analysis
   - Technical spikes/POCs
   - Competitive research
   - Expert consultation
   - Prototyping

---

## Phase 2: Discovery Document Creation

Create a discovery document with these sections:

### 1. Discovery Overview
- **Epic:** Link to epic with title
- **Discovery Goal:** What are we trying to learn?
- **Success Criteria:** How do we know discovery is complete?
- **Timeline:** Expected discovery duration (if known)
- **Stakeholders:** Who needs to be involved?

### 2. Hypothesis Map
For each major feature/capability in the epic:

| Hypothesis ID | Statement | Confidence | Validation Method | Status |
|---------------|-----------|------------|-------------------|--------|
| H1 | "Users need X because Y" | Low/Med/High | Interview/Data/Spike | Open |
| H2 | "We can integrate with Z" | Low/Med/High | Technical spike | Open |

### 3. Research Questions Matrix

Organize questions by category and priority:

#### Customer/User Discovery
| ID | Question | Priority | Method | Owner | Status |
|----|----------|----------|--------|-------|--------|
| Q1 | Who are the primary users? | High | Interviews | [TBD] | Open |
| Q2 | What pain points exist today? | High | Interviews + Data | [TBD] | Open |

#### Technical Feasibility
| ID | Question | Priority | Method | Owner | Status |
|----|----------|----------|--------|-------|--------|
| T1 | Can we integrate with X API? | High | Spike | [TBD] | Open |
| T2 | What are the performance implications? | Med | Benchmark | [TBD] | Open |

#### Business Viability
| ID | Question | Priority | Method | Owner | Status |
|----|----------|----------|--------|-------|--------|
| B1 | What's the expected ROI? | High | Analysis | [TBD] | Open |
| B2 | How does this compare to competitors? | Med | Research | [TBD] | Open |

#### Scope & Boundaries
| ID | Question | Priority | Method | Owner | Status |
|----|----------|----------|--------|-------|--------|
| S1 | What's the MVP vs full vision? | High | Discussion | [TBD] | Open |
| S2 | What's explicitly out of scope? | High | Discussion | [TBD] | Open |

### 4. Dependencies & Blockers
- External dependencies (third-party APIs, vendor decisions)
- Internal dependencies (other teams, systems)
- Information blockers (data access, stakeholder availability)
- Timeline dependencies (seasonal, market timing)

### 5. Research Plan

For each high-priority question, outline:

#### Research Activity Template
```
**Activity:** [Interview/Spike/Analysis/etc.]
**Questions Addressed:** Q1, Q2, T1
**Method:** [Detailed approach]
**Participants/Resources:** [Who/what is needed]
**Expected Duration:** [Time estimate]
**Output:** [Deliverable format]
```

### 6. Decision Framework

Define how findings will be evaluated:

| Decision Point | Options | Criteria | Owner |
|----------------|---------|----------|-------|
| Build vs Buy for X | Build, Buy, Partner | Cost, Time, Control | [TBD] |
| Target user segment | Segment A, B, Both | Market size, Fit | [TBD] |

### 7. Risk Register

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Users don't want this feature | Med | High | Early validation interviews | [TBD] |
| Technical integration too complex | Low | High | Spike before commitment | [TBD] |

### 8. Target Implementation Epics

List epics where findings may generate tickets:

| Epic | Title | Relationship |
|------|-------|--------------|
| CC-60 | [Title] | [How discoveries might feed into this] |
| CC-62 | [Title] | [How discoveries might feed into this] |

### 9. Linked Tickets

**Discovery Epic:** [{Epic_Key}]({Epic_URL}) - {Epic_Title}

| Key | Summary | Type | Discovery Focus |
|-----|---------|------|-----------------|
| [TICKET-123](url) | Ticket summary | Task | [Which questions this addresses] |

---

## Phase 3: Review & Publish

**MANDATORY CHECKPOINT - Discovery Document Review:**

```
## Discovery Document Preview for {Epic_Key}

[Full discovery document content]

---

Research Questions Identified: [count]
Hypotheses to Validate: [count]
High-Priority Questions: [count]
Target Implementation Epics: [list]

Ready to publish this discovery document to Confluence? (Yes / No / Modify)
```

**DO NOT PUBLISH** without explicit user approval.

---

## Phase 4: Publish & Output

1. Publish to Confluence at: `/epics/Discovery/{Epic_Key}/`
   - Page title: "{Epic_Key} Discovery - {Epic_Title}"

2. Verify the document was published successfully

3. Get the published document URL (`{Discovery_Document}`)

---

## Failure Conditions

| Condition | Action |
|-----------|--------|
| Epic key not found | Error message, ask user to verify epic key |
| No linked tickets | Warn user, ask if they want to continue with minimal document |
| Confluence location invalid | Ask user for correct location |
| Missing Jira/Confluence access | Provide instructions for credential setup |

---

## Output

**When complete, you MUST provide:**

```
## Discovery Document Complete!

**Discovery Document:** {Discovery_Document}

### Summary
- Epic: {Epic_Key} - {Epic_Title}
- Research Questions: [count]
- Hypotheses to Validate: [count]
- High-Priority Items: [count]
- Target Implementation Epics: [list epic keys]

### Immediate Actions Needed
1. [First research activity to start]
2. [Stakeholders to schedule]
3. [Data to gather]

### Next Steps
After completing discovery research, run:

/synthesize-discovery {Discovery_Document} [additional-source-urls...]

This will synthesize findings and create actionable tickets in target implementation epics.
```

**CRITICAL:** The Discovery Document URL is required for the synthesis step.
