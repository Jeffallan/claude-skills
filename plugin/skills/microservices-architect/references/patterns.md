# Resilience and Reliability Patterns

Essential patterns for building fault-tolerant distributed systems.

## Resilience Patterns

### Circuit Breaker

**Purpose:** Prevent cascading failures by failing fast when a dependency is unhealthy.

**How It Works:**
```
States:
1. CLOSED (normal operation)
   - Requests pass through
   - Track failure rate
   - If failures exceed threshold → OPEN

2. OPEN (failing fast)
   - Immediately reject requests
   - Return fallback response
   - After timeout period → HALF_OPEN

3. HALF_OPEN (testing recovery)
   - Allow limited test requests
   - If successful → CLOSED
   - If failed → OPEN

Configuration:
- Failure threshold: 50% failures in 10 requests
- Timeout: 30 seconds in OPEN state
- Success threshold: 2 consecutive successes in HALF_OPEN
```

**Implementation Example:**
```python
# Using resilience4j-like pattern
@CircuitBreaker(
    name="payment-service",
    fallbackMethod="paymentFallback",
    failureThreshold=50,
    waitDurationInOpenState=30000,  # 30s
    permittedNumberOfCallsInHalfOpenState=3
)
async def process_payment(order_id: str, amount: float):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMENT_SERVICE_URL}/payments",
            json={"orderId": order_id, "amount": amount},
            timeout=5.0
        )
        return response.json()

async def paymentFallback(order_id: str, amount: float, exception):
    # Log the failure
    logger.error(f"Payment service unavailable: {exception}")
    # Return graceful degradation
    return {
        "status": "pending",
        "message": "Payment processing delayed, will retry"
    }
```

**When to Use:**
```
Apply circuit breakers to:
✓ External service calls
✓ Database queries
✓ Third-party APIs
✓ Microservice-to-microservice calls

Configuration Guidelines:
- Fast services (p99 < 100ms): 5s timeout, 10s circuit open
- Medium services (p99 < 1s): 10s timeout, 30s circuit open
- Slow services (p99 > 1s): 30s timeout, 60s circuit open
```

### Retry Pattern

**Purpose:** Handle transient failures by retrying operations.

**Strategies:**

**1. Exponential Backoff:**
```
Retry delays: 100ms, 200ms, 400ms, 800ms, 1600ms

Benefits:
- Reduces load during incidents
- Gives service time to recover
- Prevents thundering herd

Implementation:
attempts = 0
max_attempts = 5
base_delay = 0.1  # 100ms

while attempts < max_attempts:
    try:
        return await make_request()
    except TransientError as e:
        attempts += 1
        if attempts == max_attempts:
            raise
        delay = base_delay * (2 ** attempts) + random.uniform(0, 0.1)
        await asyncio.sleep(delay)
```

**2. Retry with Jitter:**
```
Why: Prevents synchronized retries (thundering herd)

Full Jitter:
delay = random.uniform(0, base_delay * (2 ** attempt))

Decorrelated Jitter:
delay = min(cap, random.uniform(base, previous_delay * 3))

Recommended: Decorrelated jitter for production systems
```

**3. Idempotency Keys:**
```
Problem: Retries can cause duplicate operations

Solution: Idempotency keys
POST /api/v1/payments
Headers:
  Idempotency-Key: uuid-12345

Server Logic:
1. Check if operation with this key already processed
2. If yes, return cached response
3. If no, process and cache result
4. Cache for 24 hours

Ensures safe retries even for non-idempotent operations
```

**Retry Best Practices:**
```
DO:
✓ Only retry transient errors (timeout, 503, 429)
✓ Use exponential backoff with jitter
✓ Set maximum retry attempts (3-5)
✓ Implement overall timeout
✓ Use idempotency keys for writes
✓ Log each retry attempt

DON'T:
✗ Retry client errors (400, 401, 404)
✗ Retry without backoff (causes load spikes)
✗ Infinite retries
✗ Retry non-idempotent operations without safeguards
```

### Bulkhead Pattern

**Purpose:** Isolate resources to prevent total system failure.

**Thread Pool Isolation:**
```
Concept: Separate thread pools for different operations

Example:
- Payment Service Thread Pool: 20 threads
- Inventory Service Thread Pool: 20 threads
- Notification Service Thread Pool: 10 threads

If payment service becomes slow:
- Only payment thread pool exhausted
- Inventory and notification still work
- System partially degraded, not completely down
```

**Connection Pool Isolation:**
```
Database Connection Pools:
- Read-only queries: 50 connections
- Write queries: 20 connections
- Reporting queries: 10 connections

Heavy reporting query won't starve transactional operations
```

**Rate Limiting per Tenant:**
```
Multi-tenant SaaS application:

tenant-a: 1000 requests/minute
tenant-b: 1000 requests/minute
tenant-c: 1000 requests/minute

If tenant-a floods the system:
- Only tenant-a throttled
- tenant-b and tenant-c unaffected
```

**Implementation:**
```python
# Using semaphores for concurrency limits
class BulkheadExecutor:
    def __init__(self):
        self.payment_semaphore = asyncio.Semaphore(20)
        self.inventory_semaphore = asyncio.Semaphore(20)
        self.notification_semaphore = asyncio.Semaphore(10)

    async def call_payment_service(self, data):
        async with self.payment_semaphore:
            return await payment_service.call(data)

    async def call_inventory_service(self, data):
        async with self.inventory_semaphore:
            return await inventory_service.call(data)
```

### Timeout Pattern

**Purpose:** Prevent indefinite waiting for responses.

**Timeout Types:**

**1. Connection Timeout:**
```
Time allowed to establish connection

Recommended: 2-5 seconds
If takes longer, network likely has issues

httpx.AsyncClient(timeout=httpx.Timeout(connect=3.0))
```

**2. Read Timeout:**
```
Time allowed to receive response after connection

Varies by service:
- Fast APIs: 5 seconds
- Database queries: 10 seconds
- Complex processing: 30 seconds

httpx.AsyncClient(timeout=httpx.Timeout(read=10.0))
```

**3. Total Timeout:**
```
Overall time budget for entire operation

Example: User checkout flow
- Total budget: 30 seconds
- Payment service: 10 seconds
- Inventory check: 5 seconds
- Order creation: 5 seconds
- Buffer: 10 seconds

async with asyncio.timeout(30):
    result = await complete_checkout()
```

**Timeout Best Practices:**
```
Timeouts Hierarchy:
Parent timeout > sum of child timeouts

Request → API Gateway (30s timeout)
  → Service A (10s timeout)
    → Service B (5s timeout)
      → Database (2s timeout)

Set timeouts everywhere:
✓ HTTP clients
✓ Database connections
✓ Message consumers
✓ gRPC calls
✓ Cache operations
```

## Distributed Transaction Patterns

### Saga Pattern

**Purpose:** Manage distributed transactions across services.

**Choreography-Based Saga:**
```
Example: Order Creation Saga

Events:
1. OrderService: order.created
2. PaymentService: payment.completed OR payment.failed
3. InventoryService: inventory.reserved OR inventory.reservation.failed
4. ShippingService: shipment.created

Compensating Transactions:
If inventory.reservation.failed:
  → PaymentService listens → refund.initiated
  → OrderService listens → order.cancelled

Pros:
- Decentralized
- No single point of failure
- Services autonomous

Cons:
- Difficult to track saga state
- Complex debugging
- No saga-wide timeout
```

**Orchestration-Based Saga:**
```
Example: Order Saga Orchestrator

Saga Steps:
1. Create Order (OrderService)
2. Charge Payment (PaymentService)
3. Reserve Inventory (InventoryService)
4. Create Shipment (ShippingService)

Orchestrator Logic:
step1_result = await order_service.create_order()
if not step1_result.success:
    return failure("Order creation failed")

step2_result = await payment_service.charge(amount)
if not step2_result.success:
    await order_service.cancel_order(step1_result.order_id)
    return failure("Payment failed")

step3_result = await inventory_service.reserve(items)
if not step3_result.success:
    await payment_service.refund(step2_result.payment_id)
    await order_service.cancel_order(step1_result.order_id)
    return failure("Inventory unavailable")

# Continue saga...

Pros:
- Clear workflow
- Centralized monitoring
- Easy to understand

Cons:
- Orchestrator complexity
- Potential bottleneck
- Coupling to orchestrator
```

**Saga State Management:**
```
Persist saga state to handle failures:

CREATE TABLE saga_instances (
    saga_id UUID PRIMARY KEY,
    saga_type VARCHAR(50),
    current_step VARCHAR(50),
    status VARCHAR(20),
    payload JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

On orchestrator restart:
- Load incomplete sagas
- Resume from last completed step
- Execute remaining steps or compensations
```

### Event Sourcing

**Purpose:** Store all state changes as events, derive current state by replaying.

**Implementation:**
```
Traditional Approach:
UPDATE orders SET status = 'shipped' WHERE id = 123;
(Lost: when shipped, by whom, from where)

Event Sourcing Approach:
Events:
1. OrderPlaced { orderId, customerId, items, timestamp }
2. PaymentReceived { orderId, amount, paymentId, timestamp }
3. OrderShipped { orderId, trackingNumber, carrier, timestamp }

Current state = replay all events
```

**Event Store:**
```
CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    aggregate_id UUID,
    aggregate_type VARCHAR(50),
    event_type VARCHAR(100),
    event_data JSONB,
    version INTEGER,
    timestamp TIMESTAMP,
    correlation_id UUID
);

CREATE INDEX idx_aggregate ON events(aggregate_id, version);

Guarantees:
- Events immutable
- Events ordered by version
- Optimistic locking prevents conflicts
```

**Benefits:**
```
✓ Full audit trail
✓ Time travel (replay to any point)
✓ Event replay for debugging
✓ Multiple read models from same events
✓ Temporal queries ("show orders as of yesterday")

Challenges:
✗ Eventual consistency
✗ Event schema evolution
✗ Snapshot strategy needed
✗ Increased storage
```

### CQRS (Command Query Responsibility Segregation)

**Purpose:** Separate read and write models for different optimization strategies.

**Architecture:**
```
Write Side (Command):
- Receives commands (CreateOrder, UpdateInventory)
- Validates business rules
- Stores events in event store
- Optimized for consistency and writes

Read Side (Query):
- Listens to events
- Updates denormalized read models
- Optimized for queries
- Eventual consistency

Example:
Command: CreateOrder
  → Order aggregate validates
  → Publishes OrderCreated event
  → Event stored in event store

Query Side:
  → Listens to OrderCreated
  → Updates order_summary table (denormalized)
  → Updates customer_order_history (different view)
  → Updates order_analytics (aggregated metrics)
```

**Read Models:**
```
Multiple specialized views from same events:

1. Order Detail View (for customer):
   { orderId, items, status, total, estimatedDelivery }

2. Order List View (for admin):
   { orderId, customerName, orderDate, status, total }

3. Analytics View:
   { date, totalOrders, totalRevenue, averageOrderValue }

Each optimized for specific query patterns
```

## Fault Tolerance Patterns

### Health Checks

**Types:**

**1. Liveness Probe:**
```
Purpose: Is the service alive?

Endpoint: GET /health/live

Returns 200 if:
- Application process running
- Not deadlocked

Kubernetes Action:
- If fails: Restart container
```

**2. Readiness Probe:**
```
Purpose: Is the service ready to receive traffic?

Endpoint: GET /health/ready

Returns 200 if:
- Database connection pool healthy
- Cache accessible
- Downstream dependencies responsive

Kubernetes Action:
- If fails: Remove from load balancer
- Don't send traffic until ready
```

**3. Startup Probe:**
```
Purpose: Has the service finished initialization?

Endpoint: GET /health/startup

For slow-starting applications:
- Prevents premature liveness checks
- Allows longer startup time
```

**Implementation:**
```python
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    checks = {
        "database": await check_database(),
        "cache": await check_cache(),
        "payment_service": await check_payment_service()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_healthy else "not ready", "checks": checks}
    )
```

### Graceful Degradation

**Purpose:** Provide reduced functionality when dependencies fail.

**Strategies:**

**1. Cached Responses:**
```
async def get_product_recommendations(user_id):
    try:
        async with circuit_breaker:
            return await ml_service.get_recommendations(user_id)
    except ServiceUnavailable:
        # Fallback to cached popular products
        return await cache.get_popular_products()
```

**2. Default Values:**
```
async def get_user_preferences(user_id):
    try:
        return await preferences_service.get(user_id)
    except ServiceUnavailable:
        # Return sensible defaults
        return {
            "language": "en",
            "currency": "USD",
            "theme": "light"
        }
```

**3. Feature Toggles:**
```
if feature_flags.is_enabled("personalized_recommendations"):
    recommendations = await ml_service.get_recommendations()
else:
    # Fallback to simple algorithm
    recommendations = await get_popular_products()
```

## Summary

Resilience patterns are mandatory in distributed systems. Layer multiple patterns for defense in depth:

**Essential Stack:**
1. Timeouts (prevent hanging)
2. Retries with backoff (handle transient errors)
3. Circuit breakers (prevent cascading failures)
4. Bulkheads (isolate failures)
5. Health checks (enable auto-healing)
6. Graceful degradation (maintain partial functionality)

**Choose Saga Pattern When:**
- Distributed transaction needed
- Strong consistency not required
- Compensating transactions possible

**Choose Event Sourcing When:**
- Full audit trail required
- Temporal queries needed
- Multiple read models beneficial

Always test failure scenarios. Use chaos engineering to validate resilience.
