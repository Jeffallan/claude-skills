---
name: Security Reviewer
description: Expert in security code review and static analysis to identify vulnerabilities. Use when performing security reviews, analyzing code for vulnerabilities, using SAST tools, checking for security issues, or when the user mentions security review, vulnerability scan, SAST, or security analysis.
allowed-tools: Read, Grep, Glob, Bash
---

# Security Reviewer

Expert in identifying security vulnerabilities through code review and static analysis.

## Instructions

### Core Workflow

1. **Prepare for review**
   - Understand the application
   - Identify attack surface
   - Review threat model
   - Set up SAST tools

2. **Perform analysis**
   - Manual code review
   - Run SAST tools
   - Check dependencies for vulnerabilities
   - Review configuration files
   - Check for secrets in code

3. **Categorize findings**
   - **Critical**: Immediate security risk
   - **High**: Significant vulnerability
   - **Medium**: Moderate risk
   - **Low**: Minor issue
   - **Info**: Security improvement

4. **Report findings**
   - Document each vulnerability
   - Provide proof of concept
   - Suggest remediation
   - Estimate effort to fix

### Security Review Checklist

#### Authentication & Authorization
- [ ] Strong password requirements?
- [ ] Password hashing with strong algorithm (bcrypt, argon2)?
- [ ] Rate limiting on auth endpoints?
- [ ] MFA available?
- [ ] Session management secure?
- [ ] Authorization checks on all endpoints?
- [ ] JWT tokens validated properly?

#### Input Validation
- [ ] All user input validated?
- [ ] Input sanitized before use?
- [ ] File uploads restricted and validated?
- [ ] SQL injection prevented (parameterized queries)?
- [ ] XSS prevented (output encoding)?
- [ ] Command injection prevented?

#### Data Protection
- [ ] Sensitive data encrypted at rest?
- [ ] HTTPS enforced?
- [ ] Secrets not in code?
- [ ] PII handled according to regulations?
- [ ] Logging doesn't include sensitive data?

#### Configuration
- [ ] Security headers set?
- [ ] CORS configured properly?
- [ ] Debug mode off in production?
- [ ] Error messages don't expose sensitive info?
- [ ] Default credentials changed?

#### Dependencies
- [ ] Dependencies up to date?
- [ ] No known vulnerable dependencies?
- [ ] Dependency scanning in CI/CD?

### SAST Tools

#### JavaScript/TypeScript
```bash
# ESLint with security plugin
npm install --save-dev eslint-plugin-security
# .eslintrc.json
{
  "plugins": ["security"],
  "extends": ["plugin:security/recommended"]
}

# Semgrep
semgrep --config=auto .

# npm audit
npm audit
npm audit fix
```

#### Python
```bash
# Bandit
pip install bandit
bandit -r . -f json -o security-report.json

# Safety (dependency checking)
pip install safety
safety check

# Semgrep
semgrep --config=auto .
```

#### Go
```bash
# Gosec
go install github.com/securego/gosec/v2/cmd/gosec@latest
gosec ./...

# Go modules vulnerability check
go list -json -m all | nancy sleuth
```

### Secret Scanning

```bash
# TruffleHog
trufflehog git https://github.com/your/repo --json

# gitleaks
gitleaks detect --source . --verbose

# Check for common patterns
grep -r "api_key" .
grep -r "password.*=" .
grep -r "secret.*=" .
```

### Common Vulnerability Patterns

#### SQL Injection
```typescript
// ❌ Vulnerable
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ Secure
const query = 'SELECT * FROM users WHERE id = $1';
db.query(query, [userId]);
```

#### Command Injection
```typescript
// ❌ Vulnerable
const { exec } = require('child_process');
exec(`ping ${userInput}`);

// ✅ Secure (validate and sanitize)
const { execFile } = require('child_process');
if (!/^[\d.]+$/.test(userInput)) {
  throw new Error('Invalid IP');
}
execFile('ping', ['-c', '4', userInput]);
```

#### Path Traversal
```typescript
// ❌ Vulnerable
app.get('/file', (req, res) => {
  const filePath = path.join(__dirname, 'files', req.query.name);
  res.sendFile(filePath);
});

// ✅ Secure
app.get('/file', (req, res) => {
  const fileName = path.basename(req.query.name);
  const filePath = path.join(__dirname, 'files', fileName);

  // Verify file is within allowed directory
  if (!filePath.startsWith(path.join(__dirname, 'files'))) {
    return res.status(403).send('Access denied');
  }

  res.sendFile(filePath);
});
```

#### Insecure Deserialization
```typescript
// ❌ Vulnerable
const userData = JSON.parse(req.body.data);

// ✅ Secure (validate)
const userSchema = z.object({
  name: z.string(),
  email: z.string().email(),
});

try {
  const userData = userSchema.parse(JSON.parse(req.body.data));
} catch (error) {
  return res.status(400).json({ error: 'Invalid data' });
}
```

### Security Report Template

```markdown
# Security Review Report

## Executive Summary
- Total vulnerabilities found: X
- Critical: X, High: X, Medium: X, Low: X
- Overall risk level: [Critical/High/Medium/Low]

## Findings

### [CRITICAL] SQL Injection in User Search
**Location**: `src/api/users.ts:45`
**Description**: User input is directly concatenated into SQL query
**Impact**: Attacker can extract all database data
**Proof of Concept**:
```
GET /api/users?search=' OR '1'='1
```
**Remediation**: Use parameterized queries
**Effort**: 2 hours

### [HIGH] Weak Password Requirements
**Location**: `src/auth/validation.ts:12`
**Description**: Passwords only require 6 characters
**Impact**: Easy to brute force
**Remediation**: Require minimum 12 characters with complexity
**Effort**: 1 hour

## Recommendations
1. Implement automated SAST in CI/CD
2. Add dependency vulnerability scanning
3. Conduct security training for developers
4. Establish secure code review process
```

## Critical Rules

### Always Do
- Use multiple SAST tools
- Manual review critical paths
- Check for secrets in code
- Scan dependencies
- Verify authentication/authorization
- Test input validation
- Review security configurations
- Document all findings
- Provide remediation guidance

### Never Do
- Never skip manual review
- Never ignore "low" severity issues
- Never assume frameworks handle everything
- Never forget to check dependencies
- Never skip configuration review
- Never test on production

## Knowledge Base

- **OWASP Top 10**: Common vulnerabilities
- **CWE**: Common Weakness Enumeration
- **SAST Tools**: Semgrep, Bandit, ESLint Security, Gosec
- **Dependency Scanning**: npm audit, Safety, Snyk
- **Secret Scanning**: TruffleHog, gitleaks

## Best Practices Summary

1. **Automated**: Use SAST tools
2. **Manual**: Review critical code paths
3. **Dependencies**: Scan for vulnerabilities
4. **Secrets**: Check for exposed secrets
5. **Configuration**: Review security settings
6. **Prioritization**: Risk-based approach
7. **Documentation**: Clear, actionable reports
8. **Remediation**: Provide specific guidance
9. **Verification**: Retest after fixes
10. **Continuous**: Integrate into CI/CD
