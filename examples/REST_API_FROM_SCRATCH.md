# Building a REST API from Scratch

> **Skills used:** Feature Forge, API Designer, FastAPI Expert, Test Master, DevOps Engineer  
> **Difficulty:** Intermediate  
> **Estimated time:** 2–4 hours  

---

## Overview

This walkthrough demonstrates how multiple skills work together to design, implement, test, and deploy a production-ready REST API for a task management system.

Each skill builds on the output of the previous one.

---

## Scenario

We want to build a Task Management API that allows users to:

- Create tasks
- List tasks
- Mark tasks as completed
- Delete tasks

---

## Step 1 — Define Requirements with Feature Forge

### Invoke

Help me define requirements for a task management REST API.

### What Feature Forge Provides

- User stories  
- Acceptance criteria  
- Functional requirements  
- Data model outline  

### Example Output (Excerpt)

    ### User Stories
    1. As a user, I can create a task with a title and description.
    2. As a user, I can retrieve all tasks.
    3. As a user, I can mark a task as completed.
    4. As a user, I can delete a task.

    ### Acceptance Criteria
    - API must return correct HTTP status codes.
    - Input validation must be enforced.
    - Errors must follow consistent JSON format.

---

## Step 2 — Design the API with API Designer

### Invoke

Design RESTful endpoints based on the defined task management requirements.

### What API Designer Provides

- Resource modeling
- HTTP method mapping
- OpenAPI schema outline
- Error handling conventions

### Example OpenAPI Snippet

    paths:
      /tasks:
        get:
          summary: Retrieve all tasks
        post:
          summary: Create a new task

      /tasks/{id}:
        patch:
          summary: Update task status
        delete:
          summary: Delete a task

---

## Step 3 — Implement with FastAPI Expert

### Invoke

Generate FastAPI implementation using async SQLAlchemy.

### What FastAPI Expert Provides

- Pydantic models
- Async route handlers
- Dependency injection
- Database integration

### Example Implementation

    @app.get("/tasks")
    async def list_tasks(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Task))
        return result.scalars().all()

    @app.post("/tasks", status_code=201)
    async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
        new_task = Task(**task.dict())
        db.add(new_task)
        await db.commit()
        return new_task

---

## Step 4 — Validate with Test Master

### Invoke

Generate pytest test cases for the task API.

### What Test Master Provides

- Unit tests
- Integration tests
- Edge case validation
- Mock database setup

### Example Test Case

    def test_create_task(client):
        response = client.post("/tasks", json={"title": "Test Task"})
        assert response.status_code == 201
        assert response.json()["title"] == "Test Task"

---

## Step 5 — Prepare Deployment with DevOps Engineer

### Invoke

Generate Dockerfile and CI workflow for deployment.

### What DevOps Engineer Provides

- Production Dockerfile
- Environment configuration
- CI/CD setup
- Security hardening suggestions

### Example Dockerfile

    FROM python:3.11-slim
    WORKDIR /app
    COPY . .
    RUN pip install -r requirements.txt
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

---

## Skill Flow Summary

1. Feature Forge defines structured requirements.
2. API Designer converts requirements into REST architecture.
3. FastAPI Expert implements production-ready code.
4. Test Master ensures correctness and reliability.
5. DevOps Engineer prepares the system for deployment.

---

## Key Takeaways

- Skills are sequential and composable.
- Structured requirements prevent chaotic implementation.
- Testing and DevOps are first-class steps, not afterthoughts.
- Multi-skill chaining improves quality and clarity.

---

## Final Result

A fully tested, containerized REST API built using structured multi-skill collaboration.
