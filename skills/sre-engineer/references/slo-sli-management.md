# SLO/SLI Management

## SLI Definition Patterns

Service Level Indicators are quantitative measurements of service behavior.

### Request-Based SLIs

```python
# Availability SLI: Proportion of successful requests
# Good events: HTTP 200-299, 4XX (client errors don't count against SLI)
# Total events: All requests

def calculate_availability_sli(metrics):
    """Calculate availability SLI from request metrics."""
    successful_requests = metrics['http_2xx'] + metrics['http_4xx']
    total_requests = metrics['total_requests']

    if total_requests == 0:
        return 1.0  # No traffic = 100% available

    return successful_requests / total_requests

# Example: 99.9% of requests return successfully
# SLI = successful_requests / total_requests
```

### Latency-Based SLIs

```python
def calculate_latency_sli(latency_histogram, threshold_ms=500):
    """Calculate latency SLI from histogram.

    Args:
        latency_histogram: dict mapping latency buckets to request counts
        threshold_ms: latency threshold in milliseconds

    Returns:
        float: Proportion of requests faster than threshold
    """
    fast_requests = sum(
        count for bucket, count in latency_histogram.items()
        if bucket <= threshold_ms
    )
    total_requests = sum(latency_histogram.values())

    return fast_requests / total_requests if total_requests > 0 else 1.0

# Example: 99% of requests complete in <500ms
# SLI = requests_under_500ms / total_requests
```

## SLO Configuration

```yaml
# slo_config.yaml - Production API SLO definitions
apiVersion: sre/v1
kind: ServiceLevelObjective
metadata:
  service: payment-api
  environment: production
spec:
  slos:
    - name: availability
      description: "Users can successfully complete payment requests"
      sli:
        metric: http_requests_total
        query: |
          sum(rate(http_requests_total{status=~"2..|4..", service="payment-api"}[30d]))
          /
          sum(rate(http_requests_total{service="payment-api"}[30d]))
      target: 0.999  # 99.9%
      window: 30d

    - name: latency
      description: "Payment requests complete quickly"
      sli:
        metric: http_request_duration_seconds
        query: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket{service="payment-api"}[30d]))
            by (le)
          ) < 0.5
      target: 0.99  # 99% of requests under 500ms
      window: 30d
```

## Golden Signals

The four golden signals every service should measure:

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class GoldenSignals:
    """Four golden signals of monitoring."""

    # Latency: Time to service requests (success vs failure)
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float

    # Traffic: Demand on your system (requests/sec)
    requests_per_second: float

    # Errors: Rate of failed requests
    error_rate: float  # 0.0 to 1.0

    # Saturation: How "full" is your service (CPU, memory, disk)
    cpu_utilization: float  # 0.0 to 1.0
    memory_utilization: float  # 0.0 to 1.0

    def is_healthy(self, slo_targets: Dict[str, float]) -> bool:
        """Check if all signals are within SLO targets."""
        return (
            self.latency_p99_ms <= slo_targets['latency_p99_ms'] and
            self.error_rate <= (1 - slo_targets['availability']) and
            self.cpu_utilization <= slo_targets['max_cpu'] and
            self.memory_utilization <= slo_targets['max_memory']
        )
```

## SLO Calculation Examples

```python
from datetime import timedelta
from typing import NamedTuple

class SLOTarget(NamedTuple):
    """SLO target configuration."""
    target: float  # 0.999 for 99.9%
    window: timedelta  # 30 days

    @property
    def error_budget(self) -> float:
        """Calculate error budget (1 - target)."""
        return 1 - self.target

    @property
    def allowed_downtime(self) -> timedelta:
        """Calculate allowed downtime in window."""
        total_seconds = self.window.total_seconds()
        allowed_seconds = total_seconds * self.error_budget
        return timedelta(seconds=allowed_seconds)

# Example SLOs
availability_slo = SLOTarget(target=0.999, window=timedelta(days=30))
print(f"Error budget: {availability_slo.error_budget * 100}%")
print(f"Allowed downtime: {availability_slo.allowed_downtime}")
# Output:
# Error budget: 0.1%
# Allowed downtime: 43.2 minutes per 30 days

latency_slo = SLOTarget(target=0.99, window=timedelta(days=30))
print(f"99% of requests must be fast")
print(f"1% can be slow: {latency_slo.error_budget * 100}%")
```

## Multi-Window SLO Tracking

```python
class MultiWindowSLO:
    """Track SLO compliance across multiple time windows."""

    def __init__(self, target: float):
        self.target = target
        self.windows = {
            '1h': timedelta(hours=1),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30),
        }

    def check_compliance(self, sli_values: Dict[str, float]) -> Dict[str, bool]:
        """Check if SLI meets target in each window.

        Args:
            sli_values: Dict mapping window name to measured SLI

        Returns:
            Dict mapping window name to compliance boolean
        """
        return {
            window: sli >= self.target
            for window, sli in sli_values.items()
        }

    def get_burn_rate(self, current_sli: float) -> float:
        """Calculate error budget burn rate.

        Burn rate > 1.0 means burning budget faster than sustainable.
        """
        error_budget = 1 - self.target
        current_error_rate = 1 - current_sli

        if error_budget == 0:
            return float('inf')

        return current_error_rate / error_budget

# Usage
slo = MultiWindowSLO(target=0.999)
current_sli = 0.997  # 99.7% availability

burn_rate = slo.get_burn_rate(current_sli)
print(f"Burn rate: {burn_rate}x")
# If burn_rate = 3.0, burning budget 3x faster than sustainable
```

## SLO Review Checklist

Before finalizing SLOs:

1. **User-centric**: Does it measure user-facing impact?
2. **Achievable**: Can you meet it with current architecture?
3. **Measurable**: Can you accurately track the SLI?
4. **Meaningful**: Does violating it require action?
5. **Documented**: Is the calculation clear and agreed upon?
6. **Budgeted**: Is there an error budget policy?

## Common SLO Targets

```yaml
# Typical SLO targets by service tier
tier_1_critical:
  availability: 99.99%  # 4m 23s downtime/month
  latency_p99: 100ms

tier_2_important:
  availability: 99.9%   # 43m 28s downtime/month
  latency_p99: 500ms

tier_3_standard:
  availability: 99.5%   # 3h 37m downtime/month
  latency_p99: 1000ms
```
