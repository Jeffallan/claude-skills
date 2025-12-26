---
description: Synthesize discovery findings into actionable implementation tickets
argument-hint: <source-url> [source-url...] [--target=<epic-key>]
---

# Synthesize Discovery Findings

**Arguments:** $ARGUMENTS

---

## Argument Parsing

Parse the arguments to extract:
- `{Source_URLs}` - One or more Confluence document URLs (space-separated)
- `{Target_Epic}` - Optional target implementation epic (via `--target=CC-XX`)

**Examples:**
- `/synthesize-discovery https://confluence/doc1` → Single source, auto-detect target epics
- `/synthesize-discovery https://confluence/doc1 https://confluence/doc2` → Multiple sources
- `/synthesize-discovery https://confluence/doc1 --target=CC-62` → Single source, specific target epic
- `/synthesize-discovery doc1-url doc2-url doc3-url --target=CC-62` → Multiple sources, specific target

**Supported Source Types:**
- Discovery Documents (from `/create-epic-discovery`)
- Research findings documents
- Interview summaries
- Technical spike reports
- Competitive analysis documents
- Any Confluence page with structured findings

---

## Workflow Chain

```
/create-epic-discovery <epic-key>  → Discovery Document
         ↓
[Manual research, interviews, experiments]
         ↓
/synthesize-discovery <doc-urls...>  → Synthesis Document (YOU ARE HERE)
         ↓
Creates tickets in target implementation epics
         ↓
/create-implementation-plan <overview-doc>  → Implementation planning continues
```

---

## Phase 0: Source Retrieval

1. **Fetch all source documents** from the provided URLs

2. **Extract from each source:**
   - Document type (discovery doc, research findings, spike report, etc.)
   - Key findings and insights
   - Validated/invalidated hypotheses
   - Answered research questions
   - Remaining unknowns
   - Recommendations

3. **Identify target implementation epics:**
   - If `--target` specified, use that epic
   - Otherwise, extract from "Target Implementation Epics" sections
   - If none found, ask user to specify

4. **FAILURE CONDITION - Missing Information:**

   If sources cannot be fetched or no target epics identified:

   **STOP and prompt the user:**
   ```
   I was unable to retrieve required information.

   Sources Retrieved: [count]/[total]
   Failed Sources: [list URLs that failed]
   Target Epics Found: [list or "None"]

   Please provide:
   1. Confirm source URLs are accessible
   2. Target implementation epic(s): [e.g., CC-62, CC-60]
   ```

   **DO NOT PROCEED** until confirmed.

5. **MANDATORY CHECKPOINT - Sources Confirmation:**

   ```
   Please confirm before I proceed:

   Sources to Synthesize:
   1. [URL] - [Document Title] ([type])
   2. [URL] - [Document Title] ([type])
   ...

   Target Implementation Epic(s): [list]

   Is this correct? (Yes / No / Correct)
   ```

   **DO NOT PROCEED** without explicit user confirmation.

---

## Phase 1: Cross-Source Analysis

1. **Consolidate findings across all sources:**
   - Merge hypothesis validation results
   - Combine research question answers
   - Identify consistent themes
   - Note contradictions or conflicts

2. **Create findings inventory:**

   | Finding ID | Source(s) | Category | Finding | Confidence | Actionable |
   |------------|-----------|----------|---------|------------|------------|
   | F1 | Doc1, Doc2 | User Need | Users want X | High | Yes |
   | F2 | Doc1 | Technical | API supports Y | Med | Yes |
   | F3 | Doc3 | Business | ROI is Z | Low | Needs validation |

3. **Identify patterns:**
   - Recurring themes across sources
   - Convergent conclusions
   - Divergent opinions requiring resolution

4. **Catalog remaining unknowns:**
   - Questions still unanswered
   - New questions that emerged
   - Areas needing further research

---

## Phase 2: Recommendation Generation

1. **Generate feature recommendations:**
   For each actionable finding, determine:
   - Should this become a ticket?
   - What type of work is it? (Feature, Enhancement, Spike, Research)
   - Which implementation epic does it belong to?
   - What's the priority based on findings?
   - Are there dependencies on other recommendations?

2. **Create recommendation matrix:**

   | Rec ID | Based On | Title | Type | Target Epic | Priority | Dependencies |
   |--------|----------|-------|------|-------------|----------|--------------|
   | R1 | F1, F2 | Implement X feature | Story | CC-62 | High | None |
   | R2 | F3 | Validate ROI assumption | Spike | CC-60 | Med | R1 |
   | R3 | F1 | Design user flow for X | Task | CC-62 | High | None |

3. **Identify scope decisions needed:**
   - Features that could go multiple directions
   - Trade-offs requiring stakeholder input
   - MVP vs future phase decisions

---

## Phase 3: Synthesis Document Creation

Create a comprehensive synthesis document:

### 1. Synthesis Overview
- **Discovery Epic:** Link to original discovery epic
- **Sources Analyzed:** List all source documents with links
- **Synthesis Date:** When this synthesis was created
- **Target Implementation Epics:** Links to target epics

### 2. Executive Summary
- **Key Insight:** One-paragraph summary of most important discovery
- **Recommendation:** High-level direction based on findings
- **Confidence Level:** Overall confidence in recommendations
- **Major Decisions Needed:** List any blocking decisions

### 3. Consolidated Findings

#### Validated Hypotheses
| ID | Original Hypothesis | Validation Status | Evidence | Implications |
|----|---------------------|-------------------|----------|--------------|
| H1 | [statement] | Validated | [sources] | [what this means] |
| H2 | [statement] | Partially Validated | [sources] | [caveats] |
| H3 | [statement] | Invalidated | [sources] | [pivot needed] |

#### Research Questions Answered
| ID | Question | Answer | Confidence | Source(s) |
|----|----------|--------|------------|-----------|
| Q1 | [question] | [answer] | High/Med/Low | [docs] |

#### Key Insights
Narrative summary of the most important learnings, organized by theme:

**User/Customer Insights:**
- [Insight with supporting evidence]

**Technical Insights:**
- [Insight with supporting evidence]

**Business Insights:**
- [Insight with supporting evidence]

### 4. Remaining Unknowns

| ID | Unknown | Impact | Recommendation | Priority |
|----|---------|--------|----------------|----------|
| U1 | [what we don't know] | [why it matters] | [next step] | High/Med/Low |

### 5. Recommendations by Epic

For each target implementation epic:

#### {Epic_Key}: {Epic_Title}

**Recommended Tickets:**

| # | Title | Type | Priority | Story Points | Dependencies | Based On |
|---|-------|------|----------|--------------|--------------|----------|
| 1 | [title] | Story | High | 5 | None | F1, F2 |
| 2 | [title] | Task | Med | 3 | #1 | F3 |

**Scope Recommendations:**
- What should be included in MVP
- What should be deferred to future phases
- What should NOT be built based on findings

**Risk Adjustments:**
- New risks identified from discovery
- Updated risk levels based on findings
- Mitigation strategies learned

### 6. Decision Log

Decisions that need to be made before implementation:

| Decision | Options | Recommendation | Rationale | Owner | Deadline |
|----------|---------|----------------|-----------|-------|----------|
| [decision] | A, B, C | B | [why] | [who] | [when] |

### 7. Source Cross-Reference

Map findings back to sources:

| Source | Key Contributions | Findings Referenced |
|--------|-------------------|---------------------|
| [Doc1 URL] | [what this doc contributed] | F1, F2, F5 |
| [Doc2 URL] | [what this doc contributed] | F3, F4 |

### 8. Appendix: Full Findings Inventory

Complete list of all findings extracted from sources with full detail.

---

## Phase 4: Review & Approval

**MANDATORY CHECKPOINT - Synthesis Review:**

```
## Synthesis Document Preview

[Full synthesis document content]

---

Summary:
- Sources Analyzed: [count]
- Findings Extracted: [count]
- Hypotheses Validated: [count] / Invalidated: [count]
- Recommended Tickets: [count]
- Target Epics: [list]

Ready to proceed? (Yes / No / Modify)
```

- **Yes** → Continue to ticket creation
- **No** → Ask what changes are needed
- **Modify** → User provides feedback, regenerate

**DO NOT PROCEED** without explicit approval.

---

## Phase 5: Ticket Creation

**MANDATORY CHECKPOINT - Ticket Creation Approval:**

Before creating any tickets, present the full list:

```
## Proposed Tickets from Discovery Synthesis

### Epic: {Epic_Key_1}

| # | Title | Type | Points | Priority |
|---|-------|------|--------|----------|
| 1 | [title] | Story | 5 | High |
| 2 | [title] | Task | 3 | Med |

### Epic: {Epic_Key_2}

| # | Title | Type | Points | Priority |
|---|-------|------|--------|----------|
| 1 | [title] | Spike | 2 | High |

Total: [count] tickets across [count] epics

Create these tickets? (Yes / No / Modify)
```

- **Yes** → Create all tickets
- **No** → Skip ticket creation, just publish synthesis document
- **Modify** → User adjusts list, re-confirm

**DO NOT CREATE TICKETS** without explicit approval.

### Ticket Creation Process

For each approved ticket:

1. **Create ticket in Jira** under the target epic
2. **Set ticket fields:**
   - Summary: [Title]
   - Type: Story/Task/Bug/Spike
   - Epic Link: {Target_Epic}
   - Story Points: [estimated]
   - Priority: [from synthesis]
   - Labels: `from-discovery`, `{Discovery_Epic_Key}`

3. **Populate description using template:**

```markdown
## Source
- Discovery Epic: [{Discovery_Epic_Key}]({url})
- Synthesis Document: [{Synthesis_Doc}]({url})
- Based on Findings: [F1, F2, ...]

## Context
[Why this ticket was created based on discovery findings]

## Summary
[What this ticket accomplishes]

## Acceptance Criteria
- [ ] [Criterion derived from findings]
- [ ] [Criterion derived from findings]

## Notes from Discovery
- [Relevant insights that inform implementation]
- [Constraints or considerations discovered]

---
*This ticket was generated from discovery synthesis. See source documents for full context.*
```

4. **Link tickets:**
   - Link to discovery epic as "discovered by"
   - Link dependencies between tickets
   - Link to any relevant existing tickets

---

## Phase 6: Publish & Output

1. **Publish synthesis document** to Confluence:
   - Location: `/epics/Discovery/{Discovery_Epic_Key}/Synthesis/`
   - Title: "{Discovery_Epic_Key} Synthesis - [Date]"

2. **Update discovery document** with link to synthesis

3. **Update target epic(s)** with:
   - Link to synthesis document
   - Summary of tickets created

---

## Output

**When complete, you MUST provide:**

```
## Discovery Synthesis Complete!

**Synthesis Document:** {Synthesis_Document_URL}

### Sources Analyzed
1. [Doc1 Title]({url})
2. [Doc2 Title]({url})
...

### Summary
- Total Findings: [count]
- Validated Hypotheses: [count]
- Invalidated Hypotheses: [count]
- Remaining Unknowns: [count]

### Tickets Created

#### {Epic_Key_1}: {Epic_Title}
| Key | Title | Type | Points |
|-----|-------|------|--------|
| CC-XXX | [title] | Story | 5 |
| CC-XXX | [title] | Task | 3 |

#### {Epic_Key_2}: {Epic_Title}
| Key | Title | Type | Points |
|-----|-------|------|--------|
| CC-XXX | [title] | Spike | 2 |

**Total:** [count] tickets, [sum] story points

### Decisions Pending
1. [Decision needing resolution]
2. [Decision needing resolution]

### Next Steps
1. Resolve pending decisions listed above
2. Review and refine created tickets
3. Run implementation planning:

/create-implementation-plan {Target_Epic_Overview_Doc}
```

---

## Failure Conditions

| Condition | Action |
|-----------|--------|
| Source URL not accessible | List failed URLs, ask for alternatives |
| No target epic specified or found | Ask user to specify target epic(s) |
| Conflicting findings across sources | Document conflicts, ask user to resolve |
| Jira ticket creation fails | Log error, continue with remaining tickets |
| Confluence publish fails | Provide document content for manual publishing |

---

## Agent Delegation

**Before synthesis:**

- **Document Analysis:** Use Explore agents to analyze each source document in parallel
- **Pattern Recognition:** Identify themes and patterns across sources
- **Cross-Reference:** Map findings to their sources

**During ticket creation:**

- **Validation:** Verify target epics exist and are accessible
- **Dependency Mapping:** Ensure ticket dependencies are correctly ordered
