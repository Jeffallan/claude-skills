# Inter-Service Communication Patterns

Comprehensive guide for designing communication between microservices.

## Communication Styles

### Synchronous Communication

**REST APIs:**
```
When to Use:
- Request/response pattern needed
- Client needs immediate result
- Simple CRUD operations
- Public-facing APIs

Design Principles:
- Resource-oriented URLs
- HTTP verbs (GET, POST, PUT, DELETE, PATCH)
- Stateless operations
- Idempotent operations where possible
- Proper status codes (200, 201, 400, 404, 500)

Example:
GET    /api/v1/orders/{orderId}
POST   /api/v1/orders
PUT    /api/v1/orders/{orderId}
DELETE /api/v1/orders/{orderId}
PATCH  /api/v1/orders/{orderId}/status
```

**gRPC:**
```
When to Use:
- Low-latency requirements
- Strong typing needed
- Streaming data
- Internal service-to-service calls
- Polyglot environments

Advantages:
- Binary protocol (faster than JSON)
- Built-in code generation
- Bi-directional streaming
- HTTP/2 multiplexing
- Strong schema enforcement via Protobuf

Example Proto:
service OrderService {
  rpc GetOrder(OrderRequest) returns (OrderResponse);
  rpc CreateOrder(CreateOrderRequest) returns (OrderResponse);
  rpc StreamOrders(StreamRequest) returns (stream OrderResponse);
}

message OrderRequest {
  string order_id = 1;
}

message OrderResponse {
  string order_id = 1;
  string status = 2;
  repeated OrderItem items = 3;
}
```

**GraphQL:**
```
When to Use:
- Frontend-driven data requirements
- Aggregating data from multiple services
- Flexible query requirements
- Reducing over-fetching/under-fetching

Federation Pattern:
- Each service owns its subdomain schema
- Gateway stitches schemas together
- Clients query unified API
- Services resolve their own fields

Example:
# User Service Schema
type User @key(fields: "id") {
  id: ID!
  name: String!
  email: String!
}

# Order Service Schema
extend type User @key(fields: "id") {
  id: ID! @external
  orders: [Order!]!
}
```

### Asynchronous Communication

**Message Queues (Point-to-Point):**
```
When to Use:
- Task distribution
- Load leveling
- Guaranteed delivery needed
- Single consumer per message

Examples:
- RabbitMQ with work queues
- AWS SQS
- Azure Service Bus Queues

Pattern:
Producer → Queue → Consumer
- Consumer acknowledges message
- Unacknowledged messages redelivered
- Dead letter queue for failures

Use Cases:
- Background job processing
- Email/SMS sending
- Image processing
- Report generation
```

**Event Streaming (Pub/Sub):**
```
When to Use:
- Multiple consumers need same event
- Event sourcing
- Real-time data pipelines
- Audit logging
- CQRS read model updates

Kafka Example:
Topics:
- order.created
- order.updated
- order.cancelled

Producers:
- OrderService publishes events

Consumers:
- NotificationService (send confirmation email)
- InventoryService (reserve stock)
- AnalyticsService (track metrics)
- WarehouseService (prepare shipment)

Each consumer processes independently
```

**Event-Driven Architecture:**
```
Event Types:

1. Domain Events:
   - order.placed
   - payment.completed
   - shipment.dispatched

   Characteristics:
   - Represent something that happened
   - Immutable
   - Past tense naming
   - Contain minimal necessary data

2. Integration Events:
   - Published across bounded contexts
   - Designed for external consumption
   - Schema versioned
   - Backward compatible

3. Command Events:
   - Imperative (do something)
   - Example: process.order, send.notification
   - Use sparingly (prefer domain events)

Event Schema Example:
{
  "eventId": "uuid",
  "eventType": "order.placed",
  "eventVersion": "1.0",
  "timestamp": "2025-12-14T10:00:00Z",
  "aggregateId": "order-12345",
  "correlationId": "request-uuid",
  "payload": {
    "orderId": "12345",
    "customerId": "67890",
    "totalAmount": 99.99,
    "currency": "USD"
  }
}
```

## Communication Patterns

### Request/Response

**Synchronous Request/Response:**
```
Pattern:
Client → Service A → Service B → Response

Pros:
- Simple to implement
- Immediate feedback
- Easy to debug

Cons:
- Tight temporal coupling
- Cascading failures
- Higher latency
- Blocking operations

Use When:
- Real-time user interaction
- Small number of hops (max 2-3)
- Low latency requirements
- Failure of dependency should fail request
```

**Asynchronous Request/Response:**
```
Pattern:
1. Client sends request to Service A
2. Service A returns request ID immediately
3. Service A processes asynchronously
4. Client polls or receives webhook when complete

Implementation:
POST /api/v1/orders
Response: 202 Accepted
{
  "requestId": "req-12345",
  "statusUrl": "/api/v1/requests/req-12345"
}

GET /api/v1/requests/req-12345
Response: 200 OK
{
  "status": "completed",
  "result": { ... }
}

Alternative: WebSocket notification when ready
```

### Fire and Forget

**Pattern:**
```
Client → Message Queue → Consumer

Characteristics:
- Client doesn't wait for response
- Eventual consistency
- High throughput
- Loose coupling

Example:
User uploads image:
1. API returns 202 Accepted immediately
2. Message queued: image.uploaded
3. Worker processes asynchronously:
   - Generate thumbnails
   - Optimize image
   - Update database
4. User notified via WebSocket/SSE when ready

Pros:
- Non-blocking
- Resilient (retry on failure)
- Scalable (multiple workers)

Cons:
- No immediate feedback
- Requires status tracking
- Complex error handling
```

### Event Choreography

**Pattern:**
```
Distributed workflow via events (no central orchestrator)

Example: Order Placement
1. OrderService publishes: order.created
2. PaymentService listens, processes payment, publishes: payment.completed
3. InventoryService listens, reserves stock, publishes: inventory.reserved
4. ShippingService listens, creates shipment, publishes: shipment.created
5. NotificationService listens to all, sends appropriate notifications

Pros:
- No single point of failure
- Services highly decoupled
- Scales independently

Cons:
- Difficult to understand full workflow
- Hard to debug
- No central monitoring
- Eventual consistency challenges
```

### Saga Orchestration

**Pattern:**
```
Central orchestrator manages distributed transaction

Example: Order Saga
Orchestrator: OrderSagaService

Steps:
1. Create Order (OrderService)
2. Process Payment (PaymentService)
3. Reserve Inventory (InventoryService)
4. Create Shipment (ShippingService)

If step 3 fails:
- Compensate step 2: Refund payment
- Compensate step 1: Cancel order

Implementation:
- State machine tracks progress
- Stores saga state persistently
- Handles retries and compensations
- Sends commands to services

Pros:
- Clear workflow visibility
- Easier debugging
- Centralized monitoring

Cons:
- Orchestrator can become bottleneck
- Single point of failure (mitigate with HA)
- More complex implementation
```

## Protocol Selection Guide

### Decision Matrix

**REST vs gRPC:**
```
Use REST when:
- Public API (external clients)
- Browser-based clients
- Human-readable debugging needed
- Wide tooling support required
- Caching at HTTP layer

Use gRPC when:
- Internal service-to-service
- Low latency critical
- Strong typing needed
- Bi-directional streaming
- Polyglot teams (code generation)
```

**Synchronous vs Asynchronous:**
```
Use Synchronous when:
- User waiting for response
- Strong consistency required
- Simple request/response
- Low latency possible (<100ms)
- Few service hops (1-2)

Use Asynchronous when:
- Long-running operations (>5s)
- Multiple consumers need same data
- Decoupling services
- High throughput required
- Eventual consistency acceptable
```

**Message Queue vs Event Stream:**
```
Use Message Queue (RabbitMQ, SQS) when:
- Single consumer per message
- Task distribution
- Guaranteed processing
- Simpler model sufficient

Use Event Stream (Kafka) when:
- Multiple consumers per event
- Event replay needed
- High throughput (millions/sec)
- Event sourcing
- Long retention required
```

## API Design Best Practices

### RESTful API Design

**URL Structure:**
```
Good:
GET    /api/v1/customers/{customerId}/orders
POST   /api/v1/orders
GET    /api/v1/orders/{orderId}/items

Avoid:
GET    /api/v1/getCustomerOrders?customerId=123
POST   /api/v1/createOrder
```

**Versioning Strategies:**
```
1. URL Versioning:
   /api/v1/orders
   /api/v2/orders
   Pros: Clear, easy to route
   Cons: URL pollution

2. Header Versioning:
   Accept: application/vnd.company.v1+json
   Pros: Clean URLs
   Cons: Harder to debug

3. Query Parameter:
   /api/orders?version=1
   Pros: Flexible
   Cons: Easy to miss

Recommendation: URL versioning for simplicity
```

**Pagination:**
```
Cursor-Based (Recommended):
GET /api/v1/orders?cursor=abc123&limit=20
Response:
{
  "data": [...],
  "nextCursor": "xyz789",
  "hasMore": true
}

Offset-Based (Simple but problematic):
GET /api/v1/orders?page=2&pageSize=20
Problem: Results change if data inserted
```

### gRPC Best Practices

**Error Handling:**
```
Use standard gRPC status codes:
- OK (0)
- INVALID_ARGUMENT (3)
- NOT_FOUND (5)
- ALREADY_EXISTS (6)
- PERMISSION_DENIED (7)
- RESOURCE_EXHAUSTED (8)
- FAILED_PRECONDITION (9)
- UNAVAILABLE (14)

Include error details:
rpc CreateOrder(CreateOrderRequest) returns (OrderResponse) {
  // On error, return status with details
}

Error details in metadata for rich context
```

**Streaming Patterns:**
```
1. Server Streaming:
   rpc ListOrders(ListRequest) returns (stream Order);
   Use: Large result sets

2. Client Streaming:
   rpc UploadImages(stream Image) returns (UploadResponse);
   Use: Bulk uploads

3. Bidirectional Streaming:
   rpc Chat(stream Message) returns (stream Message);
   Use: Real-time communication
```

## Summary

Choose communication patterns based on:
- Consistency requirements (strong vs eventual)
- Latency tolerance
- Coupling tolerance
- Complexity budget
- Team expertise

**Rule of Thumb:**
- Synchronous for reads and simple writes
- Asynchronous for complex workflows
- Events for cross-aggregate updates
- Sagas for distributed transactions

Always implement timeouts, retries, and circuit breakers regardless of pattern chosen.
