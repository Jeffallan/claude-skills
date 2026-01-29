# Project Structure and Module Management

## Standard Project Layout

```
myproject/
├── cmd/                    # Main applications
│   ├── server/
│   │   └── main.go        # Entry point for server
│   └── cli/
│       └── main.go        # Entry point for CLI tool
├── internal/              # Private application code
│   ├── api/              # API handlers
│   ├── service/          # Business logic
│   └── repository/       # Data access layer
├── pkg/                   # Public library code
│   └── models/           # Shared models
├── api/                   # API definitions
│   ├── openapi.yaml      # OpenAPI spec
│   └── proto/            # Protocol buffers
├── web/                   # Web assets
│   ├── static/
│   └── templates/
├── scripts/               # Build and install scripts
├── configs/              # Configuration files
├── deployments/          # Docker, K8s configs
├── test/                 # Additional test data
├── docs/                 # Documentation
├── go.mod               # Module definition
├── go.sum               # Dependency checksums
├── Makefile             # Build automation
└── README.md
```

## go.mod Basics

```go
// Initialize module
// go mod init github.com/user/project

module github.com/user/myproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/lib/pq v1.10.9
    go.uber.org/zap v1.26.0
)

require (
    // Indirect dependencies (automatically managed)
    github.com/bytedance/sonic v1.9.1 // indirect
    github.com/chenzhuoyu/base64x v0.0.0-20221115062448-fe3a3abad311 // indirect
)

// Replace directive for local development
replace github.com/user/mylib => ../mylib

// Retract directive to mark bad versions
retract v1.0.1 // Contains critical bug
```

## Module Commands

```bash
# Initialize module
go mod init github.com/user/project

# Add missing dependencies
go mod tidy

# Download dependencies
go mod download

# Verify dependencies
go mod verify

# Show module graph
go mod graph

# Show why package is needed
go mod why github.com/user/package

# Vendor dependencies (copy to vendor/)
go mod vendor

# Update dependency
go get -u github.com/user/package

# Update to specific version
go get github.com/user/package@v1.2.3

# Update all dependencies
go get -u ./...

# Remove unused dependencies
go mod tidy
```

## Internal Packages

```go
// internal/ packages can only be imported by code in the parent tree

myproject/
├── internal/
│   ├── auth/           # Can only be imported by myproject
│   │   └── jwt.go
│   └── database/
│       └── postgres.go
└── pkg/
    └── models/         # Can be imported by anyone
        └── user.go

// This works (same project):
import "github.com/user/myproject/internal/auth"

// This fails (different project):
import "github.com/other/project/internal/auth" // Error!

// Internal subdirectories
myproject/
└── api/
    └── internal/       # Can only be imported by code in api/
        └── helpers.go
```

## Package Organization

```go
// user/user.go - Domain package
package user

import (
    "context"
    "time"
)

// User represents a user entity
type User struct {
    ID        string
    Email     string
    CreatedAt time.Time
}

// Repository defines data access interface
type Repository interface {
    Create(ctx context.Context, user *User) error
    GetByID(ctx context.Context, id string) (*User, error)
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id string) error
}

// Service handles business logic
type Service struct {
    repo Repository
}

// NewService creates a new user service
func NewService(repo Repository) *Service {
    return &Service{repo: repo}
}

func (s *Service) RegisterUser(ctx context.Context, email string) (*User, error) {
    user := &User{
        ID:        generateID(),
        Email:     email,
        CreatedAt: time.Now(),
    }
    return user, s.repo.Create(ctx, user)
}
```

## Multi-Module Repository (Monorepo)

```
monorepo/
├── go.work              # Workspace file
├── services/
│   ├── api/
│   │   ├── go.mod
│   │   └── main.go
│   └── worker/
│       ├── go.mod
│       └── main.go
└── shared/
    └── models/
        ├── go.mod
        └── user.go

// go.work
go 1.21

use (
    ./services/api
    ./services/worker
    ./shared/models
)

// Commands:
// go work init ./services/api ./services/worker
// go work use ./shared/models
// go work sync
```

## Build Tags and Constraints

```go
// +build integration
// integration_test.go

package myapp

import "testing"

func TestIntegration(t *testing.T) {
    // Integration test code
}

// Build: go test -tags=integration

// File-level build constraints (Go 1.17+)
//go:build linux && amd64

package myapp

// Multiple constraints
//go:build linux || darwin
//go:build amd64

// Negation
//go:build !windows

// Common tags:
// linux, darwin, windows, freebsd
// amd64, arm64, 386, arm
// cgo, !cgo
```

## Makefile Example

```makefile
# Makefile
.PHONY: build test lint clean run

# Variables
BINARY_NAME=myapp
BUILD_DIR=bin
GO=go
GOFLAGS=-v

# Build the application
build:
	$(GO) build $(GOFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME) ./cmd/server

# Run tests
test:
	$(GO) test -v -race -coverprofile=coverage.out ./...

# Run tests with coverage report
test-coverage: test
	$(GO) tool cover -html=coverage.out

# Run linters
lint:
	golangci-lint run ./...

# Format code
fmt:
	$(GO) fmt ./...
	goimports -w .

# Run the application
run:
	$(GO) run ./cmd/server

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)
	rm -f coverage.out

# Install dependencies
deps:
	$(GO) mod download
	$(GO) mod tidy

# Build for multiple platforms
build-all:
	GOOS=linux GOARCH=amd64 $(GO) build -o $(BUILD_DIR)/$(BINARY_NAME)-linux-amd64 ./cmd/server
	GOOS=darwin GOARCH=amd64 $(GO) build -o $(BUILD_DIR)/$(BINARY_NAME)-darwin-amd64 ./cmd/server
	GOOS=windows GOARCH=amd64 $(GO) build -o $(BUILD_DIR)/$(BINARY_NAME)-windows-amd64.exe ./cmd/server

# Run with race detector
run-race:
	$(GO) run -race ./cmd/server

# Generate code
generate:
	$(GO) generate ./...

# Docker build
docker-build:
	docker build -t $(BINARY_NAME):latest .

# Help
help:
	@echo "Available targets:"
	@echo "  build         - Build the application"
	@echo "  test          - Run tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Run linters"
	@echo "  fmt           - Format code"
	@echo "  run           - Run the application"
	@echo "  clean         - Clean build artifacts"
	@echo "  deps          - Install dependencies"
```

## Dockerfile Multi-Stage Build

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o server ./cmd/server

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy binary from builder
COPY --from=builder /app/server .

# Copy config files if needed
COPY --from=builder /app/configs ./configs

EXPOSE 8080

CMD ["./server"]
```

## Version Information

```go
// version/version.go
package version

import "runtime"

var (
    // Set via ldflags during build
    Version   = "dev"
    GitCommit = "none"
    BuildTime = "unknown"
)

// Info returns version information
func Info() map[string]string {
    return map[string]string{
        "version":    Version,
        "git_commit": GitCommit,
        "build_time": BuildTime,
        "go_version": runtime.Version(),
        "os":         runtime.GOOS,
        "arch":       runtime.GOARCH,
    }
}

// Build with version info:
// go build -ldflags "-X github.com/user/project/version.Version=1.0.0 \
//   -X github.com/user/project/version.GitCommit=$(git rev-parse HEAD) \
//   -X github.com/user/project/version.BuildTime=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

## Go Generate

```go
// models/user.go
//go:generate mockgen -source=user.go -destination=../mocks/user_mock.go -package=mocks

package models

type UserRepository interface {
    GetUser(id string) (*User, error)
    SaveUser(user *User) error
}

// tools.go - Track tool dependencies
//go:build tools

package tools

import (
    _ "github.com/golang/mock/mockgen"
    _ "golang.org/x/tools/cmd/stringer"
)

// Install tools:
// go install github.com/golang/mock/mockgen@latest

// Run generate:
// go generate ./...
```

## Configuration Management

```go
// config/config.go
package config

import (
    "os"
    "time"

    "github.com/kelseyhightower/envconfig"
)

type Config struct {
    Server   ServerConfig
    Database DatabaseConfig
    Redis    RedisConfig
}

type ServerConfig struct {
    Host         string        `envconfig:"SERVER_HOST" default:"0.0.0.0"`
    Port         int           `envconfig:"SERVER_PORT" default:"8080"`
    ReadTimeout  time.Duration `envconfig:"SERVER_READ_TIMEOUT" default:"10s"`
    WriteTimeout time.Duration `envconfig:"SERVER_WRITE_TIMEOUT" default:"10s"`
}

type DatabaseConfig struct {
    URL          string `envconfig:"DATABASE_URL" required:"true"`
    MaxOpenConns int    `envconfig:"DB_MAX_OPEN_CONNS" default:"25"`
    MaxIdleConns int    `envconfig:"DB_MAX_IDLE_CONNS" default:"5"`
}

type RedisConfig struct {
    Addr     string `envconfig:"REDIS_ADDR" default:"localhost:6379"`
    Password string `envconfig:"REDIS_PASSWORD"`
    DB       int    `envconfig:"REDIS_DB" default:"0"`
}

// Load loads configuration from environment
func Load() (*Config, error) {
    var cfg Config
    if err := envconfig.Process("", &cfg); err != nil {
        return nil, err
    }
    return &cfg, nil
}
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `go mod init` | Initialize module |
| `go mod tidy` | Add/remove dependencies |
| `go mod download` | Download dependencies |
| `go get package@version` | Add/update dependency |
| `go build -ldflags "-X ..."` | Set version info |
| `go generate ./...` | Run code generation |
| `GOOS=linux go build` | Cross-compile |
| `go work init` | Initialize workspace |
