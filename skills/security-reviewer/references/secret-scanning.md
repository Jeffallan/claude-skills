# Secret Scanning

## Gitleaks

```bash
# Install
brew install gitleaks

# Scan current directory
gitleaks detect --source . --verbose

# Scan with report
gitleaks detect --source . -f json -r gitleaks-report.json

# Scan git history
gitleaks detect --source . --log-opts="--all"

# Use baseline (ignore known)
gitleaks detect --baseline-path .gitleaks-baseline.json
```

## TruffleHog

```bash
# Install
pip install trufflehog

# Scan filesystem
trufflehog filesystem .

# Scan git repo
trufflehog git file://. --since-commit HEAD~100

# Scan with JSON output
trufflehog filesystem . --json > trufflehog-report.json
```

## Manual Grep Patterns

```bash
# Common secret patterns
grep -rn "api_key\|apikey\|api-key" --include="*.{ts,js,py}" .
grep -rn "secret\|password\|passwd" --include="*.{ts,js,py}" .
grep -rn "private_key\|privatekey" --include="*.{ts,js,py}" .
grep -rn "access_token\|accesstoken" --include="*.{ts,js,py}" .

# AWS credentials
grep -rn "AKIA[0-9A-Z]{16}" .
grep -rn "aws_secret_access_key" .

# Base64 encoded (potential secrets)
grep -rn "[A-Za-z0-9+/]{40,}=" .

# JWT tokens
grep -rn "eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\." .
```

## Common Secret Patterns

| Type | Pattern | Example |
|------|---------|---------|
| AWS Access Key | `AKIA[0-9A-Z]{16}` | AKIAIOSFODNN7EXAMPLE |
| AWS Secret Key | 40 char base64 | wJalrXUtnFEMI/K7MDENG... |
| GitHub Token | `ghp_[A-Za-z0-9]{36}` | ghp_xxxxxxxxxxxx |
| Slack Token | `xox[baprs]-` | xoxb-xxx-xxx |
| Stripe Key | `sk_live_[A-Za-z0-9]{24}` | sk_live_xxxx |
| Private Key | `-----BEGIN.*PRIVATE KEY-----` | RSA/EC keys |
| JWT | `eyJ[A-Za-z0-9_-]*\.eyJ` | Encoded tokens |

## Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

## CI/CD Integration

```yaml
# GitHub Actions
- name: Gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# GitLab CI
secret_detection:
  image: zricethezav/gitleaks
  script:
    - gitleaks detect --source . -f sarif -r gl-secret-detection-report.sarif
  artifacts:
    reports:
      secret_detection: gl-secret-detection-report.sarif
```

## Remediation Steps

1. **Rotate immediately** - Consider secret compromised
2. **Remove from history** - Use git filter-branch or BFG
3. **Add to .gitignore** - Prevent future commits
4. **Use env variables** - Move to environment
5. **Use secret manager** - AWS Secrets Manager, Vault

```bash
# Remove from git history (BFG)
bfg --replace-text passwords.txt repo.git

# Or git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret" \
  --prune-empty --tag-name-filter cat -- --all
```

## Quick Reference

| Tool | Best For | Speed |
|------|----------|-------|
| Gitleaks | Git history | Fast |
| TruffleHog | Deep scanning | Medium |
| grep | Quick checks | Fast |
| GitHub Secret Scanning | GitHub repos | Auto |
