# Architecture Decision Guide

> Reference for: Fullstack Guardian
> Load when: Making technology choices, designing system architecture

## Technology Selection Matrix

### Backend Framework Selection

| Framework | Best For | Pros | Cons |
|-----------|----------|------|------|
| **NestJS** | Enterprise apps, microservices | TypeScript-first, dependency injection, excellent docs | Opinionated, steeper learning curve |
| **Express** | Simple APIs, flexibility | Minimal, huge ecosystem, well-known | Manual structure, less opinionated |
| **Fastify** | High performance APIs | Fast, schema validation, plugins | Smaller ecosystem than Express |
| **FastAPI** | Python APIs, ML integration | Auto-docs, type hints, fast | Python ecosystem only |
| **Go/Gin** | High-performance services | Compiled, concurrent, fast | Verbose, less rapid development |

**Decision criteria:**
- Team expertise: Choose familiar stack
- Performance needs: Go/Fastify for high throughput
- Type safety: NestJS/FastAPI for TypeScript/Python
- Flexibility: Express for custom architectures

### Frontend Framework Selection

| Framework | Best For | Pros | Cons |
|-----------|----------|------|------|
| **React** | Most use cases, large apps | Huge ecosystem, flexible, well-supported | Not batteries-included, decision fatigue |
| **Vue** | Progressive enhancement | Gentle learning curve, good docs, reactive | Smaller ecosystem than React |
| **Angular** | Enterprise apps | Complete framework, TypeScript native | Heavy, opinionated, steep curve |
| **Svelte** | Performance-critical apps | Compiled, no virtual DOM, small bundle | Smaller ecosystem, fewer resources |
| **Next.js** | SSR/SSG apps, SEO | React + routing + SSR, excellent DX | Vercel-centric, complexity for simple apps |

**Decision criteria:**
- SEO requirements: Next.js/Nuxt for SSR
- Team size: Angular for large teams, Vue for small
- Ecosystem: React for maximum third-party support
- Performance: Svelte for minimal bundle size

### Database Selection

| Database | Best For | Pros | Cons |
|----------|----------|------|------|
| **PostgreSQL** | Relational data, ACID | Feature-rich, reliable, JSON support | Complex queries can be slow |
| **MySQL** | Read-heavy workloads | Mature, fast reads, replication | Less feature-rich than Postgres |
| **MongoDB** | Flexible schemas, rapid dev | Schema-less, horizontal scaling | No transactions (old versions) |
| **Redis** | Caching, sessions, queues | Extremely fast, versatile | In-memory only, data structures limited |
| **DynamoDB** | AWS serverless, high scale | Managed, predictable performance | Vendor lock-in, query limitations |

**Decision criteria:**
- ACID requirements: PostgreSQL/MySQL
- Flexible schemas: MongoDB
- Caching layer: Redis (always)
- AWS serverless: DynamoDB
- Default choice: PostgreSQL (most versatile)

### State Management (Frontend)

| Solution | Best For | Complexity | Bundle Size |
|----------|----------|------------|-------------|
| **React Context** | Simple state, few updates | Low | None (built-in) |
| **Zustand** | Medium apps, simplicity | Low | 1KB |
| **Redux Toolkit** | Complex state, time-travel debug | Medium | 15KB |
| **Jotai/Recoil** | Atomic state, derived state | Medium | 3KB |
| **MobX** | Observable state, OOP style | Medium | 16KB |
| **TanStack Query** | Server state only | Low | 12KB |

**Decision criteria:**
- Simple app: Context or Zustand
- Complex state logic: Redux Toolkit
- Server state: TanStack Query (don't use global state)
- Real-time apps: Zustand + WebSocket

## Monolith vs Microservices

### Decision Matrix

| Factor | Monolith | Microservices |
|--------|----------|---------------|
| **Team size** | < 10 developers | > 10 developers |
| **System complexity** | Simple domain | Complex, bounded contexts |
| **Deployment** | Simple, all-at-once | Complex, independent services |
| **Scaling** | Vertical scaling | Horizontal per service |
| **Development speed** | Fast initially | Slower setup, faster iteration |
| **Infrastructure** | Simpler (1 app, 1 DB) | Complex (K8s, service mesh, multiple DBs) |
| **Data consistency** | ACID transactions | Eventual consistency, sagas |
| **Testing** | Easier integration tests | More complex testing |
| **Monitoring** | Single app to monitor | Distributed tracing needed |

### When to Use Monolith
```
✓ Starting new product (validate idea first)
✓ Small team (< 10 developers)
✓ Simple domain with few bounded contexts
✓ Need rapid development
✓ Limited infrastructure budget
✓ Straightforward deployment requirements
```

### When to Use Microservices
```
✓ Large team (> 10 developers)
✓ Clear bounded contexts in domain
✓ Different services have different scaling needs
✓ Need independent deployment cycles
✓ Multiple teams working independently
✓ Polyglot requirements (different languages)
✓ Have DevOps expertise and infrastructure
```

### Modular Monolith (Recommended Middle Ground)
```typescript
// Structure monolith with clear boundaries
project/
├── src/
│   ├── modules/
│   │   ├── users/
│   │   │   ├── users.module.ts
│   │   │   ├── users.service.ts
│   │   │   ├── users.controller.ts
│   │   │   └── users.repository.ts
│   │   ├── orders/
│   │   │   ├── orders.module.ts
│   │   │   └── ...
│   │   └── payments/
│   │       └── ...
│   └── shared/
│       ├── database/
│       └── auth/

// Clear module boundaries, can split later if needed
```

## API Architecture Patterns

### REST vs GraphQL

| Aspect | REST | GraphQL |
|--------|------|---------|
| **Best for** | CRUD operations, public APIs | Complex queries, mobile apps |
| **Learning curve** | Low | Medium-high |
| **Over-fetching** | Common issue | Solved by design |
| **Under-fetching** | Requires multiple requests | Single request |
| **Caching** | HTTP caching works well | More complex caching |
| **Versioning** | URL versioning (/v1, /v2) | Schema evolution |
| **Tooling** | Swagger, Postman | GraphiQL, Apollo Studio |

**Choose REST when:**
- Building simple CRUD APIs
- Need HTTP caching
- Public API with many consumers
- Team unfamiliar with GraphQL

**Choose GraphQL when:**
- Mobile apps need flexible queries
- Complex data requirements
- Rapid frontend iteration
- Real-time subscriptions needed

### BFF Pattern (Backend for Frontend)

```typescript
// Use when frontend needs differ from backend APIs
// Mobile BFF: Returns minimal data, optimized responses
@Controller('mobile-bff')
export class MobileBFFController {
  @Get('dashboard')
  async getMobileDashboard(@CurrentUser() user: User) {
    const [profile, notifications] = await Promise.all([
      this.userService.getProfile(user.id),
      this.notificationService.getUnread(user.id, 5), // Only 5 for mobile
    ]);
    return { profile, notifications }; // Minimal payload
  }
}

// Web BFF: Returns richer data
@Controller('web-bff')
export class WebBFFController {
  @Get('dashboard')
  async getWebDashboard(@CurrentUser() user: User) {
    const [profile, notifications, analytics, recentActivity] = await Promise.all([
      this.userService.getProfile(user.id),
      this.notificationService.getUnread(user.id, 20), // More for web
      this.analyticsService.getUserStats(user.id),
      this.activityService.getRecent(user.id),
    ]);
    return { profile, notifications, analytics, recentActivity };
  }
}
```

## Authentication Strategy

### JWT vs Session-based

| Aspect | JWT | Session |
|--------|-----|---------|
| **Scalability** | Stateless, horizontal scaling | Requires session store |
| **Performance** | No DB lookup per request | DB/Redis lookup needed |
| **Revocation** | Complex (requires blacklist) | Simple (delete session) |
| **Security** | Token can't be invalidated | Easy to invalidate |
| **Mobile/SPA** | Ideal for token storage | Requires cookies |
| **Microservices** | Easy to share across services | Harder to share |

**Hybrid approach (Recommended):**
```typescript
// Short-lived access token (15min) + refresh token (7 days)
interface AuthTokens {
  accessToken: string;   // JWT, 15 minutes, stored in memory
  refreshToken: string;  // Opaque token, 7 days, httpOnly cookie
}

// Access token: Stateless, fast validation
// Refresh token: Stored in DB, can be revoked
```

### SSO Integration Options

| Provider | Use Case | Complexity |
|----------|----------|------------|
| **OAuth2/OIDC** | Standard protocol, most IdPs | Medium |
| **SAML** | Enterprise customers, legacy | High |
| **Social logins** | B2C apps (Google, GitHub) | Low |
| **Auth0/Okta** | Managed solution, rapid setup | Low |

## Caching Strategy

### Layered Caching Approach

```typescript
// Layer 1: CDN caching (static assets)
// CloudFront, Cloudflare

// Layer 2: API response caching (Redis)
const cacheKey = `user:${userId}:profile`;
let profile = await redis.get(cacheKey);

if (!profile) {
  profile = await db.users.findById(userId);
  await redis.setex(cacheKey, 300, JSON.stringify(profile)); // 5 min TTL
}

// Layer 3: Database query caching
// PostgreSQL prepared statements, query plan caching

// Layer 4: Application-level caching
const userCache = new LRU({ max: 1000 });
```

### Cache Invalidation Patterns

```typescript
// Write-through: Update cache on write
async updateUser(id: string, data: UpdateUserDto) {
  const user = await db.users.update(id, data);
  await redis.set(`user:${id}`, JSON.stringify(user), 'EX', 300);
  return user;
}

// Write-behind: Invalidate cache, lazy load
async updateUser(id: string, data: UpdateUserDto) {
  const user = await db.users.update(id, data);
  await redis.del(`user:${id}`); // Delete, will reload on next read
  return user;
}

// Event-based: Invalidate related caches
eventBus.on('user.updated', async ({ userId }) => {
  await Promise.all([
    redis.del(`user:${userId}`),
    redis.del(`user:${userId}:posts`),
    redis.del(`user:${userId}:followers`),
  ]);
});
```

## Deployment Strategy

### Environment Progression

```
Development → Staging → Production

Development:
- Local dev servers
- Docker Compose for dependencies
- Hot reload enabled
- Debug logging
- Relaxed security

Staging:
- Production-like environment
- Real integrations (test mode)
- E2E tests run here
- Performance testing
- Security scanning

Production:
- High availability setup
- Blue-green deployment
- Monitoring & alerting
- Automated rollback
- Strict security
```

### Deployment Patterns

| Pattern | Downtime | Rollback | Complexity | Use When |
|---------|----------|----------|------------|----------|
| **Recreate** | Yes | Manual | Low | Dev/staging only |
| **Rolling** | No | Gradual | Medium | Standard deployments |
| **Blue-Green** | No | Instant | Medium | Zero-downtime required |
| **Canary** | No | Gradual | High | High-risk changes |
| **A/B Testing** | No | Gradual | High | Feature validation |

## Quick Decision Trees

### "Which database should I use?"
```
Need ACID transactions? → PostgreSQL
NoSQL with flexible schema? → MongoDB
Caching/sessions/queues? → Redis
AWS serverless? → DynamoDB
High read throughput? → PostgreSQL + read replicas
```

### "Monolith or microservices?"
```
New product? → Modular monolith
Team < 10 people? → Modular monolith
Clear bounded contexts? → Consider microservices
Different scaling needs? → Microservices
Limited DevOps resources? → Monolith
```

### "REST or GraphQL?"
```
Simple CRUD? → REST
Mobile app with flexible queries? → GraphQL
Public API? → REST
Complex data requirements? → GraphQL
Team knows GraphQL? → GraphQL, otherwise REST
```

### "Which state management?"
```
Simple app, few global state? → React Context
Server state (API data)? → TanStack Query
Medium complexity? → Zustand
Complex state logic? → Redux Toolkit
Real-time updates? → Zustand + WebSocket
```
