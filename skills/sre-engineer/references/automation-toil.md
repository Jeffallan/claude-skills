# Automation and Toil Reduction

## Toil Definition

Toil is manual, repetitive, automatable work that scales linearly with service growth.

```python
from dataclasses import dataclass
from enum import Enum

class ToilCategory(Enum):
    """Categories of operational toil."""
    MANUAL_INTERVENTION = "manual"
    REPETITIVE_TASKS = "repetitive"
    NO_ENDURING_VALUE = "no_value"
    SCALES_WITH_SERVICE = "scales"
    INTERRUPT_DRIVEN = "reactive"

@dataclass
class ToilItem:
    """Track a specific toil activity."""
    name: str
    frequency_per_week: int
    minutes_per_occurrence: int
    category: ToilCategory
    automation_difficulty: str  # 'easy', 'medium', 'hard'

    @property
    def weekly_hours(self) -> float:
        """Calculate weekly hours spent on this toil."""
        return (self.frequency_per_week * self.minutes_per_occurrence) / 60

    @property
    def annual_hours(self) -> float:
        """Calculate annual hours spent on this toil."""
        return self.weekly_hours * 52

    def roi_score(self) -> float:
        """Calculate ROI score for automation (higher = better).

        Score considers time saved vs. difficulty.
        """
        difficulty_multiplier = {
            'easy': 1.0,
            'medium': 0.5,
            'hard': 0.25,
        }
        return self.annual_hours * difficulty_multiplier.get(
            self.automation_difficulty, 0.1
        )

# Example toil inventory
toil_items = [
    ToilItem(
        name="Manual database failover",
        frequency_per_week=2,
        minutes_per_occurrence=30,
        category=ToilCategory.MANUAL_INTERVENTION,
        automation_difficulty='medium',
    ),
    ToilItem(
        name="Restarting hung processes",
        frequency_per_week=5,
        minutes_per_occurrence=15,
        category=ToilCategory.REPETITIVE_TASKS,
        automation_difficulty='easy',
    ),
    ToilItem(
        name="Log file cleanup",
        frequency_per_week=7,
        minutes_per_occurrence=10,
        category=ToilCategory.SCALES_WITH_SERVICE,
        automation_difficulty='easy',
    ),
]

# Calculate total toil and prioritize automation
total_weekly_hours = sum(item.weekly_hours for item in toil_items)
print(f"Total weekly toil: {total_weekly_hours:.1f} hours")

# Sort by ROI score to prioritize automation
sorted_items = sorted(toil_items, key=lambda x: x.roi_score(), reverse=True)
for item in sorted_items:
    print(f"{item.name}: {item.roi_score():.1f} ROI score")
```

## Self-Healing Systems

Automate common failure remediation.

```python
# auto_healing.py - Self-healing automation examples
import subprocess
import logging
from typing import Callable, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HealthCheck:
    """Define a health check and remediation."""
    name: str
    check: Callable[[], bool]
    remediate: Callable[[], bool]
    max_retries: int = 3

class SelfHealer:
    """Automatically remediate common failures."""

    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}

    def register(self, check: HealthCheck):
        """Register a health check with remediation."""
        self.health_checks[check.name] = check

    def run(self):
        """Run all health checks and remediate failures."""
        for name, check in self.health_checks.items():
            if not check.check():
                logger.warning(f"Health check failed: {name}")
                self._remediate(check)

    def _remediate(self, check: HealthCheck):
        """Attempt remediation with retries."""
        for attempt in range(check.max_retries):
            logger.info(f"Remediation attempt {attempt + 1}/{check.max_retries}")

            if check.remediate():
                logger.info(f"Remediation successful: {check.name}")
                return

            if check.check():
                logger.info(f"Health check passed after remediation: {check.name}")
                return

        logger.error(f"Remediation failed after {check.max_retries} attempts")
        self._escalate(check)

    def _escalate(self, check: HealthCheck):
        """Escalate to on-call when auto-remediation fails."""
        # Send alert to on-call
        logger.error(f"ESCALATING: {check.name} - auto-remediation failed")

# Example health checks
def check_disk_space() -> bool:
    """Check if disk space is above 20%."""
    result = subprocess.run(
        ["df", "-h", "/"],
        capture_output=True,
        text=True
    )
    # Parse df output and check available space
    lines = result.stdout.strip().split('\n')
    if len(lines) > 1:
        fields = lines[1].split()
        use_percent = int(fields[4].rstrip('%'))
        return use_percent < 80
    return True

def cleanup_disk() -> bool:
    """Clean up old log files."""
    try:
        # Delete logs older than 7 days
        subprocess.run(
            ["find", "/var/log", "-name", "*.log", "-mtime", "+7", "-delete"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def check_service_responsive() -> bool:
    """Check if service responds to health endpoint."""
    try:
        result = subprocess.run(
            ["curl", "-f", "http://localhost:8080/health"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False

def restart_service() -> bool:
    """Restart the service."""
    try:
        subprocess.run(
            ["systemctl", "restart", "myservice"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

# Set up self-healing
healer = SelfHealer()
healer.register(HealthCheck(
    name="disk_space",
    check=check_disk_space,
    remediate=cleanup_disk,
))
healer.register(HealthCheck(
    name="service_health",
    check=check_service_responsive,
    remediate=restart_service,
))

# Run as cron job or systemd timer
if __name__ == "__main__":
    healer.run()
```

## Runbook Automation

Convert manual runbooks to automated scripts.

```python
# runbook_automation.py
from typing import List, Tuple
from dataclasses import dataclass
import subprocess
import json

@dataclass
class RunbookStep:
    """A single step in a runbook."""
    description: str
    command: str
    critical: bool = True  # Stop on failure?
    verify: str | None = None  # Optional verification command

class AutomatedRunbook:
    """Execute runbook steps automatically."""

    def __init__(self, name: str):
        self.name = name
        self.steps: List[RunbookStep] = []

    def add_step(self, step: RunbookStep):
        """Add a step to the runbook."""
        self.steps.append(step)

    def execute(self, dry_run: bool = False) -> Tuple[bool, List[str]]:
        """Execute all runbook steps.

        Args:
            dry_run: If True, only print commands without executing

        Returns:
            tuple: (success, output_lines)
        """
        outputs = []

        for i, step in enumerate(self.steps, 1):
            outputs.append(f"\n[Step {i}/{len(self.steps)}] {step.description}")

            if dry_run:
                outputs.append(f"Would run: {step.command}")
                continue

            # Execute command
            try:
                result = subprocess.run(
                    step.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode != 0:
                    outputs.append(f"ERROR: {result.stderr}")
                    if step.critical:
                        return False, outputs
                else:
                    outputs.append(result.stdout)

                # Run verification if specified
                if step.verify:
                    verify_result = subprocess.run(
                        step.verify,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                    if verify_result.returncode != 0:
                        outputs.append(f"VERIFICATION FAILED: {verify_result.stderr}")
                        if step.critical:
                            return False, outputs

            except subprocess.TimeoutExpired:
                outputs.append(f"ERROR: Command timed out")
                if step.critical:
                    return False, outputs

        return True, outputs

# Example: Database failover runbook
failover_runbook = AutomatedRunbook("Database Failover")

failover_runbook.add_step(RunbookStep(
    description="Stop writes to primary database",
    command="kubectl exec -it postgres-primary-0 -- psql -c 'ALTER SYSTEM SET default_transaction_read_only = on;'",
    critical=True,
))

failover_runbook.add_step(RunbookStep(
    description="Wait for replication lag to clear",
    command="sleep 10",
    critical=False,
))

failover_runbook.add_step(RunbookStep(
    description="Promote replica to primary",
    command="kubectl exec -it postgres-replica-0 -- pg_ctl promote",
    critical=True,
    verify="kubectl exec -it postgres-replica-0 -- psql -c 'SELECT pg_is_in_recovery();' | grep -q 'f'",
))

failover_runbook.add_step(RunbookStep(
    description="Update service to point to new primary",
    command="kubectl patch service postgres -p '{\"spec\":{\"selector\":{\"role\":\"replica\"}}}'",
    critical=True,
))

# Execute
success, output = failover_runbook.execute(dry_run=False)
print('\n'.join(output))
```

## Capacity Planning Automation

```python
# capacity_planner.py - Automated capacity planning
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

@dataclass
class CapacityMetrics:
    """Historical capacity metrics."""
    timestamp: datetime
    requests_per_second: float
    cpu_utilization: float
    memory_utilization: float

class CapacityPlanner:
    """Automated capacity planning and forecasting."""

    def __init__(self, metrics: list[CapacityMetrics]):
        self.metrics = metrics

    def forecast_growth(self, days_ahead: int = 90) -> dict:
        """Forecast resource usage growth.

        Uses linear regression on historical data.
        """
        # Extract time series
        timestamps = [(m.timestamp - self.metrics[0].timestamp).days
                      for m in self.metrics]
        cpu_values = [m.cpu_utilization for m in self.metrics]
        mem_values = [m.memory_utilization for m in self.metrics]

        # Fit linear trend
        cpu_trend = np.polyfit(timestamps, cpu_values, deg=1)
        mem_trend = np.polyfit(timestamps, mem_values, deg=1)

        # Forecast
        future_day = timestamps[-1] + days_ahead
        cpu_forecast = np.polyval(cpu_trend, future_day)
        mem_forecast = np.polyval(mem_trend, future_day)

        return {
            'days_ahead': days_ahead,
            'cpu_forecast': min(cpu_forecast, 1.0),
            'memory_forecast': min(mem_forecast, 1.0),
            'cpu_threshold_breach': cpu_forecast > 0.8,
            'memory_threshold_breach': mem_forecast > 0.8,
        }

    def recommend_scaling(self, forecast: dict) -> str:
        """Recommend scaling action based on forecast."""
        if forecast['cpu_threshold_breach'] or forecast['memory_threshold_breach']:
            return f"SCALE UP: Forecast shows >80% utilization in {forecast['days_ahead']} days"

        return "OK: No scaling needed"

# Example usage
historical_metrics = [
    CapacityMetrics(
        timestamp=datetime.now() - timedelta(days=30),
        requests_per_second=1000,
        cpu_utilization=0.45,
        memory_utilization=0.50,
    ),
    CapacityMetrics(
        timestamp=datetime.now() - timedelta(days=15),
        requests_per_second=1200,
        cpu_utilization=0.55,
        memory_utilization=0.60,
    ),
    CapacityMetrics(
        timestamp=datetime.now(),
        requests_per_second=1500,
        cpu_utilization=0.65,
        memory_utilization=0.70,
    ),
]

planner = CapacityPlanner(historical_metrics)
forecast = planner.forecast_growth(days_ahead=90)
recommendation = planner.recommend_scaling(forecast)

print(f"90-day forecast: CPU={forecast['cpu_forecast']:.1%}, Memory={forecast['memory_forecast']:.1%}")
print(recommendation)
```

## Automation Testing

```python
# test_automation.py - Test automation scripts before production
import unittest
from unittest.mock import patch, MagicMock

class TestSelfHealing(unittest.TestCase):
    """Test self-healing automation."""

    @patch('subprocess.run')
    def test_disk_cleanup_success(self, mock_run):
        """Test successful disk cleanup."""
        mock_run.return_value = MagicMock(returncode=0)

        result = cleanup_disk()

        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_service_restart_with_retry(self, mock_run):
        """Test service restart retries on failure."""
        # First attempt fails, second succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1),  # First restart fails
            MagicMock(returncode=0),  # Second restart succeeds
        ]

        # Implementation would retry on failure
        # Assert retry logic works correctly
```

## Toil Reduction Metrics

```python
# Track toil reduction progress
class ToilTracker:
    """Track toil reduction over time."""

    def __init__(self):
        self.snapshots = []

    def record_snapshot(self, week: int, toil_hours: float, team_hours: float):
        """Record toil snapshot for a week."""
        self.snapshots.append({
            'week': week,
            'toil_hours': toil_hours,
            'team_hours': team_hours,
            'toil_percentage': (toil_hours / team_hours * 100) if team_hours > 0 else 0,
        })

    def toil_trend(self) -> str:
        """Calculate if toil is increasing or decreasing."""
        if len(self.snapshots) < 2:
            return "insufficient data"

        first_pct = self.snapshots[0]['toil_percentage']
        last_pct = self.snapshots[-1]['toil_percentage']

        if last_pct < first_pct:
            return f"improving ({first_pct:.1f}% → {last_pct:.1f}%)"
        else:
            return f"worsening ({first_pct:.1f}% → {last_pct:.1f}%)"

# Target: <50% toil, ideally <30%
tracker = ToilTracker()
tracker.record_snapshot(week=1, toil_hours=30, team_hours=40)  # 75% toil
tracker.record_snapshot(week=4, toil_hours=20, team_hours=40)  # 50% toil
tracker.record_snapshot(week=8, toil_hours=12, team_hours=40)  # 30% toil

print(f"Toil trend: {tracker.toil_trend()}")
```
