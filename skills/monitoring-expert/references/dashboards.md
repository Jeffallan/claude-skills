# Dashboards

> Reference for: Monitoring Expert
> Load when: Creating dashboards, Grafana, visualization

## RED Method (Request-focused)

```
Rate     - Requests per second
Errors   - Failed requests per second
Duration - Response time distribution
```

```promql
# Rate
sum(rate(http_requests_total[5m]))

# Errors
sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m]))

# Duration (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## USE Method (Resource-focused)

```
Utilization - % time resource is busy
Saturation  - Queue depth, backlog
Errors      - Error events
```

```promql
# CPU Utilization
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Saturation
node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes

# Disk Errors
rate(node_disk_io_time_weighted_seconds_total[5m])
```

## Dashboard Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE OVERVIEW                         │
│  Request Rate │ Error Rate │ p50 Latency │ p99 Latency     │
├─────────────────────────────────────────────────────────────┤
│                    REQUEST METRICS                          │
│  [Graph: Requests/s by endpoint]                           │
│  [Graph: Error rate over time]                             │
├─────────────────────────────────────────────────────────────┤
│                    LATENCY METRICS                          │
│  [Heatmap: Latency distribution]                           │
│  [Graph: p50, p95, p99 over time]                          │
├─────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE                           │
│  CPU │ Memory │ Disk │ Network                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Panels

### Stat Panel (Single Value)

```promql
# Current RPS
sum(rate(http_requests_total[5m]))

# Error percentage
sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m])) * 100
```

### Time Series

```promql
# Requests by status
sum by (status) (rate(http_requests_total[5m]))

# Latency percentiles
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Table

```promql
# Top endpoints by error rate
topk(10,
  sum by (path) (rate(http_requests_total{status=~"5.."}[5m]))
  /
  sum by (path) (rate(http_requests_total[5m]))
)
```

## Business Metrics Dashboard

```promql
# Orders per minute
sum(rate(orders_created_total[5m])) * 60

# Revenue (if tracked)
sum(increase(order_value_dollars_sum[1h]))

# Active users (gauge)
active_users_total
```

## Quick Reference

| Method | Focus | Metrics |
|--------|-------|---------|
| RED | Services | Rate, Errors, Duration |
| USE | Resources | Utilization, Saturation, Errors |

| Panel Type | Use Case |
|------------|----------|
| Stat | Single KPI |
| Time Series | Trends over time |
| Heatmap | Latency distribution |
| Table | Top N, details |
| Gauge | Current vs threshold |
