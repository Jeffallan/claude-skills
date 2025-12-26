---
description: Complete a ticket after execution - transitions Jira to "In Review" and updates the implementation plan
argument-hint: [ticket-key] (optional if context available)
---

# Complete Ticket Workflow

**Purpose:** Finalize a ticket after `/execute-ticket` by transitioning Jira and updating the implementation plan.

---

## Step 1: Identify Ticket and Context

**If argument provided:** Use `$ARGUMENTS` as the ticket key.

**If no argument:** Look back in the conversation for:
- The most recently executed ticket (from `/execute-ticket`)
- The implementation plan URL (extracted during execution)

**If ticket cannot be identified:**
```
I couldn't identify which ticket to complete. Please provide the ticket key:

/complete-ticket <ticket-key>
```

---

## Step 2: Gather Completion Details

**From the Jira ticket:**
- Implementation Plan URL (from ticket description)

**From conversation context:**

| Field | Source |
|-------|--------|
| Ticket Key | From argument or recent `/execute-ticket` |
| Changes Made | From the completion summary presented |
| Files Modified | From the completion summary |
| Tests Added | From the completion summary |
| Deviations | Any approved deviations discussed |
| Follow-up Tickets | Any tickets created during implementation |

**If completion summary not found in context:**
```
I couldn't find a completion summary in this conversation.

Please either:
1. Run `/execute-ticket {ticket-key}` first
2. Provide a brief summary of what was done
```

**If Implementation Plan URL not in ticket:**
```
The ticket doesn't have an Implementation Plan URL.

Please provide the Implementation Plan URL to update:
```

---

## Step 3: Confirm Before Finalizing

Present a brief confirmation:

```
## Ready to Complete {Ticket_Key}

**Changes to make:**
- Transition Jira to "In Review"
- Update implementation plan with completion details

**Summary extracted from context:**
- Files modified: [count]
- Tests added: [count]
- Deviations: [Yes/None]
- Follow-up tickets: [Yes/None]

Proceed? (Yes / No)
```

**Wait for user confirmation before proceeding.**

---

## Step 4: Execute Finalization

**4a. Transition Jira ticket to "In Review"**

```
Use: jira_get_transitions to find "In Review" transition ID
Use: jira_transition_issue to transition the ticket
```

**4b. Update the Implementation Plan in Confluence**

Fetch the current implementation plan page and update:

1. **Completion Status table** - Add row:
   | Ticket | Status | Completed Date | Notes |
   | [ticket] | ✅ Complete | [today's date] | [brief summary] |

2. **Execution Order table** - Update ticket's Status column to "✅ Complete"

3. **Parallel Execution Strategy wave table** - Update ticket's Status to "✅ Complete"

4. **Add Completion Details section:**
   ```
   ## {Ticket_Key} Completion Details

   **Completed:** [date]

   ### Changes Made
   * [extracted from summary]

   ### Tests Added
   * [extracted from summary]

   ### Deviations
   [Any deviations, or "None"]

   ### Follow-up Tickets
   [Any follow-up tickets, or "None"]
   ```

---

## Step 5: Confirm Completion

```
## {Ticket_Key} Completed

- [x] Jira transitioned to "In Review"
- [x] Implementation plan updated (version N)

**Next steps:**
- Create git commit using the suggested commit message
- Create PR when ready
```

---

## Error Handling

**If Jira transition fails:**
- Report the error
- Ask user if they want to retry or skip

**If Confluence update fails:**
- Report the error
- Provide the completion details so user can manually update if needed

**If implementation plan URL not found:**
- Fetch the ticket from Jira
- Extract the implementation plan URL from the description
- If still not found, ask user to provide it

---

## Standalone Usage

This command can be used standalone (without prior `/execute-ticket`) if the user provides details:

```
/complete-ticket CC-123
```

If no context is available, prompt user for:
1. Implementation plan URL
2. Brief summary of changes made
3. Files modified
4. Tests added (if any)
5. Any deviations or follow-up tickets
