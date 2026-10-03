# Analysis Process

## Step 1: Project Structure

```bash
# Find entry points
Glob: **/main.{ts,js,py,go}
Glob: **/app.{ts,js,py}
Glob: **/index.{ts,js}

# Find routes/controllers
Glob: **/routes/**/*.{ts,js}
Glob: **/controllers/**/*.{ts,js}
Grep: @Controller|@Get|@Post|router\.|app\.get
```

## Step 2: Data Models

```bash
# Database schemas
Glob: **/models/**/*.{ts,js,py}
Glob: **/schema*.{ts,js,py,sql}
Glob: **/migrations/**/*
Grep: @Entity|class.*Model|schema\s*=
```

## Step 3: Business Logic

```bash
# Services and logic
Glob: **/services/**/*.{ts,js}
Grep: async.*function|export.*class
```

## Step 4: Authentication & Security

```bash
# Auth patterns
Glob: **/auth/**/*
Glob: **/guards/**/*
Grep: @Guard|middleware|passport|jwt
```

## Step 5: External Integrations

```bash
# External calls
Grep: fetch\(|axios\.|HttpService|request\(
Glob: **/integrations/**/*
Glob: **/clients/**/*
```

## Step 6: Configuration

```bash
# Config files
Glob: **/*.config.{ts,js}
Glob: **/.env*
Glob: **/config/**/*
```

## Quick Reference

| Pattern | Purpose |
|---------|---------|
| `**/main.{ts,js,py}` | Entry points |
| `**/routes/**/*` | API routes |
| `**/models/**/*` | Data models |
| `@Controller\|@Get` | NestJS patterns |
| `router.\|app.get` | Express patterns |
