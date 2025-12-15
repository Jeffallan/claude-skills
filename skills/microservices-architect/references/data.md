# Data Management in Microservices

Comprehensive guide for managing data across distributed services.

## Fundamental Principles

### Database per Service

**Core Principle:** Each microservice owns its data exclusively.

**Rules:**
```
✓ DO:
- Each service has its own database/schema
- Service owns all CRUD operations on its data
- Other services access data via APIs only
- Service can choose its own database technology

✗ DON'T:
- Share database between services
- Direct database queries across services
- Shared tables or schemas
- Database-level joins across services
```

**Implementation Options:**

**1. Separate Database Instances:**
```
UserService → PostgreSQL instance 1
OrderService → PostgreSQL instance 2
InventoryService → PostgreSQL instance 3

Pros:
- Complete isolation
- Independent scaling
- No shared resource contention

Cons:
- Higher infrastructure cost
- More operational overhead
```

**2. Separate Schemas:**
```
Same PostgreSQL instance:
- Schema: user_service
- Schema: order_service
- Schema: inventory_service

Pros:
- Lower cost
- Easier local development

Cons:
- Shared resource (CPU, memory)
- Not true isolation
- Scaling limitations

Recommendation: Use separate schemas for dev/test, separate instances for production
```

**3. Polyglot Persistence:**
```
Each service chooses optimal database:

UserService → PostgreSQL
  (Relational data, ACID transactions)

ProductCatalog → Elasticsearch
  (Full-text search, faceted navigation)

SessionStore → Redis
  (Fast key-value, TTL support)

EventLog → Kafka
  (Event streaming, replay)

RecommendationEngine → MongoDB
  (Flexible schema, denormalized data)

Benefits: Right tool for the job
Challenges: Multiple technologies to manage
```

## Data Consistency Patterns

### Strong Consistency vs Eventual Consistency

**Strong Consistency:**
```
Definition: Read after write returns latest value

Requires:
- Distributed transaction (2PC, 3PC)
- Coordination across services
- Blocking operations

Cost:
- Higher latency
- Reduced availability (CAP theorem)
- Complexity

When to Use:
- Financial transactions
- Inventory reservations
- Critical business operations
- Regulatory requirements
```

**Eventual Consistency:**
```
Definition: System converges to consistent state over time

Characteristics:
- Temporary inconsistencies acceptable
- Non-blocking operations
- Higher availability
- Lower latency

Example:
1. Order placed (OrderService)
2. Immediately return success to user
3. Event published: order.created
4. InventoryService eventually processes event
5. Stock count updated (few milliseconds later)

When to Use:
- Social media feeds
- Analytics dashboards
- Recommendation systems
- Non-critical updates
```

### Managing Cross-Service Data

**Problem:** Order service needs customer data owned by User service.

**Anti-Pattern Solutions:**
```
✗ Direct database access
✗ Shared database
✗ Database replication between services
```

**Proper Solutions:**

**1. API Composition:**
```
Client Query: Get order with customer details

API Gateway:
1. GET /orders/123 from OrderService
   Response: { orderId: 123, customerId: 456, items: [...] }

2. GET /customers/456 from UserService
   Response: { customerId: 456, name: "John", email: "john@example.com" }

3. Combine responses and return to client

Pros:
- Maintains service boundaries
- Real-time data

Cons:
- Multiple network calls (latency)
- Partial failure handling complex
- N+1 query problem
```

**2. Data Replication via Events:**
```
OrderService maintains denormalized customer data:

CREATE TABLE orders (
    order_id UUID PRIMARY KEY,
    customer_id UUID,
    customer_name VARCHAR(255),  -- Denormalized
    customer_email VARCHAR(255), -- Denormalized
    order_total DECIMAL,
    created_at TIMESTAMP
);

UserService publishes events:
- customer.created
- customer.updated
- customer.deleted

OrderService subscribes and updates local copy:

async def on_customer_updated(event):
    await db.execute(
        "UPDATE orders SET customer_name = $1, customer_email = $2 WHERE customer_id = $3",
        event.name, event.email, event.customer_id
    )

Pros:
- Fast queries (no joins across services)
- Resilient to UserService downtime

Cons:
- Eventual consistency
- Storage duplication
- Keeping data in sync
```

**3. CQRS with Shared Read Model:**
```
Write Models (Command Side):
- UserService writes to user_db
- OrderService writes to order_db

Read Model (Query Side):
- Dedicated database for queries
- Subscribes to events from both services
- Denormalized view for efficient queries

Example Read Model:
CREATE TABLE order_details_view (
    order_id UUID,
    customer_id UUID,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    items JSONB,
    order_total DECIMAL,
    order_status VARCHAR(50)
);

Pros:
- Optimized for queries
- No cross-service calls
- Can rebuild from events

Cons:
- Eventual consistency
- Additional infrastructure
- Event replay mechanism needed
```

## Distributed Transactions

### Two-Phase Commit (2PC)

**How It Works:**
```
Phase 1: Prepare
Coordinator asks all participants: "Can you commit?"
- Service A: YES
- Service B: YES
- Service C: YES

Phase 2: Commit
If all YES:
  Coordinator tells all: "Commit"
If any NO:
  Coordinator tells all: "Rollback"

Example:
Transfer $100 from Account A to Account B

Prepare:
- AccountService A: Can deduct $100? YES (balance sufficient)
- AccountService B: Can add $100? YES (account active)

Commit:
- AccountService A: Deduct $100 (committed)
- AccountService B: Add $100 (committed)
```

**Problems with 2PC:**
```
✗ Blocking protocol (participants wait for coordinator)
✗ Single point of failure (coordinator down = all blocked)
✗ Reduced availability
✗ Poor performance (synchronous coordination)
✗ Doesn't scale well

Recommendation: Avoid 2PC in microservices, use Saga pattern instead
```

### Saga Pattern (Recommended)

**Orchestration-Based Saga:**
```
Transfer Money Saga:

Steps:
1. Debit Account A
2. Credit Account B

Compensations:
1. Credit Account A (reverse debit)

Saga Orchestrator:
saga_state = {
    "saga_id": "saga-123",
    "status": "in_progress",
    "steps_completed": []
}

# Step 1
result1 = await account_service.debit(account_a, 100)
if not result1.success:
    return fail_saga("Insufficient funds")

saga_state["steps_completed"].append("debit_a")

# Step 2
result2 = await account_service.credit(account_b, 100)
if not result2.success:
    # Compensate step 1
    await account_service.credit(account_a, 100)
    return fail_saga("Account B invalid")

saga_state["status"] = "completed"
return success_saga()
```

**Saga State Persistence:**
```
CREATE TABLE saga_state (
    saga_id UUID PRIMARY KEY,
    saga_type VARCHAR(50),
    current_step INTEGER,
    max_steps INTEGER,
    status VARCHAR(20),
    payload JSONB,
    steps_completed JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

After each step:
UPDATE saga_state
SET
    current_step = current_step + 1,
    steps_completed = jsonb_array_append(steps_completed, 'step_name'),
    updated_at = NOW()
WHERE saga_id = $1;

On failure, load saga state and execute compensations
```

**Idempotency for Saga Steps:**
```
Each saga step must be idempotent:

Debit Operation:
async def debit_account(account_id, amount, saga_id):
    # Check if already processed
    existing = await db.fetchone(
        "SELECT * FROM transactions WHERE saga_id = $1 AND operation = 'debit'",
        saga_id
    )
    if existing:
        return {"success": True, "transaction_id": existing.id}

    # Process debit
    result = await db.execute(
        "UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1",
        amount, account_id
    )

    if result.rowcount == 0:
        return {"success": False, "error": "Insufficient funds"}

    # Record transaction
    await db.execute(
        "INSERT INTO transactions (saga_id, account_id, amount, operation) VALUES ($1, $2, $3, 'debit')",
        saga_id, account_id, amount
    )

    return {"success": True}

Compensating Operation:
async def compensate_debit(account_id, amount, saga_id):
    await credit_account(account_id, amount, saga_id)
```

## Event Sourcing

### Core Concepts

**Event Store:**
```
All state changes stored as immutable events

Example: Bank Account

Events:
1. AccountOpened { accountId: "acc-123", customerId: "cust-456", initialBalance: 0 }
2. MoneyDeposited { accountId: "acc-123", amount: 1000, timestamp: "2025-01-15T10:00:00Z" }
3. MoneyWithdrawn { accountId: "acc-123", amount: 200, timestamp: "2025-01-16T14:30:00Z" }
4. MoneyDeposited { accountId: "acc-123", amount: 500, timestamp: "2025-01-17T09:15:00Z" }

Current Balance = 0 + 1000 - 200 + 500 = 1300

Replay all events to reconstruct current state
```

**Event Schema:**
```json
{
  "eventId": "evt-789",
  "aggregateId": "acc-123",
  "aggregateType": "BankAccount",
  "eventType": "MoneyDeposited",
  "eventVersion": "1.0",
  "timestamp": "2025-01-15T10:00:00Z",
  "correlationId": "corr-456",
  "causationId": "cmd-123",
  "payload": {
    "amount": 1000,
    "currency": "USD",
    "source": "wire_transfer"
  },
  "metadata": {
    "userId": "user-789",
    "ipAddress": "192.168.1.1"
  }
}
```

### Snapshots

**Problem:** Replaying thousands of events is slow.

**Solution:** Periodic snapshots.

```
Event Stream:
1. AccountOpened (version 1)
2. MoneyDeposited (version 2)
...
1000. MoneyDeposited (version 1000)
[SNAPSHOT at version 1000: balance = $50,000]
1001. MoneyWithdrawn (version 1001)
...
1500. MoneyDeposited (version 1500)

To get current state:
1. Load snapshot at version 1000 (balance = $50,000)
2. Replay events 1001-1500 (only 500 events)

Much faster than replaying all 1500 events

Snapshot Strategy:
- Every 100 events
- Or every 24 hours
- Async background process
```

**Snapshot Table:**
```sql
CREATE TABLE snapshots (
    aggregate_id UUID,
    aggregate_type VARCHAR(50),
    version INTEGER,
    state JSONB,
    created_at TIMESTAMP,
    PRIMARY KEY (aggregate_id, version)
);

CREATE INDEX idx_latest_snapshot ON snapshots(aggregate_id, version DESC);
```

### Event Schema Evolution

**Challenge:** Events are immutable, but requirements change.

**Strategies:**

**1. Event Versioning:**
```
Version 1:
{
  "eventType": "OrderPlaced",
  "eventVersion": "1.0",
  "payload": {
    "orderId": "123",
    "amount": 99.99
  }
}

Version 2 (added customer email):
{
  "eventType": "OrderPlaced",
  "eventVersion": "2.0",
  "payload": {
    "orderId": "123",
    "amount": 99.99,
    "customerEmail": "customer@example.com"
  }
}

Event Handler:
def handle_order_placed(event):
    if event.eventVersion == "1.0":
        # Handle old format
        process_order_v1(event.payload)
    elif event.eventVersion == "2.0":
        # Handle new format
        process_order_v2(event.payload)
```

**2. Event Upcasting:**
```
Transform old events to new format during replay:

def upcast_event(event):
    if event.eventType == "OrderPlaced" and event.eventVersion == "1.0":
        # Transform to v2.0
        return {
            "eventType": "OrderPlaced",
            "eventVersion": "2.0",
            "payload": {
                **event.payload,
                "customerEmail": "unknown@example.com"  # Default value
            }
        }
    return event
```

**3. Event Transformation:**
```
Create new event types, keep old ones for historical accuracy:

Old: OrderPlaced
New: OrderPlacedV2

Projections handle both:
- Old events for historical data
- New events for current processing
```

## Data Synchronization

### Change Data Capture (CDC)

**Purpose:** Capture database changes and publish as events.

**How It Works:**
```
Database transaction log → CDC Tool → Event Stream

Example with Debezium:

PostgreSQL:
INSERT INTO orders (id, customer_id, total) VALUES (123, 456, 99.99);

Debezium captures:
{
  "before": null,
  "after": {
    "id": 123,
    "customer_id": 456,
    "total": 99.99,
    "created_at": "2025-01-15T10:00:00Z"
  },
  "op": "c",  // create
  "ts_ms": 1705314000000
}

Published to Kafka topic: postgres.public.orders

Other services subscribe and update their read models
```

**Benefits:**
```
✓ No application code changes
✓ Guaranteed delivery (based on database transaction log)
✓ Captures all changes (even from direct DB access)
✓ Low latency
✓ Ordering preserved

Use Cases:
- Keep search index synchronized
- Update cache automatically
- Replicate to data warehouse
- Trigger workflows on database changes
```

### Materialized Views

**Purpose:** Pre-computed denormalized views for fast queries.

**Pattern:**
```
Event-Driven Materialized View:

1. Services publish domain events
2. View service subscribes to events
3. Updates materialized view in real-time

Example: Order Summary View

Events:
- order.created
- order.payment_received
- order.shipped
- order.delivered

Materialized View:
CREATE TABLE order_summary (
    order_id UUID PRIMARY KEY,
    customer_id UUID,
    customer_name VARCHAR(255),
    order_date TIMESTAMP,
    total_amount DECIMAL,
    status VARCHAR(50),
    items_count INTEGER,
    last_updated TIMESTAMP
);

View Service:
async def on_order_created(event):
    await db.execute(
        "INSERT INTO order_summary (order_id, customer_id, status, ...) VALUES (...)",
        event.data
    )

async def on_order_shipped(event):
    await db.execute(
        "UPDATE order_summary SET status = 'shipped', last_updated = NOW() WHERE order_id = $1",
        event.order_id
    )
```

## Data Partitioning

### Horizontal Partitioning (Sharding)

**When to Use:**
```
- Single database can't handle load
- Data size exceeds single server capacity
- Want to distribute geographically
```

**Sharding Strategies:**

**1. Hash-Based Sharding:**
```
Shard = hash(customer_id) % num_shards

customer_id: cust-123 → hash → 7234 → mod 4 → Shard 2
customer_id: cust-456 → hash → 9812 → mod 4 → Shard 0

Pros:
- Even distribution
- Simple to implement

Cons:
- Adding shards requires re-sharding
- Range queries difficult
```

**2. Range-Based Sharding:**
```
Shard 0: customer_id 0-999
Shard 1: customer_id 1000-1999
Shard 2: customer_id 2000-2999

Pros:
- Range queries efficient
- Easy to add shards

Cons:
- Uneven distribution (hotspots)
- Requires shard map
```

**3. Geography-Based Sharding:**
```
Shard US: customers in USA
Shard EU: customers in Europe
Shard APAC: customers in Asia-Pacific

Pros:
- Data locality (GDPR compliance)
- Lower latency

Cons:
- Uneven distribution
- Cross-shard queries complex
```

**Shard Management:**
```
Shard Map Service:

GET /shard-location?customer_id=cust-123
Response: { "shard": "shard-2", "endpoint": "db2.example.com" }

Application logic:
customer_id = request.customer_id
shard_info = await shard_map.get_shard(customer_id)
db_connection = connection_pool.get(shard_info.endpoint)
result = await db_connection.query("SELECT * FROM customers WHERE id = $1", customer_id)
```

## Summary

Data management in microservices requires careful design:

**Key Principles:**
- Database per service (non-negotiable)
- Embrace eventual consistency where possible
- Use Saga pattern for distributed transactions
- Event sourcing for audit trail and temporal queries
- CQRS for read/write optimization
- CDC for data synchronization

**Decision Framework:**
- Strong consistency → Saga with careful compensation logic
- Audit trail → Event sourcing
- Complex queries → CQRS with read models
- Large scale → Sharding with appropriate strategy

Always design for failure: compensating transactions, idempotent operations, and proper monitoring are essential.
