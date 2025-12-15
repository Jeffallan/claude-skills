# Microservices Architect Skill

Senior distributed systems architect specializing in cloud-native microservices architectures, resilience patterns, and operational excellence.

## Overview

This skill provides comprehensive guidance for designing, implementing, and operating microservices-based systems. It covers service decomposition strategies, communication patterns, data management, resilience patterns, and observability practices.

## When to Use

Invoke this skill when working on:

- Decomposing monolithic applications into microservices
- Defining service boundaries using domain-driven design
- Designing inter-service communication (REST, gRPC, events)
- Implementing distributed transaction patterns (Saga, CQRS)
- Setting up service mesh architectures (Istio, Linkerd)
- Establishing resilience patterns (circuit breakers, retries, bulkheads)
- Building event-driven architectures with message queues
- Implementing distributed tracing and observability
- Managing data consistency across services
- Designing for high availability and fault tolerance

## Key Concepts

### Service Decomposition
- Domain-driven design and bounded contexts
- Service sizing guidelines (avoiding nano-services and distributed monoliths)
- Strangler fig pattern for monolith migration
- Team topology alignment (Conway's Law)

### Communication Patterns
- Synchronous (REST, gRPC, GraphQL)
- Asynchronous (message queues, event streaming)
- Request/response, fire-and-forget, choreography, orchestration
- Protocol selection guidance

### Resilience Patterns
- Circuit breakers for cascading failure prevention
- Retry strategies with exponential backoff and jitter
- Bulkhead pattern for resource isolation
- Timeout configuration at all levels
- Health checks and graceful degradation

### Data Management
- Database per service pattern
- Event sourcing and CQRS
- Distributed transactions with Saga pattern
- Change data capture (CDC)
- Data partitioning and sharding strategies

### Observability
- The three pillars: metrics, logs, distributed tracing
- SLI/SLO/SLA definitions and error budgets
- Alerting strategies and runbook development
- Incident response workflows

## Reference Files

| File | Purpose | Key Topics |
|------|---------|------------|
| `decomposition.md` | Service boundaries | DDD, bounded contexts, service sizing, strangler pattern |
| `communication.md` | Inter-service communication | REST vs gRPC, sync vs async, event-driven architecture |
| `patterns.md` | Resilience patterns | Circuit breakers, saga, retry, bulkhead, timeout |
| `data.md` | Data management | Database per service, event sourcing, CQRS, CDC |
| `observability.md` | Monitoring and tracing | Metrics, logs, traces, SLOs, alerting |

## Architecture Principles

### Must Do
- Apply domain-driven design for service boundaries
- Use database per service pattern (no shared databases)
- Implement circuit breakers for all external calls
- Add correlation IDs to trace requests across services
- Use asynchronous communication for cross-aggregate operations
- Design for failure with graceful degradation
- Implement comprehensive health checks
- Use API versioning from the start

### Must Not Do
- Create distributed monoliths (services that must deploy together)
- Share databases between services
- Use synchronous calls for long-running operations
- Skip distributed tracing implementation
- Ignore network latency and partial failures
- Create chatty interfaces requiring many round trips
- Store shared state without proper consistency patterns
- Deploy to production without observability

## Technology Stack

### Service Communication
- REST APIs with proper versioning
- gRPC for low-latency internal communication
- GraphQL Federation for aggregation
- Apache Kafka or RabbitMQ for async messaging
- NATS for lightweight pub/sub

### Service Mesh
- Istio (feature-rich, complex)
- Linkerd (lightweight, simpler)
- Consul Connect (service discovery + mesh)

### Observability
- Prometheus (metrics collection)
- Grafana (visualization)
- Jaeger or Zipkin (distributed tracing)
- ELK Stack or Loki (log aggregation)
- OpenTelemetry (instrumentation standard)

### Container Orchestration
- Kubernetes (de facto standard)
- Docker Swarm (simpler alternative)
- Amazon ECS/Fargate (managed containers)

## Common Patterns

### Service Discovery
Services register themselves and discover other services dynamically rather than using hard-coded endpoints.

### API Gateway
Single entry point for external clients that routes requests to appropriate microservices, handles cross-cutting concerns (auth, rate limiting, etc.).

### Saga Pattern
Manage distributed transactions across services using either choreography (event-driven) or orchestration (centralized coordinator).

### Event Sourcing
Store all state changes as immutable events, reconstruct current state by replaying events.

### CQRS
Separate read and write models, optimize each for its specific use case.

### Circuit Breaker
Prevent cascading failures by failing fast when a dependency is unhealthy.

## Decision Framework

### When to Use Microservices
- Large, complex domains requiring independent scaling
- Multiple teams working on different features
- Different parts need different technologies
- High availability requirements with isolated failures
- Rapid, independent deployment cadence needed

### When NOT to Use Microservices
- Small applications or startups (overhead too high)
- Team lacks distributed systems experience
- Network is unreliable or latency-sensitive
- Strong consistency required everywhere
- Operations team can't handle complexity

### Synchronous vs Asynchronous
- Synchronous: User waiting, simple request/response, low latency possible
- Asynchronous: Long-running operations, multiple consumers, decoupling needed

### Saga vs 2PC
- Saga: Eventual consistency acceptable, better availability, scalable
- 2PC: Strong consistency required (avoid in microservices if possible)

## Related Skills

- **DevOps Engineer** - CI/CD pipelines and container orchestration
- **Kubernetes Specialist** - Advanced Kubernetes patterns and operators
- **GraphQL Architect** - Federation for distributed schemas
- **Architecture Designer** - High-level system design
- **Monitoring Expert** - Observability stack implementation

## Best Practices

1. Start with a modular monolith, decompose when needed
2. Define clear service boundaries using domain-driven design
3. Each service owns its data completely (database per service)
4. Use asynchronous communication for cross-aggregate operations
5. Implement circuit breakers and retries with exponential backoff
6. Add distributed tracing from day one
7. Define SLOs and track error budgets
8. Design for failure - chaos engineering and fault injection testing
9. Automate everything - deployment, testing, monitoring
10. Document service contracts and maintain them

## Getting Started

For a new microservices project:

1. **Domain Analysis** - Event storming workshop to identify bounded contexts
2. **Service Boundaries** - Define initial service boundaries based on DDD
3. **Communication Design** - Choose protocols and patterns (REST/gRPC/events)
4. **Data Strategy** - Plan database per service, event schemas
5. **Infrastructure** - Set up Kubernetes, service mesh, observability stack
6. **Implementation** - Build services with resilience patterns built-in
7. **Testing** - Unit, integration, contract tests, chaos engineering
8. **Deployment** - Progressive delivery with canary deployments
9. **Monitoring** - Dashboards, alerts, runbooks
10. **Iteration** - Continuously improve based on production feedback

## Additional Resources

- "Building Microservices" by Sam Newman
- "Designing Data-Intensive Applications" by Martin Kleppmann
- "Domain-Driven Design" by Eric Evans
- "Release It!" by Michael Nygard
- "Site Reliability Engineering" by Google
- Martin Fowler's blog on microservices patterns
- microservices.io pattern catalog

## Contributing

This skill is maintained as part of the claude-skills repository. Contributions welcome for:
- Additional patterns and anti-patterns
- Real-world case studies
- Tool comparisons and recommendations
- Updated best practices as ecosystem evolves
