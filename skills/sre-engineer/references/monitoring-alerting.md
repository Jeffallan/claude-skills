# Monitoring and Alerting

## Golden Signals Monitoring

Monitor the four golden signals for every service.

```yaml
# prometheus_rules.yaml - Golden signals recording rules
groups:
  - name: golden_signals
    interval: 30s
    rules:
      # Latency: Request duration
      - record: service:http_request_duration_seconds:p50
        expr: |
          histogram_quantile(0.50,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
          )

      - record: service:http_request_duration_seconds:p95
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
          )

      - record: service:http_request_duration_seconds:p99
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
          )

      # Traffic: Requests per second
      - record: service:http_requests:rate5m
        expr: |
          sum(rate(http_requests_total[5m])) by (service)

      # Errors: Error rate
      - record: service:http_requests:error_rate5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
          /
          sum(rate(http_requests_total[5m])) by (service)

      # Saturation: Resource utilization
      - record: service:cpu_utilization
        expr: |
          avg(rate(container_cpu_usage_seconds_total[5m])) by (service)

      - record: service:memory_utilization
        expr: |
          avg(container_memory_working_set_bytes / container_spec_memory_limit_bytes)
          by (service)
```

## Alert Design Principles

Good alerts are actionable, not just informative.

```yaml
# alerts.yaml - SLO-based alerting
groups:
  - name: slo_alerts
    rules:
      # Multi-window burn rate alert (fast burn)
      - alert: ErrorBudgetBurnRateFast
        expr: |
          (
            service:http_requests:error_rate5m > (14.4 * 0.001)
            and
            service:http_requests:error_rate1h > (14.4 * 0.001)
          )
        for: 2m
        labels:
          severity: critical
          slo: availability
        annotations:
          summary: "Fast error budget burn on {{ $labels.service }}"
          description: |
            Service {{ $labels.service }} is burning error budget at 14.4x rate.
            At this rate, 30-day budget will exhaust in 2 days.

            Current error rate: {{ $value | humanizePercentage }}
            Threshold: 1.44%

            RUNBOOK: https://runbooks.example.com/error-budget-burn

      # Slow burn rate alert
      - alert: ErrorBudgetBurnRateSlow
        expr: |
          (
            service:http_requests:error_rate6h > (6 * 0.001)
            and
            service:http_requests:error_rate1d > (6 * 0.001)
          )
        for: 15m
        labels:
          severity: warning
          slo: availability
        annotations:
          summary: "Slow error budget burn on {{ $labels.service }}"
          description: |
            Service {{ $labels.service }} is burning error budget at 6x rate.

            RUNBOOK: https://runbooks.example.com/error-budget-burn

      # Latency SLO violation
      - alert: LatencySLOViolation
        expr: |
          service:http_request_duration_seconds:p99 > 0.5
        for: 5m
        labels:
          severity: warning
          slo: latency
        annotations:
          summary: "P99 latency exceeds 500ms on {{ $labels.service }}"
          description: |
            P99 latency is {{ $value }}s, exceeding 500ms threshold.

            Check:
            1. Database query performance
            2. External API latency
            3. Resource saturation (CPU/memory)

            RUNBOOK: https://runbooks.example.com/high-latency

      # Saturation alert
      - alert: HighMemoryUtilization
        expr: |
          service:memory_utilization > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.service }}"
          description: |
            Memory utilization is {{ $value | humanizePercentage }}.

            Actions:
            1. Check for memory leaks
            2. Review recent deployments
            3. Consider scaling up

            RUNBOOK: https://runbooks.example.com/high-memory
```

## Alert Runbook Template

Every alert must link to a runbook with clear remediation steps.

```markdown
# Runbook: Error Budget Burn Rate

## Alert: ErrorBudgetBurnRateFast

### Description
The service is consuming error budget faster than sustainable rate.
At current rate, the 30-day error budget will be exhausted within 2 days.

### Severity: Critical

### Impact
- Users experiencing elevated error rates
- Risk of SLO violation and feature freeze
- Potential customer impact

### Triage Steps

1. **Check current error rate**
   ```promql
   rate(http_requests_total{status=~"5..", service="api"}[5m])
   ```

2. **Identify error types**
   ```bash
   kubectl logs -l app=api --tail=100 | grep ERROR
   ```

3. **Check recent deployments**
   ```bash
   kubectl rollout history deployment/api
   ```

4. **Review dependencies**
   - Database health
   - External API status
   - Infrastructure issues

### Remediation

**If caused by recent deployment:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/api

# Verify rollback
kubectl rollout status deployment/api
```

**If database issue:**
```bash
# Check database connections
kubectl exec -it postgres-0 -- psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
kubectl exec -it postgres-0 -- psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**If traffic spike:**
```bash
# Scale up replicas
kubectl scale deployment/api --replicas=10

# Enable rate limiting
kubectl apply -f rate-limit-config.yaml
```

### Communication

**Slack template:**
```
:fire: INCIDENT: Error budget burn rate critical

Service: api
Error rate: [X]%
Impact: [describe user impact]
ETA: [when will it be resolved]

Incident doc: [link]
```

### Prevention
- Add integration tests for this failure mode
- Implement circuit breaker for external dependencies
- Add capacity planning for traffic spikes
```

## Dashboard Configuration

```python
# grafana_dashboard.py - Generate SLO dashboard using Grafana SDK
from grafana_dashboard import Dashboard, Panel, Target

def create_slo_dashboard(service: str) -> dict:
    """Create SLO monitoring dashboard for a service."""

    dashboard = Dashboard(
        title=f"{service} - SLO Dashboard",
        tags=["slo", "sre", service],
        refresh="1m",
    )

    # SLI Current Value
    dashboard.add_panel(
        Panel(
            title="Availability SLI (30d)",
            targets=[
                Target(
                    expr=f"""
                    sum(rate(http_requests_total{{
                        status=~"2..",
                        service="{service}"
                    }}[30d]))
                    /
                    sum(rate(http_requests_total{{service="{service}"}}[30d]))
                    """,
                    legendFormat="Current SLI",
                ),
            ],
            thresholds=[
                {"value": 0.999, "color": "red"},
                {"value": 0.9995, "color": "yellow"},
                {"value": 1.0, "color": "green"},
            ],
        )
    )

    # Error Budget Remaining
    dashboard.add_panel(
        Panel(
            title="Error Budget Remaining",
            targets=[
                Target(
                    expr=f"""
                    (0.001 - (1 - (
                      sum(rate(http_requests_total{{
                          status=~"2..",
                          service="{service}"
                      }}[30d]))
                      /
                      sum(rate(http_requests_total{{service="{service}"}}[30d]))
                    ))) / 0.001 * 100
                    """,
                    legendFormat="Budget Remaining %",
                ),
            ],
            unit="percent",
        )
    )

    # Burn Rate
    dashboard.add_panel(
        Panel(
            title="Error Budget Burn Rate",
            targets=[
                Target(
                    expr=f"""
                    (1 - (
                      sum(rate(http_requests_total{{
                          status=~"2..",
                          service="{service}"
                      }}[1h]))
                      /
                      sum(rate(http_requests_total{{service="{service}"}}[1h]))
                    )) / 0.001
                    """,
                    legendFormat="1h burn rate",
                ),
            ],
            thresholds=[
                {"value": 1.0, "color": "green"},
                {"value": 6.0, "color": "yellow"},
                {"value": 14.4, "color": "red"},
            ],
        )
    )

    # Golden Signals
    dashboard.add_row("Golden Signals")

    dashboard.add_panel(
        Panel(
            title="Latency (P50, P95, P99)",
            targets=[
                Target(
                    expr=f'service:http_request_duration_seconds:p50{{service="{service}"}}',
                    legendFormat="p50",
                ),
                Target(
                    expr=f'service:http_request_duration_seconds:p95{{service="{service}"}}',
                    legendFormat="p95",
                ),
                Target(
                    expr=f'service:http_request_duration_seconds:p99{{service="{service}"}}',
                    legendFormat="p99",
                ),
            ],
            unit="s",
        )
    )

    return dashboard.to_json()
```

## Alert Fatigue Prevention

```python
from dataclasses import dataclass
from typing import List

@dataclass
class AlertQualityMetrics:
    """Track alert quality to prevent fatigue."""
    total_alerts: int
    actionable_alerts: int  # Required manual intervention
    false_positives: int
    auto_resolved: int  # Resolved before human action

    @property
    def precision(self) -> float:
        """Percentage of alerts that were actionable."""
        if self.total_alerts == 0:
            return 0.0
        return (self.actionable_alerts / self.total_alerts) * 100

    @property
    def toil_ratio(self) -> float:
        """Percentage of alerts that required manual work."""
        if self.total_alerts == 0:
            return 0.0
        return ((self.actionable_alerts + self.false_positives) / self.total_alerts) * 100

# Target: >90% precision, <30% toil
metrics = AlertQualityMetrics(
    total_alerts=100,
    actionable_alerts=85,
    false_positives=5,
    auto_resolved=10,
)

print(f"Alert precision: {metrics.precision}%")
print(f"Toil ratio: {metrics.toil_ratio}%")
```

## On-Call Alert Guidelines

```yaml
# on_call_alert_standards.yaml
alert_standards:
  page_worthy:
    - "Immediate user impact (>5% of users affected)"
    - "SLO violation in progress"
    - "Error budget burn rate critical (>10x)"
    - "Security incident"
    - "Data loss risk"

  not_page_worthy:
    - "Predictive alerts without current impact"
    - "Informational metrics"
    - "Non-user-facing issues"
    - "Slow trends (address during business hours)"

  alert_routing:
    critical:
      - page: on-call engineer
      - slack: "#incidents"
      - create: incident doc

    warning:
      - slack: "#alerts"
      - ticket: auto-create if persists >1h

    info:
      - dashboard: only
```
