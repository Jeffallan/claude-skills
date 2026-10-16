#!/usr/bin/env python3
"""Create a new skill skeleton that follows this repository's conventions."""

import argparse
import json
from pathlib import Path
import re
import sys

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GITHUB_USER_PATTERN = re.compile(r"^(?!-)(?!.*--)[A-Za-z0-9-]{1,39}(?<!-)$")
DOMAINS = (
    "language",
    "backend",
    "frontend",
    "infrastructure",
    "api-architecture",
    "quality",
    "devops",
    "security",
    "data-ml",
    "platform",
    "specialized",
    "workflow",
)

TEMPLATE = """---
name: {name}
description: {description}
license: MIT
metadata:
  author: https://github.com/{author}
  version: "1.0.0"
  domain: {domain}
  triggers: TODO
  role: specialist
  scope: implementation
  output-format: code
  related-skills: TODO
---

# {title}

TODO: Define the skill's role in one sentence.

## Role Definition

TODO: Describe the expertise and boundaries of this skill.

## When to Use This Skill

- TODO: Add concrete triggering scenarios.

## Core Workflow

1. **Assess** - TODO
2. **Plan** - TODO
3. **Implement** - TODO
4. **Validate** - TODO
5. **Deliver** - TODO

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Core guidance | `references/overview.md` | Applying the skill's detailed patterns |

## Constraints

### MUST DO

- TODO

### MUST NOT DO

- TODO

## Output Templates

When completing TODO, provide:

1. TODO

## Knowledge Reference

TODO

[Documentation](https://jeffallan.github.io/claude-skills/skills/{domain}/{name}/)
"""

REFERENCE_TEMPLATE = """# {title} Reference

Use this file for detailed guidance that should load only when the task requires it.

## When to Load

- TODO: Add specific contexts that require this reference.

## Guidance

TODO: Replace this placeholder with complete, focused guidance and practical examples.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Skill directory name in lowercase hyphen-case")
    parser.add_argument("--domain", choices=DOMAINS, required=True)
    parser.add_argument("--description", required=True, help="Capability and 'Use when' trigger description")
    parser.add_argument("--author", required=True, help="GitHub username credited in skill metadata")
    parser.add_argument("--output", type=Path, default=Path("skills"), help="Parent directory (default: skills)")
    parser.add_argument("--dry-run", action="store_true", help="Preview paths and content without writing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not NAME_PATTERN.fullmatch(args.name):
        print("error: name must use lowercase letters, digits, and single hyphens", file=sys.stderr)
        return 2
    if "Use when" not in args.description:
        print("error: description must include a 'Use when' trigger clause", file=sys.stderr)
        return 2
    if "\n" in args.description or "\r" in args.description:
        print("error: description must be a single line", file=sys.stderr)
        return 2
    if not GITHUB_USER_PATTERN.fullmatch(args.author):
        print("error: author must be a valid GitHub username", file=sys.stderr)
        return 2

    skill_dir = args.output / args.name
    if skill_dir.exists():
        print(f"error: refusing to overwrite existing directory: {skill_dir}", file=sys.stderr)
        return 1

    content = TEMPLATE.format(
        name=args.name,
        title=" ".join(part.capitalize() for part in args.name.split("-")),
        description=json.dumps(args.description),
        domain=args.domain,
        author=args.author,
    )

    if args.dry_run:
        print(f"Would create {skill_dir / 'SKILL.md'}")
        print(f"Would create {skill_dir / 'references' / 'overview.md'}")
        print()
        print(content)
        return 0

    references_dir = skill_dir / "references"
    references_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(content)
    (references_dir / "overview.md").write_text(
        REFERENCE_TEMPLATE.format(title=" ".join(part.capitalize() for part in args.name.split("-")))
    )
    print(f"Created {skill_dir / 'SKILL.md'}")
    print(f"Created {references_dir / 'overview.md'}")
    print(f"Next: replace TODOs, add references, then run python scripts/validate-skills.py --skill {args.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
