# Claude Skills Project Overview

## Purpose
A curated collection of agent skills following the [Agent Skills specification](https://agentskills.io/specification). Skills provide structured context (role, workflow, constraints, code examples) that AI coding agents load to perform specialized tasks. The project includes 66 skills across multiple domains, 9 workflow commands, and 365+ reference files.

## Tech Stack
- **Primary content**: Markdown (SKILL.md files, reference files, docs)
- **Scripts**: Python 3 (validation, docs updates)
- **Config**: YAML frontmatter in skill files, JSON (version.json, plugin.json)
- **CI/CD**: GitHub Actions
- **Linting**: ruff, ruff-format, pyright (Python); prettier (JS/JSON)
- **Social preview**: Node.js + Puppeteer for screenshot generation

## Project Structure
```
skills/                    # 66 skill directories
  {skill-name}/
    SKILL.md               # Tier 1: ~80-150 lines, frontmatter + body
    references/             # Tier 2: 100-600 line deep-content files
scripts/
  validate-skills.py       # Validate YAML, descriptions, references, counts
  update-docs.py           # Sync version/counts across all docs
  validate-markdown.py     # Check markdown syntax issues
docs/                      # Documentation site content
commands/                  # 9 workflow command definitions
.claude-plugin/            # Plugin manifest for Claude Code marketplace
research/                  # Research docs (superpowers, etc.)
version.json               # Single source of truth for version + counts
CLAUDE.md                  # Project instructions for Claude
MODELCLAUDE.md             # Model-facing behavioral instructions
```

## Key Design Principles
- **Progressive Disclosure**: Metadata (~100 tokens) → SKILL.md (<5000 tokens) → References (on demand)
- **Description Trap**: No process steps in descriptions. Format: `[Brief capability statement]. Use when [triggering conditions].`
- **Framework Idiom Principle**: Reference files reflect idiomatic framework practices, not generic patterns
