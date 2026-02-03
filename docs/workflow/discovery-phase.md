# Discovery Phase

Optional research phase triggered when `feature-forge` identifies unknowns that require human investigation before planning can proceed.

---

## Purpose

Not every feature needs discovery. When the feature-forge interview surfaces questions that cannot be answered from existing knowledge — user interviews needed, competitive analysis required, technical spikes pending — those unknowns route here. Discovery provides structure for research and converts findings into actionable epics and tickets.

## Commands

| Order | Command | Summary |
|-------|---------|---------|
| 1 | `discovery:create` | Create a structured discovery workspace with research questions and hypotheses |
| 2 | `discovery:synthesize` | Consolidate research artifacts into findings, recommendations, and proposed tickets |
| 3 | `discovery:approve` | Resolve blocking decisions and create tickets in the ticketing system |

Between steps 1 and 2, humans conduct the actual research: user interviews, technical spikes, competitive analysis, design sprints.

## Outputs

- **Discovery document** — Research questions, hypotheses, research plan
- **Synthesis document** — Consolidated findings, recommendations, proposed tickets with blocking decisions
- **Tickets** — Epics and tickets created in the ticketing system, grounded in research

## Prerequisites

- Feature-forge spec with Discovery Recommendation section (recommended)
- Ticketing system access (Jira)
- Documentation system access (Confluence)

## External Skills

- **feature-forge** — Produces the spec that identifies unknowns triggering discovery

## Next Steps

After discovery, proceed to the [Planning Phase](planning-phase.md) to create the epic plan and implementation plan from the created tickets.
