# Observability in Microservices

Comprehensive guide for monitoring, tracing, and debugging distributed systems.

## The Three Pillars

### 1. Metrics

**Purpose:** Quantitative measurements of system behavior over time.

**Categories:**

**Business Metrics:**
```
Examples:
- Orders per minute
- Revenue per hour
- Active users
- Conversion rate
- Cart abandonment rate

Why Important:
- Align with business goals
- Detect business anomalies
- Inform scaling decisions

Implementation:
from prometheus_client import Counter, Histogram

orders_total = Counter(
    'orders_total',
    'Total number of orders',
    ['status', 'payment_method']
)

order_value = Histogram(
    'order_value_dollars',
    'Order value in dollars',
    buckets=[10, 50, 100, 500, 1000, 5000]
)

# In code
orders_total.labels(status='completed', payment_method='credit_card').inc()
order_value.observe(order.total_amount)
```

**System Metrics:**
```
Infrastructure:
- CPU usage
- Memory usage
- Disk I/O
- Network throughput

Application:
- Request rate
- Error rate
- Request duration (latency)
- Active connections
- Thread pool utilization

Database:
- Query duration
- Connection pool usage
- Slow queries
- Deadlocks

Message Queue:
- Queue depth
- Message processing rate
- Consumer lag
- Dead letter queue size
```

**The Four Golden Signals (Google SRE):**
```
1. Latency:
   - Time to serve requests
   - Track p50, p95, p99, p99.9
   - Separate success vs error latency

   request_duration = Histogram(
       'http_request_duration_seconds',
       'HTTP request duration',
       ['method', 'endpoint', 'status']
   )

2. Traffic:
   - Requests per second
   - Transactions per second
   - Concurrent users

   requests_total = Counter(
       'http_requests_total',
       'Total HTTP requests',
       ['method', 'endpoint', 'status']
   )

3. Errors:
   - Rate of failed requests
   - 4xx vs 5xx errors
   - Exception types

   errors_total = Counter(
       'errors_total',
       'Total errors',
       ['service', 'error_type']
   )

4. Saturation:
   - Resource utilization
   - Queue depth
   - Thread pool usage

   connection_pool_usage = Gauge(
       'db_connection_pool_active',
       'Active database connections'
   )
```

**RED Method (for services):**
```
- Rate: Requests per second
- Errors: Failed requests per second
- Duration: Request latency distribution

Perfect for microservices dashboards
```

**USE Method (for resources):**
```
- Utilization: Percentage of time resource busy
- Saturation: Queue depth or waiting threads
- Errors: Error count

Perfect for infrastructure monitoring
```

### 2. Logs

**Purpose:** Discrete event records with context.

**Structured Logging:**
```json
{
  "timestamp": "2025-12-14T15:30:45.123Z",
  "level": "INFO",
  "service": "order-service",
  "version": "1.2.3",
  "traceId": "abc123def456",
  "spanId": "span789",
  "userId": "user-123",
  "message": "Order created successfully",
  "orderId": "order-456",
  "totalAmount": 99.99,
  "currency": "USD",
  "duration_ms": 45,
  "endpoint": "/api/v1/orders",
  "method": "POST",
  "statusCode": 201
}
```

**Log Levels:**
```
ERROR:
- Application errors
- Failed operations
- Exceptions
Use: Alerts, immediate attention

WARN:
- Degraded functionality
- Retry attempts
- Deprecated API usage
Use: Investigation, potential issues

INFO:
- Business events (order created, user logged in)
- System events (service started, configuration loaded)
Use: Audit trail, business analytics

DEBUG:
- Detailed execution flow
- Variable values
- Function entry/exit
Use: Development, troubleshooting

TRACE:
- Very detailed debugging
Use: Deep troubleshooting (disabled in production usually)
```

**Correlation IDs:**
```
Request flow across services:

Client Request → API Gateway
                 ↓ (correlationId: corr-123)
                 Order Service
                 ↓ (correlationId: corr-123)
                 Payment Service
                 ↓ (correlationId: corr-123)
                 Notification Service

All logs include correlationId: corr-123
Easy to trace entire request flow

Implementation:
import logging
from contextvars import ContextVar

correlation_id_var = ContextVar('correlation_id', default=None)

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        return True

# Middleware
async def correlation_middleware(request, call_next):
    correlation_id = request.headers.get('X-Correlation-ID', str(uuid4()))
    correlation_id_var.set(correlation_id)
    response = await call_next(request)
    response.headers['X-Correlation-ID'] = correlation_id
    return response
```

**Log Aggregation:**
```
Services → Log Shipper → Centralized Log Storage → Visualization

Tools:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- EFK Stack (Elasticsearch, Fluentd, Kibana)
- Loki (from Grafana)
- CloudWatch Logs (AWS)
- Stackdriver (GCP)

Query Examples:
# Find all errors for specific user
service:"order-service" AND level:"ERROR" AND userId:"user-123"

# Find slow requests
service:"payment-service" AND duration_ms:>5000

# Find requests with specific correlation ID
correlationId:"corr-123"
```

### 3. Distributed Tracing

**Purpose:** Visualize request flow across services, identify bottlenecks.

**Concepts:**

**Trace:**
```
Entire request journey across all services

Example: User places order
Trace ID: trace-abc123

Spans in trace:
1. api-gateway: /checkout (200ms)
2. order-service: createOrder (150ms)
3. payment-service: processPayment (80ms)
4. inventory-service: reserveItems (40ms)
5. notification-service: sendEmail (30ms)

Total: 200ms (some parallel execution)
```

**Span:**
```
Single operation within a trace

Span attributes:
{
  "traceId": "trace-abc123",
  "spanId": "span-456",
  "parentSpanId": "span-123",
  "name": "POST /api/v1/orders",
  "startTime": "2025-12-14T15:30:45.000Z",
  "endTime": "2025-12-14T15:30:45.150Z",
  "duration": 150,
  "status": "OK",
  "attributes": {
    "http.method": "POST",
    "http.url": "/api/v1/orders",
    "http.status_code": 201,
    "user.id": "user-123",
    "order.id": "order-456",
    "order.total": 99.99
  },
  "events": [
    {
      "timestamp": "2025-12-14T15:30:45.050Z",
      "name": "Validating order items"
    },
    {
      "timestamp": "2025-12-14T15:30:45.100Z",
      "name": "Calling payment service"
    }
  ]
}
```

**Implementation (OpenTelemetry):**
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup tracing
provider = TracerProvider()
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831
)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)

# Instrument FastAPI
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# Manual span creation
tracer = trace.get_tracer(__name__)

async def create_order(order_data):
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("order.items_count", len(order_data.items))
        span.set_attribute("order.total", order_data.total)

        # Database operation
        with tracer.start_as_current_span("db.insert_order"):
            order_id = await db.insert_order(order_data)

        # Call payment service
        with tracer.start_as_current_span("http.payment_service") as payment_span:
            payment_span.set_attribute("http.url", f"{PAYMENT_URL}/payments")
            result = await payment_service.charge(order_id, order_data.total)

        return order_id
```

**Trace Visualization:**
```
Jaeger UI shows:

Timeline view:
|-- api-gateway (200ms) ----------------------------------|
    |-- order-service (150ms) ------------------------|
        |-- db.insert_order (30ms) --|
        |-- payment-service (80ms) -----------------|
            |-- db.create_transaction (20ms) ----|
        |-- notification-service (30ms) ----------|

Critical path highlighted
Bottlenecks identified (payment-service taking 80ms)
Parallel operations visible
```

**Sampling Strategies:**
```
Problem: Tracing every request is expensive

Solutions:

1. Probabilistic Sampling:
   - Trace 1% of requests
   - Good for high-volume services

2. Rate Limiting Sampling:
   - Max 100 traces per second
   - Prevents overwhelming trace backend

3. Tail-Based Sampling:
   - Trace all errors
   - Trace slow requests (>5s)
   - Sample 1% of fast successful requests

4. Priority Sampling:
   - Always trace premium users
   - Always trace critical endpoints
   - Sample others

Implementation:
from opentelemetry.sdk.trace.sampling import (
    ParentBasedTraceIdRatioBased,
    ALWAYS_ON,
    ALWAYS_OFF
)

# Sample 1% of traces
sampler = ParentBasedTraceIdRatioBased(0.01)

# Or custom sampler
class CustomSampler:
    def should_sample(self, context, trace_id, name, attributes):
        # Always sample errors
        if attributes.get("http.status_code", 0) >= 500:
            return ALWAYS_ON

        # Always sample slow requests
        if attributes.get("duration_ms", 0) > 5000:
            return ALWAYS_ON

        # Sample 1% of others
        return ParentBasedTraceIdRatioBased(0.01).should_sample(...)
```

## Service Level Objectives (SLOs)

### Defining SLOs

**SLI (Service Level Indicator):**
```
Quantitative measure of service level

Examples:
- Request latency: p99 < 200ms
- Availability: 99.9% of requests succeed
- Throughput: Handle 10,000 requests/sec
```

**SLO (Service Level Objective):**
```
Target value for SLI

Examples:
- 99.9% of requests complete in < 200ms
- 99.95% availability over 30 days
- Zero data loss

SLO Components:
- Metric: What you measure (latency, availability)
- Target: Threshold (99.9%, 200ms)
- Time window: Evaluation period (30 days, weekly)
```

**SLA (Service Level Agreement):**
```
Contract with consequences if SLO not met

Example:
- SLO: 99.9% availability
- SLA: If availability < 99.9%, customers get 10% credit

SLA ≤ SLO (leave buffer for incidents)
```

**Error Budget:**
```
Allowed failure to meet SLO = (100% - SLO target)

Example:
SLO: 99.9% availability
Error budget: 0.1% = 43.8 minutes downtime per month

Error budget consumed:
- Outages
- Slow responses
- Failed requests

When error budget exhausted:
- Freeze feature deployments
- Focus on reliability
- Only critical fixes deployed

Benefits:
- Balances innovation vs stability
- Data-driven deployment decisions
- Aligns engineering priorities
```

### Implementing SLO Monitoring

**Prometheus + Grafana:**
```
# SLI: Availability
availability_sli = (
    sum(rate(http_requests_total{status!~"5.."}[30d]))
    /
    sum(rate(http_requests_total[30d]))
) * 100

# SLI: Latency
latency_sli = histogram_quantile(
    0.99,
    rate(http_request_duration_seconds_bucket[30d])
)

# Error Budget
error_budget_remaining = (
    1 - (target_slo / 100)
) - (
    1 - (availability_sli / 100)
)

Alert when error budget < 10%:
alert: ErrorBudgetCritical
expr: error_budget_remaining < 0.1
annotations:
  summary: "Error budget critically low"
  description: "Only 10% error budget remaining. Freeze deployments."
```

## Alerting Strategies

### Alert Levels

**Critical (Page immediately):**
```
Conditions:
- Service completely down
- Error rate > 50%
- Data loss occurring
- SLO burn rate critical

Actions:
- Page on-call engineer
- Incident created automatically
- Escalate if not acknowledged in 5 min

Example:
alert: ServiceDown
expr: up{service="payment-service"} == 0
for: 1m
severity: critical
```

**Warning (Investigate soon):**
```
Conditions:
- Elevated error rate (5-10%)
- Latency degraded (p99 > 500ms)
- Queue depth increasing
- Error budget < 25%

Actions:
- Slack notification
- Create ticket
- Investigate during business hours

Example:
alert: HighErrorRate
expr: rate(http_requests_total{status="500"}[5m]) > 0.05
for: 10m
severity: warning
```

**Info (Awareness):**
```
Conditions:
- Deployment completed
- Scaling event
- Configuration changed
- Capacity threshold reached

Actions:
- Log to monitoring system
- Dashboard annotation
- Optional Slack notification
```

### Alert Best Practices

**Actionable Alerts:**
```
Bad Alert:
"High CPU usage"

Good Alert:
"CPU usage > 80% on order-service-pod-abc for 10 minutes
Runbook: https://wiki.company.com/runbooks/high-cpu
Likely cause: Memory leak or infinite loop
Actions: 1) Check recent deployments 2) Review logs for exceptions 3) Consider rolling back"

Include:
✓ What is wrong
✓ Why it matters
✓ How to investigate
✓ Runbook link
✓ Suggested actions
```

**Avoid Alert Fatigue:**
```
Problems:
- Too many alerts
- False positives
- Non-actionable alerts
- Duplicate alerts

Solutions:
- Alert on symptoms, not causes
- Proper thresholds and durations
- Alert aggregation (don't alert per pod, alert per service)
- Regular alert review and tuning
- Auto-resolve alerts
- Silence during maintenance

Good Practice:
for: 5m  # Don't alert on transient spikes
group_by: [service]  # Aggregate per service
group_wait: 30s  # Wait before sending
group_interval: 5m  # Batch notifications
```

## Observability Stack

### Recommended Tools

**Metrics:**
```
Collection: Prometheus
- Pull-based metrics
- Time-series database
- Powerful query language (PromQL)
- Service discovery

Visualization: Grafana
- Beautiful dashboards
- Alerting integration
- Multiple data sources
- Template variables

Alternative: Datadog, New Relic, CloudWatch
```

**Logs:**
```
Aggregation: ELK Stack
- Elasticsearch (storage & search)
- Logstash / Fluentd (collection)
- Kibana (visualization)

Or: Loki (lightweight alternative)
- Integrates with Grafana
- Labels instead of full-text indexing
- Lower resource usage

Alternative: Splunk, Datadog, CloudWatch Logs
```

**Tracing:**
```
Backend: Jaeger or Zipkin
- Trace storage
- Trace visualization
- Dependency graphs
- Performance analysis

Instrumentation: OpenTelemetry
- Vendor-neutral standard
- Auto-instrumentation for common frameworks
- Manual instrumentation API
- Export to any backend

Alternative: Datadog APM, New Relic, Lightstep
```

**All-in-One:**
```
Observability platforms:
- Datadog (metrics, logs, traces, RUM)
- New Relic (APM, logs, infrastructure)
- Dynatrace (auto-instrumentation, AI)

Pros:
- Unified experience
- Correlated data
- Easier setup

Cons:
- Vendor lock-in
- Higher cost
- Less flexibility
```

### Implementation Checklist

**For Each Service:**
```
✓ Structured logging with correlation IDs
✓ Metrics exported (Prometheus format)
✓ Distributed tracing instrumented
✓ Health check endpoints (/health/live, /health/ready)
✓ Graceful shutdown handling
✓ Resource limits set (CPU, memory)
✓ Alerts configured for critical paths
✓ Dashboards created
✓ Runbooks documented
✓ On-call rotation established
```

**For System-Wide:**
```
✓ Centralized log aggregation
✓ Distributed tracing backend
✓ Metrics aggregation and storage
✓ Unified dashboards (service overview)
✓ Alert routing configured
✓ Incident management process
✓ Post-mortem template
✓ SLO definitions and tracking
✓ Dependency mapping
✓ Chaos engineering experiments
```

## Troubleshooting Workflow

**Incident Response:**
```
1. Detect (Alert fires)
   - Check dashboard
   - Verify alert is valid
   - Assess impact

2. Triage (Determine severity)
   - Critical: Page on-call
   - Warning: Create ticket
   - How many users affected?
   - What functionality broken?

3. Investigate (Find root cause)
   - Check recent deployments
   - Review logs (search by correlation ID)
   - Analyze traces (slow operations)
   - Check metrics (resource saturation)
   - Examine dependencies

4. Mitigate (Stop the bleeding)
   - Rollback deployment
   - Scale up resources
   - Failover to backup
   - Enable circuit breakers
   - Rate limit traffic

5. Resolve (Fix root cause)
   - Deploy fix
   - Verify resolution
   - Monitor for recurrence

6. Post-mortem (Learn and improve)
   - Timeline of events
   - Root cause analysis
   - Action items
   - Update runbooks
```

**Using Traces to Debug:**
```
Scenario: API returning 500 errors

1. Find failing trace:
   - Filter: status = error, service = api-gateway
   - Sort by timestamp (most recent)

2. Analyze span waterfall:
   - Identify which service failed (order-service returned 500)
   - Check error message in span
   - Review span attributes

3. Correlate with logs:
   - Extract trace ID from failed trace
   - Search logs: traceId:"trace-abc123"
   - Find exception stack trace

4. Check related metrics:
   - order-service error rate spiked 10 min ago
   - Corresponds with deployment
   - Likely cause: Bad deployment

5. Remediate:
   - Rollback order-service
   - Verify errors stopped
   - Create ticket for bug fix
```

## Summary

Observability is non-negotiable in microservices:

**Must-Haves:**
- Structured logging with correlation IDs
- Metrics (RED/USE methodology)
- Distributed tracing (OpenTelemetry)
- Centralized log aggregation
- SLO tracking with error budgets
- Actionable alerts with runbooks

**Best Practices:**
- Correlate metrics, logs, and traces
- Define SLOs based on user experience
- Alert on symptoms, not causes
- Maintain runbooks for common issues
- Regular post-mortems and learning
- Practice incident response with game days

Without observability, you're flying blind in production.
