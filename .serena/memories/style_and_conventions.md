# Style and Conventions

## Skill Frontmatter
Required fields: `name`, `description`
Optional: `license` (always MIT), `allowed-tools`, `metadata`

### Description Format
`[Brief capability statement]. Use when [triggering conditions].`
- Capability verbs OK (generates, configures, implements)
- Process steps NOT OK (first do X, then Y, finally Z)
- Max 1024 characters
- Must contain "Use when" somewhere in the description

### Name Format
- Lowercase letters, numbers, hyphens only
- Must match directory name
- Max 64 characters

### Metadata Fields
- `author`: GitHub profile URL
- `version`: Quoted semver (e.g., "1.1.0")
- `domain`: One of: language, backend, frontend, infrastructure, api-architecture, quality, devops, security, data-ml, platform, specialized, workflow
- `triggers`: Comma-separated keywords
- `role`: specialist | expert | architect | engineer
- `scope`: implementation | review | design | system-design | testing | analysis | infrastructure | optimization | architecture
- `output-format`: code | document | report | architecture | specification | schema | manifests | analysis | analysis-and-code | code+analysis
- `related-skills`: Comma-separated existing skill directory names

## SKILL.md Body
- Target 80-150 lines (max 500)
- Sections: Core Workflow, Reference Guide (routing table), Constraints (MUST DO / MUST NOT DO)
- Inline code examples OK if under ~40 lines; larger examples go to reference files

## Reference Files
- 100-600 lines per file
- Single topic focus
- Complete working code examples
- Cross-reference related skills

## Python Scripts
- Pre-commit hooks: ruff, ruff-format, pyright
- Type hints required
