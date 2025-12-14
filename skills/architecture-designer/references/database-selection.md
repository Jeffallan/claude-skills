# Database Selection

> Reference for: Architecture Designer
> Load when: Choosing database technology

## Database Types

| Type | Examples | Best For |
|------|----------|----------|
| **Relational** | PostgreSQL, MySQL | Transactions, complex queries, relationships |
| **Document** | MongoDB, Firestore | Flexible schemas, rapid iteration |
| **Key-Value** | Redis, DynamoDB | Caching, sessions, high throughput |
| **Time-Series** | TimescaleDB, InfluxDB | Metrics, IoT, analytics |
| **Graph** | Neo4j, Neptune | Relationships, social networks |
| **Search** | Elasticsearch, Meilisearch | Full-text search, logs |

## Relational (PostgreSQL, MySQL)

```
Best For:
- Financial transactions (ACID compliance)
- Complex queries with joins
- Data integrity requirements
- Structured, predictable schemas

When to Avoid:
- Highly variable schemas
- Massive horizontal scaling needs
- Simple key-value access patterns
```

| Feature | PostgreSQL | MySQL |
|---------|------------|-------|
| JSON support | Excellent (JSONB) | Good (JSON) |
| Full-text search | Built-in | Basic |
| Extensions | Rich ecosystem | Limited |
| Replication | Streaming, logical | Statement, row-based |

## Document (MongoDB, Firestore)

```
Best For:
- Flexible, evolving schemas
- Hierarchical data (nested documents)
- Rapid prototyping
- Content management

When to Avoid:
- Complex transactions across documents
- Heavy relational queries
- Strict schema requirements
```

## Key-Value (Redis, DynamoDB)

```
Best For:
- Session storage
- Caching layer
- Real-time leaderboards
- Rate limiting counters

When to Avoid:
- Complex queries
- Relational data
- Large value sizes (>1MB)
```

## Time-Series (TimescaleDB, InfluxDB)

```
Best For:
- Metrics and monitoring
- IoT sensor data
- Financial tick data
- Event logging with timestamps

When to Avoid:
- Frequent updates to existing records
- Complex relational queries
- Non-time-based access patterns
```

## Decision Matrix

| Requirement | Recommended |
|-------------|-------------|
| ACID transactions | PostgreSQL, MySQL |
| Flexible schema | MongoDB, Firestore |
| High-speed caching | Redis |
| Time-series data | TimescaleDB, InfluxDB |
| Social relationships | Neo4j |
| Full-text search | Elasticsearch |
| Serverless scale | DynamoDB, Firestore |

## Quick Reference

| Question | If Yes → |
|----------|----------|
| Need ACID transactions? | Relational (PostgreSQL) |
| Schema changes frequently? | Document (MongoDB) |
| Sub-millisecond reads? | Key-Value (Redis) |
| Time-based queries? | Time-Series |
| Traversing relationships? | Graph (Neo4j) |
| Full-text search primary? | Elasticsearch |
