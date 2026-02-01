# v0.5.0 Workflow Narrative

A walkthrough of the full project lifecycle from zero to shipped features.

**Related documents:**
- Consolidated plan: [`docs/v0.5.0-plan.md`](v0.5.0-plan.md)
- YAML schema: [`docs/workflow/workflow-definition-schema.md`](workflow/workflow-definition-schema.md)
- Workflow manifest: [`commands/workflow-manifest.yaml`](../commands/workflow-manifest.yaml)

---

## Act 1: Project Onboarding (Intake Phase — Run Once)

You've just been brought onto a codebase. Maybe it's a legacy app, maybe it's a startup MVP that grew fast. Before any feature work happens, you need to understand what exists.

### Step 1: `intake:document-codebase`

You run this first. The agent scans the entire codebase and identifies every function, class, module, and endpoint that lacks documentation. It prioritizes public APIs and external-facing interfaces first, then works inward to internal services and utilities. Before touching anything, it presents a scope summary — "I found 247 undocumented functions across 38 files. Here's the breakdown by module." You approve, and it generates docstrings/JSDoc/XML docs throughout the codebase. When it's done, you have a codebase where any developer (or agent) can read a function signature and understand what it does without tracing the implementation.

> **Inputs:** directory (string, optional — defaults to project root)
> **Outputs:** documentation-report (summary of functions, classes, modules documented)
> **YAML:** [`commands/intake/document-codebase.yaml`](../commands/intake/document-codebase.yaml)
> **Next:** `intake:capture-behavior`

### Step 2: `intake:capture-behavior`

Now that the code is documented, the agent scans for untested behavior. It identifies functions, endpoints, and components that have no test coverage. It builds a test plan — not for what the code *should* do, but for what it *currently does*. These are characterization tests. The agent writes tests that assert current behavior: "When you call `calculateTotal` with these inputs, it returns this value." It runs the tests against the live code to verify they pass. The point isn't to validate correctness — it's to create a safety net so you'll know immediately if future changes break existing behavior.

> **Inputs:** directory (string, optional — defaults to project root)
> **Outputs:** characterization-tests (test files asserting current behavior), coverage-report (summary of behavior captured)
> **YAML:** [`commands/intake/capture-behavior.yaml`](../commands/intake/capture-behavior.yaml)
> **Next:** `intake:create-system-description`

### Step 3: `intake:create-system-description`

This is the capstone of onboarding. The agent launches parallel analysis — one thread maps the architecture (services, databases, queues), another catalogs the API surface area, another traces security patterns (auth, encryption, access controls), and another maps external dependencies. The output is a SOC2-style living document at `docs/system-description.md`. It reads like a system overview you'd hand to an auditor or a new senior engineer: what the system does, how data flows through it, what's exposed externally, how it's deployed, what third-party services it depends on. This document becomes the shared context for everything that follows.

> **Inputs:** directory (string, optional — defaults to project root)
> **Outputs:** system-description (file at `docs/system-description.md` — SOC2-style living document)
> **YAML:** [`commands/intake/create-system-description.yaml`](../commands/intake/create-system-description.yaml)
> **Next:** Feature definition with feature-forge

**After intake, you have:** documented code, behavioral tests, and a system description. This is a one-time cost. You don't run intake again.

---

## Interlude: Common Ground (On Demand)

At any point — now, or later during planning, or mid-execution — you can run `/common-ground`. It surfaces assumptions the agent is making about your project: "I assume you're using PostgreSQL for the primary datastore." "I assume the API uses JWT authentication." You confirm, correct, or flag unknowns. This runs whenever you feel assumptions are building up. There's no prescribed moment; you use judgment.

> **Inputs:** --list (flag, read-only view), --check (flag, quick validation), --graph (flag, mermaid diagram)
> **Outputs:** ground-file (`COMMON-GROUND.md` with assumptions by confidence tier), ground-index (`ground.index.json` for programmatic access)
> **YAML:** [`commands/common-ground/common-ground.yaml`](../commands/common-ground/common-ground.yaml)
> **Next:** On demand — no prescribed next step

---

## Act 2: Product Discovery (Human-Driven, Parallel to Intake)

While intake is happening on the technical side, the product side is doing its own work. This part is primarily human — the agent assists but doesn't drive.

### Identify Value Propositions

A product person, founder, or stakeholder defines the value propositions. For example, a SaaS product might have:
- VP1: Save time for primary users
- VP2: Monetize through a secondary audience
- VP3: Expand to adjacent market segments
- VP4: Drive growth through network effects

Each VP has a customer segment, a value statement, and a feature set. This work happens in markdown files, Obsidian, Notion, whiteboards, interviews — whatever the team uses. The agent doesn't own this phase, but it can help structure notes.

### Identify Feature Set

For each value proposition, the team identifies concrete features: User Dashboard, Notification System, Billing Integration, Admin Panel. These get written up as feature descriptions — brief enough to understand the intent, detailed enough to know the scope.

---

## Act 3: Feature Definition (Per Feature)

### Feature Forge (Skill, not a slash command)

For each identified feature, you invoke feature-forge. It reads the system description first — so it already knows your architecture, your API patterns, your database schema, your auth model. It doesn't ask you questions it can answer from the system description.

Then it runs a structured interview: PM perspective ("Who uses this? What's the core value?") and Dev perspective ("What existing components does this touch? What's the data model?"). It asks one question at a time, using multiple-choice where possible to reduce cognitive load.

Throughout the interview, every question about proposed functionality includes a standing option: **"Needs additional discovery."** If you don't have the data to answer a question — maybe you need user interviews, competitive analysis, or a technical spike — you select this option. Feature-forge records it, skips the question, and moves on. You're never blocked by unknowns during the interview.

The output is `specs/{feature-name}.spec.md` — a specification with:
- Functional requirements (optionally in EARS format for complex features, simpler format for straightforward ones)
- Non-functional requirements
- Acceptance criteria (Given/When/Then)
- Error handling table
- High-level implementation TODOs (intentionally *not* detailed — that's the planning phase's job)
- A workflow integration section noting the target epic and pointing to `/planning:impl-plan` for detailed steps
- If any questions were flagged: a **Discovery Recommendation** section listing the specific unknowns

If unknowns were flagged, feature-forge presents a choice: run discovery now (recommended), skip to planning with unknowns flagged as risks, or handle research separately and run `discovery:create` later. If nothing was flagged, no recommendation appears — you go straight to planning or move on to the next feature.

**You repeat this for every feature in the release.**

---

## Act 4: Discovery (Optional — When Research Is Needed)

Not every feature needs this. If the feature-forge spec is sufficient — no unknowns were flagged during the interview — you skip straight to Planning. But some features have open questions that need human research: user interviews, competitive analysis, technical spikes, design exploration. You'll know because feature-forge told you — every question you answered with "Needs additional discovery" is now listed in the spec's Discovery Recommendation section.

### Step 4: `discovery:create`

You give it a **topic** — not a Jira epic key, just a topic. "User onboarding flow" or "Payment integration options." You point it at whatever sources you have: the feature-forge spec, meeting notes, domain research markdown files, PDFs, URLs. It creates a structured discovery workspace with research questions, hypotheses, unknowns, domain context, and stakeholder inputs. The workspace lives locally (or in your configured doc system).

> **Inputs:** topic (string), sources (file[], optional — markdown, PDFs, URLs, meeting notes, feature-forge specs)
> **Outputs:** discovery workspace (directory at `docs/discovery/{topic}/`)
> **YAML:** [`commands/project/discovery/create.yaml`](../commands/project/discovery/create.yaml)
> **Next:** Human research phase, then `discovery:synthesize`

### Human Research Phase

This is the gap where humans do the work. Conduct user interviews. Run a design sprint. Build a proof of concept. Do competitive analysis. Fill out the business model canvas. The discovery workspace gives structure to what you're investigating, but the research itself is human labor.

### Step 5: `discovery:synthesize`

After research is done, you point the agent at all your artifacts — the discovery workspace, interview transcripts, research notes, spike results, meeting notes. It consolidates everything into actionable recommendations. The key output: proposed **epics AND tickets**. Not just tickets — full epic structures aligned with value propositions. "Based on the research, here are 3 epics with 14 total tickets across them."

> **Inputs:** discovery workspace refs, local docs, research artifacts (file[])
> **Outputs:** synthesis document (consolidated findings + proposed epic/ticket structure)
> **YAML:** [`commands/project/discovery/synthesize.yaml`](../commands/project/discovery/synthesize.yaml)
> **Next:** `discovery:approve`

### Step 6: `discovery:approve`

You review the synthesis. The agent presents any blocking decisions that need resolving ("Should we use Stripe or build custom payment processing?"). You resolve them.

Then it checks whether the proposed epics exist in your ticketing system. If they don't — and this is the fix for issue #103 — it offers options: auto-create the epics, map to existing ones, skip, or cancel. You choose. It creates the epics first, then creates tickets linked to those epics. All of this works against whatever backend you configured — Jira, GitHub Issues, or local markdown files.

> **Inputs:** synthesis document ref, decisions (optional — pre-resolved blocking decisions)
> **Outputs:** created epics + tickets (in configured ticketing backend)
> **YAML:** [`commands/project/discovery/approve.yaml`](../commands/project/discovery/approve.yaml)
> **Next:** `planning:epic-plan`

**After discovery, you have:** epics and tickets in your ticketing system, grounded in research and aligned with value propositions.

---

## Act 5: Planning

### Step 7: `planning:epic-plan`

You point it at an epic. The agent reads the feature-forge spec (if one exists) so it doesn't re-derive requirements. It fetches all linked tickets, then launches parallel agents to explore the codebase — one finds affected files, another discovers API patterns, another maps component patterns, another locates test conventions, another finds reference implementations.

The output is a stakeholder-readable overview document: purpose, goals, requirements summary, technical change overview with a risk assessment (7-dimension scoring), impact analysis, testing strategy, acceptance criteria. This is the document you share with your tech lead, your PM, your architect. It's meant to be read by humans making decisions, not by agents executing code.

> **Inputs:** epic key (string), feature spec (auto-detected from `specs/{feature_name}.spec.md`)
> **Outputs:** overview document (stakeholder-readable plan with requirements, risk assessment, testing strategy)
> **YAML:** [`commands/project/planning/epic-plan.yaml`](../commands/project/planning/epic-plan.yaml)
> **Next:** `planning:impl-plan`

### Step 8: `planning:impl-plan`

This is where the overview becomes executable. The agent takes the overview document and turns it into a coordination plan: topologically sorted execution order, parallel execution waves (which tickets can be worked simultaneously), and — the enhancement — **skill-aware ticket descriptions**.

For each ticket, it reads what skills are available in the project and crafts the ticket description to invoke the right one. A React component ticket gets a description that references `react-expert`. A test suite ticket references `test-master`. A database migration ticket references `database-optimizer`. Each ticket becomes self-contained: implementation steps with file paths and code snippets, files to modify, complete test code, acceptance criteria checklist.

> **Inputs:** overview document ref (from `planning:epic-plan`)
> **Outputs:** implementation plan (execution order + parallel waves), updated tickets (self-contained with skill-aware descriptions)
> **YAML:** [`commands/project/planning/impl-plan.yaml`](../commands/project/planning/impl-plan.yaml)
> **Next:** `execution:execute-ticket`

**After planning, you have:** a stakeholder overview, a coordination plan, and self-contained tickets that any developer (or agent) can pick up and execute independently.

---

## Act 6: Execution (Per Ticket, Repeated)

This is where code gets written. The split between execute and complete exists for a practical reason — implementations can be long, conversations may need compacting, and the completion phase was being dropped when bundled with execution.

### Step 9: `execution:execute-ticket` (repeated per ticket)

You give it a ticket key. The agent fetches the ticket, reads the self-contained implementation details, and starts coding. It follows the implementation steps, writes the code changes, creates the tests, runs them, verifies acceptance criteria. If it encounters deviations from the plan, it flags them at a checkpoint. When done, it presents a completion summary: what changed, what tests were added, what was different from the plan.

> **Inputs:** ticket key (string)
> **Outputs:** completion summary (changes made, files modified, tests added, deviations from plan)
> **YAML:** [`commands/project/execution/execute-ticket.yaml`](../commands/project/execution/execute-ticket.yaml)
> **Next:** `execution:complete-ticket`

### Step 10: `execution:complete-ticket` (repeated per ticket)

After execution, you run completion as a separate command. It transitions the ticket status (In Progress → In Review), updates the implementation plan's status tables (completion status, execution order, parallel wave tracking), and records the details of what was actually implemented.

Then the incremental system description update: if the changes affect APIs, external dependencies, security patterns, or data models, the agent proposes specific updates to `docs/system-description.md`. "This ticket added a new `/api/v2/teams` endpoint — I'll update the API Surface Area section." Checkpoint approval, then it applies the update. This keeps the system description accurate as the codebase evolves, without requiring a big-bang documentation effort.

> **Inputs:** ticket key (string, optional if context available from prior execute-ticket)
> **Outputs:** transitioned ticket (status → "In Review"), updated implementation plan, updated system description (if applicable)
> **YAML:** [`commands/project/execution/complete-ticket.yaml`](../commands/project/execution/complete-ticket.yaml)
> **Next:** Next ticket (`execution:execute-ticket`) or `retrospectives:complete-epic` when all tickets done

**You repeat steps 9-10 for every ticket in the epic. Parallel waves mean multiple developers/agents can work tickets simultaneously.**

---

## Act 7: Retrospective

### Step 11: `retrospectives:complete-epic`

All tickets are done. You run this on the epic. The agent verifies all tickets are complete (blocks if any aren't), then generates a comprehensive completion report: what was built, what deviated from the plan, what patterns emerged, what was learned, quality assessment. It moves documentation from the "in progress" location to the "complete" location in your doc system. It closes the epic in the ticketing system.

Finally, it does a full system description review — not just incremental updates, but a holistic check. Did the architecture change? Do the mermaid diagrams still reflect reality? Are there new external dependencies that weren't captured ticket-by-ticket? Checkpoint approval, then it updates the system description to reflect the post-epic state of the system.

> **Inputs:** epic key (string)
> **Outputs:** completion report (deliverables, quality metrics, lessons learned), closed epic, updated system description (holistic post-epic review)
> **YAML:** [`commands/project/retrospectives/complete-epic.yaml`](../commands/project/retrospectives/complete-epic.yaml)
> **Next:** Next feature cycle — feature-forge reads updated system description

**The system description is now current. The next feature-forge invocation will read the updated system description, and the cycle begins again.**

---

## The Full DAG at a Glance

```
INTAKE (once)           PRODUCT DISCOVERY (human, parallel)
  |                       |
  system-description      value props -> features
  |                       |
  +--------------- feature-forge (per feature) ---------------+
  |                       |                                    |
  |                 discovery (optional, when research         |
  |                   needed, human + agent)                   |
  |                       |                                    |
  |                 approve -> epics + tickets                 |
  |                       |                                    |
  +--------------- planning (epic-plan + impl-plan) ----------+
                          |
                    execution (execute + complete x N)
                          |
                    retrospective (complete-epic)
                          |
                    system description updated
                          |
                    next feature -> feature-forge reads updated state
```

The cycle is self-reinforcing: each completed feature makes the system description more accurate, which makes the next feature-forge session more informed, which makes the next planning phase more precise.
