---
name: Architecture Designer
description: Expert in software architecture, system design, design patterns, and architectural decision making. Use when designing systems, choosing architectures, evaluating trade-offs, creating technical designs, or when the user mentions architecture, system design, design patterns, scalability, or architectural decisions.
---

# Architecture Designer

Expert in designing scalable, maintainable software architectures and making sound architectural decisions.

## Instructions

### Core Workflow

1. **Understand requirements**
   - Functional requirements
   - Non-functional requirements (performance, scalability, security)
   - Constraints (budget, timeline, team skills)
   - Future growth expectations

2. **Design approach**
   - Choose architectural style (monolith, microservices, serverless, etc.)
   - Define components and boundaries
   - Design data flow and storage
   - Plan for scalability and resilience

3. **Document decisions**
   - Create Architecture Decision Records (ADRs)
   - Document trade-offs
   - Create diagrams (C4, UML, etc.)
   - Define interfaces and contracts

4. **Validate design**
   - Review against requirements
   - Consider failure modes
   - Estimate costs
   - Get stakeholder buy-in

### Architectural Styles

#### Monolithic Architecture
**Pros**: Simple to develop/deploy, easy transactions, straightforward testing
**Cons**: Scaling challenges, technology lock-in, can become complex
**Use when**: Small teams, simple domains, MVP/prototypes

#### Microservices Architecture
**Pros**: Independent scaling, technology flexibility, fault isolation
**Cons**: Distributed complexity, operational overhead, data consistency challenges
**Use when**: Large teams, complex domains, need independent scaling

#### Serverless Architecture
**Pros**: No server management, auto-scaling, pay-per-use
**Cons**: Cold starts, vendor lock-in, debugging challenges
**Use when**: Variable load, event-driven, want to minimize ops

#### Event-Driven Architecture
**Pros**: Loose coupling, scalability, flexibility
**Cons**: Complexity, eventual consistency, debugging
**Use when**: Async operations, multiple consumers, real-time needs

### Design Patterns

#### Repository Pattern
```typescript
interface UserRepository {
  findById(id: string): Promise<User | null>;
  findAll(): Promise<User[]>;
  save(user: User): Promise<User>;
  delete(id: string): Promise<void>;
}

class PostgresUserRepository implements UserRepository {
  constructor(private db: Database) {}

  async findById(id: string): Promise<User | null> {
    const result = await this.db.query('SELECT * FROM users WHERE id = $1', [id]);
    return result.rows[0] || null;
  }

  // ... other methods
}
```

#### Factory Pattern
```typescript
interface DatabaseConnection {
  connect(): Promise<void>;
  query(sql: string): Promise<any>;
}

class DatabaseFactory {
  static create(type: 'postgres' | 'mysql'): DatabaseConnection {
    switch (type) {
      case 'postgres':
        return new PostgresConnection();
      case 'mysql':
        return new MySQLConnection();
      default:
        throw new Error('Unknown database type');
    }
  }
}
```

#### Strategy Pattern
```typescript
interface PaymentStrategy {
  pay(amount: number): Promise<void>;
}

class CreditCardPayment implements PaymentStrategy {
  async pay(amount: number) {
    // Credit card payment logic
  }
}

class PayPalPayment implements PaymentStrategy {
  async pay(amount: number) {
    // PayPal payment logic
  }
}

class PaymentProcessor {
  constructor(private strategy: PaymentStrategy) {}

  async processPayment(amount: number) {
    await this.strategy.pay(amount);
  }
}
```

### Architecture Decision Records (ADR)

```markdown
# ADR 001: Use PostgreSQL for Primary Database

## Status
Accepted

## Context
We need to choose a database for our application that handles:
- Complex queries and joins
- ACID transactions
- JSON data support
- Strong consistency

## Decision
We will use PostgreSQL as our primary database.

## Consequences

### Positive
- Strong ACID guarantees
- Excellent JSON support (JSONB)
- Rich query capabilities
- Proven scalability
- Strong community support

### Negative
- More complex than NoSQL for simple use cases
- Scaling writes requires partitioning
- Higher operational overhead than managed NoSQL

### Neutral
- Team has moderate PostgreSQL experience
- Will need to invest in PostgreSQL training

## Alternatives Considered
- MongoDB: Better for unstructured data, but weaker consistency
- MySQL: Similar to PostgreSQL, but weaker JSON support
- DynamoDB: Great scalability, but limited query capabilities
```

### Scalability Patterns

#### Horizontal Scaling
- Load balancer + multiple instances
- Stateless services
- Shared nothing architecture

#### Vertical Scaling
- Increase instance resources
- Limited by hardware
- Simple but has ceiling

####Database Scaling
- Read replicas
- Sharding
- CQRS (Command Query Responsibility Segregation)

#### Caching Strategy
```
Client -> CDN (static assets)
       -> Application Cache (Redis)
       -> Database Cache
       -> Database
```

### Resilience Patterns

#### Circuit Breaker
```typescript
class CircuitBreaker {
  private failureCount = 0;
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  private lastFailureTime?: number;

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime! > 60000) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await operation();
      if (this.state === 'HALF_OPEN') {
        this.state = 'CLOSED';
        this.failureCount = 0;
      }
      return result;
    } catch (error) {
      this.failureCount++;
      this.lastFailureTime = Date.now();

      if (this.failureCount >= 5) {
        this.state = 'OPEN';
      }

      throw error;
    }
  }
}
```

#### Retry with Exponential Backoff
```typescript
async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;

      const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Critical Rules

### Always Do
- Document architectural decisions (ADRs)
- Consider non-functional requirements
- Design for failure
- Keep it simple (YAGNI - You Aren't Gonna Need It)
- Plan for observability
- Consider team skills and size
- Evaluate trade-offs explicitly
- Design for testability
- Consider security from the start
- Plan for data consistency

### Never Do
- Never over-engineer for hypothetical requirements
- Never ignore operational complexity
- Never skip documentation
- Never choose architecture based on hype
- Never ignore cost implications
- Never forget about the team maintaining it
- Never assume perfect network/infrastructure

## Knowledge Base

- **Patterns**: GoF patterns, Enterprise patterns, Cloud patterns
- **Styles**: Monolith, Microservices, Serverless, Event-Driven
- **Principles**: SOLID, DRY, KISS, YAGNI
- **CAP Theorem**: Consistency, Availability, Partition Tolerance
- **Tools**: C4 diagrams, UML, Architecture Decision Records

## Best Practices Summary

1. **Requirements First**: Understand before designing
2. **Simplicity**: Start simple, evolve as needed
3. **Documentation**: ADRs for all major decisions
4. **Trade-offs**: Document pros/cons explicitly
5. **Resilience**: Design for failure
6. **Scalability**: Plan for growth
7. **Security**: Consider from the start
8. **Observability**: Build it in
9. **Team**: Match architecture to team capabilities
10. **Evolution**: Architecture evolves, plan for change
