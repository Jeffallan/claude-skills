# Chaos Experiment Design

> Reference for: Chaos Engineer
> Load when: Designing experiments, hypothesis formulation, blast radius planning

## Experiment Template

```yaml
name: "Database Connection Pool Exhaustion"
hypothesis: "When the database connection pool is exhausted, the application will gracefully degrade and return 503 errors without cascading failures"

steady_state:
  metrics:
    - name: "Error Rate"
      threshold: "< 0.1%"
      source: "prometheus"
      query: "rate(http_requests_total{status=~'5..'}[5m])"
    - name: "Latency P99"
      threshold: "< 500ms"
      source: "datadog"
    - name: "Active Connections"
      threshold: "> 10"
      query: "pg_stat_activity_count"

blast_radius:
  environment: "staging"
  traffic_percentage: 10
  duration_seconds: 300
  max_error_rate: "5%"
  auto_rollback: true

injection:
  type: "resource_exhaustion"
  target: "database_connections"
  method: "connection_leak"
  parameters:
    leak_rate: 5  # connections per second
    max_leaked: 50

safety:
  rollback_triggers:
    - "error_rate > 5%"
    - "manual_kill_switch"
    - "duration_exceeded"
  rollback_time_limit_seconds: 30
  alerts:
    - slack: "#chaos-engineering"
    - pagerduty: "chaos-team"

success_criteria:
  - "Circuit breakers activate within 10s"
  - "503 errors returned (not 500)"
  - "No cascading failures to other services"
  - "System recovers within 60s of rollback"
```

## Hypothesis Formulation

```python
def create_hypothesis(component: str, failure: str, expected_behavior: str) -> dict:
    """
    Create well-formed chaos hypothesis.

    Format: "Given [normal state], when [failure occurs],
             then [expected behavior], measured by [metrics]"
    """
    return {
        "given": f"System is in steady state with {component} functioning normally",
        "when": f"{failure} occurs",
        "then": expected_behavior,
        "measured_by": [
            "Error rate remains below threshold",
            "Latency stays within SLO",
            "No data loss or corruption",
            "Recovery time within RTO"
        ]
    }

# Example
hypothesis = create_hypothesis(
    component="payment service",
    failure="50% packet loss to payment gateway",
    expected_behavior="Requests timeout gracefully, retry queue activates, "
                     "users see clear error messages"
)
```

## Blast Radius Control

```python
from dataclasses import dataclass
from enum import Enum

class BlastRadiusLevel(Enum):
    MINIMAL = "single_instance_dev"
    LOW = "single_instance_staging"
    MEDIUM = "percentage_staging"
    HIGH = "percentage_production"
    CRITICAL = "full_production"

@dataclass
class BlastRadiusConfig:
    level: BlastRadiusLevel
    environment: str
    target_percentage: float  # 0-100
    canary_users: list[str]
    feature_flag: str
    auto_rollback: bool
    max_duration_seconds: int

    def validate(self):
        """Enforce safety rules."""
        if self.level == BlastRadiusLevel.CRITICAL:
            raise ValueError("CRITICAL blast radius requires explicit approval")

        if self.environment == "production" and self.target_percentage > 10:
            if not self.feature_flag or not self.auto_rollback:
                raise ValueError("Production >10% requires feature flag AND auto-rollback")

        if self.max_duration_seconds > 600:
            raise ValueError("Max duration cannot exceed 10 minutes without approval")

# Progressive blast radius expansion
def progressive_rollout() -> list[BlastRadiusConfig]:
    return [
        BlastRadiusConfig(
            level=BlastRadiusLevel.MINIMAL,
            environment="dev",
            target_percentage=100,
            canary_users=[],
            feature_flag="chaos_dev",
            auto_rollback=True,
            max_duration_seconds=300
        ),
        BlastRadiusConfig(
            level=BlastRadiusLevel.LOW,
            environment="staging",
            target_percentage=100,
            canary_users=[],
            feature_flag="chaos_staging",
            auto_rollback=True,
            max_duration_seconds=600
        ),
        BlastRadiusConfig(
            level=BlastRadiusLevel.MEDIUM,
            environment="production",
            target_percentage=1,
            canary_users=["internal_team"],
            feature_flag="chaos_prod_canary",
            auto_rollback=True,
            max_duration_seconds=300
        )
    ]
```

## Safety Mechanisms

```python
import asyncio
from typing import Callable

class ChaosExperimentSafety:
    def __init__(self, config: dict):
        self.config = config
        self.kill_switch_active = False
        self.metrics = {}

    async def run_with_safety(self, chaos_fn: Callable):
        """Execute chaos with automatic safety checks."""
        # Pre-flight checks
        if not await self.verify_steady_state():
            raise Exception("System not in steady state - aborting")

        # Set up rollback trigger
        rollback_task = asyncio.create_task(self.monitor_for_rollback())
        chaos_task = asyncio.create_task(chaos_fn())

        try:
            # Wait for either chaos completion or rollback trigger
            done, pending = await asyncio.wait(
                [chaos_task, rollback_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            if rollback_task in done:
                # Rollback triggered - cancel chaos
                chaos_task.cancel()
                await self.rollback()

        finally:
            await self.ensure_system_recovery()

    async def verify_steady_state(self) -> bool:
        """Check all steady state metrics are within threshold."""
        for metric in self.config['steady_state']['metrics']:
            value = await self.query_metric(metric['query'])
            if not self.within_threshold(value, metric['threshold']):
                return False
        return True

    async def monitor_for_rollback(self):
        """Continuously monitor for rollback triggers."""
        start_time = asyncio.get_event_loop().time()

        while True:
            # Check duration limit
            if asyncio.get_event_loop().time() - start_time > \
               self.config['blast_radius']['duration_seconds']:
                return "duration_exceeded"

            # Check manual kill switch
            if self.kill_switch_active:
                return "manual_kill_switch"

            # Check error rate
            error_rate = await self.query_metric("error_rate")
            if error_rate > float(self.config['blast_radius']['max_error_rate'].strip('%')):
                return "error_rate_exceeded"

            await asyncio.sleep(5)  # Check every 5 seconds
```

## Quick Reference

| Phase | Key Actions | Time Limit |
|-------|-------------|------------|
| Design | Hypothesis, metrics, blast radius | 1 hour |
| Review | Team review, safety check | 30 min |
| Prepare | Setup monitoring, rollback | 1 hour |
| Execute | Run experiment, monitor | 5-10 min |
| Rollback | Restore steady state | < 30 sec |
| Learn | Document findings, plan fixes | 2 hours |
