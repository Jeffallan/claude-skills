# Capacity Planning

> Reference for: Monitoring Expert
> Load when: Capacity planning, scaling, resource forecasting

## Growth Projection

### Linear Projection

```python
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Historical data
data = pd.DataFrame({
    'month': range(1, 13),
    'requests_per_second': [100, 120, 145, 160, 180, 200, 220, 245, 270, 290, 310, 330]
})

# Train model
model = LinearRegression()
X = data[['month']].values
y = data['requests_per_second'].values
model.fit(X, y)

# Forecast next 6 months
future_months = np.array([[13], [14], [15], [16], [17], [18]])
predictions = model.predict(future_months)

print("Projected RPS in 6 months:", predictions[-1])
```

### Prometheus Queries for Trends

```promql
# Monthly growth rate
(
  rate(http_requests_total[30d])
  /
  rate(http_requests_total[30d] offset 30d)
) - 1

# Predict resource exhaustion
predict_linear(
  node_memory_MemAvailable_bytes[1h],
  3600 * 24 * 30  # 30 days ahead
)

# Storage growth
predict_linear(
  node_filesystem_avail_bytes[7d],
  3600 * 24 * 90  # 90 days ahead
)
```

## Resource Forecasting

### CPU Requirements

```javascript
// Current capacity
const currentRPS = 1000;
const currentCPU = 0.65;  // 65% utilization
const targetCPU = 0.70;   // Target 70% max

// Projected load
const projectedRPS = 2500;

// Required CPU capacity
const cpuScalingFactor = projectedRPS / currentRPS;
const requiredCPU = (currentCPU * cpuScalingFactor) / targetCPU;

console.log(`Current: ${currentRPS} RPS @ ${currentCPU * 100}% CPU`);
console.log(`Projected: ${projectedRPS} RPS requires ${requiredCPU.toFixed(2)}x CPU`);
```

### Memory Requirements

```javascript
// Memory per request (average)
const avgMemoryPerRequest = 2048;  // bytes
const concurrentRequests = 500;
const overhead = 1.3;  // 30% overhead for GC, OS, etc.

const requiredMemory = (avgMemoryPerRequest * concurrentRequests * overhead) / (1024 ** 3);
console.log(`Required memory: ${requiredMemory.toFixed(2)} GB`);
```

### Database Connections

```javascript
// Connections per instance
const connectionsPerInstance = 100;
const instances = 5;
const utilizationTarget = 0.75;

// Available connections
const totalConnections = connectionsPerInstance * instances;
const effectiveConnections = totalConnections * utilizationTarget;

// RPS capacity
const avgRequestsPerConnection = 10;
const maxRPS = effectiveConnections * avgRequestsPerConnection;

console.log(`Max sustainable RPS: ${maxRPS}`);
```

## Scaling Strategies

### Horizontal Scaling Calculator

```javascript
function calculateInstances(targetRPS, instanceCapacity, bufferPercent = 20) {
  // Account for buffer
  const effectiveCapacity = instanceCapacity * (1 - bufferPercent / 100);

  // Calculate required instances
  const requiredInstances = Math.ceil(targetRPS / effectiveCapacity);

  // Account for availability zones
  const minInstancesPerAZ = 2;
  const zones = 3;
  const minTotal = minInstancesPerAZ * zones;

  return Math.max(requiredInstances, minTotal);
}

console.log(calculateInstances(5000, 1000));  // 7 instances
```

### Auto-scaling Configuration

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 30
        - type: Pods
          value: 4
          periodSeconds: 30
      selectPolicy: Max
```

### AWS Auto Scaling

```json
{
  "AutoScalingGroupName": "app-asg",
  "MinSize": 3,
  "MaxSize": 20,
  "DesiredCapacity": 5,
  "TargetTrackingScalingPolicies": [
    {
      "TargetValue": 70.0,
      "PredefinedMetricSpecification": {
        "PredefinedMetricType": "ASGAverageCPUUtilization"
      },
      "ScaleInCooldown": 300,
      "ScaleOutCooldown": 60
    },
    {
      "TargetValue": 1000.0,
      "CustomizedMetricSpecification": {
        "MetricName": "RequestCountPerTarget",
        "Namespace": "AWS/ApplicationELB",
        "Statistic": "Sum"
      }
    }
  ]
}
```

## Performance Budgets

### Response Time Budget

```javascript
const performanceBudget = {
  // Page load budgets
  ttfb: 200,          // Time to First Byte (ms)
  fcp: 1000,          // First Contentful Paint (ms)
  lcp: 2500,          // Largest Contentful Paint (ms)

  // API budgets
  apiP50: 100,        // 50th percentile (ms)
  apiP95: 500,        // 95th percentile (ms)
  apiP99: 1000,       // 99th percentile (ms)

  // Resource budgets
  jsBundle: 200,      // JavaScript bundle size (KB)
  cssBundle: 50,      // CSS bundle size (KB)
  images: 500,        // Total images (KB)

  // Infrastructure budgets
  cpuUtilization: 70,     // Max % during normal load
  memoryUtilization: 80,  // Max % during normal load
  errorRate: 0.01,        // Max 1% error rate
};

function checkBudget(actual, budget, metric) {
  if (actual > budget) {
    console.warn(`Budget exceeded for ${metric}: ${actual} > ${budget}`);
    return false;
  }
  return true;
}
```

## Cost Optimization

### Instance Sizing

```javascript
function optimizeInstanceSize(workload) {
  const instances = [
    { type: 't3.small', vcpu: 2, memory: 2, cost: 0.0208 },
    { type: 't3.medium', vcpu: 2, memory: 4, cost: 0.0416 },
    { type: 't3.large', vcpu: 2, memory: 8, cost: 0.0832 },
    { type: 'm5.large', vcpu: 2, memory: 8, cost: 0.096 },
    { type: 'm5.xlarge', vcpu: 4, memory: 16, cost: 0.192 },
  ];

  const filtered = instances.filter(i =>
    i.vcpu >= workload.requiredVCPU &&
    i.memory >= workload.requiredMemory
  );

  // Sort by cost efficiency
  return filtered.sort((a, b) => {
    const scoreA = (a.vcpu * a.memory) / a.cost;
    const scoreB = (b.vcpu * b.memory) / b.cost;
    return scoreB - scoreA;
  })[0];
}

const recommendation = optimizeInstanceSize({
  requiredVCPU: 2,
  requiredMemory: 4,
});

console.log('Recommended instance:', recommendation);
```

## Capacity Alerts

```yaml
# Prometheus alerting rules
groups:
  - name: capacity
    rules:
      - alert: HighCPUPrediction
        expr: |
          predict_linear(
            node_cpu_seconds_total{mode="idle"}[1h],
            3600 * 24 * 7  # 7 days ahead
          ) < 0.2
        for: 1h
        annotations:
          summary: CPU capacity will be exhausted in 7 days

      - alert: DiskSpaceProjection
        expr: |
          predict_linear(
            node_filesystem_avail_bytes[7d],
            3600 * 24 * 30
          ) < 1e9  # Less than 1GB in 30 days
        annotations:
          summary: Disk space will run out in 30 days

      - alert: DatabaseConnectionsNearLimit
        expr: |
          pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 10m
        annotations:
          summary: Database connections at 80% capacity

      - alert: ScalingRecommendation
        expr: |
          rate(http_requests_total[5m]) >
          (instance_capacity * instance_count * 0.7)
        annotations:
          summary: Consider scaling up - traffic approaching capacity
```

## Quick Reference

| Metric | Buffer | Reasoning |
|--------|--------|-----------|
| CPU | 30% | Headroom for spikes |
| Memory | 20% | GC and OS overhead |
| Connections | 25% | Connection churn |
| Storage | 40% | Growth + snapshots |

| Planning Horizon | Update Frequency |
|------------------|------------------|
| 3 months | Weekly |
| 6 months | Bi-weekly |
| 12 months | Monthly |

| Scaling Trigger | Action |
|-----------------|--------|
| 70% CPU | Start planning |
| 80% CPU | Scale up |
| 90% CPU | Emergency scaling |
| 60% CPU for 24h | Scale down |
