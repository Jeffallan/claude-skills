---
name: Monitoring Expert
description: Expert in application monitoring, observability, logging, metrics, and alerting. Use when setting up monitoring, observability, logging, metrics, tracing, alerting, APM, or when the user mentions monitoring, observability, Prometheus, Grafana, ELK, DataDog, or New Relic.
---

# Monitoring Expert

Expert in building comprehensive monitoring and observability solutions for production systems.

## Instructions

### Core Workflow

1. **Understand requirements**
   - Identify what needs monitoring
   - Determine SLIs/SLOs/SLAs
   - Understand alert requirements
   - Identify stakeholders

2. **Implement Three Pillars of Observability**
   - **Logs**: Structured logging
   - **Metrics**: Time-series data
   - **Traces**: Distributed tracing

3. **Set up monitoring stack**
   - Choose tools (Prometheus, Grafana, ELK, DataDog, etc.)
   - Implement instrumentation
   - Configure dashboards
   - Set up alerts

4. **Define SLIs/SLOs**
   - Service Level Indicators (what to measure)
   - Service Level Objectives (targets)
   - Error budgets
   - Alerting thresholds

### Logging Best Practices

```typescript
// Structured logging (JSON)
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'user-service' },
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

logger.info('User logged in', {
  userId: user.id,
  email: user.email,
  ip: req.ip,
});

logger.error('Database connection failed', {
  error: error.message,
  stack: error.stack,
  database: config.database,
});
```

### Metrics (Prometheus)

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const register = new Registry();

// Counter - monotonically increasing
const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register],
});

// Histogram - distribution of values
const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10],
  registers: [register],
});

// Gauge - value that can go up or down
const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  registers: [register],
});

// Middleware to track metrics
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;

    httpRequestsTotal.labels(req.method, req.route.path, res.statusCode).inc();
    httpRequestDuration.labels(req.method, req.route.path, res.statusCode).observe(duration);
  });

  next();
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

### Distributed Tracing (OpenTelemetry)

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'my-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

### Alerting Rules (Prometheus)

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }}s"

      - alert: ServiceDown
        expr: up{job="api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
```

### Health Checks

```typescript
app.get('/health', async (req, res) => {
  const checks = {
    uptime: process.uptime(),
    timestamp: Date.now(),
    status: 'ok',
    checks: {
      database: await checkDatabase(),
      redis: await checkRedis(),
      externalApi: await checkExternalApi(),
    },
  };

  const isHealthy = Object.values(checks.checks).every(check => check.status === 'ok');

  res.status(isHealthy ? 200 : 503).json(checks);
});

async function checkDatabase() {
  try {
    await db.query('SELECT 1');
    return { status: 'ok' };
  } catch (error) {
    return { status: 'error', message: error.message };
  }
}
```

### Dashboards (Grafana)

Key metrics to display:
- **RED metrics** (Rate, Errors, Duration)
  - Request rate
  - Error rate
  - Request duration (latency)
- **USE metrics** (Utilization, Saturation, Errors)
  - CPU/Memory utilization
  - Queue depth
  - Error counts
- **Business metrics**
  - Active users
  - Transactions per second
  - Revenue metrics

## Critical Rules

### Always Do
- Implement structured logging
- Define SLIs/SLOs
- Set up meaningful alerts
- Monitor the four golden signals (latency, traffic, errors, saturation)
- Include context in logs (request ID, user ID, etc.)
- Use log levels appropriately
- Monitor dependencies
- Set up dashboards
- Document runbooks for alerts

### Never Do
- Never log sensitive data (passwords, tokens, PII)
- Never alert on everything (alert fatigue)
- Never ignore monitoring in development
- Never skip health checks
- Never hardcode thresholds without reasoning
- Never collect metrics without using them

## Knowledge Base

- **Tools**: Prometheus, Grafana, ELK Stack, DataDog, New Relic, Sentry
- **Concepts**: SLIs, SLOs, SLAs, Error budgets
- **Patterns**: RED metrics, USE metrics, Four golden signals
- **Protocols**: OpenTelemetry, StatsD, Syslog

## Best Practices Summary

1. **Three Pillars**: Logs, Metrics, Traces
2. **Structured Logging**: JSON format with context
3. **Meaningful Metrics**: Track what matters
4. **Smart Alerts**: Actionable, not noisy
5. **Dashboards**: Clear, focused, role-specific
6. **SLOs**: Define and track service objectives
7. **Health Checks**: Comprehensive dependency checks
8. **Documentation**: Runbooks for all alerts
9. **Testing**: Test monitoring and alerts
10. **Privacy**: Never log sensitive data
