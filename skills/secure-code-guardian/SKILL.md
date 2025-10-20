---
name: Secure Code Guardian
description: Expert in writing secure code and preventing vulnerabilities. Use when implementing security features, writing authentication/authorization, handling sensitive data, preventing common vulnerabilities (OWASP Top 10), or when the user mentions secure coding, security, authentication, authorization, or vulnerabilities.
---

# Secure Code Guardian

Expert in writing secure code and implementing security best practices to prevent vulnerabilities.

## Instructions

### Core Workflow

1. **Understand security requirements**
   - Authentication needs
   - Authorization requirements
   - Data sensitivity levels
   - Compliance requirements (GDPR, HIPAA, etc.)
   - Threat model

2. **Implement security controls**
   - Input validation
   - Output encoding
   - Authentication mechanisms
   - Authorization checks
   - Encryption (at rest and in transit)
   - Secure session management

3. **Prevent OWASP Top 10**
   - Injection attacks
   - Broken authentication
   - Sensitive data exposure
   - XML External Entities (XXE)
   - Broken access control
   - Security misconfiguration
   - Cross-Site Scripting (XSS)
   - Insecure deserialization
   - Using components with known vulnerabilities
   - Insufficient logging & monitoring

4. **Secure development practices**
   - Principle of least privilege
   - Defense in depth
   - Fail securely
   - Keep security simple
   - Don't trust user input

### OWASP Top 10 Prevention

#### 1. SQL Injection Prevention

```typescript
// ❌ Vulnerable to SQL injection
const query = `SELECT * FROM users WHERE email = '${userEmail}'`;
db.query(query);

// ✅ Use parameterized queries
const query = 'SELECT * FROM users WHERE email = $1';
db.query(query, [userEmail]);

// ✅ Or use an ORM
const user = await User.findOne({ where: { email: userEmail } });
```

#### 2. Authentication Best Practices

```typescript
import bcrypt from 'bcrypt';

// Password hashing
async function hashPassword(password: string): Promise<string> {
  const saltRounds = 12; // Minimum 10
  return await bcrypt.hash(password, saltRounds);
}

// Password verification
async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return await bcrypt.compare(password, hash);
}

// Strong password requirements
function isStrongPassword(password: string): boolean {
  const minLength = 12;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumbers = /\d/.test(password);
  const hasSpecialChar = /[!@#$%^&*]/.test(password);

  return password.length >= minLength &&
         hasUpperCase &&
         hasLowerCase &&
         hasNumbers &&
         hasSpecialChar;
}

// Rate limiting for login attempts
const loginAttempts = new Map<string, { count: number; resetTime: number }>();

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const attempts = loginAttempts.get(ip);

  if (!attempts || now > attempts.resetTime) {
    loginAttempts.set(ip, { count: 1, resetTime: now + 15 * 60 * 1000 }); // 15 min
    return true;
  }

  if (attempts.count >= 5) {
    return false; // Too many attempts
  }

  attempts.count++;
  return true;
}
```

#### 3. XSS Prevention

```typescript
// ❌ Vulnerable to XSS
element.innerHTML = userInput;

// ✅ Use textContent or sanitize
element.textContent = userInput;

// Or use a sanitization library
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);

// React automatically escapes
<div>{userInput}</div> // Safe

// Backend: Set Content-Security-Policy header
app.use((req, res, next) => {
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
  );
  next();
});
```

#### 4. CSRF Prevention

```typescript
// Use CSRF tokens
import csrf from 'csurf';

app.use(csrf({ cookie: true }));

app.get('/form', (req, res) => {
  res.render('form', { csrfToken: req.csrfToken() });
});

// In form
// <input type="hidden" name="_csrf" value="{{ csrfToken }}">

// For APIs: Use custom headers
// X-CSRF-Token: <token>
```

#### 5. Authorization Best Practices

```typescript
// Role-Based Access Control (RBAC)
enum Role {
  USER = 'user',
  ADMIN = 'admin',
  MODERATOR = 'moderator',
}

interface User {
  id: string;
  role: Role;
}

function requireRole(allowedRoles: Role[]) {
  return (req, res, next) => {
    const user: User = req.user;

    if (!user) {
      return res.status(401).json({ error: 'Not authenticated' });
    }

    if (!allowedRoles.includes(user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }

    next();
  };
}

// Usage
app.delete('/users/:id', requireRole([Role.ADMIN]), deleteUser);

// Resource-based authorization
async function canAccessResource(userId: string, resourceId: string): Promise<boolean> {
  const resource = await Resource.findById(resourceId);
  return resource.ownerId === userId || await isAdmin(userId);
}

app.get('/resource/:id', async (req, res) => {
  if (!await canAccessResource(req.user.id, req.params.id)) {
    return res.status(403).json({ error: 'Access denied' });
  }
  // Return resource
});
```

#### 6. Sensitive Data Handling

```typescript
// Environment variables for secrets
const JWT_SECRET = process.env.JWT_SECRET;
const DB_PASSWORD = process.env.DB_PASSWORD;

// Never log sensitive data
// ❌ Don't do this
console.log('User:', user); // May contain password hash

// ✅ Log safely
console.log('User:', { id: user.id, email: user.email });

// Encrypt sensitive data at rest
import crypto from 'crypto';

const algorithm = 'aes-256-gcm';
const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');

function encrypt(text: string): { encrypted: string; iv: string; tag: string } {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(algorithm, key, iv);

  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');

  return {
    encrypted,
    iv: iv.toString('hex'),
    tag: cipher.getAuthTag().toString('hex'),
  };
}

function decrypt(encrypted: string, iv: string, tag: string): string {
  const decipher = crypto.createDecipheriv(
    algorithm,
    key,
    Buffer.from(iv, 'hex')
  );
  decipher.setAuthTag(Buffer.from(tag, 'hex'));

  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');

  return decrypted;
}
```

#### 7. Security Headers

```typescript
import helmet from 'helmet';

app.use(helmet()); // Sets various security headers

// Or manually:
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  next();
});
```

### Input Validation

```typescript
import { z } from 'zod';

// Define schema
const userSchema = z.object({
  email: z.string().email(),
  password: z.string().min(12),
  age: z.number().int().positive().max(150),
  website: z.string().url().optional(),
});

// Validate input
function validateUser(data: unknown) {
  try {
    return userSchema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ValidationError(error.errors);
    }
    throw error;
  }
}

// Sanitize strings
function sanitizeString(input: string): string {
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove < and >
    .substring(0, 1000); // Limit length
}
```

### Secure Session Management

```typescript
import session from 'express-session';
import RedisStore from 'connect-redis';

app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true, // HTTPS only
    httpOnly: true, // No JavaScript access
    maxAge: 1000 * 60 * 60 * 24, // 1 day
    sameSite: 'strict', // CSRF protection
  },
}));

// Regenerate session ID after login
app.post('/login', async (req, res) => {
  const user = await authenticateUser(req.body);

  req.session.regenerate((err) => {
    if (err) {
      return res.status(500).json({ error: 'Session error' });
    }

    req.session.userId = user.id;
    res.json({ success: true });
  });
});
```

## Critical Rules

### Always Do
- Validate all input
- Use parameterized queries
- Hash passwords with bcrypt/argon2
- Use HTTPS in production
- Implement rate limiting
- Set security headers
- Use least privilege principle
- Encrypt sensitive data
- Log security events
- Keep dependencies updated

### Never Do
- Never trust user input
- Never store passwords in plain text
- Never log sensitive data
- Never use weak encryption (MD5, SHA1 for passwords)
- Never expose stack traces to users
- Never disable security features "temporarily"
- Never hardcode secrets
- Never use predictable IDs for sensitive resources
- Never trust client-side validation alone

## Knowledge Base

- **OWASP Top 10**: Common web vulnerabilities
- **Cryptography**: Hashing, encryption, signing
- **Authentication**: JWT, OAuth, session management
- **Authorization**: RBAC, ABAC, resource-based
- **Standards**: OWASP, NIST, PCI DSS

## Best Practices Summary

1. **Input Validation**: Never trust user input
2. **Authentication**: Strong passwords, MFA, rate limiting
3. **Authorization**: Verify every request
4. **Encryption**: Sensitive data at rest and in transit
5. **Sessions**: Secure configuration
6. **Headers**: Set all security headers
7. **Dependencies**: Keep updated
8. **Logging**: Log security events
9. **Principle of Least Privilege**: Minimum necessary permissions
10. **Defense in Depth**: Multiple layers of security
