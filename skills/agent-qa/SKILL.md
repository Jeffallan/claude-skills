---
name: agent-qa
description: Operates agent-qa tests and interprets recorded run evidence and memidex knowledge. Use when working with agent-qa.config.yaml, agent-qa test or suite files, agent_qa MCP tools, or an explicit request to test web, Android, or iOS journeys with agent-qa.
license: MIT
metadata:
  author: https://github.com/vostride
  company: https://vostride.com
  version: "1.0.0"
  domain: quality
  triggers: agent-qa, agent-qa.config.yaml, agent_qa, memidex, agent-qa run evidence
  role: specialist
  scope: testing
  output-format: report
  related-skills: test-master, playwright-expert, debugging-wizard
---

# agent-qa

Operate [agent-qa](https://github.com/vostride/agent-qa) from vostride, a natural-language web and
mobile testing tool with advanced memidex memory and self-improvement.

## Role Definition

You work with the application's existing agent-qa project and its recorded evidence.
Tie every testing conclusion to the requested journey, target, build, and completed run.
A valid test file or a successful launch does not establish that a journey passed.

## When to Use This Skill

- Author or refine natural-language tests in an agent-qa project.
- Execute a selected agent-qa test or suite against its configured environment.
- Explain a recorded failure, inspect screenshots, or review a proposed outcome correction.
- Trace the memidex knowledge a run used or learned.

For general test strategy, use Test Master. For Playwright test code, use Playwright Expert.
Do not introduce agent-qa into an unrelated testing task solely because this skill is available.

## Core Workflow

1. **Identify the task** - Locate project instructions, the configuration file, and the requested
   target or saved run. Distinguish authoring, execution, and read-only review. Existing evidence
   review does not require a new run.
2. **Check the relevant setup** - Use the installed CLI or connected MCP server. Read
   `references/project-and-runs.md` for setup or execution work; preserve existing model, platform,
   and credential choices.
3. **Prepare the requested work** - For authoring, use the installed authoring contract with observable
   actions and expectations against an existing target; inspect its write and verification receipts.
   For review, use the recorded run ID and read `references/evidence-and-memory.md`.
4. **Execute when in scope** - Run the selected test or suite, retain the actual run ID and outcome,
   and inspect evidence. For asynchronous MCP execution, an acknowledgement is not a final verdict;
   follow the returned run through supported readers or streams.
5. **Report the evidence** - State what was tested or inspected, the recorded result, and what
   remains unverified. Separate application failures, setup failures, and inconclusive evidence.
   Report learned knowledge separately from the test verdict.

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Project setup and execution | `references/project-and-runs.md` | Installing, authoring YAML, validating, running tests, or connecting MCP |
| Evidence and memidex | `references/evidence-and-memory.md` | Reviewing saved runs, exporting evidence, explaining learned knowledge, or correcting a verdict |

## Technical Guidelines

Use the project's installed version and its `--help` output. The examples were checked with agent-qa
0.2.3.
The CLI digest is `agent-qa digest RUN_ID`, not a subcommand of `runs`.
MCP integrations can namespace tool names; discover the available tools and input schemas before
calling them.

Start a read-only review with:

```bash
npx agent-qa runs list --json
```

Choose the requested run from that result. If it is absent, report that absence; a different test's
success does not establish coverage.

For authoring, discover the installed capability catalog with `npx agent-qa init --agent`.
It reports workspace posture and current operations without initializing the project.
Use `npx agent-qa skills --json` to locate version-matched authoring and schema guidance.
Prefer the connected MCP authoring tools when available.
The host creates canonical IDs; never invent one or duplicate another test's ID for a new test.
Read the actual write or refusal receipt before reporting a test as created.
Authoring verification can execute a test, so it is outside an explicitly read-only task.
In YAML steps, use `{{secret:NAME}}` to reference a configured secret.
The recorded `[secret:NAME]` marker is masked output, not a value to type into an application.

## Constraints

### MUST DO

- Use supported CLI JSON readers or MCP tools for recorded data; inspect their errors before drawing
  conclusions.
- Keep run IDs, test identities, targets, and zero-based step indices attached to evidence.
- Read the `AGENTS.md` policy in the project’s `agent-qa-knowledge` directory before changing
  committed knowledge.
- Preserve masked values such as `[secret:NAME]`; use configured secret references in tests.
- Report validation and dry runs as non-execution checks.

### MUST NOT DO

- Query or edit `.agent-qa/` databases, cache files, or derived indexes directly.
- Treat missing records, queued work, or an unverified repaired test as a passing run.
- Start a new run or change knowledge merely to answer a read-only evidence question.
- Weaken an expected outcome to make a failing application appear correct.
- Assume all logs and screenshots are redacted; only configured secret values receive masking.

## Output Templates

Provide the requested test changes or a short report containing:

1. Target and test or suite, plus the actual run ID when available.
2. Checks performed and the recorded verdict, with relevant step evidence.
3. Setup problems, missing coverage, or other limits on the conclusion.
4. Any knowledge or outcome changes actually applied, with their receipts.

The skill is MIT-licensed; the separately installed agent-qa runtime uses
[FSL-1.1-ALv2](https://github.com/vostride/agent-qa/blob/main/LICENSE.md).

[Documentation](https://jeffallan.github.io/claude-skills/skills/quality/agent-qa/)
