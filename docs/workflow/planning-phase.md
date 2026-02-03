# Planning Phase

Transforms an epic with tickets into a stakeholder-readable overview and a developer-executable implementation plan.

---

## Purpose

Planning bridges the gap between "what to build" (discovery/feature-forge output) and "how to build it" (execution). It produces two complementary documents: an overview for decision-makers and a coordination plan for implementers.

## Commands

| Order | Command | Summary |
|-------|---------|---------|
| 1 | `planning:epic-plan` | Analyze codebase and tickets to produce a stakeholder-readable overview document |
| 2 | `planning:impl-plan` | Convert overview into an executable implementation plan with self-contained tickets |

## Outputs

- **Overview document** — Purpose, requirements, risk assessment (7-dimension scoring), impact analysis, testing strategy, acceptance criteria
- **Implementation plan** — Topologically sorted execution order, parallel execution waves, agent recommendations
- **Updated tickets** — Each Jira ticket enriched with self-contained implementation details, file paths, code snippets, test code, and acceptance criteria

## Prerequisites

- Epic with linked tickets in the ticketing system
- Completed discovery phase (if discovery was needed)
- Ticketing system access (Jira)
- Documentation system access (Confluence)

## Next Steps

After planning, proceed to the [Execution Phase](execution-phase.md). Each ticket is now self-contained and can be picked up independently by a developer or agent.
