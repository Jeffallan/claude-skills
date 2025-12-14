# Three-Perspective Design

> Reference for: Fullstack Guardian
> Load when: Starting feature implementation

## Design Template

For every feature, address all three layers:

```markdown
## Feature: [Feature Name]

### [Frontend]
- UI components needed
- Client-side validation
- Loading/error states
- Optimistic UI updates
- Accessibility considerations

### [Backend]
- API endpoints (method, path)
- Request/response schemas
- Database operations
- Business logic
- External service calls

### [Security]
- Authentication requirements
- Authorization rules
- Input sanitization
- Rate limiting
- Audit logging
```

## Example: User Profile Update

```markdown
## Feature: User Profile Update

### [Frontend]
- Form with name, email, bio, avatar fields
- Client-side validation with real-time feedback
- Loading states during submission
- Error/success message display
- Optimistic UI updates

### [Backend]
- PUT /api/users/:id endpoint
- Pydantic/Zod schema validation
- Database transaction with rollback on error
- Audit logging for profile changes
- Email verification if email changes

### [Security]
- Authorization: users can only update own profile
- Input sanitization against XSS
- Rate limiting (10 req/min per user)
- File upload validation for avatar (type, size)
- CSRF protection on form submission
```

## Technical Design Document

Create `specs/{feature_name}_design.md` with:

```markdown
# Feature: {Name}

## Requirements (EARS Format)
While <precondition>, when <trigger>, the system shall <response>.

Example: While a user is logged in, when they click Save, the system shall
persist the form data and display a success message.

## Architecture
- Frontend: [Components, state management]
- Backend: [Endpoints, data models]
- Security: [Auth, validation, protection]

## Implementation Plan
- [ ] Step 1: Create Pydantic/Zod schemas
- [ ] Step 2: Implement API endpoint
- [ ] Step 3: Build UI component
- [ ] Step 4: Add error handling
- [ ] Step 5: Write tests
```

## Quick Reference

| Layer | Key Concerns |
|-------|--------------|
| Frontend | UX, validation, states, accessibility |
| Backend | API, data, logic, performance |
| Security | Auth, authz, sanitization, logging |
