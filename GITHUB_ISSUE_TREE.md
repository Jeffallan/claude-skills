# GitHub Issue Tree: Implementing Jira-like Hierarchies

A comprehensive guide to creating Epic → Story → Task hierarchies in GitHub Issues using native task lists and the "Tracked by" feature.

## Table of Contents

- [Overview](#overview)
- [Why This Workaround](#why-this-workaround)
- [Core Concepts](#core-concepts)
- [Label Setup](#label-setup)
- [Issue Templates](#issue-templates)
- [Creating the Hierarchy](#creating-the-hierarchy)
- [How "Tracked by" Works](#how-tracked-by-works)
- [Naming Conventions](#naming-conventions)
- [Real-World Example](#real-world-example)
- [Querying and Filtering](#querying-and-filtering)
- [Best Practices](#best-practices)
- [Limitations vs Jira](#limitations-vs-jira)
- [Advanced Workflows](#advanced-workflows)

---

## Overview

GitHub Issues doesn't natively support hierarchical issue types like Jira's Epic → Story → Task structure. However, by combining task lists with cross-references, we can create a surprisingly effective hierarchy that:

- Provides visual progress tracking with progress bars
- Shows automatic "Tracked by" relationships
- Maintains bidirectional linking between parent and child issues
- Works seamlessly with GitHub Projects and automation
- Requires no third-party tools or plugins

**What we'll build:**

```
Epic #100: User Authentication System
├── Progress: ████████░░ 80% (4 of 5 stories completed)
├── Story #101: Login Flow ✓
│   ├── Task #104: API endpoint ✓
│   ├── Task #105: UI component ✓
│   └── Task #106: Tests ✓
├── Story #102: Registration ✓
│   ├── Task #107: Validation logic ✓
│   └── Task #108: Email verification ✓
├── Story #103: Password Reset (In Progress)
│   ├── Task #109: Reset token generation ✓
│   └── Task #110: Email template (Open)
└── Story #111: OAuth Integration (Open)
```

---

## Why This Workaround

### The Problem

GitHub Issues is flat by design. While this simplicity works for many projects, teams migrating from Jira or managing complex features need:

1. **Hierarchical organization** - Group related work into logical units
2. **Progress visibility** - See completion status at a glance
3. **Scope management** - Break large features into manageable pieces
4. **Sprint planning** - Organize work into achievable increments

### The Solution

GitHub's task list feature (introduced in 2022) provides:

- **Checkboxes that link to issues** - `- [ ] #123`
- **Automatic progress bars** - Visual completion tracking
- **Bidirectional linking** - "Tracked by" appears on child issues
- **Markdown-based** - No special syntax or tools needed

### When to Use This

Use hierarchical issues when:

- Developing complex features spanning multiple PRs
- Coordinating work across multiple team members
- Planning sprints or releases
- Migrating from Jira to GitHub
- Managing dependencies between issues

Don't overcomplicate small projects - flat issues work fine for simple bug fixes or single-person repositories.

---

## Core Concepts

### Three-Tier Hierarchy

| Level | Purpose | Typical Scope | Assignee |
|-------|---------|---------------|----------|
| **Epic** | Large initiative spanning multiple sprints | 2-6 weeks, 3-10 stories | Product/Team Lead |
| **Story** | User-facing feature or capability | 3-5 days, 2-5 tasks | Feature Owner |
| **Task** | Technical implementation unit | 4-8 hours, 1 PR | Developer |

### Task List Syntax

GitHub recognizes these patterns:

```markdown
- [ ] #123 - Unchecked, links to issue #123
- [x] #124 - Checked, marks issue as complete
- [ ] Description without issue number - Simple checkbox
- [ ] #125 Story: Login implementation - Descriptive text
```

**Important:** GitHub automatically:
- Creates clickable links from issue numbers
- Shows progress bars when task lists contain issue references
- Adds "Tracked by #parent" to child issues
- Updates progress when child issues are closed

### Visual Hierarchy

```
Epic (type:epic)
  │
  ├─ Story (type:story, epic:100)
  │    │
  │    ├─ Task (type:task, story:101)
  │    ├─ Task (type:task, story:101)
  │    └─ Task (type:task, story:101)
  │
  └─ Story (type:story, epic:100)
       │
       └─ Task (type:task, story:102)
```

---

## Label Setup

Labels help filter and organize hierarchical issues. Set up these labels once per repository.

### Required Labels

Create labels using `gh` CLI:

```bash
# Issue type labels
gh label create "type:epic" \
  --description "Large initiative spanning multiple stories" \
  --color "7057ff"

gh label create "type:story" \
  --description "User-facing feature or capability" \
  --color "0e8a16"

gh label create "type:task" \
  --description "Technical implementation unit" \
  --color "1d76db"

# Status labels
gh label create "status:planning" \
  --description "Still being defined" \
  --color "fbca04"

gh label create "status:ready" \
  --description "Ready for development" \
  --color "0e8a16"

gh label create "status:in-progress" \
  --description "Currently being worked on" \
  --color "1d76db"

gh label create "status:blocked" \
  --description "Cannot proceed due to dependency" \
  --color "d93f0b"

gh label create "status:review" \
  --description "Awaiting review or testing" \
  --color "fbca04"

# Priority labels
gh label create "priority:high" \
  --description "High priority work" \
  --color "d93f0b"

gh label create "priority:medium" \
  --description "Medium priority work" \
  --color "fbca04"

gh label create "priority:low" \
  --description "Low priority work" \
  --color "0e8a16"
```

### Optional Enhancement Labels

```bash
# Epic-specific relationship labels
gh label create "epic:auth" \
  --description "Part of User Authentication epic" \
  --color "7057ff"

gh label create "epic:payments" \
  --description "Part of Payment Processing epic" \
  --color "7057ff"

# Estimation labels (Fibonacci sequence)
gh label create "estimate:1" --color "c2e0c6"
gh label create "estimate:2" --color "c2e0c6"
gh label create "estimate:3" --color "c2e0c6"
gh label create "estimate:5" --color "c2e0c6"
gh label create "estimate:8" --color "c2e0c6"
gh label create "estimate:13" --color "c2e0c6"
```

### Bulk Label Creation

Save this as `labels.json`:

```json
[
  {"name": "type:epic", "color": "7057ff", "description": "Large initiative spanning multiple stories"},
  {"name": "type:story", "color": "0e8a16", "description": "User-facing feature or capability"},
  {"name": "type:task", "color": "1d76db", "description": "Technical implementation unit"},
  {"name": "status:planning", "color": "fbca04", "description": "Still being defined"},
  {"name": "status:ready", "color": "0e8a16", "description": "Ready for development"},
  {"name": "status:in-progress", "color": "1d76db", "description": "Currently being worked on"},
  {"name": "status:blocked", "color": "d93f0b", "description": "Cannot proceed due to dependency"},
  {"name": "priority:high", "color": "d93f0b", "description": "High priority work"},
  {"name": "priority:medium", "color": "fbca04", "description": "Medium priority work"},
  {"name": "priority:low", "color": "0e8a16", "description": "Low priority work"}
]
```

Then create all labels:

```bash
cat labels.json | jq -r '.[] | "gh label create \"\(.name)\" --description \"\(.description)\" --color \"\(.color)\""' | bash
```

---

## Issue Templates

Create reusable templates for consistent issue creation.

### Epic Template

Save as `.github/ISSUE_TEMPLATE/epic.md`:

```markdown
---
name: Epic
about: Large initiative spanning multiple stories
title: '[EPIC] '
labels: 'type:epic, status:planning'
assignees: ''
---

## Epic Overview

**Goal:** [Describe the high-level business objective]

**Value Proposition:** [Why are we building this? What problem does it solve?]

**Success Metrics:**
- [Metric 1: e.g., 50% reduction in login time]
- [Metric 2: e.g., 90% user satisfaction]
- [Metric 3: e.g., Zero security incidents]

## User Stories

<!-- Add stories as task list items. Create story issues first, then link here. -->

### In Scope
- [ ] #<story-number> [Story title]
- [ ] #<story-number> [Story title]
- [ ] #<story-number> [Story title]

### Out of Scope (Future Consideration)
- [ ] [Feature or capability deferred to later]
- [ ] [Feature or capability deferred to later]

## Dependencies

- **Blocks:** #<issue> - [What this epic blocks]
- **Blocked by:** #<issue> - [What blocks this epic]
- **Related to:** #<issue> - [Related epics or initiatives]

## Technical Considerations

- [Key architectural decision or constraint]
- [Technology choices or requirements]
- [Performance/security/scalability concerns]

## Timeline

- **Target Start:** YYYY-MM-DD
- **Target Completion:** YYYY-MM-DD
- **Actual Start:** [Fill when started]
- **Actual Completion:** [Fill when completed]

## Acceptance Criteria

- [ ] All stories completed and merged
- [ ] Documentation updated
- [ ] Tests passing (unit, integration, e2e)
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Deployed to production

## Notes

[Additional context, links to designs, stakeholder discussions, etc.]
```

### Story Template

Save as `.github/ISSUE_TEMPLATE/story.md`:

```markdown
---
name: Story
about: User-facing feature or capability
title: '[STORY] '
labels: 'type:story, status:planning'
assignees: ''
---

## User Story

**As a** [user type]
**I want** [goal or desire]
**So that** [benefit or value]

## Description

[Detailed description of what needs to be built]

## Epic

**Tracked by Epic:** #<epic-number>

## Tasks

<!-- Create task issues first, then link here with checkboxes -->

### Backend
- [ ] #<task-number> [API endpoint implementation]
- [ ] #<task-number> [Database schema/migration]
- [ ] #<task-number> [Business logic/validation]

### Frontend
- [ ] #<task-number> [UI component implementation]
- [ ] #<task-number> [State management]
- [ ] #<task-number> [Form validation/error handling]

### Testing & Documentation
- [ ] #<task-number> [Unit tests]
- [ ] #<task-number> [Integration tests]
- [ ] #<task-number> [E2E tests]
- [ ] #<task-number> [Documentation updates]

## Acceptance Criteria

- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]
- [ ] [Specific, testable criterion 3]
- [ ] [Specific, testable criterion 4]

## Design

**Mockups/Wireframes:** [Link to Figma, screenshots, or design files]

**API Contract:**
```json
// Example request/response
```

## Dependencies

- **Depends on:** #<issue> - [Must be completed first]
- **Blocks:** #<issue> - [This blocks other work]

## Estimation

**Story Points:** [1, 2, 3, 5, 8, 13]
**Estimated Hours:** [Development time estimate]

## Notes

[Additional context, technical decisions, edge cases, etc.]
```

### Task Template

Save as `.github/ISSUE_TEMPLATE/task.md`:

```markdown
---
name: Task
about: Technical implementation unit
title: '[TASK] '
labels: 'type:task, status:ready'
assignees: ''
---

## Task Description

[Clear, concise description of the technical work]

## Story

**Tracked by Story:** #<story-number>

## Implementation Details

**Files to modify:**
- `path/to/file1.ts`
- `path/to/file2.ts`

**Approach:**
1. [Step-by-step implementation approach]
2. [Step 2]
3. [Step 3]

**Code example/pseudocode:**
```typescript
// Example of expected implementation
```

## Acceptance Criteria

- [ ] Code implements specification
- [ ] Unit tests added/updated
- [ ] No breaking changes to existing functionality
- [ ] Code reviewed and approved
- [ ] Documentation updated (if needed)

## Testing Checklist

- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] Manual testing completed
- [ ] Edge cases handled

## Pull Request Checklist

- [ ] PR created and linked to this issue
- [ ] CI/CD pipeline passing
- [ ] Code review approved
- [ ] Merged to main branch

## Estimated Time

**Hours:** [e.g., 4-6 hours]

## Notes

[Technical notes, gotchas, or considerations]
```

---

## Creating the Hierarchy

Step-by-step workflow for building issue hierarchies.

### Step 1: Create the Epic (Top-Down Approach)

```bash
# Create epic with template
gh issue create \
  --title "[EPIC] User Authentication System" \
  --label "type:epic,status:planning,priority:high" \
  --body "$(cat .github/ISSUE_TEMPLATE/epic.md)"

# Note the issue number (e.g., #100)
```

**Alternative: Use GitHub UI**
1. Navigate to Issues → New Issue
2. Select "Epic" template
3. Fill in the template
4. Submit

### Step 2: Create Story Issues

Create stories that belong to the epic:

```bash
# Story 1
gh issue create \
  --title "[STORY] Login Flow Implementation" \
  --label "type:story,status:planning,epic:auth" \
  --body "Tracked by Epic: #100

As a user
I want to log in with email and password
So that I can access my account securely

## Tasks
<!-- Will add task links here -->
"

# Story 2
gh issue create \
  --title "[STORY] User Registration" \
  --label "type:story,status:planning,epic:auth" \
  --body "Tracked by Epic: #100"

# Story 3
gh issue create \
  --title "[STORY] Password Reset Flow" \
  --label "type:story,status:planning,epic:auth" \
  --body "Tracked by Epic: #100"
```

### Step 3: Link Stories to Epic

Update epic #100 to include story task list:

```bash
gh issue edit 100 --body "$(cat <<'EOF'
## Epic Overview
Implement comprehensive user authentication system.

## Stories

- [ ] #101 Login Flow Implementation
- [ ] #102 User Registration
- [ ] #103 Password Reset Flow

## Timeline
Target: Q1 2025
EOF
)"
```

**Result:** Epic #100 now shows a progress bar tracking 0/3 stories.

### Step 4: Create Task Issues

For each story, create granular tasks:

```bash
# Tasks for Story #101 (Login Flow)
gh issue create \
  --title "[TASK] Implement JWT authentication endpoint" \
  --label "type:task,status:ready,story:101" \
  --assignee "@me" \
  --body "Tracked by Story: #101

Implement POST /api/auth/login endpoint with JWT token generation."

gh issue create \
  --title "[TASK] Create login form component" \
  --label "type:task,status:ready,story:101" \
  --assignee "@me"

gh issue create \
  --title "[TASK] Add login flow tests" \
  --label "type:task,status:ready,story:101" \
  --assignee "@me"
```

### Step 5: Link Tasks to Story

Update story #101 with task list:

```bash
gh issue edit 101 --body "$(cat <<'EOF'
**Tracked by Epic:** #100

As a user I want to log in with email and password.

## Tasks

### Backend
- [ ] #104 Implement JWT authentication endpoint

### Frontend
- [ ] #105 Create login form component

### Testing
- [ ] #106 Add login flow tests
EOF
)"
```

### Step 6: Work the Tasks

As work progresses:

1. **Assign and start task:**
   ```bash
   gh issue edit 104 --add-label "status:in-progress"
   ```

2. **Create PR and link:**
   ```bash
   gh pr create \
     --title "Implement JWT authentication endpoint" \
     --body "Closes #104"
   ```

3. **Merge PR:** Task #104 automatically closes

4. **Check task in story:**
   ```bash
   # Manually check the task in story #101
   # Or let GitHub auto-check when #104 closes
   ```

### Bottom-Up Approach (Alternative)

Some teams prefer creating tasks first:

```bash
# 1. Create all task issues
gh issue create --title "[TASK] JWT endpoint" --label "type:task"
gh issue create --title "[TASK] Login form" --label "type:task"
gh issue create --title "[TASK] Login tests" --label "type:task"

# 2. Create story and link tasks immediately
gh issue create \
  --title "[STORY] Login Flow" \
  --label "type:story" \
  --body "## Tasks
- [ ] #104 JWT endpoint
- [ ] #105 Login form
- [ ] #106 Login tests"

# 3. Create epic and link stories
gh issue create \
  --title "[EPIC] Authentication" \
  --label "type:epic" \
  --body "## Stories
- [ ] #101 Login Flow
- [ ] #102 Registration
- [ ] #103 Password Reset"
```

---

## How "Tracked by" Works

GitHub automatically creates bidirectional relationships.

### Automatic Behavior

When you add `- [ ] #123` to an issue body:

1. **Parent issue** shows task list with checkbox
2. **Child issue #123** shows banner: "Tracked by #parent"
3. **Progress bar** appears on parent showing completion percentage
4. **Closing child** automatically updates parent's progress

### Example Progression

**Initial State:**
```
Epic #100: User Authentication
├── Progress: ░░░░░░░░░░ 0% (0 of 3 completed)
├── [ ] #101 Login Flow
├── [ ] #102 Registration
└── [ ] #103 Password Reset
```

**After Story #101 Completes:**
```
Epic #100: User Authentication
├── Progress: ███░░░░░░░ 33% (1 of 3 completed)
├── [x] #101 Login Flow ✓
├── [ ] #102 Registration
└── [ ] #103 Password Reset
```

**Issue #101 Shows:**
```
┌─────────────────────────────────────┐
│ Tracked by #100                      │
│ User Authentication System           │
└─────────────────────────────────────┘

[Story #101 content here]
```

### Multi-Level Tracking

Tasks can show both story and epic:

```
Task #104: JWT endpoint
┌─────────────────────────────────────┐
│ Tracked by                           │
│  #101 Login Flow Implementation      │
│  #100 User Authentication System     │
└─────────────────────────────────────┘
```

This happens when:
- Task #104 is in Story #101's task list
- Story #101 is in Epic #100's task list

### Manual vs Automatic Checking

**Automatic (Recommended):**
- Close child issue → Checkbox auto-checks
- Reopen child issue → Checkbox auto-unchecks

**Manual:**
- Edit parent issue body
- Change `- [ ] #123` to `- [x] #123`
- Useful for non-issue tasks or milestones

---

## Naming Conventions

Consistent naming improves scannability and filtering.

### Title Prefixes

Use bracket prefixes to identify issue types at a glance:

```
[EPIC] User Authentication System
[STORY] Login Flow Implementation
[TASK] Implement JWT authentication endpoint
```

**Enforcement via gh CLI:**

```bash
# Epic
gh issue create --title "[EPIC] ${EPIC_NAME}"

# Story
gh issue create --title "[STORY] ${STORY_NAME}"

# Task
gh issue create --title "[TASK] ${TASK_NAME}"
```

### Title Structure

**Epics:** `[EPIC] Noun Phrase`
```
✓ [EPIC] User Authentication System
✓ [EPIC] Payment Processing Integration
✓ [EPIC] Multi-Language Support
✗ [EPIC] Implement Auth (too vague)
✗ [EPIC] Fix Login (should be story or task)
```

**Stories:** `[STORY] User-Facing Feature`
```
✓ [STORY] Login Flow Implementation
✓ [STORY] Shopping Cart Checkout
✓ [STORY] Dark Mode Toggle
✗ [STORY] Add JWT (too technical, not user-facing)
✗ [STORY] Fix Bug (should be task or bug label)
```

**Tasks:** `[TASK] Specific Technical Work`
```
✓ [TASK] Implement JWT authentication endpoint
✓ [TASK] Create LoginForm component
✓ [TASK] Add unit tests for auth service
✗ [TASK] Do login stuff (too vague)
✗ [TASK] User can log in (should be story)
```

### Label Naming

**Pattern:** `category:value`

```
type:epic, type:story, type:task
status:planning, status:ready, status:in-progress
priority:high, priority:medium, priority:low
epic:auth, epic:payments, epic:reporting
```

**Benefits:**
- Enables grouping: `label:type:*`
- Clear hierarchy: easier to understand relationships
- Better filtering: `label:"type:story" label:"epic:auth"`

### Branch Naming

Link branches to issues:

```
epic/100-user-authentication
story/101-login-flow
task/104-jwt-endpoint
```

**Automation:**
```bash
ISSUE_NUM=104
ISSUE_TITLE=$(gh issue view $ISSUE_NUM --json title -q .title)
BRANCH_NAME="task/${ISSUE_NUM}-$(echo $ISSUE_TITLE | sed 's/\[TASK\] //' | tr '[:upper:]' '[:lower:]' | tr ' ' '-')"

git checkout -b "$BRANCH_NAME"
```

---

## Real-World Example

Complete workflow for implementing a User Authentication epic.

### The Feature

**Business Requirement:**
"Users need to securely create accounts, log in, and reset forgotten passwords."

### Step-by-Step Implementation

#### Week 1: Planning

**1. Create Epic (#100)**

```bash
gh issue create \
  --title "[EPIC] User Authentication System" \
  --label "type:epic,status:planning,priority:high" \
  --body "$(cat <<'EOF'
## Epic Overview

**Goal:** Implement secure user authentication with email/password and OAuth support.

**Value Proposition:** Enable user accounts to support personalized experiences and data security.

**Success Metrics:**
- Login time < 2 seconds
- 99.9% uptime for auth services
- Zero security incidents in first 90 days
- 90%+ user satisfaction with auth flow

## Stories

- [ ] #101 Login Flow Implementation
- [ ] #102 User Registration Flow
- [ ] #103 Password Reset Flow
- [ ] #104 OAuth Integration (Google, GitHub)
- [ ] #105 Session Management

## Timeline

- **Target Start:** 2025-01-15
- **Target Completion:** 2025-02-28

## Acceptance Criteria

- [ ] All stories completed and merged
- [ ] Security audit passed
- [ ] Load tested (1000 concurrent users)
- [ ] Documentation complete
- [ ] Deployed to production
EOF
)"
```

**2. Create Stories**

```bash
# Story 1: Login Flow
gh issue create \
  --title "[STORY] Login Flow Implementation" \
  --label "type:story,status:planning,epic:auth,priority:high" \
  --body "Tracked by Epic: #100

As a registered user
I want to log in with my email and password
So that I can access my personalized account

## Tasks
<!-- Will add tasks below -->

## Acceptance Criteria
- [ ] User can log in with valid credentials
- [ ] Invalid credentials show clear error message
- [ ] Account locks after 5 failed attempts
- [ ] JWT token expires after 24 hours
- [ ] Remember me option extends session to 30 days"

# Story 2: Registration
gh issue create \
  --title "[STORY] User Registration Flow" \
  --label "type:story,status:planning,epic:auth,priority:high" \
  --body "Tracked by Epic: #100

As a new user
I want to create an account
So that I can use the platform

## Acceptance Criteria
- [ ] Email validation enforced
- [ ] Password strength requirements displayed
- [ ] Email verification sent on registration
- [ ] Duplicate emails rejected gracefully"

# Story 3: Password Reset
gh issue create \
  --title "[STORY] Password Reset Flow" \
  --label "type:story,status:ready,epic:auth,priority:medium" \
  --body "Tracked by Epic: #100

As a user who forgot my password
I want to reset it via email
So that I can regain access to my account"
```

**3. Update Epic with Stories**

```bash
gh issue edit 100 --body "$(cat <<'EOF'
## Epic Overview

**Goal:** Implement secure user authentication system.

## Stories

- [ ] #101 Login Flow Implementation
- [ ] #102 User Registration Flow
- [ ] #103 Password Reset Flow
- [ ] #104 OAuth Integration
- [ ] #105 Session Management

## Timeline
Target: Q1 2025
EOF
)"
```

#### Week 2: Sprint 1 - Login Flow

**4. Break Story #101 into Tasks**

```bash
# Backend tasks
gh issue create \
  --title "[TASK] Create User model and database schema" \
  --label "type:task,status:ready,story:101,backend" \
  --assignee "developer1" \
  --body "Tracked by Story: #101

Create User model with fields:
- email (unique)
- password_hash
- created_at
- updated_at
- last_login

Use bcrypt for password hashing."

gh issue create \
  --title "[TASK] Implement POST /api/auth/login endpoint" \
  --label "type:task,status:ready,story:101,backend" \
  --assignee "developer1"

gh issue create \
  --title "[TASK] Implement JWT token generation" \
  --label "type:task,status:ready,story:101,backend" \
  --assignee "developer1"

# Frontend tasks
gh issue create \
  --title "[TASK] Create LoginForm component" \
  --label "type:task,status:ready,story:101,frontend" \
  --assignee "developer2"

gh issue create \
  --title "[TASK] Implement auth state management" \
  --label "type:task,status:ready,story:101,frontend" \
  --assignee "developer2"

gh issue create \
  --title "[TASK] Create protected route wrapper" \
  --label "type:task,status:ready,story:101,frontend" \
  --assignee "developer2"

# Testing tasks
gh issue create \
  --title "[TASK] Add unit tests for auth service" \
  --label "type:task,status:ready,story:101,testing" \
  --assignee "developer3"

gh issue create \
  --title "[TASK] Add E2E tests for login flow" \
  --label "type:task,status:ready,story:101,testing" \
  --assignee "developer3"
```

**5. Update Story #101 with Tasks**

```bash
gh issue edit 101 --body "$(cat <<'EOF'
**Tracked by Epic:** #100

As a registered user I want to log in with email and password.

## Tasks

### Backend
- [ ] #106 Create User model and database schema
- [ ] #107 Implement POST /api/auth/login endpoint
- [ ] #108 Implement JWT token generation

### Frontend
- [ ] #109 Create LoginForm component
- [ ] #110 Implement auth state management
- [ ] #111 Create protected route wrapper

### Testing
- [ ] #112 Add unit tests for auth service
- [ ] #113 Add E2E tests for login flow

## Acceptance Criteria
- [ ] User can log in with valid credentials
- [ ] Invalid credentials show error
- [ ] Account locks after 5 failed attempts
- [ ] JWT expires after 24 hours
EOF
)"
```

**6. Development Workflow**

```bash
# Developer 1 starts backend work
gh issue edit 106 --add-label "status:in-progress"

# Create feature branch
git checkout -b task/106-user-model

# ... implement code ...

# Create PR
gh pr create \
  --title "Create User model and database schema" \
  --body "Closes #106

Implements User model with:
- Email validation
- Password hashing with bcrypt
- Timestamps
- Migration script

**Testing:**
- Unit tests added
- Migration tested on dev DB" \
  --assignee "@me"

# After PR approved and merged, #106 auto-closes
# Story #101 progress updates: 1/8 tasks complete
```

**7. Sprint Progress Tracking**

```bash
# View epic progress
gh issue view 100

# Output shows:
# [EPIC] User Authentication System
# ████░░░░░░ 20% (1 of 5 stories)
#
# - [ ] #101 Login Flow Implementation (1/8 tasks)
# - [ ] #102 User Registration Flow
# - [ ] #103 Password Reset Flow
# - [ ] #104 OAuth Integration
# - [ ] #105 Session Management
```

#### Week 3-4: Complete Login Story

As tasks complete, the hierarchy auto-updates:

```
Epic #100: User Authentication
├── Progress: ████░░░░░░ 40% (2 of 5 stories)
├── [x] #101 Login Flow ✓ (8/8 tasks)
├── [x] #102 Registration ✓ (6/6 tasks)
├── [ ] #103 Password Reset (2/5 tasks)
├── [ ] #104 OAuth Integration
└── [ ] #105 Session Management
```

#### Week 5: Epic Completion

```bash
# Close final story
gh issue close 105 --comment "All session management tasks complete. Tests passing."

# Epic #100 automatically shows 100% complete
# Now ready to close epic
gh issue close 100 --comment "Epic complete! All authentication features shipped to production.

**Metrics:**
- Login time: 1.2s avg
- Zero security incidents
- 94% user satisfaction
- Deployed: 2025-02-15"
```

---

## Querying and Filtering

Use GitHub's search and `gh` CLI to navigate hierarchies.

### GitHub Web Search

**All epics:**
```
is:issue label:type:epic
```

**Open epics:**
```
is:open is:issue label:type:epic
```

**Stories for specific epic:**
```
is:issue label:type:story label:epic:auth
```

**Tasks assigned to you:**
```
is:open is:issue label:type:task assignee:@me
```

**High priority stories in progress:**
```
is:open label:type:story label:priority:high label:status:in-progress
```

**All issues related to authentication:**
```
is:issue label:epic:auth
```

### gh CLI Queries

**List all epics:**
```bash
gh issue list --label "type:epic" --state all
```

**Show epic with progress:**
```bash
gh issue view 100 --json title,body,labels,state
```

**List stories for epic:**
```bash
gh issue list --label "epic:auth" --label "type:story"
```

**Show tasks for a story:**
```bash
# Extract task numbers from story body
gh issue view 101 --json body -q .body | grep -o '#[0-9]\+' | while read task; do
  gh issue view ${task#\#} --json number,title,state -q '"#\(.number): \(.title) [\(.state)]"'
done
```

**Find blocked issues:**
```bash
gh issue list --label "status:blocked" --json number,title,labels
```

**Sprint planning - ready stories:**
```bash
gh issue list \
  --label "type:story" \
  --label "status:ready" \
  --json number,title,labels \
  --jq '.[] | "#\(.number): \(.title)"'
```

### Advanced Filtering with jq

**Stories grouped by epic:**
```bash
gh issue list --label "type:story" --state all --json number,title,labels --limit 100 | \
jq -r 'group_by(.labels[] | select(.name | startswith("epic:")) | .name) |
       .[] | "Epic: \(.[0].labels[] | select(.name | startswith("epic:")) | .name)\n" +
       (map("  - #\(.number): \(.title)") | join("\n"))'
```

**Completion percentage per epic:**
```bash
# Custom script: epic-progress.sh
#!/bin/bash
EPIC_NUM=$1

BODY=$(gh issue view $EPIC_NUM --json body -q .body)
TOTAL=$(echo "$BODY" | grep -c '- \[.\] #')
DONE=$(echo "$BODY" | grep -c '- \[x\] #')

PERCENT=$((DONE * 100 / TOTAL))
echo "Epic #$EPIC_NUM: $DONE/$TOTAL complete ($PERCENT%)"
```

**Usage:**
```bash
chmod +x epic-progress.sh
./epic-progress.sh 100
# Output: Epic #100: 3/5 complete (60%)
```

### GitHub Projects Integration

**Create project board:**
```bash
gh project create \
  --owner "your-org" \
  --title "Q1 2025 - Authentication Epic" \
  --body "Tracking Epic #100"
```

**Add issues to project:**
```bash
# Add epic and all related stories
gh project item-add PROJECT_ID --owner your-org --issue 100
gh project item-add PROJECT_ID --owner your-org --issue 101
gh project item-add PROJECT_ID --owner your-org --issue 102
```

**View project:**
```bash
gh project view PROJECT_ID --owner your-org
```

---

## Best Practices

Guidelines for effective hierarchical issue management.

### 1. Keep Hierarchies Shallow

**Do:**
```
Epic → Story → Task (3 levels max)
```

**Don't:**
```
Initiative → Epic → Story → Subtask → Microtask (too deep)
```

**Reasoning:** GitHub's task lists work best with 2-3 levels. Deeper nesting becomes hard to navigate and maintain.

### 2. One Epic per Feature

**Do:**
```
Epic #100: User Authentication
Epic #150: Payment Processing
Epic #200: Reporting Dashboard
```

**Don't:**
```
Epic #100: Q1 2025 Features
  ├── User Auth
  ├── Payments
  └── Reporting
```

**Reasoning:** Epics should represent cohesive features, not time periods. Use milestones for time-based grouping.

### 3. Limit Stories per Epic

**Recommended:** 3-10 stories per epic

**Too few (< 3):**
- Epic probably isn't needed
- Just use stories

**Too many (> 10):**
- Epic too large
- Break into multiple epics

### 4. Tasks Should Take < 1 Day

**Good task size:**
- 2-8 hours of work
- Single PR
- Clear start and end

**Signs a task is too large:**
- Takes multiple days
- Requires multiple PRs
- Should probably be a story

### 5. Use Consistent Labels

**Label strategy:**
```bash
# Always include type
type:epic, type:story, type:task

# Always include status
status:planning, status:ready, status:in-progress, status:review

# Optional: epic relationship
epic:auth, epic:payments

# Optional: component
component:backend, component:frontend, component:testing
```

### 6. Close Issues Bottom-Up

**Correct order:**
1. Complete task → Close task
2. All tasks done → Close story
3. All stories done → Close epic

**Anti-pattern:**
- Closing epic while stories are still open
- Closing story while tasks are blocked

### 7. Link PRs to Tasks, Not Stories

**Do:**
```bash
gh pr create --body "Closes #104"  # Task number
```

**Don't:**
```bash
gh pr create --body "Closes #101"  # Story number
```

**Reasoning:** One PR per task maintains clear traceability. Stories track multiple tasks.

### 8. Keep Issue Bodies Updated

**Update when:**
- Adding/removing tasks
- Changing acceptance criteria
- Blocking/unblocking work
- Status changes

**Automation:**
```bash
# Add task to story
STORY=101
NEW_TASK=114
gh issue view $STORY --json body -q .body > /tmp/story-body.md
echo "- [ ] #$NEW_TASK New task description" >> /tmp/story-body.md
gh issue edit $STORY --body-file /tmp/story-body.md
```

### 9. Use Milestones for Time Tracking

Combine with epics:

```bash
# Create milestone
gh api repos/:owner/:repo/milestones -f title="Q1 2025" -f due_on="2025-03-31T00:00:00Z"

# Add epic to milestone
gh issue edit 100 --milestone "Q1 2025"
```

**View epic + milestone:**
```bash
gh issue list --milestone "Q1 2025" --label "type:epic"
```

### 10. Document Dependencies

**In issue body:**
```markdown
## Dependencies

- **Depends on:** #95 - Database migration must complete first
- **Blocks:** #120 - Frontend work waiting on this API
- **Related:** #80 - Similar authentication work for admin panel
```

**Track with labels:**
```bash
gh label create "blocked-by:external" --color "d93f0b"
gh issue edit 104 --add-label "blocked-by:external"
```

### 11. Regular Grooming

**Weekly epic review:**
```bash
# Show all open epics and their progress
gh issue list --label "type:epic" --state open | while read num rest; do
  ./epic-progress.sh ${num#\#}
done
```

**Clean up stale issues:**
```bash
# Find issues with no updates in 30 days
gh issue list --state open --label "type:task" \
  --json number,title,updatedAt \
  --jq '.[] | select(.updatedAt < (now - 30*24*60*60 | todate)) | "#\(.number): \(.title)"'
```

### 12. Templates are Your Friend

Use issue templates consistently:
- Standardizes structure
- Reduces errors
- Speeds up issue creation
- Improves searchability

**Enforce with CI:**
```yaml
# .github/workflows/issue-validation.yml
name: Validate Issue Format

on:
  issues:
    types: [opened]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check for required labels
        if: |
          !contains(github.event.issue.labels.*.name, 'type:epic') &&
          !contains(github.event.issue.labels.*.name, 'type:story') &&
          !contains(github.event.issue.labels.*.name, 'type:task')
        run: |
          echo "::error::Issue must have a type label (type:epic, type:story, or type:task)"
          exit 1
```

---

## Limitations vs Jira

Honest comparison of what you lose (and gain) vs Jira.

### What GitHub Issues Lacks

| Feature | Jira | GitHub | Workaround |
|---------|------|---------|------------|
| **Native hierarchy** | Built-in Epic/Story/Task/Subtask | Task lists only | Use task lists + labels |
| **Custom fields** | Unlimited custom fields | Limited to labels/assignees | Use labels creatively |
| **Story points** | Native field | None | Use `estimate:X` labels |
| **Sprint planning** | Built-in sprints | None | Use milestones or GitHub Projects |
| **Advanced reporting** | Burndown charts, velocity | None | Use GitHub Projects or external tools |
| **Issue linking types** | Blocks, depends on, duplicates | Generic mentions | Document in issue body |
| **Workflows** | Customizable workflows | Labels only | Use labels + automation |
| **Time tracking** | Built-in time logging | None | Use labels or external tools |
| **Roadmaps** | Native roadmap view | None | Use GitHub Projects (beta) |
| **Bulk editing** | Full bulk edit UI | Limited | Use `gh` CLI with scripts |

### What GitHub Issues Does Better

| Feature | GitHub | Jira |
|---------|--------|------|
| **Markdown support** | Full markdown + code blocks | Limited |
| **Integration with code** | Native PR linking, code refs | Plugin required |
| **Speed** | Fast, lightweight | Often slow |
| **Search** | Powerful search syntax | Can be sluggish |
| **Developer experience** | CLI (`gh`), API, automation | Clunky UI |
| **Cost** | Free for public/private repos | Expensive at scale |
| **Simplicity** | Clean, minimal UI | Overwhelming options |
| **GitHub Actions** | Seamless automation | Requires webhooks |

### When to Use GitHub Issues

**Use GitHub Issues if:**
- Small to medium teams (< 50 people)
- Developer-focused workflows
- Want tight code integration
- Value simplicity over complexity
- Open source or GitHub-centric

**Consider Jira if:**
- Large enterprise (100+ people)
- Need extensive reporting
- Non-technical stakeholders need access
- Require complex workflows
- Need advanced resource planning

### Hybrid Approach

Many teams use both:

```
Jira: Product roadmap, high-level epics
  ↓
GitHub: Technical stories, tasks, PRs
```

**Sync with automation:**
```yaml
# .github/workflows/sync-to-jira.yml
name: Sync to Jira

on:
  issues:
    types: [opened, closed]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Create Jira issue
        if: contains(github.event.issue.labels.*.name, 'type:epic')
        uses: atlassian/gajira-create@v2
        with:
          project: PROJ
          issuetype: Epic
          summary: ${{ github.event.issue.title }}
```

---

## Advanced Workflows

Power user techniques for complex projects.

### Automated Issue Creation

**Create entire hierarchy from YAML:**

`epic-template.yaml`:
```yaml
epic:
  title: "User Authentication System"
  labels: ["type:epic", "priority:high"]
  stories:
    - title: "Login Flow Implementation"
      labels: ["type:story", "epic:auth"]
      tasks:
        - title: "Create User model"
          assignee: "developer1"
        - title: "JWT endpoint"
          assignee: "developer1"
        - title: "Login form component"
          assignee: "developer2"

    - title: "User Registration"
      labels: ["type:story", "epic:auth"]
      tasks:
        - title: "Registration endpoint"
        - title: "Email verification"
```

**Script:** `create-hierarchy.sh`
```bash
#!/bin/bash
set -e

YAML_FILE=$1

# Parse YAML and create issues
EPIC_TITLE=$(yq .epic.title $YAML_FILE)
EPIC_LABELS=$(yq '.epic.labels | join(",")' $YAML_FILE)

# Create epic
EPIC_NUM=$(gh issue create --title "$EPIC_TITLE" --label "$EPIC_LABELS" --body "Epic created from template" | grep -o '[0-9]\+$')
echo "Created Epic #$EPIC_NUM"

# Create stories
STORY_COUNT=$(yq '.epic.stories | length' $YAML_FILE)
for i in $(seq 0 $((STORY_COUNT - 1))); do
  STORY_TITLE=$(yq ".epic.stories[$i].title" $YAML_FILE)
  STORY_LABELS=$(yq ".epic.stories[$i].labels | join(\",\")" $YAML_FILE)

  STORY_NUM=$(gh issue create \
    --title "[STORY] $STORY_TITLE" \
    --label "$STORY_LABELS" \
    --body "Tracked by Epic: #$EPIC_NUM" | grep -o '[0-9]\+$')

  echo "  Created Story #$STORY_NUM"

  # Create tasks
  TASK_COUNT=$(yq ".epic.stories[$i].tasks | length" $YAML_FILE)
  TASK_LIST=""

  for j in $(seq 0 $((TASK_COUNT - 1))); do
    TASK_TITLE=$(yq ".epic.stories[$i].tasks[$j].title" $YAML_FILE)
    TASK_ASSIGNEE=$(yq ".epic.stories[$i].tasks[$j].assignee // \"\"" $YAML_FILE)

    ASSIGN_FLAG=""
    if [ -n "$TASK_ASSIGNEE" ]; then
      ASSIGN_FLAG="--assignee $TASK_ASSIGNEE"
    fi

    TASK_NUM=$(gh issue create \
      --title "[TASK] $TASK_TITLE" \
      --label "type:task,story:$STORY_NUM" \
      $ASSIGN_FLAG \
      --body "Tracked by Story: #$STORY_NUM" | grep -o '[0-9]\+$')

    echo "    Created Task #$TASK_NUM"
    TASK_LIST="$TASK_LIST\n- [ ] #$TASK_NUM $TASK_TITLE"
  done

  # Update story with tasks
  gh issue edit $STORY_NUM --body "Tracked by Epic: #$EPIC_NUM\n\n## Tasks\n$TASK_LIST"
done

echo "✓ Hierarchy created successfully!"
```

**Usage:**
```bash
chmod +x create-hierarchy.sh
./create-hierarchy.sh epic-template.yaml
```

### Progress Reporting

**Daily standup report:**

`standup-report.sh`:
```bash
#!/bin/bash

EPIC=$1
TODAY=$(date +%Y-%m-%d)

echo "# Standup Report - $TODAY"
echo "## Epic #$EPIC Progress"
echo ""

# Get epic body
BODY=$(gh issue view $EPIC --json body -q .body)

# Count progress
TOTAL=$(echo "$BODY" | grep -c '- \[.\] #' || true)
DONE=$(echo "$BODY" | grep -c '- \[x\] #' || true)
PERCENT=$((DONE * 100 / TOTAL))

echo "**Overall:** $DONE/$TOTAL stories complete ($PERCENT%)"
echo ""

# Show each story status
echo "## Story Status"
echo "$BODY" | grep -o '- \[.\] #[0-9]\+' | while read checkbox num; do
  NUM=${num#\#}
  STORY=$(gh issue view $NUM --json title,state,labels -q '{title,state,labels:[.labels[].name]}')
  TITLE=$(echo "$STORY" | jq -r .title)
  STATE=$(echo "$STORY" | jq -r .state)
  STATUS=$(echo "$STORY" | jq -r '.labels[] | select(startswith("status:"))')

  if [[ "$checkbox" == *"[x]"* ]]; then
    echo "- ✅ #$NUM: $TITLE (CLOSED)"
  else
    echo "- 🔄 #$NUM: $TITLE ($STATUS)"
  fi
done

echo ""
echo "## Today's Work"
# Show in-progress tasks
gh issue list --label "status:in-progress" --label "type:task" --json number,title,assignees \
  --jq '.[] | "- #\(.number): \(.title) (@\(.assignees[0].login))"'
```

### Dependency Tracking

**Check for circular dependencies:**

`check-dependencies.sh`:
```bash
#!/bin/bash

# Find issues with "Depends on" or "Blocked by" in body
gh issue list --state open --json number,body --limit 100 | \
jq -r '.[] | select(.body | contains("Depends on:") or contains("Blocked by:")) |
       {number, deps: (.body | scan("#[0-9]+") | tonumber)} |
       "\(.number) → \(.deps[])"' | \
sort -u > /tmp/deps.txt

# Check for cycles (simplified - use graph tool for real analysis)
cat /tmp/deps.txt
```

### Automation with GitHub Actions

**Auto-label based on hierarchy:**

`.github/workflows/auto-label.yml`:
```yaml
name: Auto-label hierarchical issues

on:
  issues:
    types: [opened, edited]

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - name: Extract epic from body
        id: extract
        uses: actions/github-script@v6
        with:
          script: |
            const body = context.payload.issue.body || '';
            const epicMatch = body.match(/Tracked by Epic: #(\d+)/);

            if (epicMatch) {
              const epicNum = epicMatch[1];
              const epic = await github.rest.issues.get({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: epicNum
              });

              // Extract epic label (e.g., "epic:auth")
              const epicLabel = epic.data.labels
                .find(l => l.name.startsWith('epic:'));

              if (epicLabel) {
                await github.rest.issues.addLabels({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: context.payload.issue.number,
                  labels: [epicLabel.name]
                });
              }
            }
```

**Auto-close epic when all stories done:**

`.github/workflows/close-epic.yml`:
```yaml
name: Auto-close completed epics

on:
  issues:
    types: [closed]

jobs:
  check-epic:
    runs-on: ubuntu-latest
    if: contains(github.event.issue.labels.*.name, 'type:story')
    steps:
      - name: Check if epic is complete
        uses: actions/github-script@v6
        with:
          script: |
            const body = context.payload.issue.body || '';
            const epicMatch = body.match(/Tracked by Epic: #(\d+)/);

            if (!epicMatch) return;

            const epicNum = epicMatch[1];
            const epic = await github.rest.issues.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: epicNum
            });

            // Check if all tasks in epic are checked
            const epicBody = epic.data.body || '';
            const allChecked = !epicBody.match(/- \[ \] #\d+/);

            if (allChecked && epic.data.state === 'open') {
              await github.rest.issues.update({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: epicNum,
                state: 'closed'
              });

              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: epicNum,
                body: '🎉 All stories completed! Auto-closing epic.'
              });
            }
```

### Dashboard Generation

**Generate markdown report:**

`dashboard.sh`:
```bash
#!/bin/bash

cat << 'EOF' > EPIC_DASHBOARD.md
# Epic Dashboard

Generated: $(date)

## Active Epics

EOF

gh issue list --label "type:epic" --state open --json number,title,body | \
jq -r '.[] | "### Epic #\(.number): \(.title)\n\n\(.body)\n\n---\n"' >> EPIC_DASHBOARD.md

echo "Dashboard generated: EPIC_DASHBOARD.md"
```

---

## Summary

### Quick Reference

**Creating hierarchy:**
```bash
# 1. Create epic
gh issue create --title "[EPIC] Name" --label "type:epic"

# 2. Create stories
gh issue create --title "[STORY] Name" --label "type:story" --body "Tracked by Epic: #100"

# 3. Create tasks
gh issue create --title "[TASK] Name" --label "type:task" --body "Tracked by Story: #101"

# 4. Link stories to epic
gh issue edit 100 --body "## Stories\n- [ ] #101\n- [ ] #102"

# 5. Link tasks to story
gh issue edit 101 --body "## Tasks\n- [ ] #103\n- [ ] #104"
```

**Querying:**
```bash
gh issue list --label "type:epic"                    # All epics
gh issue list --label "type:story" --label "epic:auth"  # Stories for epic
gh issue list --label "type:task" --assignee "@me"   # My tasks
```

**Progress tracking:**
```bash
gh issue view 100  # View epic with progress bar
```

### Key Takeaways

1. ✅ **Use task lists** - Foundation of the hierarchy
2. ✅ **Label consistently** - type:X, status:Y, epic:Z
3. ✅ **Keep shallow** - Max 3 levels (Epic → Story → Task)
4. ✅ **Link bottom-up** - Tasks → Stories → Epic
5. ✅ **Close bottom-up** - Complete tasks, then stories, then epic
6. ✅ **Automate** - Use gh CLI and GitHub Actions
7. ✅ **Template everything** - Consistency = searchability

### Next Steps

1. **Set up labels** - Run label creation commands
2. **Create templates** - Add issue templates to `.github/ISSUE_TEMPLATE/`
3. **Plan your first epic** - Start with a small feature
4. **Iterate** - Refine your process based on team needs

---

## Resources

### Documentation
- [GitHub Task Lists](https://docs.github.com/en/issues/tracking-your-work-with-issues/about-task-lists)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [GitHub Actions](https://docs.github.com/en/actions)

### Tools
- [gh CLI](https://cli.github.com/) - GitHub command-line tool
- [jq](https://stedolan.github.io/jq/) - JSON processing
- [yq](https://github.com/mikefarah/yq) - YAML processing

### Community
- [GitHub Community](https://github.community/)
- [GitHub Discussions](https://github.com/features/discussions)

---

**Last Updated:** 2025-12-14