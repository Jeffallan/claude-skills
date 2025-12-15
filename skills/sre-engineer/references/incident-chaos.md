# Incident Management and Chaos Engineering

> Reference for: SRE Engineer
> Load when: Managing incidents, postmortems, chaos experiments

## Incident Response Framework

Structured approach to incident management.

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List

class Severity(Enum):
    """Incident severity levels."""
    SEV1 = "critical"     # Complete outage, major customer impact
    SEV2 = "high"         # Partial outage, significant impact
    SEV3 = "medium"       # Degraded performance, some users affected
    SEV4 = "low"          # Minor issue, minimal impact

@dataclass
class Incident:
    """Incident tracking."""
    id: str
    title: str
    severity: Severity
    started_at: datetime
    detected_at: datetime
    resolved_at: datetime | None = None
    root_cause: str | None = None
    impact: str | None = None

    @property
    def detection_time(self) -> float:
        """Time from start to detection in minutes."""
        delta = self.detected_at - self.started_at
        return delta.total_seconds() / 60

    @property
    def mttr(self) -> float | None:
        """Mean Time To Repair in minutes."""
        if not self.resolved_at:
            return None
        delta = self.resolved_at - self.detected_at
        return delta.total_seconds() / 60

    @property
    def total_duration(self) -> float | None:
        """Total incident duration in minutes."""
        if not self.resolved_at:
            return None
        delta = self.resolved_at - self.started_at
        return delta.total_seconds() / 60

# Example incident
incident = Incident(
    id="INC-2024-001",
    title="Database connection pool exhaustion",
    severity=Severity.SEV2,
    started_at=datetime(2024, 1, 15, 14, 30),
    detected_at=datetime(2024, 1, 15, 14, 35),
    resolved_at=datetime(2024, 1, 15, 15, 10),
    root_cause="Connection leak in payment service",
    impact="Payment processing delayed for 15% of users"
)

print(f"Detection time: {incident.detection_time:.1f} minutes")
print(f"MTTR: {incident.mttr:.1f} minutes")
print(f"Total duration: {incident.total_duration:.1f} minutes")
```

## Incident Response Runbook

```yaml
# incident_response.yaml
incident_response:
  detection:
    - "Acknowledge alert in PagerDuty"
    - "Join #incident-response Slack channel"
    - "Create incident doc from template"
    - "Assess severity (SEV1-4)"

  sev1_response:  # Critical - all hands
    - "Page on-call lead + backup"
    - "Notify VP Engineering immediately"
    - "Start Zoom war room"
    - "Assign incident commander"
    - "Assign communication lead"
    - "Post status update every 15 minutes"

  sev2_response:  # High - team response
    - "Page on-call engineer"
    - "Notify team lead"
    - "Create incident channel"
    - "Post status update every 30 minutes"

  roles:
    incident_commander:
      - "Coordinate response efforts"
      - "Make decisions quickly"
      - "Delegate tasks"
      - "Communicate with stakeholders"

    communication_lead:
      - "Post regular status updates"
      - "Notify affected customers"
      - "Update status page"
      - "Summarize timeline"

    on_call_engineer:
      - "Investigate root cause"
      - "Implement fixes"
      - "Verify resolution"
      - "Document actions taken"

  resolution:
    - "Verify metrics returned to normal"
    - "Monitor for 30 minutes"
    - "Post final status update"
    - "Schedule postmortem within 48 hours"
    - "Close incident"
```

## Blameless Postmortem Template

```markdown
# Postmortem: [Incident Title]

**Date:** 2024-01-15
**Authors:** [Names]
**Status:** Complete
**Severity:** SEV2

## Summary

One-paragraph summary of what happened, impact, and resolution.

## Impact

- **Duration:** 40 minutes (14:30 - 15:10 UTC)
- **Users affected:** ~15% of payment transactions
- **Revenue impact:** Estimated $X delayed
- **SLO impact:** Consumed 2.3% of monthly error budget

## Timeline (all times UTC)

| Time  | Event |
|-------|-------|
| 14:30 | Deployment of payment-service v2.3.0 completed |
| 14:32 | Error rate begins increasing |
| 14:35 | Alert fires: HighErrorRate |
| 14:36 | On-call engineer acknowledges |
| 14:40 | Incident declared SEV2 |
| 14:45 | Root cause identified: connection leak |
| 14:50 | Rollback initiated |
| 14:55 | Rollback completed |
| 15:00 | Error rate returns to normal |
| 15:10 | Incident resolved, monitoring continued |

## Root Cause

The payment-service v2.3.0 deployment introduced a connection leak in the
database connection pool. The new retry logic was not properly closing
connections on timeout, causing the pool to exhaust after ~20 minutes.

## Resolution

Rolled back to payment-service v2.2.1, which immediately resolved the issue.

## Detection

**What went well:**
- Alert fired within 5 minutes of issue start
- Clear runbook helped quick diagnosis

**What could be improved:**
- Could have caught in staging with longer load test
- Database connection pool metrics not monitored

## Action Items

| Action | Owner | Priority | Due Date |
|--------|-------|----------|----------|
| Add connection pool monitoring | @alice | P0 | 2024-01-20 |
| Extend staging load tests to 30min | @bob | P1 | 2024-01-25 |
| Review all resource cleanup in retry logic | @charlie | P1 | 2024-01-30 |
| Add integration test for connection leaks | @dave | P2 | 2024-02-05 |

## Lessons Learned

**What went well:**
- Quick detection and response
- Effective team communication
- Clear rollback procedure

**What didn't go well:**
- Issue not caught in pre-production testing
- No monitoring for connection pool exhaustion

**Where we got lucky:**
- Issue occurred during low-traffic period
- Only affected payment service, not critical systems
```

## Chaos Engineering

Proactively test system resilience through controlled failure injection.

```python
# chaos_experiment.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable

class ExperimentStatus(Enum):
    """Chaos experiment lifecycle states."""
    PLANNED = "planned"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"

@dataclass
class ChaosExperiment:
    """Define a chaos engineering experiment."""
    name: str
    hypothesis: str  # What we expect to happen
    blast_radius: str  # Scope of impact
    rollback_plan: str
    success_criteria: str
    status: ExperimentStatus = ExperimentStatus.PLANNED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    observations: list[str] | None = None

    def should_abort(self, metrics: dict) -> bool:
        """Check if experiment should be aborted.

        Args:
            metrics: Current system metrics

        Returns:
            bool: True if experiment should abort
        """
        # Abort if error rate exceeds 10%
        if metrics.get('error_rate', 0) > 0.10:
            return True

        # Abort if latency p99 exceeds 2 seconds
        if metrics.get('latency_p99', 0) > 2.0:
            return True

        return False

# Example: Database failover experiment
db_failover_experiment = ChaosExperiment(
    name="Database Primary Failover",
    hypothesis="System automatically fails over to replica within 30s with <1% error rate",
    blast_radius="Single database instance, 50% of production traffic",
    rollback_plan="Restore primary database immediately, redirect traffic",
    success_criteria="- Failover completes in <30s\n- Error rate <1%\n- No data loss",
)
```

## Chaos Testing Patterns

```python
# chaos_patterns.py - Common chaos engineering patterns
import time
import random
from typing import Protocol

class ChaosInjector(Protocol):
    """Interface for chaos injection."""

    def inject(self) -> None:
        """Inject chaos into the system."""
        ...

    def rollback(self) -> None:
        """Remove chaos and restore normal operation."""
        ...

class LatencyInjector:
    """Inject artificial latency into requests."""

    def __init__(self, target_service: str, latency_ms: int):
        self.target_service = target_service
        self.latency_ms = latency_ms

    def inject(self) -> None:
        """Add latency using iptables or proxy."""
        # Example using tc (traffic control) on Linux
        import subprocess
        subprocess.run([
            "tc", "qdisc", "add", "dev", "eth0",
            "root", "netem", "delay", f"{self.latency_ms}ms"
        ])

    def rollback(self) -> None:
        """Remove latency."""
        import subprocess
        subprocess.run(["tc", "qdisc", "del", "dev", "eth0", "root"])

class PodKiller:
    """Kill pods to test resilience."""

    def __init__(self, namespace: str, label_selector: str, kill_percentage: float = 0.5):
        self.namespace = namespace
        self.label_selector = label_selector
        self.kill_percentage = kill_percentage
        self.killed_pods = []

    def inject(self) -> None:
        """Randomly kill pods matching selector."""
        import subprocess

        # Get pods
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", self.namespace,
             "-l", self.label_selector, "-o", "name"],
            capture_output=True,
            text=True
        )

        pods = result.stdout.strip().split('\n')
        num_to_kill = int(len(pods) * self.kill_percentage)
        pods_to_kill = random.sample(pods, num_to_kill)

        # Kill selected pods
        for pod in pods_to_kill:
            subprocess.run(["kubectl", "delete", pod, "-n", self.namespace])
            self.killed_pods.append(pod)

    def rollback(self) -> None:
        """Pods will be recreated by deployment controller."""
        # Wait for pods to be recreated
        time.sleep(30)

class NetworkPartition:
    """Simulate network partition between services."""

    def __init__(self, source_pod: str, target_service: str):
        self.source_pod = source_pod
        self.target_service = target_service

    def inject(self) -> None:
        """Block network traffic using iptables."""
        import subprocess
        subprocess.run([
            "kubectl", "exec", self.source_pod, "--",
            "iptables", "-A", "OUTPUT", "-d", self.target_service, "-j", "DROP"
        ])

    def rollback(self) -> None:
        """Restore network traffic."""
        import subprocess
        subprocess.run([
            "kubectl", "exec", self.source_pod, "--",
            "iptables", "-D", "OUTPUT", "-d", self.target_service, "-j", "DROP"
        ])
```

## Chaos Experiment Runner

```python
# chaos_runner.py - Safe chaos experiment execution
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

@dataclass
class SafetyConstraints:
    """Safety constraints for chaos experiments."""
    max_error_rate: float = 0.10  # 10%
    max_latency_p99: float = 2.0  # 2 seconds
    max_duration_minutes: int = 15
    business_hours_only: bool = True

class ChaosRunner:
    """Safely execute chaos experiments with monitoring."""

    def __init__(self, safety: SafetyConstraints):
        self.safety = safety

    def run_experiment(
        self,
        experiment: ChaosExperiment,
        injector: ChaosInjector,
        get_metrics: Callable[[], dict],
    ) -> ChaosExperiment:
        """Execute chaos experiment safely.

        Args:
            experiment: Experiment definition
            injector: Chaos injector implementation
            get_metrics: Function to fetch current metrics

        Returns:
            Updated experiment with results
        """
        # Pre-flight checks
        if self.safety.business_hours_only:
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 17:  # Business hours
                experiment.status = ExperimentStatus.ABORTED
                experiment.observations = ["Aborted: Business hours constraint"]
                return experiment

        # Baseline metrics
        baseline_metrics = get_metrics()
        print(f"Baseline metrics: {baseline_metrics}")

        # Start experiment
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now()
        experiment.observations = []

        try:
            # Inject chaos
            print(f"Injecting chaos: {experiment.name}")
            injector.inject()

            # Monitor for max duration
            start_time = datetime.now()
            max_duration = timedelta(minutes=self.safety.max_duration_minutes)

            while datetime.now() - start_time < max_duration:
                time.sleep(10)  # Check every 10 seconds

                current_metrics = get_metrics()
                experiment.observations.append(
                    f"{datetime.now().isoformat()}: {current_metrics}"
                )

                # Check safety constraints
                if experiment.should_abort(current_metrics):
                    print("ABORTING: Safety constraint violated")
                    experiment.status = ExperimentStatus.ABORTED
                    break

            else:
                # Completed successfully
                experiment.status = ExperimentStatus.SUCCESS

        except Exception as e:
            print(f"ERROR: {e}")
            experiment.status = ExperimentStatus.FAILED
            experiment.observations.append(f"Exception: {str(e)}")

        finally:
            # Always rollback
            print("Rolling back chaos injection")
            injector.rollback()
            experiment.completed_at = datetime.now()

        return experiment

# Example usage
def get_current_metrics() -> dict:
    """Fetch metrics from Prometheus."""
    # In real implementation, query Prometheus
    return {
        'error_rate': 0.02,  # 2%
        'latency_p99': 0.45,  # 450ms
    }

safety = SafetyConstraints(business_hours_only=False)
runner = ChaosRunner(safety)

experiment = ChaosExperiment(
    name="Kill 50% of API pods",
    hypothesis="API remains available with 50% pod loss",
    blast_radius="50% of API pods",
    rollback_plan="Pods auto-restart via deployment",
    success_criteria="Error rate <5%, latency p99 <1s",
)

injector = PodKiller(
    namespace="production",
    label_selector="app=api",
    kill_percentage=0.5,
)

result = runner.run_experiment(experiment, injector, get_current_metrics)
print(f"Experiment status: {result.status.value}")
```

## Game Days

Scheduled chaos engineering practice sessions.

```yaml
# gameday_plan.yaml
gameday:
  date: "2024-02-15"
  duration: "2 hours"
  participants:
    - SRE team
    - Backend engineers
    - On-call rotation

  objectives:
    - Test incident response procedures
    - Validate monitoring and alerting
    - Practice communication protocols
    - Identify gaps in runbooks

  scenarios:
    - scenario: "Database Primary Failure"
      inject: "Terminate primary database pod"
      expected: "Automatic failover to replica in <30s"

    - scenario: "API Service Overload"
      inject: "Generate 10x normal traffic"
      expected: "Rate limiting activates, no errors"

    - scenario: "Network Partition"
      inject: "Block traffic between API and database"
      expected: "Circuit breaker opens, graceful degradation"

  success_criteria:
    - "All scenarios handled without escalation"
    - "MTTR <30 minutes for all scenarios"
    - "Documentation updated with learnings"
    - "Action items created for gaps"

  safety:
    - "Run in staging environment first"
    - "VP Engineering notified beforehand"
    - "Abort plan ready for each scenario"
    - "Customer support team on standby"
```

## Chaos Engineering Maturity

```python
from enum import IntEnum

class ChaosMaturity(IntEnum):
    """Chaos engineering maturity levels."""
    NONE = 0          # No chaos testing
    AD_HOC = 1        # Occasional manual tests
    SCHEDULED = 2     # Regular game days
    CONTINUOUS = 3    # Automated in CI/CD
    CULTURE = 4       # Embedded in development

def assess_maturity(practices: dict[str, bool]) -> ChaosMaturity:
    """Assess chaos engineering maturity level."""

    if not practices.get('any_chaos_testing'):
        return ChaosMaturity.NONE

    if not practices.get('regular_game_days'):
        return ChaosMaturity.AD_HOC

    if not practices.get('automated_chaos'):
        return ChaosMaturity.SCHEDULED

    if not practices.get('chaos_in_cicd'):
        return ChaosMaturity.CONTINUOUS

    return ChaosMaturity.CULTURE

# Example assessment
current_practices = {
    'any_chaos_testing': True,
    'regular_game_days': True,
    'automated_chaos': True,
    'chaos_in_cicd': False,
}

maturity = assess_maturity(current_practices)
print(f"Chaos maturity: {maturity.name}")
# Target: CONTINUOUS or CULTURE
