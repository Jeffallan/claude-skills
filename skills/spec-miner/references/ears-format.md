# EARS Format

> Reference for: Spec Miner
> Load when: Writing observed requirements, documenting behaviors

## EARS Syntax

Easy Approach to Requirements Syntax for clear, unambiguous requirements.

### Basic Patterns

**Ubiquitous (Always)**
```
The system shall [action].
```

**Event-Driven**
```
When [trigger], the system shall [action].
```

**State-Driven**
```
While [state], the system shall [action].
```

**Conditional**
```
While [state], when [trigger], the system shall [action].
```

**Optional**
```
Where [feature enabled], the system shall [action].
```

## Example Observations

### Authentication

**OBS-AUTH-001: Login Flow**
```
While credentials are valid, when POST /auth/login is called,
the system shall return JWT access token (15m) and refresh token (7d).
```

**OBS-AUTH-002: Token Refresh**
```
While refresh token is valid, when POST /auth/refresh is called,
the system shall issue new access token.
```

**OBS-AUTH-003: Invalid Token**
```
When expired or invalid token is provided,
the system shall return 401 Unauthorized.
```

### User Management

**OBS-USER-001: User Creation**
```
While email is unique, when POST /users is called with valid data,
the system shall create user with bcrypt-hashed password (rounds=12).
```

**OBS-USER-002: Email Validation**
```
When email format is invalid,
the system shall return 400 with error message "Invalid email format".
```

### Input Validation

**OBS-INPUT-001: Required Fields**
```
When required fields are missing,
the system shall return 400 with field-specific error messages.
```

## Quick Reference

| Type | Pattern | Example Trigger |
|------|---------|-----------------|
| Ubiquitous | shall [action] | Always true |
| Event | When [X], shall | On button click |
| State | While [X], shall | While logged in |
| Conditional | While [X], when [Y], shall | While admin, when delete |
| Optional | Where [X], shall | If feature enabled |
