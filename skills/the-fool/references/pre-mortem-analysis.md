# Pre-Mortem Analysis

Pre-mortem methodology with second-order thinking for identifying how plans fail before they fail.

## Core Principle

A pre-mortem inverts the question. Instead of "Will this work?" ask: **"It's 6 months from now and this has failed. Why?"** This psychological shift bypasses optimism bias by making failure the starting point, not the thing to be argued against.

## Process

1. **Set the scene** — "Imagine it's [timeframe] from now. This plan has failed. Not a small setback — a clear failure."
2. **Generate failure narratives** — Write specific stories about how it failed
3. **Rank by likelihood and impact** — Not all failures are equal
4. **Trace consequence chains** — First → second → third order effects
5. **Identify early warning signs** — What would you see before the failure?
6. **Design mitigations** — Concrete actions, not vague "be careful"

## Failure Narrative Construction

Failure narratives must be specific. "It didn't scale" is not a narrative. "At 50K concurrent users, the database connection pool exhausted, causing cascading timeouts across all services, which triggered the circuit breaker to reject all requests for 4 minutes during peak hours" is a narrative.

### Specificity Checklist

- [ ] Names a specific trigger (not "something goes wrong")
- [ ] Includes a number or threshold
- [ ] Describes the chain of events, not just the end state
- [ ] Identifies who or what is affected
- [ ] Could actually happen (not a fantasy scenario)

### Failure Narrative Template

```markdown
**Failure: [Title]**

It's [timeframe] from now. [Specific trigger event]. This caused [first-order effect],
which led to [second-order effect]. The team discovered the problem when [detection point],
but by then [consequence]. The root cause was [underlying assumption that proved wrong].
```

### Example

```markdown
**Failure: Migration Data Loss**

It's 3 months from now. During the database migration from PostgreSQL to the new schema,
a batch job silently drops records where the `legacy_id` field contains special characters
(~2% of records). The team discovers the problem 2 weeks post-migration when a customer
reports missing order history. By then, the legacy database has been decommissioned and
backups have rotated past the migration date. The root cause was that the migration script
was tested against a sanitized staging dataset that didn't include special characters.
```

## Second-Order Consequence Chains

Every failure has consequences beyond the immediate impact. Trace at least two orders deep.

### Chain Template

```
Trigger: [event]
  → 1st order: [immediate effect]
    → 2nd order: [consequence of the 1st order effect]
      → 3rd order: [consequence of the 2nd order effect]
```

### Example Chain

```
Trigger: Key engineer leaves during migration
  → 1st order: Migration timeline slips 4 weeks
    → 2nd order: Overlap period with legacy system extends, doubling operational cost
      → 3rd order: Budget overrun triggers executive review, project gets descoped
```

### Common Second-Order Patterns

| First Order | Second Order | Third Order |
|------------|-------------|-------------|
| Feature ships late | Sales misses quarter target | Engineering loses trust, gets more oversight |
| Performance degrades | Users adopt workarounds | Workarounds become "requirements" that constrain future design |
| Team member burns out | Knowledge concentrated in fewer people | Bus factor drops, risk increases |
| Dependency breaks | Hotfix bypasses testing | New bugs introduced, confidence in releases drops |
| Data quality issue | Downstream reports are wrong | Business decisions made on bad data |

## Inversion Technique

Ask: **"What would guarantee this fails?"** Then check if any of those conditions exist.

### Guaranteed Failure Conditions

| Category | What Guarantees Failure |
|----------|----------------------|
| **People** | Single point of knowledge, no stakeholder buy-in, team doesn't believe in approach |
| **Process** | No rollback plan, no incremental validation, all-or-nothing deployment |
| **Technology** | Untested at target scale, undocumented dependencies, version lock-in |
| **Timeline** | No buffer for unknowns, dependencies on external teams with no SLA, parallel critical paths |
| **Data** | Migration without validation, no data quality checks, schema changes without backward compatibility |

## Domain-Specific Failure Patterns

### Technical Failures

| Pattern | Trigger | Typical Consequence |
|---------|---------|-------------------|
| Integration cliff | New service connects to 3+ existing systems | One integration blocks all others |
| Scale surprise | Load 10x beyond testing | Cascading failures across dependent services |
| Migration trap | "Just move the data" | Data loss, extended downtime, rollback impossible |
| Dependency rot | Pinned to abandoned library | Security vulnerability with no upgrade path |
| Config drift | Manual environment setup | "Works on my machine" becomes "works in no environment" |

### Business Failures

| Pattern | Trigger | Typical Consequence |
|---------|---------|-------------------|
| Adoption cliff | Build it and they don't come | Sunk cost with no revenue impact |
| Competitor preempt | Competitor ships similar feature first | Market positioning lost, differentiation eroded |
| Timing mismatch | Market shifts during development | Product solves yesterday's problem |
| Stakeholder reversal | Executive sponsor changes | Project loses priority, resources reallocated |
| Hidden cost | Operational burden underestimated | Feature costs more to run than it generates |

### Process Failures

| Pattern | Trigger | Typical Consequence |
|---------|---------|-------------------|
| Timeline fantasy | Estimates based on best case | Crunch, quality cuts, or scope cuts at the worst time |
| Dependency chain | Team A waits on Team B waits on Team C | Any slip cascades through all teams |
| Knowledge silo | Expert leaves or is unavailable | Progress stops; replacement ramps up for weeks |
| Scope creep | "While we're at it..." | Original goal buried under additions |
| Feedback void | No user testing until launch | Wrong product built correctly |

## Early Warning Signs

| Warning Sign | What It Indicates |
|-------------|-------------------|
| "We'll figure that out later" repeated 3+ times | Critical decisions being deferred, not resolved |
| No one can explain the rollback plan | Rollback hasn't been designed |
| Estimates keep growing | Hidden complexity being discovered incrementally |
| Key meetings keep getting rescheduled | Stakeholder alignment is weaker than assumed |
| "It works locally" | Environment parity is worse than assumed |
| Testing phase compressed | Quality will be sacrificed |
| No metrics defined for success | No one will know if this worked |

## Output Template

```markdown
## Pre-Mortem: [Plan/Decision Name]

**Timeframe:** [When would failure be evident]

### Failure Narratives

#### 1. [Failure Title] — Likelihood: High/Medium/Low | Impact: High/Medium/Low

[Specific failure narrative using the template above]

**Consequence chain:**
- 1st order: [immediate]
- 2nd order: [downstream]
- 3rd order: [systemic]

#### 2. [Failure Title] — Likelihood: High/Medium/Low | Impact: High/Medium/Low

[Narrative]

#### 3. [Failure Title] — Likelihood: High/Medium/Low | Impact: High/Medium/Low

[Narrative]

### Early Warning Signs

| Signal | Failure It Predicts | Check Frequency |
|--------|-------------------|-----------------|
| [Observable signal] | Failure #X | Weekly / Sprint / Monthly |

### Mitigations

| Failure | Mitigation | Effort | Reduces Risk By |
|---------|-----------|--------|-----------------|
| #1 | [Specific action] | Low/Med/High | [How much] |
| #2 | [Specific action] | Low/Med/High | [How much] |
| #3 | [Specific action] | Low/Med/High | [How much] |

### Inversion Check

**What would guarantee failure:** [List top 3 conditions]
**Do any exist now?** [Yes/No with specifics]
```
