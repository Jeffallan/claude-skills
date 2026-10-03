# Analysis Checklist

## Comprehensive Checklist

| Area | What to Find | Glob/Grep Patterns |
|------|--------------|-------------------|
| **Entry points** | main.ts, app.ts, index.ts | `**/main.{ts,js,py}` |
| **Routes** | Controllers, route files | `**/routes/**/*`, `@Controller` |
| **Models** | Entities, schemas | `**/models/**/*`, `@Entity` |
| **Auth** | Guards, middleware, JWT | `**/auth/**/*`, `passport` |
| **Validation** | DTOs, validators, pipes | `**/dto/**/*`, `@IsString` |
| **Error handling** | Exception filters, try/catch | `ExceptionFilter`, `catch` |
| **External calls** | HTTP clients, SDK usage | `fetch(`, `axios.` |
| **Config** | Env files, config modules | `**/.env*`, `ConfigService` |
| **Tests** | Test files reveal behaviors | `**/*.spec.ts`, `**/*.test.ts` |
| **Background jobs** | Queues, cron, workers | `@Cron`, `Bull`, `Queue` |

## Analysis Phases

### Phase 1: Structure Discovery
- [ ] Identify technology stack
- [ ] Map directory structure
- [ ] Find entry points
- [ ] List all modules/packages

### Phase 2: API Surface
- [ ] Document all endpoints
- [ ] Note HTTP methods and paths
- [ ] Identify request/response formats
- [ ] Find authentication requirements

### Phase 3: Data Layer
- [ ] Map all data models
- [ ] Document relationships
- [ ] Find migrations
- [ ] Note validation rules

### Phase 4: Business Logic
- [ ] Trace main flows
- [ ] Identify business rules
- [ ] Document state transitions
- [ ] Find external integrations

### Phase 5: Security
- [ ] Check authentication method
- [ ] Review authorization patterns
- [ ] Find input validation
- [ ] Note security configurations

### Phase 6: Quality & Testing
- [ ] Review existing tests
- [ ] Note test coverage
- [ ] Document error handling
- [ ] Find logging patterns

## Verification Questions

Before finalizing specification:

- [ ] All endpoints documented?
- [ ] All models mapped?
- [ ] Authentication flow clear?
- [ ] Error responses documented?
- [ ] External dependencies listed?
- [ ] Uncertainties flagged?
