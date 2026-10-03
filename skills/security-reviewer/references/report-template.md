# Security Report Template

## Full Report Template

```markdown
# Security Review Report

## Executive Summary

| Field | Value |
|-------|-------|
| **Application** | [Application Name] |
| **Review Date** | [YYYY-MM-DD] |
| **Reviewer** | [Name] |
| **Scope** | [Files/modules reviewed] |
| **Overall Risk Level** | [Critical/High/Medium/Low] |

### Key Findings
- X Critical vulnerabilities requiring immediate attention
- Y High-severity issues to address before deployment
- Z Medium/Low issues for future consideration

## Findings Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | X | Requires immediate fix |
| High | X | Fix before deployment |
| Medium | X | Fix in next sprint |
| Low | X | Backlog |

## Detailed Findings

### [CRITICAL] SQL Injection in User Search

| Field | Value |
|-------|-------|
| **ID** | SEC-001 |
| **Location** | `src/api/users.ts:45` |
| **CWE** | CWE-89 |
| **CVSS** | 9.8 (Critical) |

**Description**
User input directly concatenated into SQL query without sanitization.

**Vulnerable Code**
```typescript
const query = `SELECT * FROM users WHERE name LIKE '%${searchTerm}%'`;
```

**Proof of Concept**
```
GET /api/users?search=' OR '1'='1
```

**Impact**
- Full database access
- Data exfiltration
- Data modification/deletion
- Potential RCE via SQL features

**Remediation**
Use parameterized queries:
```typescript
const query = 'SELECT * FROM users WHERE name LIKE $1';
db.query(query, [`%${searchTerm}%`]);
```

**Effort**: 1 hour
**Priority**: Immediate

---

### [HIGH] Weak Password Requirements

| Field | Value |
|-------|-------|
| **ID** | SEC-002 |
| **Location** | `src/auth/validation.ts:12` |
| **CWE** | CWE-521 |
| **CVSS** | 7.5 (High) |

**Description**
Password policy requires only 6 characters with no complexity requirements.

**Current Policy**
```typescript
const isValid = password.length >= 6;
```

**Impact**
- Susceptible to brute force attacks
- Dictionary attack vulnerability

**Remediation**
Implement stronger requirements:
```typescript
const isValid =
  password.length >= 12 &&
  /[A-Z]/.test(password) &&
  /[a-z]/.test(password) &&
  /[0-9]/.test(password) &&
  /[^A-Za-z0-9]/.test(password);
```

**Effort**: 30 minutes
**Priority**: Before deployment

## Automated Scan Results

### Dependency Vulnerabilities
| Package | Severity | CVE | Fix |
|---------|----------|-----|-----|
| lodash | High | CVE-2021-xxxx | Upgrade to 4.17.21 |

### SAST Findings
| Tool | Critical | High | Medium | Low |
|------|----------|------|--------|-----|
| Semgrep | 1 | 3 | 5 | 8 |
| npm audit | 0 | 2 | 4 | 10 |

## Recommendations

### Immediate (This Sprint)
1. Fix SQL injection vulnerability (SEC-001)
2. Implement parameterized queries globally
3. Update vulnerable dependencies

### Short-term (Next Sprint)
1. Strengthen password policy (SEC-002)
2. Add input validation middleware
3. Enable security headers

### Long-term
1. Implement SAST in CI/CD pipeline
2. Schedule regular security reviews
3. Security training for developers

## Appendix

### Tools Used
- Semgrep v1.x
- npm audit
- Gitleaks v8.x
- Manual code review

### References
- OWASP Top 10 2021
- CWE Database
- CVSS Calculator
```

## Severity Definitions

| Severity | CVSS Score | Response Time |
|----------|------------|---------------|
| Critical | 9.0 - 10.0 | Immediate |
| High | 7.0 - 8.9 | 24-48 hours |
| Medium | 4.0 - 6.9 | 1-2 weeks |
| Low | 0.1 - 3.9 | Next release |

## Quick Reference

| Section | Purpose |
|---------|---------|
| Executive Summary | Management overview |
| Findings Summary | Quick count by severity |
| Detailed Findings | Technical details |
| Scan Results | Automated tool output |
| Recommendations | Prioritized action items |
