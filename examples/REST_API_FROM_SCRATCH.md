# Building a REST API from Scratch

> **Skills used:** Feature Forge (`feature-forge`), API Designer (`api-designer`), Golang Pro (`golang-pro`), Test
> Master (`test-master`), DevOps Engineer (`devops-engineer`)
> **Estimated time:** 2-4 hours
> **Difficulty:** Intermediate

## Overview

This walkthrough builds a small task management API in Go. It starts with a spec, turns the spec into an OpenAPI
contract, implements two endpoints, tests them, and packages the result in a Docker image. Each step hands its
output to the next skill, so nothing gets re-typed.

---

## Step 1: Define requirements with Feature Forge

**Prompt:**

```text
Define requirements for a task management API. Users can create tasks with a title and a due date, list their
tasks, and mark a task as done.
```

**What the skill does:** `feature-forge` runs a short interview (its Discover and Interview steps), then writes
the spec in EARS format and ends with an implementation checklist.

**Output excerpt:**

```markdown
### Requirements

- When a user submits a title and an optional due date, the system shall create a task with status "open".
- When a user lists tasks, the system shall return only that user's tasks, newest first.
- When a user marks a task as done, the system shall set its status to "done" and record the time.

### Acceptance criteria

- Creating a task without a title returns an error.
- A user cannot see or change another user's tasks.
```

Save the spec. The next step reads it. Committing it with the code is a good default, so the design decisions
stay next to the implementation.

---

## Step 2: Design the contract with API Designer

**Prompt:**

```text
Design REST endpoints for this spec and write an OpenAPI 3.1 file for them.
```

**What the skill does:** `api-designer` models the resources first, then writes the endpoints and the OpenAPI
file. Its workflow includes a lint check on the spec:

```bash
npx @redocly/cli lint openapi.yaml
```

**Output excerpt:**

```yaml
paths:
  /tasks:
    get:
      summary: List the current user's tasks
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [open, done]
      responses:
        '200':
          description: Task list
    post:
      summary: Create a task
      responses:
        '201':
          description: Task created
        '422':
          description: Validation failed
```

Fix lint errors now. A contract that fails lint will produce handlers that disagree with the docs.

---

## Step 3: Implement with Golang Pro

**Prompt:**

```text
Implement the /tasks endpoints from openapi.yaml in Go, using net/http and a Postgres store.
```

**What the skill does:** `golang-pro` designs small interfaces first, then writes the handlers, and runs
`go vet ./...` before moving on.

**Output excerpt:**

```go
type Task struct {
	ID     int64     `json:"id"`
	Title  string    `json:"title"`
	Status string    `json:"status"`
	DueAt  time.Time `json:"due_at,omitempty"`
}

func (h *Handler) createTask(w http.ResponseWriter, r *http.Request) {
	var in struct {
		Title string `json:"title"`
	}
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}
	if strings.TrimSpace(in.Title) == "" {
		writeError(w, http.StatusUnprocessableEntity, "title is required")
		return
	}
	task, err := h.store.CreateTask(r.Context(), userID(r), in.Title)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "could not create task")
		return
	}
	writeJSON(w, http.StatusCreated, task)
}
```

Note how the validation error maps to the `422` response in the contract. That match is the point of writing the
contract first.

---

## Step 4: Test with Test Master

**Prompt:**

```text
Write table-driven tests for the /tasks handlers, including the empty-title case and the cross-user case.
```

**What the skill does:** `test-master` plans the test cases from the acceptance criteria, then writes them.
For Go handlers it uses `httptest`, which is also what `golang-pro` expects in its own testing step.

**Output excerpt:**

```go
func TestCreateTask(t *testing.T) {
	tests := []struct {
		name string
		body string
		want int
	}{
		{"valid title", `{"title":"Write docs"}`, http.StatusCreated},
		{"empty title", `{"title":""}`, http.StatusUnprocessableEntity},
		{"bad json", `{`, http.StatusBadRequest},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodPost, "/tasks", strings.NewReader(tt.body))
			rec := httptest.NewRecorder()
			handler.ServeHTTP(rec, req)
			if rec.Code != tt.want {
				t.Errorf("got status %d, want %d", rec.Code, tt.want)
			}
		})
	}
}
```

Run the tests with the race detector on, as both skills require: `go test -race ./...`.

---

## Step 5: Package with DevOps Engineer

**Prompt:**

```text
Write a multi-stage Dockerfile for this Go API and a GitHub Actions workflow that runs go vet and the tests,
then builds the image.
```

**What the skill does:** `devops-engineer` writes the Dockerfile and the pipeline, then checks the config
before calling it done.

**Output excerpt:**

```dockerfile
FROM golang:1.23 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/api ./cmd/api

FROM gcr.io/distroless/static-debian12
COPY --from=build /out/api /api
EXPOSE 8080
ENTRYPOINT ["/api"]
```

---

## Key takeaways

1. The spec from step 1 is the input to every later step. Write it once, reuse it four times.
2. The contract in step 2 decides the error codes. The handler in step 3 just follows it.
3. The tests in step 4 come from the acceptance criteria, not from the finished code.
