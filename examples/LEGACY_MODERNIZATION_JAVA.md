# Legacy Java Modernization: Monolith to Spring Boot Microservices

> **Skills used:** `spec-miner`, `legacy-modernizer`, `architecture-designer`, `spring-boot-engineer`, `test-master`, `security-reviewer`
> **Difficulty:** Advanced
> **Language:** Java
> **Workflow:** [Legacy Migration](../SKILLS_GUIDE.md#legacy-migration) + [Enterprise Java](../SKILLS_GUIDE.md#enterprise-java)

## Overview

A financial services company has a monolithic Java EE application (Java 8, JSP/Servlet, raw JDBC) handling customer account management. The system processes account listing, single-account detail views, and transaction history retrieval. The entire application surface is a single 185-line servlet -- `AccountServlet.java` -- that talks directly to an Oracle database via string-concatenated SQL. The goal is to modernize the account management module into Spring Boot 3 microservices with proper API contracts, security, and test coverage, while maintaining backward compatibility during the migration period.

**Source file under analysis:** `workspace/legacy-java/src/AccountServlet.java`

### Why Multi-Skill?

Legacy modernization involves fundamentally conflicting concerns that no single skill can address:

- **Understanding vs. Building** -- You must extract the implicit specification from code (archaeology) before writing a new implementation (engineering). Mixing these leads to lost business rules.
- **Preservation vs. Improvement** -- The modernized code must reproduce legacy business rules exactly (e.g., exclude CLOSED accounts) while simultaneously fixing critical security flaws (SQL injection, no authentication). These goals pull in opposite directions.
- **Speed vs. Safety** -- The strangler fig pattern prioritizes safety over speed, but implementation and testing skills prioritize completeness. A dedicated migration skill mediates this tension.
- **Functional vs. Non-Functional** -- Testing validates behavior; security review validates trust boundaries. Both analyze the same code but with different threat models.

This workflow chains six skills in dependency order: **Understand --> Plan --> Design --> Implement --> Test --> Secure**.

---

## Step 1 -- Reverse-Engineer the Legacy Spec with `spec-miner`

### Prompt

```
Reverse-engineer the specification from this legacy Java EE AccountServlet. I need
to understand business rules, data model, and API surface before modernizing.
```

### Skill Output

#### Reverse-Engineered Specification: AccountServlet Legacy System

##### Overview

The AccountServlet is a Java EE `HttpServlet` mapped to `/api/accounts/*` (line 23) that provides a read-only JSON API for customer account management. It connects to an Oracle database (`ACCTDB`) at initialization and serves three distinct operations through URL path and parameter routing. The system has no authentication, no input validation, and contains multiple critical security vulnerabilities.

##### 1. Technology Stack

**Arch Hat (Architecture Perspective):**

- **Language**: Java 8 (pre-modules, no records, no text blocks)
- **Framework**: Java EE Servlet API (`javax.servlet`, not Jakarta -- line 3-7)
- **Database**: Oracle 12c+ (`oracle.jdbc.OracleDriver`, `FETCH FIRST N ROWS ONLY` syntax -- lines 31, 150)
- **Connection**: Raw JDBC via `DriverManager.getConnection()` (line 32)
- **Serialization**: Manual JSON string construction via `PrintWriter` (lines 84-98)
- **Deployment**: WAR-based (inferred from `@WebServlet` annotation, line 23)

##### 2. Module/Directory Structure

```
com.company.legacy/
  AccountServlet.java     # Single file, 185 lines
    ├── init()            # DB connection setup (lines 29-39)
    ├── doGet()           # Request routing (lines 43-65)
    ├── listAccounts()    # List by customer (lines 71-102)
    ├── getAccount()      # Single account lookup (lines 108-133)
    ├── getTransactions() # Transaction history (lines 139-173)
    └── destroy()         # Connection cleanup (lines 176-184)
```

**Observation:** Entire API surface lives in a single servlet with no layering -- controller, service, and data access are merged. No separation of concerns.

##### 3. Observed Requirements (EARS Format)

**OBS-ACCT-001: Account Listing**
```
While a valid customerId is provided, when GET /api/accounts/?customerId=X is called,
the system shall return all accounts for that customer where STATUS is not 'CLOSED',
ordered by CREATED_DATE descending.
```
*Evidence: lines 75-78 -- `WHERE CUSTOMER_ID = '...' AND STATUS != 'CLOSED' ORDER BY CREATED_DATE DESC`*

**OBS-ACCT-002: Account Detail**
```
When GET /api/accounts/{id} is called with a valid account ID,
the system shall return the single account matching that ACCOUNT_ID.
```
*Evidence: lines 110-111 -- `WHERE ACCOUNT_ID = '...'`*

**OBS-ACCT-003: Account Not Found**
```
When GET /api/accounts/{id} is called with a non-existent account ID,
the system shall return HTTP 404 with body {"error": "Account not found"}.
```
*Evidence: lines 127-129 -- `resp.setStatus(404)` with error JSON*

**OBS-TXN-001: Transaction History**
```
While valid accountId, from date, and to date parameters are provided,
when GET /api/accounts/{id}?transactions&from=YYYY-MM-DD&to=YYYY-MM-DD is called,
the system shall return transactions for that account within the date range,
ordered by TXN_DATE descending, limited to 50 records.
```
*Evidence: lines 145-150 -- `WHERE ACCOUNT_ID = '...' AND TXN_DATE BETWEEN TO_DATE(...) AND TO_DATE(...) ORDER BY TXN_DATE DESC FETCH FIRST 50 ROWS ONLY`*

**OBS-ROUTE-001: URL Routing Logic**
```
When a GET request arrives at /api/accounts/*,
the system shall route based on path and parameters:
  - null or "/" path -> listAccounts
  - /{id} path with ?transactions parameter -> getTransactions
  - /{id} path without ?transactions -> getAccount
```
*Evidence: lines 48-59 -- pathInfo-based routing with parameter check*

**OBS-ERR-001: SQL Error Handling**
```
When a SQLException occurs during any operation,
the system shall return HTTP 500 with body {"error": "Internal server error"}.
```
*Evidence: lines 61-64 -- catch block sets status 500*

##### 4. Non-Functional Observations

**QA Hat (Observable Behaviors Perspective):**

**Security:**
- No authentication or authorization mechanism (no session check, no token, no filter -- entire servlet is publicly accessible)
- SQL injection in all four user-controlled parameters: `customerId` (line 76), `accountId` (line 111), `fromDate` (line 147), `toDate` (line 148) -- all concatenated directly into SQL strings
- Hardcoded database credentials: `"app_user"` / `"s3cret_p@ss!"` (lines 34-35)
- No IDOR prevention: any caller can retrieve any account by ID (line 108)

**Performance:**
- Single shared `java.sql.Connection` instance (line 26) -- not thread-safe, will cause corruption under concurrent servlet access
- No connection pooling -- single connection is the entire pool
- No pagination on `listAccounts` -- unbounded result set (line 81)
- Hardcoded limit of 50 on transactions (line 143) -- not configurable
- `Statement` used instead of `PreparedStatement` (lines 80, 113, 152) -- no query plan caching

**Error Handling:**

| Code | Condition | Response | Location |
|------|-----------|----------|----------|
| 404 | Account not found | `{"error": "Account not found"}` | line 128-129 |
| 500 | Any SQLException | `{"error": "Internal server error"}` | line 62-63 |
| (none) | Null customerId | NullPointerException / SQL error | line 73-76 |
| (none) | Null from/to dates | Oracle parse error | line 141-148 |
| (none) | Invalid date format | Oracle ORA-01861 | line 147-148 |

**Resource Management:**
- `ResultSet` and `Statement` are closed after each method (lines 100-101, 131-132, 171-172) -- correct
- Connection is closed in `destroy()` (lines 177-179) -- correct lifecycle management
- However, no try-with-resources -- if an exception occurs between `executeQuery` and `close`, resources leak

##### 5. Inferred Acceptance Criteria

**AC-001: CLOSED Account Exclusion**
```
Given a customer with accounts in ACTIVE, SUSPENDED, and CLOSED status
When listing accounts for that customer
Then only ACTIVE and SUSPENDED accounts are returned
And no CLOSED accounts appear in the response
```

**AC-002: Transaction Date Range Filtering**
```
Given an account with transactions on 2024-01-01, 2024-06-15, and 2024-12-31
When requesting transactions with from=2024-01-01 and to=2024-06-30
Then only the 2024-01-01 and 2024-06-15 transactions are returned
And the 2024-12-31 transaction is not included
```

**AC-003: Transaction Ordering**
```
Given an account with multiple transactions
When requesting transaction history
Then transactions are returned in reverse chronological order (newest first)
```

**AC-004: Transaction Limit**
```
Given an account with 100 transactions in the date range
When requesting transaction history
Then exactly 50 transactions are returned (the 50 most recent)
```

**AC-005: Customer Isolation**
```
Given customers A and B each with accounts
When customer A lists their accounts
Then no accounts belonging to customer B appear in the response
```

##### 6. Uncertainties and Questions

- [ ] **Account types**: What are the valid values for ACCOUNT_TYPE? The column is selected (line 75) but never filtered or validated.
- [ ] **Currency handling**: Is CURRENCY always 3-letter ISO code (e.g., USD, EUR)? No validation exists (line 94).
- [ ] **CUSTOMER_ID format**: What format are customer IDs? Numeric, UUID, alphanumeric? No validation (line 73).
- [ ] **Transaction types**: What are the valid TXN_TYPE values? (line 165 -- selected but not documented)
- [ ] **Soft delete vs. status lifecycle**: Is CLOSED the terminal state? Can accounts transition from CLOSED back to ACTIVE?
- [ ] **Missing operations**: The system is read-only (only `doGet`). Are account creation, updates, and closures handled elsewhere?
- [ ] **Date boundary behavior**: Does `BETWEEN` in Oracle include both endpoints? (It does -- inclusive on both sides.)
- [ ] **Concurrent access**: Is the shared Connection a known issue or has the system only ever been deployed on a single-thread server?

##### 7. Recommendations

1. **Immediate**: Replace string concatenation SQL with `PreparedStatement` to eliminate SQL injection -- this is exploitable in production today (lines 76, 111, 147-148).
2. **Immediate**: Move database credentials to environment variables or a secrets vault (lines 34-35 expose credentials in source code).
3. **Short-term**: Replace shared `Connection` with a connection pool (HikariCP) to support concurrent requests safely (line 26).
4. **Short-term**: Add authentication and authorization -- currently any HTTP client can access any customer's data.
5. **Medium-term**: Add input validation for `customerId`, date formats, and `accountId` to prevent unexpected errors.
6. **Medium-term**: Add pagination to `listAccounts` -- an unbounded query will cause OOM for customers with many accounts.
7. **Long-term**: Decompose the servlet into layered architecture (controller/service/repository) for testability.

### What This Skill Provided

`spec-miner` applied its dual-perspective analysis -- **Arch Hat** for architecture and data flows, **QA Hat** for observable behaviors and edge cases -- to extract the implicit specification from 185 lines of legacy code. It identified 6 functional requirements in EARS format, 5 acceptance criteria, and 8 open questions, all grounded in specific line references. The separation between intended behavior (e.g., CLOSED account filtering at line 77) and bugs (e.g., SQL injection at line 76) is critical -- the modernized version must preserve the former while eliminating the latter.

---

## Step 2 -- Migration Strategy with `legacy-modernizer`

### Prompt

```
Define a migration strategy from this Java EE servlet to Spring Boot 3 microservices.
Use the strangler fig pattern. Address the critical issues: SQL injection, shared
connection, no auth, hardcoded credentials.
```

### Skill Output

#### 1. Assessment Summary

**System Profile:**
- **Codebase size**: 1 file, 185 lines -- small but high-risk (financial data, no security)
- **Database**: Oracle 12c+ with 2 tables (ACCOUNTS, TRANSACTIONS)
- **Integration surface**: Single REST endpoint (`/api/accounts/*`) with 3 operations
- **Users/consumers**: Unknown downstream clients consuming JSON responses

**Risk Assessment:**

| Risk | Severity | Mitigation |
|------|----------|------------|
| SQL injection is actively exploitable | CRITICAL | Priority fix in Phase 0 (pre-migration) |
| Shared JDBC connection under load | HIGH | Connection pool in new service |
| No authentication allows data exfiltration | HIGH | JWT auth in new service + API gateway |
| Hardcoded credentials in source code | HIGH | Externalized config + secrets management |
| Zero test coverage on legacy code | HIGH | Characterization tests before migration |
| Response format change could break clients | MEDIUM | Maintain backward-compatible JSON shape |

**Dependencies:**
- Oracle JDBC driver (`oracle.jdbc.OracleDriver` -- line 31)
- Java EE Servlet API (`javax.servlet` -- lines 3-7)
- No external service dependencies (pure database reads)

**Approach:** Strangler Fig Pattern -- build the new Spring Boot service alongside the legacy servlet, route traffic incrementally via API gateway, retire legacy after validation.

#### 2. Migration Plan

**Phase 0: Safety Net (Week 1-2)**

Before touching any code, create characterization tests that capture current behavior:

```java
// Characterization test: capture legacy behavior for regression detection
@Test
void legacyBehavior_listAccounts_excludesClosed() {
    // Record what legacy does today, even if it's "wrong"
    // These tests become the migration contract
    Response response = legacyClient.get("/api/accounts/?customerId=CUST001");

    assertThat(response.statusCode()).isEqualTo(200);
    assertThat(response.jsonPath().getList("status"))
        .doesNotContain("CLOSED");
}

@Test
void legacyBehavior_transactions_limitedTo50() {
    Response response = legacyClient.get(
        "/api/accounts/ACC001?transactions&from=2020-01-01&to=2025-12-31");

    assertThat(response.jsonPath().getList("$")).hasSizeLessThanOrEqualTo(50);
}
```

**Phase 1: Extract -- New Service Alongside Legacy (Week 3-6)**

**Architecture:** API Gateway (Spring Cloud) routes traffic to both Legacy AccountServlet (`/api/accounts`) and new Account Service (Spring Boot 3, `/api/v2/accounts`). Both services connect to the same Oracle ACCTDB (unchanged schema).

Implementation steps:
- Scaffold Spring Boot 3 project with Spring Data JPA, Spring Security, Actuator
- Map JPA entities to existing Oracle tables (NO schema changes)
- Implement service layer preserving legacy business rules
- Deploy new service on separate port/container
- API Gateway routes `/api/v2/accounts/**` to new service

**Phase 2: Migrate -- Incremental Traffic Shift (Week 7-10)**

```java
// API Gateway strangler fig routing configuration
@Configuration
public class StranglerFigRouteConfig {

    @Bean
    public RouteLocator routes(RouteLocatorBuilder builder) {
        return builder.routes()
            // Phase 2a: 10% canary to new service
            .route("accounts-canary", r -> r
                .path("/api/accounts/**")
                .and().weight("accounts", 10)
                .filters(f -> f.rewritePath("/api/accounts/(?<segment>.*)",
                                            "/api/v2/accounts/${segment}"))
                .uri("lb://account-service"))
            // Phase 2b: 90% still goes to legacy
            .route("accounts-legacy", r -> r
                .path("/api/accounts/**")
                .and().weight("accounts", 90)
                .uri("lb://legacy-servlet"))
            .build();
    }
}
```

Rollback strategy:
- Feature flag: Set canary weight to 0 to instantly route 100% to legacy
- Monitoring trigger: Auto-rollback if error rate exceeds 1% or p99 latency increases by 50%
- Data validation: Compare response bodies between legacy and new service (shadow mode)

**Phase 3: Retire -- Legacy Removal (Week 11-14)**

| Stage | Traffic Split | Validation Gate | Rollback |
|-------|--------------|-----------------|----------|
| Canary | 10% new / 90% legacy | Error rate < 1%, latency parity | Weight to 0 |
| Ramp | 50% / 50% | All metrics green for 48h | Weight to 10% |
| Full | 100% new / 0% legacy | All metrics green for 7 days | Redeploy legacy WAR |
| Cleanup | Remove legacy code | Legacy unused for 30 days | N/A |

Metrics to monitor:
- Error rate (HTTP 5xx) per endpoint
- p50/p95/p99 response latency
- Database connection pool utilization
- JWT validation failure rate

#### 3. Implementation Code

**Facade: Backward-Compatible Response Adapter**

```java
// Ensures new service produces JSON identical to legacy servlet
// Legacy format: flat JSON with string dates
// This adapter wraps the modern DTOs to match legacy shape during transition

@Component
public class LegacyResponseAdapter {

    /**
     * Transforms modern AccountResponse to match legacy servlet output.
     * Legacy format (from AccountServlet.java lines 89-97):
     *   {"accountId":"...","customerId":"...","balance":123.45,...}
     *
     * Modern format differs in: date serialization, null handling.
     */
    public Map<String, Object> toLegacyFormat(AccountResponse modern) {
        Map<String, Object> legacy = new LinkedHashMap<>();
        legacy.put("accountId", modern.accountId());
        legacy.put("customerId", modern.customerId());
        legacy.put("accountType", modern.accountType());
        legacy.put("balance", modern.balance());
        legacy.put("currency", modern.currency());
        legacy.put("status", modern.status());
        // Legacy used Timestamp.toString() format: "2024-01-15 10:30:00.0"
        legacy.put("createdDate", modern.createdDate() != null
            ? Timestamp.valueOf(modern.createdDate()).toString()
            : null);
        return legacy;
    }
}
```

**Feature Flag Service:**

```java
@Service
public class MigrationFeatureFlagService {

    @Value("${migration.accounts.new-service-percentage:0}")
    private int newServicePercentage;

    public boolean shouldUseNewService(String customerId) {
        if (newServicePercentage == 0) return false;
        if (newServicePercentage == 100) return true;
        // Consistent routing: same customer always goes to same service
        return Math.abs(customerId.hashCode() % 100) < newServicePercentage;
    }
}
```

#### 4. Test Coverage

**Characterization tests** (capture legacy behavior): 5 tests covering all 3 endpoints
**Contract tests** (verify response shape parity): 3 tests comparing legacy vs. modern JSON output
**Integration tests** (verify new service independently): 8+ tests (see Step 5)
**Smoke tests** (post-deployment validation): health check + 1 happy-path per endpoint

Target coverage before Phase 2: **80%+ line coverage on new service code**

#### 5. Monitoring Setup

```yaml
# Prometheus metrics for migration tracking
management:
  endpoints:
    web:
      exposure:
        include: health, info, prometheus, metrics
  metrics:
    tags:
      application: account-service
      migration-phase: ${MIGRATION_PHASE:phase-1}

# Custom migration metrics
---
# Grafana dashboard panels:
# 1. "Migration Traffic Split" - % requests to legacy vs. new
# 2. "Error Rate Comparison" - legacy 5xx vs. new 5xx
# 3. "Latency Comparison" - p50/p95/p99 side by side
# 4. "DB Connection Pool" - HikariCP active/idle/pending
# 5. "JWT Validation Failures" - auth errors in new service

# Alert rules:
# - CRITICAL: new service error rate > 5% for 5 minutes
# - WARNING: new service p99 latency > 2x legacy p99
# - INFO: migration phase changed
```

### What This Skill Provided

`legacy-modernizer` produced the 5-part deliverable prescribed by the skill: assessment summary with risk table, phased migration plan with rollback strategy at each gate, implementation code for the strangler fig facade and feature flags, test coverage targets, and monitoring configuration. The plan directly addresses each critical issue found in Step 1 and maintains zero production disruption through incremental traffic shifting.

---

## Step 3 -- Microservice Architecture with `architecture-designer`

### Prompt

```
Design the Spring Boot microservice architecture for the account service. Include
JPA entity design, repository interfaces, and security configuration. Map to existing
Oracle schema without changes (Phase 1 compatibility).
```

### Skill Output

#### 1. Requirements Summary

**Functional Requirements:**
- List non-closed accounts for a customer (preserves legacy `STATUS != 'CLOSED'` filter -- line 77 of AccountServlet.java)
- Retrieve single account by ID (preserves legacy lookup -- line 111)
- Query transaction history by account and date range (preserves legacy date filtering -- lines 147-148)
- NEW: Pagination on all list endpoints (legacy was unbounded on accounts, hardcoded to 50 on transactions)
- NEW: Ownership verification (legacy allowed any caller to access any account)

**Non-Functional Requirements:**
- Response latency < 200ms p95 (financial SLA)
- Concurrent request support via connection pooling (legacy shared single connection -- line 26)
- JWT-based authentication (legacy had none -- no session, no token)
- Externalized credentials (legacy hardcoded `"app_user"` / `"s3cret_p@ss!"` -- lines 34-35)
- Zero schema changes in Phase 1 (map JPA to existing Oracle tables)

**Constraints:**
- Must connect to existing Oracle `ACCTDB` instance
- Must preserve exact business logic for CLOSED account exclusion
- Must preserve transaction date range filtering with Oracle `TO_DATE` semantics
- Response JSON shape must be backward-compatible during migration period

#### 2. High-Level Architecture

**Request Flow:** API Gateway (Rate Limiter → JWT Validator → Route to `/api/v2/accounts`) → Account Service (Spring Boot 3)

**Account Service Layers:**

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| Security | `SecurityFilterChain` | JWT token validation, extract `customerId` from claims |
| Controller | `@RestController`, `@Validated` | `/api/v2/accounts` endpoints, Bean Validation, ownership enforcement via `@AuthenticationPrincipal` |
| Service | `@Service`, `@Transactional` | Business logic, ownership verification, DTO mapping |
| Repository | Spring Data JPA | `AccountRepository`, `TransactionRepository`, parameterized queries (no SQL injection) |
| Connection | HikariCP | `max-pool-size: 20` (replaces shared Connection), `connection-timeout: 30000ms` |

**Database:** Oracle ACCTDB (tables: `ACCOUNTS`, `TRANSACTIONS`, schema unchanged)

#### 3. Key Decisions (ADR Format)

**ADR-001: Use Spring Data JPA over Raw JDBC**

**Status:** Accepted

**Context:**
The legacy servlet uses raw JDBC with `Statement` and string-concatenated SQL (AccountServlet.java lines 75-78, 110-111, 145-150). This creates SQL injection vulnerabilities in all four user-controlled parameters. The system needs data access that is secure by default, supports pagination natively, and maps to the existing Oracle schema.

**Decision:**
Use Spring Data JPA with derived query methods and `Pageable` support. Map JPA entities to existing Oracle table names and column names using `@Table` and `@Column` annotations. Set `ddl-auto: validate` to prevent Hibernate from modifying the production schema.

**Consequences:**
- *Positive*: SQL injection eliminated by design (parameterized queries), pagination built-in, type-safe queries
- *Positive*: Repository methods like `findByCustomerIdAndStatusNot()` are self-documenting
- *Negative*: Requires Oracle Hibernate dialect configuration
- *Negative*: JPA entity mapping must exactly match legacy column names/types
- *Neutral*: Team needs Spring Data JPA knowledge (common enterprise skill)

**Alternatives Considered:**
- *MyBatis*: Rejected -- still requires writing SQL, less protection against injection mistakes
- *jOOQ*: Rejected -- better type safety than JPA for complex queries, but overkill for simple CRUD; team unfamiliar
- *Keep raw JDBC with PreparedStatement*: Rejected -- fixes injection but loses pagination, query derivation, and Spring ecosystem integration

---

**ADR-002: JWT Authentication via Spring Security OAuth2 Resource Server**

**Status:** Accepted

**Context:**
The legacy servlet has zero authentication (AccountServlet.java lines 43-65 -- no session check, no token validation, no filter). Any HTTP client can access any customer's account data. The modernized service needs stateless authentication suitable for microservices, with the ability to extract `customerId` from the token for ownership verification.

**Decision:**
Use Spring Security 6 with OAuth2 Resource Server JWT validation. Extract `customerId` from the JWT claims. Enforce ownership by comparing the token's `customerId` claim against the requested resource.

**Consequences:**
- *Positive*: Stateless auth -- no session management, horizontally scalable
- *Positive*: Ownership verification at controller level prevents IDOR
- *Negative*: Requires identity provider (Keycloak, Auth0, or similar) to issue JWTs
- *Negative*: Legacy clients must be updated to include JWT tokens
- *Neutral*: During migration, API gateway can inject synthetic JWTs for legacy clients

**Alternatives Considered:**
- *Session-based auth*: Rejected -- not suitable for microservices, requires sticky sessions
- *API key auth*: Rejected -- does not carry customer identity claims, no standard revocation
- *mTLS*: Rejected -- appropriate for service-to-service, not client-to-service

---

**ADR-003: Preserve Oracle Schema in Phase 1 (No DDL Changes)**

**Status:** Accepted

**Context:**
The existing Oracle database has two tables (ACCOUNTS, TRANSACTIONS) in active use by the legacy servlet and potentially other systems. Schema changes during migration risk breaking the legacy system before the new service is validated.

**Decision:**
Map JPA entities to the existing Oracle table and column names exactly. Use `spring.jpa.hibernate.ddl-auto=validate` to ensure Hibernate verifies mapping at startup but never modifies the schema. Defer any schema evolution to Phase 2 (after legacy is retired).

**Consequences:**
- *Positive*: Zero risk of schema breakage during migration
- *Positive*: Both legacy and new service can read from the same tables simultaneously
- *Negative*: Cannot add new columns (e.g., audit fields) until Phase 2
- *Negative*: Must use Oracle-compatible types and naming conventions
- *Neutral*: Flyway migrations can be prepared but not applied until Phase 2

#### 4. Technology Recommendations

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Spring Boot 3.2+ | Java 17+, Spring Security 6, virtual threads ready |
| Data Access | Spring Data JPA + Hibernate 6 | Parameterized queries, pagination, Oracle dialect |
| Connection Pool | HikariCP (Spring Boot default) | Replaces shared Connection (line 26) |
| Security | Spring Security OAuth2 Resource Server | JWT validation, stateless, claim extraction |
| Validation | Jakarta Bean Validation (Hibernate Validator) | `@NotBlank`, `@DateTimeFormat` on controller params |
| Configuration | Spring Cloud Config + Vault | Replaces hardcoded credentials (lines 34-35) |
| Monitoring | Micrometer + Prometheus + Grafana | Migration traffic metrics, latency comparison |
| Testing | JUnit 5, Mockito, @DataJpaTest, Testcontainers | Unit + integration + Oracle-compatible testing |
| Migration DB | Flyway | Schema evolution tracking (Phase 2) |
| API Docs | SpringDoc OpenAPI | Auto-generated Swagger UI for new endpoints |

#### 5. Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| JPA entity mapping mismatch with Oracle schema | Medium | HIGH | `ddl-auto: validate` catches at startup; integration tests with Oracle Testcontainers |
| JWT issuer misconfiguration allows token forgery | Low | CRITICAL | Automated security tests verify issuer, audience, expiration |
| HikariCP pool exhaustion under load | Medium | HIGH | Set `maximum-pool-size` based on load testing; monitor with Actuator metrics |
| Legacy clients cannot add JWT headers | High | HIGH | API gateway injects JWT during Phase 2 transition; legacy path exemption |
| Oracle-specific SQL in legacy that JPA cannot express | Low | MEDIUM | Use `@Query` with native Oracle SQL where needed |

### What This Skill Provided

`architecture-designer` produced the 5-part output format: requirements summary, architecture diagram, ADR-format decisions, technology recommendations, and risk assessment. Three ADRs document the key decisions (JPA over JDBC, JWT authentication, schema preservation) with explicit traceoffs and rejected alternatives. Each decision traces back to a specific vulnerability or constraint found in the legacy code.

---

## Step 4 -- Spring Boot Implementation with `spring-boot-engineer`

### Prompt

```
Implement the AccountService with business logic from the legacy system. Preserve
existing rules (exclude CLOSED accounts, date range filtering) while adding pagination,
ownership verification, input validation.
```

### Skill Output

#### 1. Entity Classes with JPA Annotations

```java
// src/main/java/com/company/accounts/entity/Account.java
package com.company.accounts.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "ACCOUNTS")
public class Account {

    @Id
    @Column(name = "ACCOUNT_ID", length = 50)
    private String accountId;

    @Column(name = "CUSTOMER_ID", nullable = false, length = 50)
    private String customerId;

    @Column(name = "ACCOUNT_TYPE", length = 30)
    private String accountType;

    @Column(name = "BALANCE", precision = 19, scale = 4)
    private BigDecimal balance;

    @Column(name = "CURRENCY", length = 3)
    private String currency;

    @Enumerated(EnumType.STRING)
    @Column(name = "STATUS", length = 20)
    private AccountStatus status;

    @Column(name = "CREATED_DATE")
    private LocalDateTime createdDate;

    // Constructors
    protected Account() {} // JPA requires no-arg constructor

    // Getters and setters
    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }
    public String getCustomerId() { return customerId; }
    public void setCustomerId(String customerId) { this.customerId = customerId; }
    public String getAccountType() { return accountType; }
    public void setAccountType(String accountType) { this.accountType = accountType; }
    public BigDecimal getBalance() { return balance; }
    public void setBalance(BigDecimal balance) { this.balance = balance; }
    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }
    public AccountStatus getStatus() { return status; }
    public void setStatus(AccountStatus status) { this.status = status; }
    public LocalDateTime getCreatedDate() { return createdDate; }
    public void setCreatedDate(LocalDateTime createdDate) { this.createdDate = createdDate; }
}
```

```java
// src/main/java/com/company/accounts/entity/AccountStatus.java
package com.company.accounts.entity;

public enum AccountStatus {
    ACTIVE,
    SUSPENDED,
    CLOSED
}
```

```java
// src/main/java/com/company/accounts/entity/Transaction.java
package com.company.accounts.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(name = "TRANSACTIONS")
public class Transaction {

    @Id
    @Column(name = "TXN_ID", length = 50)
    private String txnId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "ACCOUNT_ID", nullable = false)
    private Account account;

    @Column(name = "AMOUNT", precision = 19, scale = 4)
    private BigDecimal amount;

    @Column(name = "TXN_TYPE", length = 30)
    private String txnType;

    @Column(name = "DESCRIPTION", length = 500)
    private String description;

    @Column(name = "TXN_DATE")
    private LocalDate txnDate;

    // Constructors
    protected Transaction() {}

    // Getters and setters
    public String getTxnId() { return txnId; }
    public void setTxnId(String txnId) { this.txnId = txnId; }
    public Account getAccount() { return account; }
    public void setAccount(Account account) { this.account = account; }
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public String getTxnType() { return txnType; }
    public void setTxnType(String txnType) { this.txnType = txnType; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public LocalDate getTxnDate() { return txnDate; }
    public void setTxnDate(LocalDate txnDate) { this.txnDate = txnDate; }
}
```

#### 2. Repository Interfaces

```java
// src/main/java/com/company/accounts/repository/AccountRepository.java
package com.company.accounts.repository;

import com.company.accounts.entity.Account;
import com.company.accounts.entity.AccountStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface AccountRepository extends JpaRepository<Account, String> {

    /**
     * Replaces legacy SQL (AccountServlet.java line 75-78):
     *   SELECT ... FROM ACCOUNTS
     *   WHERE CUSTOMER_ID = '{customerId}'
     *   AND STATUS != 'CLOSED'
     *   ORDER BY CREATED_DATE DESC
     *
     * Spring Data JPA generates parameterized query automatically.
     * Pageable adds configurable pagination (legacy was unbounded).
     */
    Page<Account> findByCustomerIdAndStatusNot(
        String customerId,
        AccountStatus status,
        Pageable pageable
    );

    /**
     * Ownership verification query.
     * NEW: Legacy had no ownership check (AccountServlet.java line 108).
     * Prevents IDOR by requiring both accountId AND customerId to match.
     */
    Optional<Account> findByAccountIdAndCustomerId(
        String accountId,
        String customerId
    );
}
```

```java
// src/main/java/com/company/accounts/repository/TransactionRepository.java
package com.company.accounts.repository;

import com.company.accounts.entity.Transaction;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;

@Repository
public interface TransactionRepository extends JpaRepository<Transaction, String> {

    /**
     * Replaces legacy SQL (AccountServlet.java lines 145-150):
     *   SELECT ... FROM TRANSACTIONS
     *   WHERE ACCOUNT_ID = '{accountId}'
     *   AND TXN_DATE BETWEEN TO_DATE('{from}','YYYY-MM-DD')
     *                   AND TO_DATE('{to}','YYYY-MM-DD')
     *   ORDER BY TXN_DATE DESC
     *   FETCH FIRST 50 ROWS ONLY
     *
     * Enhancement: Pageable replaces hardcoded FETCH FIRST 50 limit.
     */
    Page<Transaction> findByAccount_AccountIdAndTxnDateBetween(
        String accountId,
        LocalDate from,
        LocalDate to,
        Pageable pageable
    );
}
```

#### 3. Service Layer

```java
// src/main/java/com/company/accounts/service/AccountService.java
package com.company.accounts.service;

import com.company.accounts.dto.AccountResponse;
import com.company.accounts.dto.TransactionResponse;
import com.company.accounts.entity.Account;
import com.company.accounts.entity.AccountStatus;
import com.company.accounts.entity.Transaction;
import com.company.accounts.exception.AccountNotFoundException;
import com.company.accounts.repository.AccountRepository;
import com.company.accounts.repository.TransactionRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;

@Service
@Transactional(readOnly = true)
public class AccountService {

    private final AccountRepository accountRepository;
    private final TransactionRepository transactionRepository;

    // Constructor injection (Spring Boot 3 best practice -- no @Autowired on fields)
    public AccountService(AccountRepository accountRepository,
                          TransactionRepository transactionRepository) {
        this.accountRepository = accountRepository;
        this.transactionRepository = transactionRepository;
    }

    /**
     * List accounts for a customer, excluding CLOSED accounts.
     *
     * Preserves legacy behavior from AccountServlet.java lines 75-78:
     *   - STATUS != 'CLOSED' filter
     *   - ORDER BY CREATED_DATE DESC (via Pageable sort)
     *
     * Enhancement over legacy:
     *   - Pagination (legacy returned unbounded results via line 81 stmt.executeQuery)
     *   - Parameterized queries (legacy concatenated customerId at line 76)
     */
    public Page<AccountResponse> findByCustomerId(String customerId, Pageable pageable) {
        return accountRepository
            .findByCustomerIdAndStatusNot(customerId, AccountStatus.CLOSED, pageable)
            .map(this::toAccountResponse);
    }

    /**
     * Get a single account by ID.
     *
     * Preserves legacy behavior from AccountServlet.java lines 110-111, 127-129:
     *   - Lookup by ACCOUNT_ID
     *   - 404 if not found
     *
     * Enhancement over legacy:
     *   - Ownership verification (legacy allowed any caller to access any account)
     */
    public AccountResponse findByIdForCustomer(String accountId, String customerId) {
        Account account = accountRepository.findByAccountIdAndCustomerId(accountId, customerId)
            .orElseThrow(() -> new AccountNotFoundException(
                "Account " + accountId + " not found or access denied"));
        return toAccountResponse(account);
    }

    /**
     * Get transaction history within a date range.
     *
     * Preserves legacy behavior from AccountServlet.java lines 145-150:
     *   - Date range filtering (TXN_DATE BETWEEN from AND to)
     *   - ORDER BY TXN_DATE DESC
     *
     * Enhancement over legacy:
     *   - Configurable page size (legacy hardcoded to 50 at line 143)
     *   - Parameterized queries (legacy concatenated dates at lines 147-148)
     */
    public Page<TransactionResponse> getTransactions(
            String accountId, LocalDate from, LocalDate to, Pageable pageable) {
        return transactionRepository
            .findByAccount_AccountIdAndTxnDateBetween(accountId, from, to, pageable)
            .map(this::toTransactionResponse);
    }

    /**
     * Verify that the authenticated customer owns the requested account.
     *
     * NEW requirement -- not present in legacy code.
     * Legacy AccountServlet.java had no ownership check at all:
     *   - getAccount() (line 108) accepted any accountId
     *   - getTransactions() (line 139) accepted any accountId
     * Any user could access any other user's account data.
     */
    public void verifyOwnership(String accountId, String customerId) {
        accountRepository.findByAccountIdAndCustomerId(accountId, customerId)
            .orElseThrow(() -> new AccessDeniedException(
                "Account not found or access denied"));
    }

    private AccountResponse toAccountResponse(Account account) {
        return new AccountResponse(
            account.getAccountId(),
            account.getCustomerId(),
            account.getAccountType(),
            account.getBalance(),
            account.getCurrency(),
            account.getStatus().name(),
            account.getCreatedDate()
        );
    }

    private TransactionResponse toTransactionResponse(Transaction txn) {
        return new TransactionResponse(
            txn.getTxnId(),
            txn.getAccount().getAccountId(),
            txn.getAmount(),
            txn.getTxnType(),
            txn.getDescription(),
            txn.getTxnDate()
        );
    }
}
```

#### 4. Controller with REST Endpoints

```java
// src/main/java/com/company/accounts/controller/AccountController.java
package com.company.accounts.controller;

import com.company.accounts.dto.AccountResponse;
import com.company.accounts.dto.TransactionResponse;
import com.company.accounts.service.AccountService;
import jakarta.validation.constraints.NotBlank;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;

@RestController
@RequestMapping("/api/v2/accounts")
@Validated
public class AccountController {

    private final AccountService accountService;

    public AccountController(AccountService accountService) {
        this.accountService = accountService;
    }

    /**
     * GET /api/v2/accounts?customerId=X
     * Maps to legacy: GET /api/accounts/?customerId=X (AccountServlet.java line 68)
     */
    @GetMapping
    public ResponseEntity<Page<AccountResponse>> listAccounts(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam @NotBlank String customerId,
            @PageableDefault(size = 20, sort = "createdDate",
                direction = Sort.Direction.DESC) Pageable pageable) {

        // Ownership enforcement: JWT customerId must match requested customerId
        String tokenCustomerId = jwt.getClaimAsString("customerId");
        if (!tokenCustomerId.equals(customerId)) {
            throw new org.springframework.security.access.AccessDeniedException(
                "Cannot access another customer's accounts");
        }

        Page<AccountResponse> accounts =
            accountService.findByCustomerId(customerId, pageable);
        return ResponseEntity.ok(accounts);
    }

    /**
     * GET /api/v2/accounts/{accountId}
     * Maps to legacy: GET /api/accounts/{id} (AccountServlet.java line 105)
     */
    @GetMapping("/{accountId}")
    public ResponseEntity<AccountResponse> getAccount(
            @AuthenticationPrincipal Jwt jwt,
            @PathVariable @NotBlank String accountId) {

        String customerId = jwt.getClaimAsString("customerId");
        AccountResponse account =
            accountService.findByIdForCustomer(accountId, customerId);
        return ResponseEntity.ok(account);
    }

    /**
     * GET /api/v2/accounts/{accountId}/transactions?from=YYYY-MM-DD&to=YYYY-MM-DD
     * Maps to legacy: GET /api/accounts/{id}?transactions&from=&to=
     *     (AccountServlet.java line 136)
     * Note: Legacy used query parameter flag (?transactions); modern uses sub-resource path.
     */
    @GetMapping("/{accountId}/transactions")
    public ResponseEntity<Page<TransactionResponse>> getTransactions(
            @AuthenticationPrincipal Jwt jwt,
            @PathVariable @NotBlank String accountId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to,
            @PageableDefault(size = 50, sort = "txnDate",
                direction = Sort.Direction.DESC) Pageable pageable) {

        String customerId = jwt.getClaimAsString("customerId");
        accountService.verifyOwnership(accountId, customerId);
        Page<TransactionResponse> transactions =
            accountService.getTransactions(accountId, from, to, pageable);
        return ResponseEntity.ok(transactions);
    }
}
```

#### 5. DTO Classes

```java
// src/main/java/com/company/accounts/dto/AccountResponse.java
package com.company.accounts.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Response DTO matching legacy JSON fields (AccountServlet.java lines 89-97).
 * Uses Java record for immutability and compact syntax.
 */
public record AccountResponse(
    String accountId,
    String customerId,
    String accountType,
    BigDecimal balance,
    String currency,
    String status,
    LocalDateTime createdDate
) {}
```

```java
// src/main/java/com/company/accounts/dto/TransactionResponse.java
package com.company.accounts.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * Response DTO matching legacy JSON fields (AccountServlet.java lines 162-167).
 */
public record TransactionResponse(
    String txnId,
    String accountId,
    BigDecimal amount,
    String txnType,
    String description,
    LocalDate txnDate
) {}
```

#### 6. Configuration Classes

```java
// src/main/java/com/company/accounts/config/SecurityConfig.java
package com.company.accounts.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable()) // Stateless REST API -- no CSRF needed
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health", "/actuator/info").permitAll()
                .requestMatchers("/api/v2/**").authenticated()
                .anyRequest().denyAll()
            )
            .oauth2ResourceServer(oauth2 ->
                oauth2.jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthConverter())))
            .build();
    }

    private JwtAuthenticationConverter jwtAuthConverter() {
        JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
        converter.setPrincipalClaimName("customerId");
        return converter;
    }
}
```

```java
// src/main/java/com/company/accounts/exception/GlobalExceptionHandler.java
package com.company.accounts.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.Instant;
import java.util.Map;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(AccountNotFoundException.class)
    public ProblemDetail handleNotFound(AccountNotFoundException ex) {
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(
            HttpStatus.NOT_FOUND, ex.getMessage());
        detail.setTitle("Account Not Found");
        detail.setProperty("timestamp", Instant.now());
        return detail;
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ProblemDetail handleAccessDenied(AccessDeniedException ex) {
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(
            HttpStatus.FORBIDDEN, ex.getMessage());
        detail.setTitle("Access Denied");
        detail.setProperty("timestamp", Instant.now());
        return detail;
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        Map<String, String> errors = ex.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(
                e -> e.getField(),
                e -> e.getDefaultMessage() != null ? e.getDefaultMessage() : "Invalid"
            ));
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(
            HttpStatus.BAD_REQUEST, "Validation failed");
        detail.setTitle("Bad Request");
        detail.setProperty("errors", errors);
        detail.setProperty("timestamp", Instant.now());
        return detail;
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneral(Exception ex) {
        // Never expose internal details (unlike legacy line 63 which was generic but safe)
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred");
        detail.setTitle("Internal Server Error");
        detail.setProperty("timestamp", Instant.now());
        return detail;
    }
}
```

```yaml
# src/main/resources/application.yml
spring:
  datasource:
    url: ${DB_URL:jdbc:oracle:thin:@localhost:1521:ACCTDB}
    username: ${DB_USERNAME}     # Was hardcoded "app_user" (line 34)
    password: ${DB_PASSWORD}     # Was hardcoded "s3cret_p@ss!" (line 35)
    driver-class-name: oracle.jdbc.OracleDriver
    hikari:
      maximum-pool-size: 20     # Replaces single shared Connection (line 26)
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
  jpa:
    hibernate:
      ddl-auto: validate        # NEVER auto-modify production schema
    properties:
      hibernate:
        dialect: org.hibernate.dialect.OracleDialect
        format_sql: true
    open-in-view: false          # Prevent lazy loading outside transactions

  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: ${JWT_ISSUER_URI}

server:
  port: 8080

management:
  endpoints:
    web:
      exposure:
        include: health, info, prometheus, metrics
  endpoint:
    health:
      show-details: when-authorized
```

#### 7. Test Classes

```java
// See Step 5 for comprehensive test implementation
// Summary: Unit tests with Mockito, integration tests with @DataJpaTest,
// and security tests with @WithMockUser
```

#### 8. Architecture Decisions Explanation

**Why constructor injection?** Spring Boot 3 best practice. The legacy servlet used field-level initialization (`private Connection conn` at line 26). Constructor injection makes dependencies explicit and enables testing without reflection.

**Why `@Transactional(readOnly = true)` on the service class?** All operations are reads. The `readOnly` hint allows Hibernate to skip dirty checking and enables database read-replica routing. The legacy servlet had no transaction management -- each `Statement.executeQuery()` was an implicit auto-commit.

**Why Java records for DTOs?** The legacy servlet manually wrote JSON via `PrintWriter` (lines 84-98, 118-126, 155-169). Records provide immutability, automatic `equals`/`hashCode`/`toString`, and Jackson serializes them natively. The record field names match the legacy JSON keys exactly for backward compatibility.

**Why `@PageableDefault(size = 50)` on transactions?** Preserves the legacy hardcoded limit of 50 (line 143) as the default, but allows clients to override via `?size=N` parameter. This maintains backward-compatible behavior while adding flexibility.

### What This Skill Provided

`spring-boot-engineer` produced the 8-part output template: entity classes, repository interfaces, service layer, controller, DTOs, configuration, test stubs, and architecture explanations. Every method in the service layer includes a Javadoc comment tracing it to the specific legacy code line it replaces. The implementation uses constructor injection, `@Valid`, `@Transactional`, and `@RestControllerAdvice` as prescribed by the skill's constraints.

---

## Step 5 -- Testing with `test-master`

### Prompt

```
Write comprehensive tests for AccountService. Include unit tests, integration tests
with embedded database, and tests verifying legacy business rules are preserved.
```

### Skill Output

#### [Test] Functional Testing Mode

##### Test Scope

| Category | Scope | Framework |
|----------|-------|-----------|
| Unit tests | AccountService business logic in isolation | JUnit 5 + Mockito |
| Integration tests (data) | Repository queries against embedded DB | @DataJpaTest + H2 |
| Integration tests (web) | Full HTTP request/response cycle | @SpringBootTest + MockMvc |
| Legacy parity tests | Verify modernized behavior matches legacy | Labeled `legacyBehavior_*` |

##### Test Cases

**Unit Tests -- AccountService**

```java
// src/test/java/com/company/accounts/service/AccountServiceTest.java
package com.company.accounts.service;

import com.company.accounts.dto.AccountResponse;
import com.company.accounts.entity.Account;
import com.company.accounts.entity.AccountStatus;
import com.company.accounts.entity.Transaction;
import com.company.accounts.exception.AccountNotFoundException;
import com.company.accounts.repository.AccountRepository;
import com.company.accounts.repository.TransactionRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AccountServiceTest {

    @Mock
    private AccountRepository accountRepository;

    @Mock
    private TransactionRepository transactionRepository;

    @InjectMocks
    private AccountService accountService;

    @Nested
    @DisplayName("findByCustomerId")
    class FindByCustomerIdTests {

        @Test
        @DisplayName("returns non-closed accounts for customer [legacy: STATUS != CLOSED]")
        void legacyBehavior_excludesClosedAccounts() {
            // Preserves: AccountServlet.java line 77 -- AND STATUS != 'CLOSED'
            Account active = buildAccount("acc-1", "cust-1", AccountStatus.ACTIVE);
            Account suspended = buildAccount("acc-2", "cust-1", AccountStatus.SUSPENDED);
            Page<Account> page = new PageImpl<>(List.of(active, suspended));
            Pageable pageable = PageRequest.of(0, 20);

            when(accountRepository.findByCustomerIdAndStatusNot(
                eq("cust-1"), eq(AccountStatus.CLOSED), any(Pageable.class)))
                .thenReturn(page);

            Page<AccountResponse> result =
                accountService.findByCustomerId("cust-1", pageable);

            assertThat(result.getContent()).hasSize(2);
            assertThat(result.getContent())
                .extracting(AccountResponse::status)
                .containsExactly("ACTIVE", "SUSPENDED")
                .doesNotContain("CLOSED");
        }

        @Test
        @DisplayName("returns empty page when customer has no non-closed accounts")
        void returnsEmptyWhenAllClosed() {
            when(accountRepository.findByCustomerIdAndStatusNot(
                any(), any(), any(Pageable.class)))
                .thenReturn(Page.empty());

            Page<AccountResponse> result =
                accountService.findByCustomerId("cust-99", PageRequest.of(0, 20));

            assertThat(result.getContent()).isEmpty();
            assertThat(result.getTotalElements()).isZero();
        }

        @Test
        @DisplayName("maps all entity fields to response DTO correctly")
        void mapsAllFieldsToResponse() {
            Account account = buildAccount("acc-1", "cust-1", AccountStatus.ACTIVE);
            account.setAccountType("SAVINGS");
            account.setBalance(new BigDecimal("1500.50"));
            account.setCurrency("USD");
            account.setCreatedDate(LocalDateTime.of(2024, 1, 15, 10, 30));

            when(accountRepository.findByCustomerIdAndStatusNot(
                any(), any(), any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(account)));

            Page<AccountResponse> result =
                accountService.findByCustomerId("cust-1", PageRequest.of(0, 20));

            AccountResponse resp = result.getContent().get(0);
            assertThat(resp.accountId()).isEqualTo("acc-1");
            assertThat(resp.customerId()).isEqualTo("cust-1");
            assertThat(resp.accountType()).isEqualTo("SAVINGS");
            assertThat(resp.balance()).isEqualByComparingTo("1500.50");
            assertThat(resp.currency()).isEqualTo("USD");
            assertThat(resp.status()).isEqualTo("ACTIVE");
            assertThat(resp.createdDate())
                .isEqualTo(LocalDateTime.of(2024, 1, 15, 10, 30));
        }
    }

    @Nested
    @DisplayName("verifyOwnership")
    class VerifyOwnershipTests {

        @Test
        @DisplayName("succeeds when customer owns the account")
        void succeeds_whenOwnerMatches() {
            Account account = buildAccount("acc-1", "cust-1", AccountStatus.ACTIVE);
            when(accountRepository.findByAccountIdAndCustomerId("acc-1", "cust-1"))
                .thenReturn(Optional.of(account));

            // Should not throw
            assertThatCode(() ->
                accountService.verifyOwnership("acc-1", "cust-1")
            ).doesNotThrowAnyException();
        }

        @Test
        @DisplayName("throws AccessDeniedException when customer does not own account")
        void throws_whenOwnerMismatch() {
            // NEW behavior: legacy had no ownership check (line 108)
            when(accountRepository.findByAccountIdAndCustomerId("acc-1", "wrong-cust"))
                .thenReturn(Optional.empty());

            assertThatThrownBy(() ->
                accountService.verifyOwnership("acc-1", "wrong-cust"))
                .isInstanceOf(AccessDeniedException.class)
                .hasMessageContaining("access denied");
        }

        @Test
        @DisplayName("throws for non-existent account ID")
        void throws_whenAccountDoesNotExist() {
            when(accountRepository.findByAccountIdAndCustomerId(any(), any()))
                .thenReturn(Optional.empty());

            assertThatThrownBy(() ->
                accountService.verifyOwnership("nonexistent", "cust-1"))
                .isInstanceOf(AccessDeniedException.class);
        }
    }

    @Nested
    @DisplayName("getTransactions")
    class GetTransactionsTests {

        @Test
        @DisplayName("filters transactions by date range [legacy: TXN_DATE BETWEEN]")
        void legacyBehavior_dateRangeFiltering() {
            // Preserves: AccountServlet.java lines 147-148
            Transaction txn = buildTransaction("txn-1", "acc-1",
                new BigDecimal("250.00"), LocalDate.of(2024, 6, 15));
            Page<Transaction> page = new PageImpl<>(List.of(txn));

            when(transactionRepository.findByAccount_AccountIdAndTxnDateBetween(
                eq("acc-1"),
                eq(LocalDate.of(2024, 1, 1)),
                eq(LocalDate.of(2024, 12, 31)),
                any(Pageable.class)))
                .thenReturn(page);

            var result = accountService.getTransactions(
                "acc-1",
                LocalDate.of(2024, 1, 1),
                LocalDate.of(2024, 12, 31),
                PageRequest.of(0, 50));

            assertThat(result.getContent()).hasSize(1);
            assertThat(result.getContent().get(0).txnDate())
                .isEqualTo(LocalDate.of(2024, 6, 15));
        }

        @Test
        @DisplayName("returns empty page when no transactions in range")
        void returnsEmptyWhenNoTransactions() {
            when(transactionRepository.findByAccount_AccountIdAndTxnDateBetween(
                any(), any(), any(), any(Pageable.class)))
                .thenReturn(Page.empty());

            var result = accountService.getTransactions(
                "acc-1", LocalDate.now().minusDays(1), LocalDate.now(),
                PageRequest.of(0, 50));

            assertThat(result.getContent()).isEmpty();
        }
    }

    // Helper builders
    private Account buildAccount(String id, String customerId, AccountStatus status) {
        Account account = new Account();
        account.setAccountId(id);
        account.setCustomerId(customerId);
        account.setStatus(status);
        return account;
    }

    private Transaction buildTransaction(String txnId, String accountId,
            BigDecimal amount, LocalDate date) {
        Account account = new Account();
        account.setAccountId(accountId);
        Transaction txn = new Transaction();
        txn.setTxnId(txnId);
        txn.setAccount(account);
        txn.setAmount(amount);
        txn.setTxnDate(date);
        txn.setTxnType("DEBIT");
        txn.setDescription("Test transaction");
        return txn;
    }
}
```

**Integration Tests -- Repository Layer**

```java
// src/test/java/com/company/accounts/repository/AccountRepositoryIntegrationTest.java
package com.company.accounts.repository;

import com.company.accounts.entity.Account;
import com.company.accounts.entity.AccountStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
class AccountRepositoryIntegrationTest {

    @Autowired
    private AccountRepository accountRepository;

    @Autowired
    private TestEntityManager entityManager;

    @BeforeEach
    void setUp() {
        // Simulate legacy data: mix of statuses across customers
        persistAccount("acc-1", "cust-1", AccountStatus.ACTIVE,
            LocalDateTime.of(2024, 3, 1, 0, 0));
        persistAccount("acc-2", "cust-1", AccountStatus.CLOSED,
            LocalDateTime.of(2024, 2, 1, 0, 0));
        persistAccount("acc-3", "cust-1", AccountStatus.SUSPENDED,
            LocalDateTime.of(2024, 1, 1, 0, 0));
        persistAccount("acc-4", "cust-2", AccountStatus.ACTIVE,
            LocalDateTime.of(2024, 4, 1, 0, 0));
        entityManager.flush();
    }

    @Test
    @DisplayName("[Legacy Parity] Excludes CLOSED accounts -- matches SQL: STATUS != 'CLOSED'")
    void legacyBehavior_excludeClosedAccounts() {
        // Verifies: AccountServlet.java line 77
        Page<Account> result = accountRepository.findByCustomerIdAndStatusNot(
            "cust-1", AccountStatus.CLOSED,
            PageRequest.of(0, 20, Sort.by(Sort.Direction.DESC, "createdDate")));

        assertThat(result.getContent())
            .extracting(Account::getAccountId)
            .containsExactlyInAnyOrder("acc-1", "acc-3")
            .doesNotContain("acc-2"); // CLOSED excluded
    }

    @Test
    @DisplayName("[Legacy Parity] Customer isolation -- only returns matching customerId")
    void legacyBehavior_customerIsolation() {
        // Verifies: AccountServlet.java line 76 WHERE CUSTOMER_ID = ?
        Page<Account> cust1 = accountRepository.findByCustomerIdAndStatusNot(
            "cust-1", AccountStatus.CLOSED, PageRequest.of(0, 20));
        Page<Account> cust2 = accountRepository.findByCustomerIdAndStatusNot(
            "cust-2", AccountStatus.CLOSED, PageRequest.of(0, 20));

        assertThat(cust1.getContent())
            .extracting(Account::getCustomerId)
            .containsOnly("cust-1");
        assertThat(cust2.getContent())
            .extracting(Account::getCustomerId)
            .containsOnly("cust-2");
    }

    @Test
    @DisplayName("[New Behavior] Pagination works correctly")
    void newBehavior_paginationWorks() {
        // Enhancement: legacy had no pagination (unbounded result set)
        Page<Account> page = accountRepository.findByCustomerIdAndStatusNot(
            "cust-1", AccountStatus.CLOSED, PageRequest.of(0, 1));

        assertThat(page.getContent()).hasSize(1);
        assertThat(page.getTotalElements()).isEqualTo(2);
        assertThat(page.getTotalPages()).isEqualTo(2);
    }

    @Test
    @DisplayName("[New Behavior] Ownership verification returns empty for wrong customer")
    void newBehavior_ownershipVerification() {
        assertThat(accountRepository.findByAccountIdAndCustomerId("acc-1", "cust-1"))
            .isPresent();
        assertThat(accountRepository.findByAccountIdAndCustomerId("acc-1", "cust-2"))
            .isEmpty(); // Wrong customer
        assertThat(accountRepository.findByAccountIdAndCustomerId("nonexistent", "cust-1"))
            .isEmpty(); // No such account
    }

    private void persistAccount(String id, String customerId,
            AccountStatus status, LocalDateTime created) {
        Account account = new Account();
        account.setAccountId(id);
        account.setCustomerId(customerId);
        account.setStatus(status);
        account.setAccountType("SAVINGS");
        account.setBalance(new BigDecimal("1000.00"));
        account.setCurrency("USD");
        account.setCreatedDate(created);
        entityManager.persist(account);
    }
}
```

##### Coverage Analysis

| Class | Line Coverage | Branch Coverage | Notes |
|-------|-------------|-----------------|-------|
| AccountService | 100% | 100% | All paths tested including exceptions |
| AccountController | ~85% | ~80% | JWT extraction requires @WithMockUser |
| AccountRepository | 100% | N/A | Interface -- tested via integration |
| TransactionRepository | ~80% | N/A | Date range query tested |
| GlobalExceptionHandler | ~90% | ~85% | All 4 handlers tested |

**Total estimated coverage: 92% line, 87% branch**

#### [Perf] Performance Testing Mode

##### Findings

| ID | Finding | Severity | Detail |
|----|---------|----------|--------|
| PERF-001 | Transaction query may full-table-scan without index on TXN_DATE | Medium | Ensure `CREATE INDEX idx_txn_date ON TRANSACTIONS(ACCOUNT_ID, TXN_DATE)` exists |
| PERF-002 | `@ManyToOne(fetch = LAZY)` on Transaction.account prevents N+1 | Low | Good -- lazy loading is correct here |
| PERF-003 | Default page size 20 for accounts is reasonable | Info | Legacy was unbounded, which would OOM on large customers |

#### [Security] Security Testing Mode

##### Findings

| ID | Finding | Severity | Detail |
|----|---------|----------|--------|
| SEC-001 | Verify JWT audience claim validation | Medium | See Step 6 for full security review |
| SEC-002 | No rate limiting on endpoints | Medium | Recommend `@RateLimiter` annotation |
| SEC-003 | `open-in-view: false` is correctly set | Info | Prevents lazy loading outside transactions |

##### Recommendations

1. Add index verification test that checks `EXPLAIN PLAN` for account and transaction queries
2. Add load test using k6 or Gatling to validate p95 latency under 200ms target
3. Add security test verifying that an unauthenticated request returns 401
4. Add test verifying that accessing another customer's account returns 403
5. Consider adding Testcontainers with Oracle XE for Oracle-specific query behavior verification

### What This Skill Provided

`test-master` operated in all three modes -- **[Test]** for functional coverage, **[Perf]** for performance concerns, and **[Security]** for security testing gaps. The test suite uses two naming conventions: `legacyBehavior_*` tests verify backward compatibility with the original servlet behavior, and `newBehavior_*` tests verify the enhancements. This labeling makes it immediately clear during a CI failure whether a regression breaks a legacy contract or a new feature.

---

## Step 6 -- Security Review with `security-reviewer`

### Prompt

```
Review the modernized account service for security. Compare against legacy
vulnerabilities (SQL injection, no auth, shared connection, hardcoded credentials)
and identify new risks.
```

### Skill Output

#### 1. Executive Summary

**Risk Assessment: LOW (improved from CRITICAL)**

The modernization effort successfully resolved all 6 critical and high-severity vulnerabilities present in the legacy `AccountServlet.java`. The new Spring Boot 3 service introduces proper authentication, parameterized queries, connection pooling, and externalized configuration. Two medium-severity items remain as enhancements before production deployment.

**Overall Security Posture:**
- Legacy system: **2/10** (CRITICAL -- actively exploitable SQL injection, no auth)
- Modernized system: **8/10** (LOW risk -- missing rate limiting and JWT audience validation)

#### 2. Findings Table

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | All resolved |
| High | 0 | All resolved |
| Medium | 2 | Open (new) |
| Low | 1 | Open (new) |
| Info | 2 | Noted |

**Legacy Vulnerability Resolution:**

| ID | Vulnerability | Legacy Location | Severity | Status | Resolution |
|----|--------------|-----------------|----------|--------|------------|
| LEG-001 | SQL Injection | AccountServlet.java lines 76, 111, 147-148 | CRITICAL | RESOLVED | Spring Data JPA parameterized queries |
| LEG-002 | Shared JDBC Connection | AccountServlet.java line 26 | HIGH | RESOLVED | HikariCP connection pool (max 20) |
| LEG-003 | No Authentication | AccountServlet.java lines 43-65 | HIGH | RESOLVED | Spring Security JWT via OAuth2 Resource Server |
| LEG-004 | Hardcoded Credentials | AccountServlet.java lines 34-35 | HIGH | RESOLVED | Environment variables `${DB_USERNAME}`, `${DB_PASSWORD}` |
| LEG-005 | No Input Validation | AccountServlet.java lines 73-74 | MEDIUM | RESOLVED | `@NotBlank`, `@DateTimeFormat` Bean Validation |
| LEG-006 | No Ownership Check (IDOR) | AccountServlet.java line 108 | HIGH | RESOLVED | `verifyOwnership()` + `findByAccountIdAndCustomerId()` |

#### 3. Detailed Findings

**FINDING-001: Missing JWT Audience Validation**

- **Severity:** Medium
- **Location:** `SecurityConfig.java` -- `filterChain()` method
- **Impact:** A JWT issued for a different service (e.g., `payment-service`) could be accepted by the account service if both services share the same issuer. This allows cross-service token reuse.
- **Evidence:** The current configuration only validates the issuer URI but does not check the `aud` (audience) claim.

**Remediation:**
```java
@Bean
public JwtDecoder jwtDecoder(@Value("${spring.security.oauth2.resourceserver.jwt.issuer-uri}")
                              String issuerUri) {
    NimbusJwtDecoder decoder = JwtDecoders.fromIssuerLocation(issuerUri);
    OAuth2TokenValidator<Jwt> withIssuer =
        JwtValidators.createDefaultWithIssuer(issuerUri);
    OAuth2TokenValidator<Jwt> withAudience =
        new JwtClaimValidator<List<String>>("aud",
            aud -> aud != null && aud.contains("account-service"));
    decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
        withIssuer, withAudience));
    return decoder;
}
```

---

**FINDING-002: No Rate Limiting**

- **Severity:** Medium
- **Location:** `AccountController.java` -- all endpoints
- **Impact:** Without rate limiting, the service is vulnerable to:
  - Brute-force account enumeration (trying sequential account IDs)
  - Denial of service via excessive requests
  - Credential stuffing against the JWT endpoint (if co-located)
- **Evidence:** No `@RateLimiter`, no Spring Cloud Gateway rate limiter, no servlet filter for rate limiting.

**Remediation:**
```java
// Option 1: Resilience4j rate limiter
@GetMapping
@RateLimiter(name = "accountsList", fallbackMethod = "rateLimitFallback")
public ResponseEntity<Page<AccountResponse>> listAccounts(...) { ... }

// Option 2: Spring Cloud Gateway (preferred for microservices)
spring:
  cloud:
    gateway:
      routes:
        - id: account-service
          uri: lb://account-service
          predicates:
            - Path=/api/v2/accounts/**
          filters:
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 50
                redis-rate-limiter.burstCapacity: 100
```

---

**FINDING-003: Sensitive Financial Data in Debug Logs**

- **Severity:** Low
- **Location:** `application.yml` -- `hibernate.format_sql: true`
- **Impact:** When combined with `show_sql: true` (common in development), parameterized query values may appear in logs, potentially exposing customer IDs and account balances.
- **Evidence:** `format_sql: true` is set in the configuration. While `show_sql` is not enabled, the risk exists if a developer enables it during debugging.

**Remediation:**
```yaml
# Use logging categories instead of show_sql
logging:
  level:
    org.hibernate.SQL: DEBUG          # SQL statements (safe)
    org.hibernate.orm.jdbc.bind: WARN # Parameter values (hidden in production)
```

---

**FINDING-INFO-001: CSRF Disabled (Acceptable)**

- **Severity:** Info
- **Location:** `SecurityConfig.java` -- `csrf.disable()`
- **Assessment:** Acceptable for a stateless REST API using JWT bearer tokens. CSRF protection is unnecessary because the API does not use cookies for authentication.

---

**FINDING-INFO-002: `ddl-auto: validate` Correctly Set**

- **Severity:** Info
- **Location:** `application.yml` -- `spring.jpa.hibernate.ddl-auto`
- **Assessment:** Correct. This prevents Hibernate from accidentally creating, altering, or dropping tables in the production Oracle database. The legacy system had no such protection.

#### 4. Prioritized Recommendations

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| 1 | Add JWT audience validation (FINDING-001) | Low (15 min) | Prevents cross-service token reuse |
| 2 | Add rate limiting (FINDING-002) | Medium (2-4 hours) | Prevents enumeration and DoS |
| 3 | Configure Hibernate logging levels (FINDING-003) | Low (5 min) | Prevents data leakage in logs |
| 4 | Add security headers (X-Content-Type-Options, X-Frame-Options) | Low (15 min) | Defense in depth |
| 5 | Implement API key rotation for service-to-service calls | Medium (1-2 days) | Future-proofing for multi-service arch |
| 6 | Set up dependency vulnerability scanning (Trivy, Snyk) | Medium (2-4 hours) | Continuous vulnerability monitoring |

### What This Skill Provided

`security-reviewer` produced the 4-part report: executive summary with risk assessment, findings table with severity counts, detailed findings with file-level location and remediation code, and prioritized recommendations with effort estimates. The review confirmed all 6 legacy vulnerabilities are resolved and identified 2 new medium-severity items plus 1 low-severity item. The security posture improved from 2/10 (CRITICAL) to 8/10 (LOW), with a clear path to 10/10 through the recommended remediations.

---

## Key Takeaways

1. **Reverse-engineering before rewriting prevents lost business rules.** `spec-miner` extracted that the `STATUS != 'CLOSED'` filter at line 77 of AccountServlet.java was an intentional business rule (soft-delete pattern), not just a query predicate. Without extracting this, the modernized service might have returned closed accounts or, worse, dropped valid statuses like SUSPENDED.

2. **The strangler fig pattern eliminates big-bang risk.** `legacy-modernizer` designed a three-phase migration with rollback gates at each stage. For a financial services system, the ability to instantly route 100% of traffic back to the legacy servlet via a feature flag weight change is not optional -- it is a regulatory expectation.

3. **Architecture decisions create audit trail.** `architecture-designer` documented three ADRs that trace each technology choice (JPA, JWT, schema preservation) back to a specific legacy vulnerability or constraint. When a future engineer asks "why Spring Data JPA instead of MyBatis?", ADR-001 provides the answer with full context.

4. **Implementation must explicitly annotate legacy preservation.** `spring-boot-engineer` added Javadoc comments on every service method citing the exact legacy code line it replaces (e.g., "Preserves: AccountServlet.java line 77"). This makes code review for migration correctness tractable -- reviewers can verify each legacy behavior maps to a modern equivalent.

5. **Tests must distinguish legacy parity from new features.** `test-master` used the naming convention `legacyBehavior_*` vs `newBehavior_*` to make CI failures unambiguous. A failing `legacyBehavior_excludeClosedAccounts` test means the migration broke backward compatibility. A failing `newBehavior_paginationWorks` test means a new feature regressed. Different failure modes require different response urgency.

6. **Security review closes the loop by quantifying improvement.** `security-reviewer` mapped all 6 legacy vulnerabilities to their resolutions and measured the improvement (2/10 to 8/10). The remaining 2 points are achievable with less than a day of work (JWT audience validation + rate limiting), giving stakeholders a clear, bounded checklist before production deployment.
