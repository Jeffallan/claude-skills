# Adding Authentication to an Existing Application

> **Skills used:** Secure Code Guardian, Framework Expert, Test Master, Security Reviewer  
> **Difficulty:** Intermediate  
> **Estimated time:** 2–3 hours  

---

## Overview

This walkthrough demonstrates how multiple skills work together to securely add authentication to an existing REST API.

The goal is to:

- Protect sensitive endpoints
- Implement JWT-based authentication
- Validate security implementation
- Prevent common vulnerabilities

---

## Scenario

We have an existing task management API with public endpoints:

- GET /tasks
- POST /tasks
- PATCH /tasks/{id}
- DELETE /tasks/{id}

Currently, anyone can access these endpoints.

We need to:

1. Add user authentication
2. Protect routes
3. Prevent unauthorized access
4. Ensure secure implementation

---

## Step 1 — Define Security Requirements with Secure Code Guardian

### Invoke

Define authentication requirements for securing a REST API using JWT.

### What Secure Code Guardian Provides

- Authentication flow design
- Password handling recommendations
- Token expiration policies
- Security best practices

### Example Output (Excerpt)

    Requirements:
    - Passwords must be hashed using bcrypt.
    - Access tokens must expire after 15 minutes.
    - Refresh tokens should be implemented.
    - Protected routes must validate JWT before execution.

This establishes security-first design principles.

---

## Step 2 — Implement JWT Authentication with Framework Expert

### Invoke

Generate FastAPI JWT authentication implementation with login and protected routes.

### What Framework Expert Provides

- User model updates
- Password hashing logic
- Login endpoint
- JWT creation and validation
- Route protection via dependencies

### Example Implementation

    from fastapi import Depends, HTTPException
    from jose import jwt

    @app.post("/login")
    async def login(user: UserLogin):
        # Validate credentials
        # Generate JWT token
        return {"access_token": token}

    @app.get("/tasks")
    async def list_tasks(current_user: User = Depends(get_current_user)):
        return await fetch_tasks()

Protected routes now require a valid token.

---

## Step 3 — Validate Security with Test Master

### Invoke

Generate test cases for authentication and authorization logic.

### What Test Master Provides

- Valid login tests
- Invalid credential tests
- Expired token tests
- Unauthorized access tests

### Example Test Snippet

    def test_protected_route_requires_token(client):
        response = client.get("/tasks")
        assert response.status_code == 401

    def test_login_returns_token(client):
        response = client.post("/login", json={"username": "user", "password": "pass"})
        assert "access_token" in response.json()

This ensures access control works as intended.

---

## Step 4 — Review Security with Security Reviewer

### Invoke

Review authentication implementation for vulnerabilities.

### What Security Reviewer Provides

- Token validation review
- Secret key storage recommendations
- Detection of hardcoded credentials
- CSRF and replay attack considerations

### Example Recommendations

    - Store JWT secret in environment variables.
    - Enable HTTPS in production.
    - Implement token revocation for logout.
    - Limit login attempts to prevent brute force attacks.

This final review strengthens the implementation.

---

## Skill Flow Summary

1. Secure Code Guardian defines authentication architecture.
2. Framework Expert implements JWT-based authentication.
3. Test Master verifies correct authorization behavior.
4. Security Reviewer validates the system against vulnerabilities.

---

## Key Takeaways

- Authentication must be designed before implementation.
- Route protection should use framework-native patterns.
- Testing prevents broken access control.
- Security review ensures production readiness.
- Multi-skill chaining leads to safer deployments.

---

## Final Result

The application now supports secure JWT-based authentication with protected routes, validated access control, and production-ready security practices.
