# Error Budget Policy

> Reference for: SRE Engineer
> Load when: Managing error budgets, burn rates, release policies

## Error Budget Fundamentals

Error budget = 1 - SLO target. It represents acceptable unreliability.

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class BudgetStatus(Enum):
    """Error budget health status."""
    HEALTHY = "healthy"      # >75% budget remaining
    WARNING = "warning"      # 25-75% budget remaining
    CRITICAL = "critical"    # <25% budget remaining
    EXHAUSTED = "exhausted"  # 0% budget remaining

@dataclass
class ErrorBudget:
    """Error budget tracker."""
    slo_target: float  # e.g., 0.999
    window_days: int   # e.g., 30

    @property
    def budget_percentage(self) -> float:
        """Total error budget as percentage."""
        return (1 - self.slo_target) * 100

    @property
    def allowed_downtime(self) -> timedelta:
        """Maximum allowed downtime in window."""
        total_minutes = self.window_days * 24 * 60
        error_minutes = total_minutes * (1 - self.slo_target)
        return timedelta(minutes=error_minutes)

    def remaining_budget(self, actual_sli: float) -> float:
        """Calculate remaining error budget percentage.

        Returns:
            float: 0.0 to 1.0, where 1.0 = 100% budget remaining
        """
        budget_used = 1 - actual_sli
        total_budget = 1 - self.slo_target

        if total_budget == 0:
            return 0.0

        return max(0.0, 1 - (budget_used / total_budget))

    def get_status(self, actual_sli: float) -> BudgetStatus:
        """Determine budget health status."""
        remaining = self.remaining_budget(actual_sli)

        if remaining <= 0:
            return BudgetStatus.EXHAUSTED
        elif remaining < 0.25:
            return BudgetStatus.CRITICAL
        elif remaining < 0.75:
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.HEALTHY

# Example
budget = ErrorBudget(slo_target=0.999, window_days=30)
print(f"Error budget: {budget.budget_percentage}%")
print(f"Allowed downtime: {budget.allowed_downtime}")
# Output:
# Error budget: 0.1%
# Allowed downtime: 43.2 minutes
```

## Burn Rate Alerting

Burn rate measures how fast you're consuming error budget.

```python
from typing import NamedTuple

class BurnRateAlert(NamedTuple):
    """Multi-window burn rate alert configuration."""
    window: timedelta
    burn_rate_threshold: float
    budget_consumed_threshold: float

    def should_alert(
        self,
        current_error_rate: float,
        total_budget: float
    ) -> bool:
        """Check if burn rate exceeds threshold.

        Args:
            current_error_rate: Current error rate (1 - SLI)
            total_budget: Total error budget (1 - SLO)

        Returns:
            bool: True if should alert
        """
        if total_budget == 0:
            return current_error_rate > 0

        burn_rate = current_error_rate / total_budget
        return burn_rate >= self.burn_rate_threshold

# Multi-window burn rate alerts (from Google SRE Workbook)
BURN_RATE_ALERTS = [
    # Fast burn: 2% budget in 1 hour = exhausted in 2 days
    BurnRateAlert(
        window=timedelta(hours=1),
        burn_rate_threshold=14.4,  # 2% of 30d budget in 1h
        budget_consumed_threshold=0.02
    ),
    # Medium burn: 5% budget in 6 hours
    BurnRateAlert(
        window=timedelta(hours=6),
        burn_rate_threshold=6.0,
        budget_consumed_threshold=0.05
    ),
    # Slow burn: 10% budget in 3 days
    BurnRateAlert(
        window=timedelta(days=3),
        burn_rate_threshold=1.0,
        budget_consumed_threshold=0.10
    ),
]

def check_burn_rate_alerts(slo_target: float, current_sli: float):
    """Check if any burn rate alerts should fire."""
    error_budget = 1 - slo_target
    error_rate = 1 - current_sli

    alerts = []
    for alert_config in BURN_RATE_ALERTS:
        if alert_config.should_alert(error_rate, error_budget):
            alerts.append(alert_config)

    return alerts
```

## Error Budget Policy Template

```yaml
# error_budget_policy.yaml
service: payment-api
slo:
  target: 99.9%
  measurement_window: 30 days

policy:
  # Actions based on remaining error budget
  actions:
    - threshold: 100%  # Budget healthy
      state: normal_operations
      actions:
        - "Continue feature development"
        - "Deploy during business hours"
        - "Standard change review process"

    - threshold: 50%   # Budget warning
      state: careful_operations
      actions:
        - "Increase code review rigor"
        - "Require senior engineer approval for deploys"
        - "Conduct pre-deployment risk assessment"
        - "Enhanced monitoring during deploys"

    - threshold: 25%   # Budget critical
      state: restricted_operations
      actions:
        - "Halt non-critical feature work"
        - "Focus on reliability improvements"
        - "Require VP approval for deployments"
        - "Deploy only critical bug fixes"
        - "Daily error budget review meetings"

    - threshold: 0%    # Budget exhausted
      state: feature_freeze
      actions:
        - "Immediate feature freeze"
        - "Deploy only emergency fixes"
        - "All hands reliability review"
        - "Mandatory postmortem for all incidents"
        - "Weekly executive review until recovered"

  # Exceptions to policy
  exceptions:
    - type: security_patch
      approval: security_team
      allowed: true

    - type: critical_business_requirement
      approval: vp_engineering + product_lead
      allowed: true
      requires_review: true
```

## Error Budget Calculation

```python
class ErrorBudgetCalculator:
    """Calculate and track error budget consumption."""

    def __init__(self, slo_target: float, window_days: int = 30):
        self.slo_target = slo_target
        self.window_days = window_days
        self.total_budget = 1 - slo_target

    def calculate_budget_status(
        self,
        good_events: int,
        total_events: int
    ) -> dict:
        """Calculate comprehensive budget status.

        Returns:
            dict: Budget status including remaining budget, burn rate, etc.
        """
        if total_events == 0:
            sli = 1.0
        else:
            sli = good_events / total_events

        budget_used = 1 - sli
        budget_remaining = self.total_budget - budget_used
        budget_remaining_pct = (
            (budget_remaining / self.total_budget * 100)
            if self.total_budget > 0 else 0
        )

        # Calculate burn rate
        burn_rate = budget_used / self.total_budget if self.total_budget > 0 else 0

        # Estimate time to exhaustion at current rate
        if burn_rate > 0:
            days_to_exhaustion = budget_remaining / budget_used * self.window_days
        else:
            days_to_exhaustion = float('inf')

        return {
            'sli': sli,
            'slo_target': self.slo_target,
            'compliant': sli >= self.slo_target,
            'budget_total': self.total_budget,
            'budget_used': budget_used,
            'budget_remaining': budget_remaining,
            'budget_remaining_pct': budget_remaining_pct,
            'burn_rate': burn_rate,
            'days_to_exhaustion': days_to_exhaustion,
            'good_events': good_events,
            'total_events': total_events,
        }

# Example usage
calc = ErrorBudgetCalculator(slo_target=0.999, window_days=30)
status = calc.calculate_budget_status(
    good_events=999_500,
    total_events=1_000_000
)

print(f"SLI: {status['sli']:.4f}")
print(f"Compliant: {status['compliant']}")
print(f"Budget remaining: {status['budget_remaining_pct']:.1f}%")
print(f"Days to exhaustion: {status['days_to_exhaustion']:.1f}")
```

## Prometheus Queries for Error Budgets

```promql
# Calculate 30-day availability SLI
sum(rate(http_requests_total{status=~"2..", job="api"}[30d]))
/
sum(rate(http_requests_total{job="api"}[30d]))

# Calculate error budget consumption
1 - (
  sum(rate(http_requests_total{status=~"2..", job="api"}[30d]))
  /
  sum(rate(http_requests_total{job="api"}[30d]))
)

# Calculate remaining error budget (for 99.9% SLO)
(0.001 - (1 - (
  sum(rate(http_requests_total{status=~"2..", job="api"}[30d]))
  /
  sum(rate(http_requests_total{job="api"}[30d]))
))) / 0.001

# Burn rate (normalized to 1.0 = sustainable)
(1 - (
  sum(rate(http_requests_total{status=~"2..", job="api"}[1h]))
  /
  sum(rate(http_requests_total{job="api"}[1h]))
)) / 0.001
```

## Decision Framework

Use this framework to make reliability vs. velocity tradeoffs:

```python
def should_deploy(
    budget_remaining: float,
    change_risk: str,  # 'low', 'medium', 'high'
    business_priority: str,  # 'low', 'medium', 'high', 'critical'
) -> tuple[bool, str]:
    """Decide if deployment should proceed.

    Returns:
        tuple: (should_deploy, reason)
    """
    # Budget exhausted - only critical changes
    if budget_remaining <= 0:
        if business_priority == 'critical':
            return True, "Critical business need, budget exhausted"
        return False, "Error budget exhausted, feature freeze in effect"

    # Budget critical (<25%)
    if budget_remaining < 0.25:
        if change_risk == 'high':
            return False, "High risk change with critical budget"
        if business_priority in ['high', 'critical']:
            return True, "High priority with critical budget - proceed carefully"
        return False, "Budget critical, deferring non-essential changes"

    # Budget warning (25-75%)
    if budget_remaining < 0.75:
        if change_risk == 'high' and business_priority == 'low':
            return False, "High risk, low priority with warning budget"
        return True, "Approved with enhanced review"

    # Budget healthy (>75%)
    return True, "Normal operations, budget healthy"
```
