# Non-Functional Requirements Checklist

> Reference for: Architecture Designer
> Load when: Gathering system requirements

## NFR Categories

### Scalability

| Question | Common Targets |
|----------|----------------|
| Expected concurrent users? | 100 / 1K / 10K / 100K |
| Requests per second? | 10 / 100 / 1000 / 10000 |
| Data volume? | GB / TB / PB |
| Growth rate? | 10% / 50% / 100% per year |
| Peak vs average load? | 2x / 5x / 10x |

### Performance

| Question | Common Targets |
|----------|----------------|
| API response time? | < 100ms / 200ms / 500ms p95 |
| Page load time? | < 1s / 2s / 3s |
| Database query time? | < 10ms / 50ms / 100ms |
| Batch processing throughput? | 1K / 10K / 100K records/hour |

### Availability

| Target | Downtime/Year | Use Case |
|--------|---------------|----------|
| 99% | 3.65 days | Internal tools |
| 99.9% | 8.76 hours | Business apps |
| 99.95% | 4.38 hours | E-commerce |
| 99.99% | 52.6 minutes | Financial systems |
| 99.999% | 5.26 minutes | Life-critical |

### Security

| Question | Considerations |
|----------|----------------|
| Authentication required? | JWT, OAuth, SAML, MFA |
| Authorization model? | RBAC, ABAC, ACL |
| Data sensitivity? | Public, internal, confidential, PII |
| Compliance requirements? | GDPR, HIPAA, PCI DSS, SOC 2 |
| Encryption needs? | At rest, in transit, end-to-end |

### Reliability

| Question | Considerations |
|----------|----------------|
| Acceptable data loss? | RPO: 0 / 1hr / 24hr |
| Recovery time target? | RTO: 1hr / 4hr / 24hr |
| Backup frequency? | Real-time / hourly / daily |
| Disaster recovery? | Single region / multi-region |

### Maintainability

| Question | Considerations |
|----------|----------------|
| Deployment frequency? | Daily / weekly / monthly |
| Deployment strategy? | Blue-green, canary, rolling |
| Monitoring requirements? | Logs, metrics, traces, alerts |
| On-call requirements? | 24/7, business hours |

### Cost

| Question | Considerations |
|----------|----------------|
| Infrastructure budget? | $/month, $/user, $/request |
| Operational budget? | FTE for maintenance |
| Cost optimization? | Reserved instances, spot instances |
| Cost alerts? | Thresholds for notification |

## Template

```markdown
## Non-Functional Requirements

### Performance
- API response time: < 200ms p95
- Page load time: < 2s
- Database query time: < 50ms

### Scalability
- Concurrent users: 10,000
- Requests per second: 1,000
- Data volume: 1TB

### Availability
- Target: 99.9% (8.76 hours/year downtime)
- RPO: 1 hour
- RTO: 4 hours

### Security
- Authentication: JWT with refresh tokens
- Authorization: Role-based (admin, user, guest)
- Compliance: GDPR, SOC 2

### Observability
- Logging: Structured JSON to ELK
- Metrics: Prometheus + Grafana
- Tracing: OpenTelemetry
- Alerts: PagerDuty integration
```

## Quick Reference

| Category | Key Metric |
|----------|------------|
| Performance | Response time (p95) |
| Scalability | Concurrent users, RPS |
| Availability | Uptime percentage |
| Reliability | RPO, RTO |
| Security | Compliance requirements |
| Cost | $/month budget |
