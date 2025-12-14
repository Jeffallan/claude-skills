# System Design Template

> Reference for: Architecture Designer
> Load when: Designing new systems

## Design Template

```markdown
# System: {System Name}

## Requirements

### Functional
- [What the system must do]
- [Core features and capabilities]

### Non-Functional
- **Performance**: Response time < 200ms p95
- **Availability**: 99.9% uptime (8.76 hours downtime/year)
- **Scalability**: Support 10,000 concurrent users
- **Security**: PCI DSS compliance required

### Constraints
- Budget: $X/month for infrastructure
- Timeline: MVP in 3 months
- Team: 5 backend, 3 frontend engineers

## High-Level Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Gateway │────▶│  Service    │
│   (Web)     │     │   (Kong)    │     │  (Node.js)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Auth     │     │  Database   │
                    │  (Auth0)    │     │ (PostgreSQL)│
                    └─────────────┘     └─────────────┘
```

## Component Details

### API Layer
- Technology: Node.js with Express/NestJS
- Responsibilities: Request routing, validation, auth
- Scaling: Horizontal via load balancer

### Data Layer
- Primary: PostgreSQL (transactions, relationships)
- Cache: Redis (sessions, hot data)
- Storage: S3 (files, images)

### External Services
- Auth: Auth0 (SSO, MFA)
- Email: SendGrid (transactional)
- Monitoring: Datadog (APM, logs)

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| PostgreSQL over MongoDB | Relational data, ACID needed |
| Redis for caching | Sub-ms latency required |
| Auth0 over custom | Reduce security risk |

## Scaling Strategy

### Current (MVP)
- Single region deployment
- 2 API instances behind ALB
- Single RDS instance

### Future (10x growth)
- Multi-region with CDN
- Auto-scaling API (2-10 instances)
- RDS read replicas

## Security Considerations
- All traffic over TLS 1.3
- JWT tokens with 15-min expiry
- Rate limiting: 100 req/min per user
- WAF for common attacks

## Failure Modes

| Failure | Impact | Mitigation |
|---------|--------|------------|
| DB down | Full outage | Multi-AZ failover |
| Cache down | Degraded perf | Fallback to DB |
| Auth down | No new logins | Cache valid tokens |
```

## Quick Reference

| Section | Key Questions |
|---------|---------------|
| Requirements | What must it do? How well? |
| Architecture | What components? How connected? |
| Decisions | Why these choices? |
| Scaling | How to grow? |
| Failures | What can break? How to recover? |
