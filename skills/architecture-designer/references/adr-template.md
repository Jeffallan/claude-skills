# ADR Template

> Reference for: Architecture Designer
> Load when: Documenting architectural decisions

## ADR Format

```markdown
# ADR-{number}: {Title}

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
[Describe the situation and forces at play. What is the problem?
What constraints exist? What are we trying to achieve?]

## Decision
[State the decision clearly. What are we going to do?]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Drawback 1]
- [Drawback 2]

### Neutral
- [Side effect that is neither good nor bad]

## Alternatives Considered
[What other options were evaluated and why were they rejected?]

## References
- [Link to relevant documentation]
- [Link to discussion/RFC]
```

## Example: Database Selection

```markdown
# ADR-001: Use PostgreSQL for primary database

## Status
Accepted

## Context
We need a relational database for our e-commerce platform that:
- Handles complex transactions with strong consistency
- Supports JSON for flexible product attributes
- Scales to millions of products and orders
- Works well with our existing Python/Node stack

Team has experience with PostgreSQL and MySQL.
Budget allows for managed database service.

## Decision
Use PostgreSQL as the primary database, hosted on AWS RDS.

## Consequences

### Positive
- ACID compliance for financial transactions
- Rich feature set (JSON, full-text search, CTEs)
- Strong community and tooling
- Excellent performance with proper indexing
- Free and open source

### Negative
- Vertical scaling has limits (addressed with read replicas)
- Requires DBA expertise for optimization
- AWS RDS costs for high availability

### Neutral
- Team will need to learn PostgreSQL-specific features
- Migration from current SQLite dev database needed

## Alternatives Considered

**MySQL**
- Rejected: Less feature-rich for JSON operations
- Considered: Similar cost, familiar to team

**MongoDB**
- Rejected: Relational data model needed for orders/inventory
- Considered: Great for product catalog flexibility

**CockroachDB**
- Rejected: Higher cost, team unfamiliar
- Considered: Better horizontal scaling

## References
- https://www.postgresql.org/docs/current/
- Internal RFC: Database Selection for E-commerce Platform
```

## ADR Naming Convention

```
docs/
└── adr/
    ├── 0001-use-postgresql-database.md
    ├── 0002-adopt-microservices.md
    ├── 0003-implement-event-sourcing.md
    └── README.md
```

## Quick Reference

| Section | Purpose | Key Question |
|---------|---------|--------------|
| Status | Current state | Is this active? |
| Context | Background | Why are we deciding? |
| Decision | The choice | What did we choose? |
| Consequences | Impact | What happens now? |
| Alternatives | Options | What else was considered? |
