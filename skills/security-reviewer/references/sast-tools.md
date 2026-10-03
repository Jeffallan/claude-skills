# SAST Tools

## JavaScript/TypeScript

```bash
# Dependency vulnerabilities
npm audit
npm audit --json > npm-audit.json

# ESLint security plugin
npm install eslint-plugin-security --save-dev
npx eslint --ext .js,.ts . --plugin security

# Snyk
npx snyk test
npx snyk code test
```

## Python

```bash
# Bandit - Python SAST
pip install bandit
bandit -r . -f json -o bandit-report.json
bandit -r . -ll  # Only high severity

# Safety - Dependency check
pip install safety
safety check
safety check -r requirements.txt --json > safety-report.json

# Pyup Safety
pip install pyupio-safety
pyupio-safety check
```

## Go

```bash
# GoSec - Go security checker
go install github.com/securego/gosec/v2/cmd/gosec@latest
gosec ./...
gosec -fmt=json -out=gosec-report.json ./...

# Go vulnerability database
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

## Multi-Language Tools

```bash
# Semgrep - Universal SAST
pip install semgrep
semgrep --config=auto .
semgrep --config=p/security-audit .
semgrep --config=p/owasp-top-ten .

# Trivy - Comprehensive scanner
brew install trivy
trivy fs .
trivy fs --security-checks vuln,secret,config .

# SonarQube (requires server)
sonar-scanner -Dsonar.projectKey=myproject
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Semgrep
  uses: returntocorp/semgrep-action@v1
  with:
    config: p/security-audit

- name: Run npm audit
  run: npm audit --audit-level=high

- name: Run Trivy
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    severity: 'CRITICAL,HIGH'
```

### GitLab CI

```yaml
security-scan:
  image: returntocorp/semgrep
  script:
    - semgrep --config=auto --json -o semgrep.json .
  artifacts:
    reports:
      sast: semgrep.json
```

## Quick Reference

| Language | Primary Tool | Dependency Check |
|----------|--------------|------------------|
| JavaScript | ESLint + security | npm audit |
| TypeScript | ESLint + security | npm audit |
| Python | Bandit | Safety |
| Go | GoSec | govulncheck |
| Java | SpotBugs | OWASP Dependency-Check |
| Ruby | Brakeman | bundler-audit |

| Tool | Strengths | Best For |
|------|-----------|----------|
| Semgrep | Multi-language, custom rules | General SAST |
| Trivy | Container + code + secrets | Comprehensive |
| Bandit | Python-specific | Python projects |
| GoSec | Go-specific | Go projects |
| npm audit | Built-in, fast | Node.js deps |
