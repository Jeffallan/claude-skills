# Acceptance Criteria

## Given-When-Then Format

```markdown
### AC-001: [Scenario Name]
Given [context/precondition]
When [action taken]
Then [expected result]
```

## Examples by Type

### Happy Path

```markdown
### AC-001: Successful Login
Given a registered user with valid credentials
When they submit the login form
Then they are redirected to the dashboard
And a success message is displayed
And their session is created

### AC-002: Add Item to Cart
Given a logged-in user viewing a product
When they click "Add to Cart"
Then the item appears in their cart
And the cart badge updates with the count
And a confirmation toast is shown
```

### Error Cases

```markdown
### AC-003: Invalid Login
Given a user with incorrect password
When they submit the login form
Then an error message "Invalid credentials" is displayed
And the password field is cleared
And they remain on the login page

### AC-004: Duplicate Email Registration
Given an email already exists in the system
When a new user tries to register with that email
Then an error message "Email already registered" is displayed
And the form is not submitted
```

### Edge Cases

```markdown
### AC-005: Empty Cart Checkout
Given a user with an empty cart
When they navigate to checkout
Then they see "Your cart is empty" message
And a "Continue Shopping" button is displayed

### AC-006: Session Expiry
Given a user whose session has expired
When they try to perform any authenticated action
Then they are redirected to login
And a message "Session expired, please log in again" is shown
And their intended action is preserved for after login
```

### Authorization

```markdown
### AC-007: Admin-Only Access
Given a regular user (non-admin)
When they try to access /admin/users
Then they receive a 403 Forbidden response
And are redirected to the home page
And an "Access denied" message is shown

### AC-008: Own Resource Only
Given a user viewing another user's profile
When they try to edit the profile
Then the edit button is not visible
And direct URL access returns 403
```

## INVEST Criteria

Good acceptance criteria follow INVEST:

| Criterion | Description | Check |
|-----------|-------------|-------|
| **I**ndependent | Can be tested alone | No dependencies on other ACs |
| **N**egotiable | Details can be discussed | Not over-specified |
| **V**aluable | Delivers user value | Ties to requirement |
| **E**stimable | Effort can be estimated | Clear scope |
| **S**mall | Testable in one session | Not too broad |
| **T**estable | Pass/fail is clear | Objective criteria |

## Quick Reference

| Scenario Type | Given | When | Then |
|---------------|-------|------|------|
| Happy path | Valid state | Valid action | Success result |
| Error | Invalid state/input | Action | Error message |
| Edge case | Boundary condition | Action | Graceful handling |
| Authorization | User role | Protected action | Appropriate access |
| Concurrency | Multiple actors | Simultaneous action | Consistent state |
