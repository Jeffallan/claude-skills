# Game Day Planning & Execution

> Reference for: Chaos Engineer
> Load when: Game day planning, organizational resilience, team drills

## Game Day Planning Template

```yaml
game_day:
  name: "Database Failover Drill"
  date: "2025-01-15"
  time: "10:00-12:00 PST"
  environment: "staging"  # Start in staging

  objectives:
    - "Verify RDS failover to standby in under 2 minutes"
    - "Validate application auto-reconnect logic"
    - "Test monitoring and alerting effectiveness"
    - "Practice incident response procedures"

  participants:
    facilitator: "chaos-engineer@company.com"
    observers:
      - "sre-team@company.com"
      - "dev-team@company.com"
    responders:
      - "on-call-engineer@company.com"
      - "database-admin@company.com"
    stakeholders:
      - "engineering-manager@company.com"

  scenarios:
    - name: "Primary database instance failure"
      duration_minutes: 30
      steps:
        - action: "Force RDS instance reboot with failover"
          expected: "Failover to standby in <2 min"
          success_criteria:
            - "Downtime < 2 minutes"
            - "No data loss"
            - "Alerts fired correctly"

    - name: "Network partition to database"
      duration_minutes: 20
      steps:
        - action: "Block network traffic to RDS security group"
          expected: "Application switches to read replica"
          success_criteria:
            - "Read-only mode activated"
            - "User-facing error messages clear"

  communication_plan:
    announcement_channel: "#game-day-announcements"
    war_room: "Zoom link: https://..."
    status_updates_every: "5 minutes"
    escalation_contacts:
      - name: "VP Engineering"
        phone: "+1-555-0100"
        threshold: "downtime > 5 minutes"

  rollback_plan:
    automatic_rollback_triggers:
      - "production traffic affected"
      - "customer complaints received"
      - "error_rate > 10%"
    manual_rollback_command: "aws rds reboot-db-instance --db-instance-identifier primary --force-failover"
    rollback_time_limit_seconds: 60

  success_metrics:
    - metric: "RTO (Recovery Time Objective)"
      target: "< 2 minutes"
      measurement: "time between failure and full recovery"
    - metric: "Alert accuracy"
      target: "100%"
      measurement: "all expected alerts fired"
    - metric: "Team response time"
      target: "< 5 minutes"
      measurement: "time to acknowledge incident"

  post_mortem:
    scheduled_for: "2025-01-16 14:00"
    template: "game-day-retro.md"
    required_attendees: "all participants"
```

## Game Day Runbook

```markdown
# Database Failover Game Day Runbook

**Date**: January 15, 2025
**Duration**: 2 hours
**Environment**: Staging

## Pre-Game Checklist (T-30 min)

- [ ] Verify all participants joined war room
- [ ] Confirm monitoring dashboards accessible
- [ ] Test rollback procedures work
- [ ] Announce game day start in #engineering
- [ ] Verify staging environment healthy
- [ ] Set up screen recording for timeline
- [ ] Prepare incident timeline spreadsheet

## Timeline

### 10:00 - Introduction (10 min)
- Facilitator explains objectives
- Review scenarios and success criteria
- Confirm roles and communication channels
- Remind everyone: this is a learning exercise

### 10:10 - Scenario 1: Primary DB Failure (30 min)

**T+0 (10:10)** - Inject failure
```bash
aws rds reboot-db-instance \
  --db-instance-identifier staging-primary \
  --force-failover
```

**Expected Timeline**:
- T+0: Reboot initiated
- T+30s: Primary becomes unavailable
- T+60s: DNS updated to standby
- T+90s: Application reconnects
- T+120s: Full recovery

**Observer Tasks**:
- [ ] Record exact time of failure injection
- [ ] Monitor application error logs
- [ ] Track alert notifications
- [ ] Document team response actions
- [ ] Screenshot dashboard states

**Questions to Answer**:
- How long until first alert?
- Did application auto-reconnect?
- Were customers impacted?
- What manual interventions needed?

### 10:40 - Debrief Scenario 1 (10 min)
- What went well?
- What could improve?
- Any surprises?
- Action items identified

### 10:50 - Scenario 2: Network Partition (20 min)

**T+0 (10:50)** - Inject failure
```bash
# Block database security group ingress
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 5432 \
  --cidr 10.0.0.0/16
```

**Expected Behavior**:
- Connection timeouts occur
- Circuit breaker opens
- Read-only mode activates
- Clear error messages shown

**Observer Tasks**:
- [ ] Monitor circuit breaker state
- [ ] Verify read-replica failover
- [ ] Check user-facing error messages
- [ ] Track degraded service duration

### 11:10 - Debrief Scenario 2 (10 min)

### 11:20 - Scenario 3: Surprise! (20 min)

**Facilitator Note**: Don't announce this scenario details beforehand.
Test true incident response capability.

**Hidden Scenario**: Combination failure
1. Database connection pool leak
2. Simultaneous cache invalidation

```python
# Connection leak simulator
import psycopg2
connections = []
for i in range(100):
    conn = psycopg2.connect(DATABASE_URL)
    connections.append(conn)
    # Intentionally don't close
```

**Observer Tasks**:
- [ ] How long to identify root cause?
- [ ] Communication effectiveness
- [ ] Cross-team coordination
- [ ] Escalation decisions

### 11:40 - Final Debrief & Wrap-up (20 min)

**Debrief Questions**:
1. What worked well?
2. What didn't work?
3. What surprised us?
4. What are our top 3 action items?
5. When should we run this again?

## Post-Game Checklist

- [ ] Restore all services to normal state
- [ ] Verify no lingering issues
- [ ] Collect all observer notes
- [ ] Export metrics and dashboards
- [ ] Schedule post-mortem meeting
- [ ] Send thank-you to participants
- [ ] Create action item tickets
- [ ] Update runbooks based on learnings
```

## Game Day Observation Template

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class GameDayObservation:
    timestamp: datetime
    observer: str
    scenario: str
    observation: str
    category: str  # technical, process, communication, surprise
    severity: str  # info, concern, critical
    photo_url: str = ""

@dataclass
class GameDayMetrics:
    scenario_name: str
    start_time: datetime
    end_time: datetime

    # Technical metrics
    time_to_detect_seconds: float
    time_to_respond_seconds: float
    time_to_recover_seconds: float
    error_rate_peak: float
    alerts_fired: List[str] = field(default_factory=list)
    alerts_missed: List[str] = field(default_factory=list)

    # Team metrics
    responders_involved: int
    escalations_needed: int
    communication_gaps: List[str] = field(default_factory=list)

    # Success criteria
    met_rto: bool = False
    met_rpo: bool = False
    zero_customer_impact: bool = False

    def calculate_mttr(self) -> float:
        """Mean Time To Recovery"""
        return (self.end_time - self.start_time).total_seconds()

    def success_rate(self) -> float:
        """Percentage of success criteria met"""
        criteria = [
            self.met_rto,
            self.met_rpo,
            self.zero_customer_impact,
            len(self.alerts_missed) == 0
        ]
        return sum(criteria) / len(criteria) * 100

# Example usage
metrics = GameDayMetrics(
    scenario_name="Database Failover",
    start_time=datetime(2025, 1, 15, 10, 10, 0),
    end_time=datetime(2025, 1, 15, 10, 12, 30),
    time_to_detect_seconds=15.0,
    time_to_respond_seconds=45.0,
    time_to_recover_seconds=150.0,
    error_rate_peak=0.05,
    alerts_fired=["DatabaseConnectionError", "HighLatency"],
    alerts_missed=["FailoverInitiated"],
    responders_involved=3,
    escalations_needed=0,
    met_rto=True,
    met_rpo=True,
    zero_customer_impact=True
)

print(f"MTTR: {metrics.calculate_mttr()}s")
print(f"Success Rate: {metrics.success_rate()}%")
```

## Surprise Scenarios Library

```yaml
# Keep these secret until game day!
surprise_scenarios:
  - name: "Cascading Failure"
    description: "Primary failure triggers secondary issue"
    injection:
      - "Database failover (expected)"
      - "Cache eviction due to new primary IP (surprise!)"
    learning_goals:
      - "Do we understand our dependencies?"
      - "Can we handle multiple simultaneous issues?"

  - name: "Monitoring Blind Spot"
    description: "Failure that doesn't trigger alerts"
    injection:
      - "Gradual connection pool leak"
      - "No immediate alerts fire"
    learning_goals:
      - "How do we discover issues without alerts?"
      - "Do we have adequate monitoring coverage?"

  - name: "Documentation Failure"
    description: "Runbook is outdated or incorrect"
    setup:
      - "Modify runbook to have incorrect commands"
      - "Or remove runbook entirely"
    learning_goals:
      - "Can team problem-solve without docs?"
      - "How quickly can we update documentation?"

  - name: "Key Person Unavailable"
    description: "Subject matter expert is unreachable"
    setup:
      - "Ask SME to not respond for 15 minutes"
    learning_goals:
      - "Is knowledge properly distributed?"
      - "Can team succeed without specific person?"

  - name: "Partial Degradation"
    description: "Service works but slowly"
    injection:
      - "Add 5 second latency instead of complete failure"
    learning_goals:
      - "Do we detect performance degradation?"
      - "What are our latency SLOs?"
```

## Post-Game Report Template

```markdown
# Game Day Report: Database Failover

**Date**: January 15, 2025
**Participants**: 12
**Duration**: 2 hours
**Environment**: Staging

## Executive Summary

Conducted database failover game day to test RDS high availability and
application resilience. Successfully failed over database in 2.5 minutes
(target: 2 min). Discovered 3 critical gaps in monitoring and 2 process
improvements needed.

## Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Time to Detect | < 30s | 15s | PASS |
| Time to Respond | < 5min | 4min 20s | PASS |
| Time to Recover | < 2min | 2min 30s | FAIL |
| Alert Accuracy | 100% | 66% | FAIL |
| Zero Customer Impact | Yes | Yes | PASS |

## What Went Well

1. Team responded quickly (4m 20s vs 5m target)
2. Runbooks were accurate and helpful
3. Communication was clear and frequent
4. No customer impact during any scenario
5. Application auto-reconnect worked perfectly

## What Didn't Go Well

1. Missing alert for failover initiation
2. Took 30s longer than target to recover
3. Connection pool exhaustion not detected
4. Dashboard didn't show replica lag clearly
5. Escalation contacts list was outdated

## Surprises

1. Cache invalidation cascaded from DB failover (unexpected)
2. Read replica had 45s replication lag we didn't know about
3. Application retried too aggressively during failover
4. Team found a workaround we hadn't documented

## Action Items

| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| Add alert for RDS failover events | @sre-team | Jan 20 | P0 |
| Update dashboard with replica lag | @platform | Jan 22 | P1 |
| Document cache invalidation behavior | @dev-team | Jan 25 | P1 |
| Add connection pool monitoring | @sre-team | Jan 27 | P0 |
| Update escalation contact list | @manager | Jan 18 | P2 |
| Tune application retry backoff | @dev-team | Feb 1 | P1 |

## Lessons Learned

1. **Monitoring Gaps**: We had blind spots in replica monitoring
2. **Cascading Effects**: DB changes affect cache in non-obvious ways
3. **Team Knowledge**: Cross-training is working well
4. **Documentation**: Runbooks saved time, keep them updated

## Next Game Day

**Proposed Date**: March 15, 2025
**Scenario**: Multi-region failover
**Scope**: Production (with safeguards)

## Appendix

- Full timeline spreadsheet: [link]
- Screen recordings: [link]
- Metrics dashboard export: [link]
- Raw observation notes: [link]
```

## Quick Reference

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Planning | 2 weeks | Define scenarios, invite participants |
| Pre-game | 30 min | Setup, verify environment, brief team |
| Execution | 2 hours | Run scenarios, observe, document |
| Debrief | 30 min | Immediate learnings, quick wins |
| Post-mortem | 1 week later | Detailed analysis, action items |
| Follow-up | 1 month | Verify improvements, plan next game day |
