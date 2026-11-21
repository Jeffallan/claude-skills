# Full-Stack Dev Skills

Specialized skills for Claude Code across languages, backend and frontend frameworks, infrastructure, APIs, testing, DevOps, security, and data and ML, plus a project workflow that takes tracker tickets to a reviewed pull request, test first.

## What's included

Each skill covers one language, framework or discipline. Claude loads a skill when your request matches it and reads the skill's deeper reference files only when the task needs them.

The workflow commands cover a project from intake to merge:

- `intake:` documents an existing codebase and pins its current behavior in tests
- `discovery:` turns rough input into tickets
- `spec:` groups tickets into specs, then plans, reviews and completes each one
- `ticket:execute` and `ticket:complete` build one ticket test first
- `common-ground` lists the assumptions Claude is making about your project so you can correct them

## Install

```bash
/plugin marketplace add jeffallan/claude-skills
/plugin install fullstack-dev-skills@fullstack-dev-skills
```

The workflow commands need [uv](https://docs.astral.sh/uv/) and a `.claude/workflow-config.json`, which the first workflow command offers to create.

## What the plugin reads, writes and runs

Skills are Markdown instructions, so they read and write only what you ask Claude to work on.

Workflow commands write specs and docs into your repository. They change tickets in your tracker through the tools you already have connected, and ask before each tracker change.

The plugin registers hooks on edits, tool calls, session stop and compaction. A hook exits at once unless a ticket is in progress, which a marker under `.git/ticket-guard/` records. During ticket work the hooks run the bundled guard, `runtime/guard.pyz`, with `uv run`; it records test evidence under `.git/ticket-guard/` and blocks edits to frozen tests.

`common-ground` keeps its ground file under `~/.claude/common-ground/`. The plugin itself sends nothing anywhere.

## Documentation

Full documentation: <https://jeffallan.github.io/claude-skills/>

Source and issues: <https://github.com/jeffallan/claude-skills>

## License

MIT
