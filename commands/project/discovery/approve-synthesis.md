---
description: Approve synthesis findings and create implementation tickets from discovery
argument-hint: <synthesis-url> [--decision=<id>:<value>...]
---

# Approve Discovery Synthesis

**Arguments:** $ARGUMENTS

---

## Argument Parsing

Parse the arguments to extract:
- `{Synthesis_URL}` - Confluence synthesis document URL (required)
- `{Decisions}` - Optional pre-provided decision resolutions (via `--decision=D1:OptionB`)

**Examples:**
- `/approve-synthesis https://confluence/synthesis-doc` → Review and approve interactively
- `/approve-synthesis https://confluence/synthesis-doc --decision=D1:B --decision=D2:Y` → Pre-resolve decisions

---

## Workflow Chain

```
/create-epic-discovery <epic-key>  → Discovery Document
         ↓
[Manual research, interviews, experiments]
         ↓
/synthesize-discovery <doc-urls...>  → Synthesis Document
         ↓
/approve-synthesis <synthesis-url>  → Creates Jira Tickets (YOU ARE HERE)
         ↓
/create-implementation-plan <overview-doc>  → Implementation planning continues
```

---

## Phase 0: Context Retrieval

1. **Fetch the synthesis document** from `{Synthesis_URL}`

2. **Extract from synthesis document:**
   - Discovery Epic link
   - Target implementation epics
   - Proposed tickets JSON (from Section 9, between `<!-- PROPOSED_TICKETS_START -->` and `<!-- PROPOSED_TICKETS_END -->` markers)
   - Blocking decisions and their status
   - Approval status

3. **FAILURE CONDITION - Invalid Synthesis Document:**

   If synthesis document cannot be fetched or lacks required sections:

   **STOP and prompt the user:**
   ```
   I was unable to retrieve the synthesis document or it is missing required data.

   URL: {Synthesis_URL}
   Issue: [document not found / missing Proposed Tickets section / invalid JSON]

   Please verify:
   1. The URL is correct and accessible
   2. The document was created by /synthesize-discovery
   3. The "Proposed Tickets Data" section (Section 9) exists
   ```

   **DO NOT PROCEED** until valid document is provided.

4. **FAILURE CONDITION - Already Approved:**

   If synthesis is already approved (`approval_status: "approved"`):

   **STOP and report:**
   ```
   This synthesis has already been approved.

   Approved By: [user]
   Approved Date: [date]
   Tickets Created: [list]

   Options:
   A) View the created tickets
   B) Create additional tickets (will append to existing)
   C) Cancel
   ```

   **DO NOT PROCEED** without user choice.

5. **MANDATORY CHECKPOINT - Synthesis Overview:**

   ```
   ## Synthesis Document Retrieved

   **Discovery Epic:** {Discovery_Epic_Key}
   **Synthesis Date:** [date]
   **Sources Analyzed:** [count]

   **Proposed Tickets:** [count] tickets, [sum] story points
   **Target Epics:** [list epic keys]
   **Blocking Decisions:** [count] pending / [count] total

   Ready to review? (Yes / No)
   ```

   **DO NOT PROCEED** without confirmation.

---

## Phase 1: Decision Resolution

1. **Check for unresolved blocking decisions:**

   Parse the `blocking_decisions` array from the JSON data.

2. **Apply any pre-provided decisions** from `--decision` arguments:

   For each `--decision=ID:Value`:
   - Validate the decision ID exists
   - Validate the value is a valid option
   - Mark as resolved

3. **FAILURE CONDITION - Unresolved Blocking Decisions:**

   If any blocking decisions remain unresolved:

   **STOP and present each decision:**
   ```
   ## Blocking Decisions Require Resolution

   The following decisions must be resolved before tickets can be created:

   ### Decision D1: [Decision Question]

   **Options:**
   A) [Option A description]
   B) [Option B description]
   C) [Option C description]

   **Recommendation:** [Option from synthesis]
   **Rationale:** [Why this was recommended]
   **Blocks Tickets:** T1, T3, T5

   Please select an option: [A/B/C]

   ---

   ### Decision D2: [Decision Question]
   ...
   ```

   **DO NOT PROCEED** until all decisions are resolved.

4. **Record decision resolutions:**

   For each resolved decision:
   - Record the chosen option
   - Record resolver (user)
   - Record timestamp
   - Update affected tickets if decision changes scope

---

## Phase 2: Ticket Review & Editing

1. **Present proposed tickets for review:**

   ```
   ## Proposed Tickets for Approval

   All blocking decisions have been resolved. Review the tickets below.

   ### Epic: {Epic_Key_1} - {Epic_Title}

   | # | ID | Title | Type | Points | Priority | Dependencies |
   |---|-----|-------|------|--------|----------|--------------|
   | 1 | T1 | [title] | Story | 5 | High | None |
   | 2 | T2 | [title] | Task | 3 | Med | T1 |

   ### Epic: {Epic_Key_2} - {Epic_Title}

   | # | ID | Title | Type | Points | Priority | Dependencies |
   |---|-----|-------|------|--------|----------|--------------|
   | 1 | T3 | [title] | Spike | 2 | High | None |

   **Total:** [count] tickets, [sum] story points

   ---

   **Options:**
   - **Approve** - Create all tickets as shown
   - **Edit** - Modify tickets before creation
   - **Cancel** - Exit without creating tickets

   What would you like to do? [Approve / Edit / Cancel]
   ```

2. **If Edit selected:**

   ```
   ## Edit Proposed Tickets

   Available actions:
   - **Add:** Add a new ticket (e.g., "Add Story 'Implement caching' to CC-62")
   - **Remove:** Remove a ticket (e.g., "Remove T3")
   - **Modify:** Change ticket details (e.g., "Modify T1 points to 8" or "Modify T2 priority to High")
   - **Done:** Finish editing and review again

   Current tickets:
   [... ticket list ...]

   Enter your changes (or "Done" to finish):
   ```

   **Editing loop:**
   - Parse user input for add/remove/modify commands
   - Apply changes to proposed tickets
   - Show updated list after each change
   - Repeat until user says "Done"
   - Return to approval checkpoint

3. **MANDATORY CHECKPOINT - Final Ticket Approval:**

   ```
   ## Final Ticket Approval

   The following tickets will be created in Jira:

   [... final ticket list with all edits applied ...]

   **Total:** [count] tickets, [sum] story points

   Create these tickets? (Yes / No)
   ```

   **DO NOT CREATE TICKETS** without explicit "Yes" approval.

---

## Phase 3: Ticket Creation

For each approved ticket:

1. **Create ticket in Jira** under the target epic:

   ```
   Creating ticket: [title]
   Epic: {Target_Epic}
   ```

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
- [ ] [Criterion from synthesis]
- [ ] [Criterion from synthesis]

## Notes from Discovery
- [Relevant insights that inform implementation]
- [Constraints or considerations discovered]

## Decisions Made
- D1: [Decision question] → [Resolution chosen]

---
*This ticket was generated from discovery synthesis. See source documents for full context.*
```

4. **Link tickets:**
   - Link to discovery epic as "discovered by"
   - Link dependencies between tickets (using Jira issue links)
   - Link to any relevant existing tickets

5. **Track created tickets:**

   Maintain mapping: `{ T1: "CC-123", T2: "CC-124", ... }`

6. **FAILURE CONDITION - Ticket Creation Fails:**

   If any ticket creation fails:

   ```
   ## Ticket Creation Error

   Failed to create ticket: [title]
   Error: [error message]

   **Tickets Created So Far:**
   - CC-123: [title]
   - CC-124: [title]

   **Remaining Tickets:**
   - [title] (failed)
   - [title] (pending)

   Options:
   A) Retry failed ticket
   B) Skip failed ticket and continue
   C) Stop and save progress

   What would you like to do? [A/B/C]
   ```

---

## Phase 4: Update & Output

1. **Update synthesis document in Confluence:**

   Add/update Section 10: Approved Tickets:

   ```markdown
   ### 10. Approved Tickets

   **Approval Date:** [timestamp]
   **Approved By:** [user]
   **Decisions Resolved:** [count]

   #### Tickets Created

   | Jira Key | Title | Type | Epic | Points |
   |----------|-------|------|------|--------|
   | [CC-123](url) | [title] | Story | CC-62 | 5 |
   | [CC-124](url) | [title] | Task | CC-62 | 3 |

   **Total:** [count] tickets, [sum] story points

   #### Decision Resolutions

   | Decision | Question | Resolution | Resolved By |
   |----------|----------|------------|-------------|
   | D1 | [question] | Option B | [user] |

   #### Changes from Original Proposal

   - Added: [list any added tickets]
   - Removed: [list any removed tickets]
   - Modified: [list any modified tickets]
   ```

2. **Update JSON approval status** in Section 9:

   ```json
   {
     "approval_status": "approved",
     "approved_by": "[user]",
     "approved_date": "[timestamp]",
     "created_tickets": {
       "T1": "CC-123",
       "T2": "CC-124"
     }
   }
   ```

3. **Update discovery epic** with:
   - Link to synthesis document
   - Summary of tickets created

---

## Output

**When complete, you MUST provide:**

```
## Synthesis Approved - Tickets Created!

**Synthesis Document:** {Synthesis_URL} (updated)

### Decisions Resolved

| Decision | Resolution |
|----------|------------|
| D1 | [chosen option] |
| D2 | [chosen option] |

### Tickets Created

#### {Epic_Key_1}: {Epic_Title}
| Key | Title | Type | Points |
|-----|-------|------|--------|
| [CC-123](url) | [title] | Story | 5 |
| [CC-124](url) | [title] | Task | 3 |

#### {Epic_Key_2}: {Epic_Title}
| Key | Title | Type | Points |
|-----|-------|------|--------|
| [CC-125](url) | [title] | Spike | 2 |

**Total:** [count] tickets, [sum] story points

### Changes from Original Proposal
- Added: [list or "None"]
- Removed: [list or "None"]
- Modified: [list or "None"]

### Next Steps
1. Review created tickets in Jira
2. Run implementation planning:

/create-implementation-plan {Target_Epic_Overview_Doc}
```

---

## Failure Conditions

| Condition | Action |
|-----------|--------|
| Synthesis URL not accessible | Ask user to verify URL |
| Missing Proposed Tickets section | Ask user to run /synthesize-discovery first |
| Invalid JSON in Proposed Tickets | Report parsing error, ask for manual fix |
| Unresolved blocking decisions | Present decisions for resolution, block ticket creation |
| Synthesis already approved | Offer options: view, append, or cancel |
| Jira ticket creation fails | Report error, offer retry/skip/stop options |
| Confluence update fails | Provide content for manual update |
| Target epic not found | Ask user to verify epic key |

---

## Agent Delegation

**Before ticket creation:**

- **Validation:** Verify target epics exist and are accessible
- **Decision Review:** Ensure all blocking decisions are properly resolved
- **Dependency Check:** Validate ticket dependencies are consistent

**During ticket creation:**

- **Parallel Creation:** Create tickets in parallel where no dependencies exist
- **Link Verification:** Verify all Jira links are created correctly
