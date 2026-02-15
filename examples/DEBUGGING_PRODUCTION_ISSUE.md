# Debugging a Production Issue

> **Skills used:** Debugging Wizard, Monitoring Expert, Framework Expert, Test Master  
> **Difficulty:** Intermediate  
> **Estimated time:** 1–3 hours  

---

## Overview

This walkthrough demonstrates how multiple skills collaborate to diagnose, reproduce, fix, and validate a production issue in a web application.

The goal is to show how structured debugging prevents guesswork and reduces time-to-resolution.

---

## Scenario

A production API endpoint `/tasks` is returning intermittent 500 errors.

Users report:

- Random failures when fetching tasks
- Occasional timeout responses
- Inconsistent behavior under load

We need to:

1. Identify the root cause
2. Fix the issue
3. Prevent regression

---

## Step 1 — Analyze Logs with Monitoring Expert

### Invoke

Show recent production errors and performance metrics for the `/tasks` endpoint.

### What Monitoring Expert Provides

- Error traces
- Stack traces
- Request timing data
- Resource usage patterns

### Example Output (Excerpt)

    Error: sqlalchemy.exc.TimeoutError
    QueuePool limit reached
    Endpoint: GET /tasks
    Average response time: 3.4s
    Peak DB connections: 100%

This suggests database connection pool exhaustion.

---

## Step 2 — Investigate Root Cause with Debugging Wizard

### Invoke

Analyze this SQLAlchemy TimeoutError and identify potential causes.

### What Debugging Wizard Provides

- Root cause analysis
- Misconfiguration detection
- Concurrency issues explanation
- Suggested fixes

### Example Output (Excerpt)

    Possible Causes:
    - Connection pool size too small
    - Connections not properly closed
    - Blocking synchronous calls in async context

    Recommended Fix:
    Ensure proper async session handling and increase pool size.

The issue appears to be improper session cleanup.

---

## Step 3 — Inspect Code with Framework Expert

### Invoke

Review FastAPI async database usage and identify incorrect session handling.

### What Framework Expert Provides

- Code-level analysis
- Best practices for async database sessions
- Correct dependency injection pattern

### Problematic Code

    async def list_tasks(db: AsyncSession):
        tasks = await db.execute(select(Task))
        return tasks.scalars().all()

### Suggested Fix

    async def list_tasks(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Task))
        return result.scalars().all()

Ensuring sessions are properly managed via dependency injection prevents connection leaks.

---

## Step 4 — Validate Fix with Test Master

### Invoke

Generate load test and regression tests for the `/tasks` endpoint.

### What Test Master Provides

- Concurrency tests
- Stress test scripts
- Edge case validation
- Regression coverage

### Example Test Snippet

    def test_tasks_endpoint_under_load(client):
        responses = [client.get("/tasks") for _ in range(50)]
        assert all(r.status_code == 200 for r in responses)

This ensures the timeout issue does not reoccur.

---

## Step 5 — Confirm Stability

After deploying the fix:

- Monitor database connection usage
- Track response times
- Validate error rate drops to zero

---

## Skill Flow Summary

1. Monitoring Expert identifies abnormal production behavior.
2. Debugging Wizard analyzes the root cause.
3. Framework Expert provides correct implementation patterns.
4. Test Master validates the fix and prevents regression.

---

## Key Takeaways

- Structured debugging reduces guesswork.
- Monitoring data should guide investigation.
- Framework best practices prevent resource leaks.
- Testing is critical after production fixes.
- Skill chaining creates a disciplined incident response workflow.

---

## Final Result

The `/tasks` endpoint is stabilized, database connections are properly managed, and regression tests ensure the issue does not return.
