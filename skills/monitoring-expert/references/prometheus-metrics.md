# Prometheus Metrics

> Reference for: Monitoring Expert
> Load when: Setting up metrics, Prometheus

## Metric Types

```typescript
import { Registry, Counter, Histogram, Gauge, Summary } from 'prom-client';

const register = new Registry();

// Counter - cumulative, only increases
const httpRequests = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status'],
  registers: [register],
});

// Histogram - distribution with buckets
const httpDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'path'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 5],
  registers: [register],
});

// Gauge - point-in-time value, can go up/down
const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  registers: [register],
});

// Summary - similar to histogram with percentiles
const responseSummary = new Summary({
  name: 'http_response_size_bytes',
  help: 'HTTP response size',
  percentiles: [0.5, 0.9, 0.99],
  registers: [register],
});
```

## HTTP Middleware

```typescript
app.use((req, res, next) => {
  const end = httpDuration.startTimer({
    method: req.method,
    path: req.route?.path || req.path,
  });

  res.on('finish', () => {
    httpRequests.inc({
      method: req.method,
      path: req.route?.path || req.path,
      status: res.statusCode,
    });
    end();
  });

  next();
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.send(await register.metrics());
});
```

## Business Metrics

```typescript
// Orders
const ordersCreated = new Counter({
  name: 'orders_created_total',
  help: 'Total orders created',
  labelNames: ['status', 'payment_method'],
});

const orderValue = new Histogram({
  name: 'order_value_dollars',
  help: 'Order value in dollars',
  buckets: [10, 50, 100, 500, 1000],
});

// Usage
ordersCreated.inc({ status: 'completed', payment_method: 'card' });
orderValue.observe(order.total);
```

## Default Metrics

```typescript
import { collectDefaultMetrics } from 'prom-client';

// Collect Node.js metrics (memory, CPU, etc.)
collectDefaultMetrics({ register });
```

## Python (prometheus_client)

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

http_requests = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status']
)

http_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'path']
)

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Quick Reference

| Type | Use Case | Example |
|------|----------|---------|
| Counter | Cumulative totals | Requests, errors |
| Gauge | Current value | Active users, queue size |
| Histogram | Distributions | Response times |
| Summary | Percentiles | Similar to histogram |

| Naming | Convention |
|--------|------------|
| Unit suffix | `_seconds`, `_bytes`, `_total` |
| Base unit | Use seconds, bytes (not ms, KB) |
| Prefix | App/service name |
