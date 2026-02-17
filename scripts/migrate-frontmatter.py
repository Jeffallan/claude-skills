#!/usr/bin/env python3
"""Migrate skill SKILL.md frontmatter to Agent Skills spec-compliant structure.

Moves triggers, role, scope, output-format under metadata key.
Adds license, metadata.author, metadata.version, metadata.domain.

Usage:
    python scripts/migrate-frontmatter.py              # Migrate all skills
    python scripts/migrate-frontmatter.py --dry-run    # Preview changes
    python scripts/migrate-frontmatter.py --skill react-expert  # Single skill
    python scripts/migrate-frontmatter.py --related-skills       # Add related-skills metadata
    python scripts/migrate-frontmatter.py --related-skills --dry-run  # Preview related-skills
"""

import argparse
import re
import sys
from pathlib import Path

# Try to import PyYAML, fall back to simple parser if not available
try:
    import yaml

    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False

SKILLS_DIR = Path("skills")

# Skill-to-domain mapping derived from SKILLS_GUIDE.md
SKILL_DOMAIN_MAP = {
    # language
    "python-pro": "language",
    "typescript-pro": "language",
    "javascript-pro": "language",
    "golang-pro": "language",
    "rust-engineer": "language",
    "sql-pro": "language",
    "cpp-pro": "language",
    "swift-expert": "language",
    "kotlin-specialist": "language",
    "csharp-developer": "language",
    "php-pro": "language",
    "java-architect": "language",
    # backend
    "nestjs-expert": "backend",
    "django-expert": "backend",
    "fastapi-expert": "backend",
    "spring-boot-engineer": "backend",
    "laravel-specialist": "backend",
    "rails-expert": "backend",
    "dotnet-core-expert": "backend",
    # frontend
    "react-expert": "frontend",
    "nextjs-developer": "frontend",
    "vue-expert": "frontend",
    "vue-expert-js": "frontend",
    "angular-architect": "frontend",
    "react-native-expert": "frontend",
    "flutter-expert": "frontend",
    # infrastructure
    "kubernetes-specialist": "infrastructure",
    "terraform-engineer": "infrastructure",
    "postgres-pro": "infrastructure",
    "cloud-architect": "infrastructure",
    "database-optimizer": "infrastructure",
    # api-architecture
    "graphql-architect": "api-architecture",
    "api-designer": "api-architecture",
    "websocket-engineer": "api-architecture",
    "microservices-architect": "api-architecture",
    "mcp-developer": "api-architecture",
    "architecture-designer": "api-architecture",
    # quality
    "test-master": "quality",
    "playwright-expert": "quality",
    "code-reviewer": "quality",
    "code-documenter": "quality",
    "debugging-wizard": "quality",
    # devops
    "devops-engineer": "devops",
    "monitoring-expert": "devops",
    "sre-engineer": "devops",
    "chaos-engineer": "devops",
    "cli-developer": "devops",
    # security
    "secure-code-guardian": "security",
    "security-reviewer": "security",
    "fullstack-guardian": "security",
    # data-ml
    "pandas-pro": "data-ml",
    "spark-engineer": "data-ml",
    "ml-pipeline": "data-ml",
    "prompt-engineer": "data-ml",
    "rag-architect": "data-ml",
    "fine-tuning-expert": "data-ml",
    # platform
    "salesforce-developer": "platform",
    "shopify-expert": "platform",
    "wordpress-pro": "platform",
    "atlassian-mcp": "platform",
    # specialized
    "legacy-modernizer": "specialized",
    "embedded-systems": "specialized",
    "game-developer": "specialized",
    # workflow
    "feature-forge": "workflow",
    "spec-miner": "workflow",
}


def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter and return (frontmatter_dict, body).

    Returns (None, content) if no valid frontmatter found.
    """
    if not content.startswith("---"):
        return None, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content

    yaml_str = parts[1]
    body = parts[2]

    if HAS_PYYAML:
        frontmatter = yaml.safe_load(yaml_str) or {}
    else:
        # Simple parser for basic key-value and list structures
        frontmatter = {}
        current_key = None
        current_list = None

        for line in yaml_str.strip().split("\n"):
            if not line.strip():
                continue
            if line.startswith("  - ") or line.startswith("    - "):
                if current_key and current_list is not None:
                    item = line.strip().lstrip("- ").strip()
                    current_list.append(item)
                continue
            if ":" in line and not line.startswith(" "):
                if current_key and current_list is not None:
                    frontmatter[current_key] = current_list
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if not value:
                    current_key = key
                    current_list = []
                else:
                    frontmatter[key] = value
                    current_key = None
                    current_list = None

        if current_key and current_list is not None:
            frontmatter[current_key] = current_list

    return frontmatter, body


def build_new_frontmatter(fm: dict, skill_name: str) -> str:
    """Build spec-compliant YAML frontmatter string with controlled key order.

    Hand-constructs YAML to avoid yaml.dump() reordering keys.
    """
    lines = ["---"]

    # Top-level spec fields: name, description
    lines.append(f"name: {fm['name']}")

    # Description may contain special YAML characters, quote if needed
    desc = fm["description"]
    if any(c in desc for c in ":#{}[]|>&*!%@`"):
        lines.append(f'description: "{desc}"')
    else:
        lines.append(f"description: {desc}")

    # license (new)
    lines.append("license: MIT")

    # allowed-tools (spec field, kept top-level if present)
    if "allowed-tools" in fm:
        lines.append(f"allowed-tools: {fm['allowed-tools']}")

    # metadata block
    lines.append("metadata:")

    # metadata.author (new)
    lines.append("  author: https://github.com/Jeffallan")

    # metadata.version (new)
    lines.append('  version: "1.0.0"')

    # metadata.domain (new, from map)
    domain = SKILL_DOMAIN_MAP.get(skill_name, "unknown")
    lines.append(f"  domain: {domain}")

    # metadata.triggers (converted from array to comma-separated string)
    triggers = fm.get("triggers", [])
    if isinstance(triggers, list):
        triggers_str = ", ".join(triggers)
    else:
        triggers_str = str(triggers)
    lines.append(f"  triggers: {triggers_str}")

    # metadata.role (moved from top-level)
    if "role" in fm:
        lines.append(f"  role: {fm['role']}")

    # metadata.scope (moved from top-level)
    if "scope" in fm:
        lines.append(f"  scope: {fm['scope']}")

    # metadata.output-format (moved from top-level)
    if "output-format" in fm:
        lines.append(f"  output-format: {fm['output-format']}")

    lines.append("---")

    return "\n".join(lines)


def extract_related_skills(body: str, valid_dirs: set[str]) -> str:
    """Extract related skill names from the ## Related Skills body section.

    Parses bold display names (e.g., **Fullstack Guardian**), converts to directory-name format (lowercase, spaces to
    hyphens), and filters to only names that exist as directories under skills/.

    Returns a comma-separated string of valid skill directory names, or empty string if none found.
    """
    # Find the ## Related Skills section
    match = re.search(r"## Related Skills\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    if not match:
        return ""

    section = match.group(1)

    # Extract bold display names: **Name**
    display_names = re.findall(r"\*\*(.+?)\*\*", section)

    # Convert to directory-name format and filter to existing directories
    related = []
    for name in display_names:
        dir_name = name.lower().replace(" ", "-")
        if dir_name in valid_dirs:
            related.append(dir_name)

    return ", ".join(related)


def add_related_skills_to_frontmatter(content: str, related_skills: str) -> str:
    """Insert related-skills into an existing metadata block in the
    frontmatter.

    Adds the related-skills line after output-format (or as the last metadata field if output-format is not present).
    """
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    fm_str = parts[1]
    body = parts[2]

    # Check if related-skills already exists
    if "  related-skills:" in fm_str:
        return content

    lines = fm_str.split("\n")
    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)
        # Insert after output-format line
        if not inserted and line.strip().startswith("output-format:"):
            new_lines.append(f"  related-skills: {related_skills}")
            inserted = True

    # If output-format wasn't found, insert before the last line (which is empty/closing)
    if not inserted:
        # Find the last metadata field line and insert after it
        for i in range(len(new_lines) - 1, -1, -1):
            if new_lines[i].startswith("  ") and ":" in new_lines[i]:
                new_lines.insert(i + 1, f"  related-skills: {related_skills}")
                inserted = True
                break

    new_fm = "\n".join(new_lines)
    return f"---{new_fm}---{body}"


def migrate_related_skills(
    skill_dir: Path,
    valid_dirs: set[str],
    dry_run: bool = False,
) -> tuple[bool, str]:
    """Add related-skills metadata to a single skill's frontmatter.

    Returns (success, message).
    """
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return False, f"{skill_name}: SKILL.md not found"

    content = skill_md.read_text()
    fm, body = parse_frontmatter(content)

    if fm is None:
        return False, f"{skill_name}: No valid frontmatter found"

    # Check if already has related-skills
    metadata = fm.get("metadata", {})
    if isinstance(metadata, dict) and "related-skills" in metadata:
        return True, f"{skill_name}: Already has related-skills (skipped)"

    # Extract related skills from body
    related_skills = extract_related_skills(body, valid_dirs)

    # Add to frontmatter
    new_content = add_related_skills_to_frontmatter(content, related_skills)

    if dry_run:
        print(f"  {skill_name}: related-skills: {related_skills or '(empty)'}")
        return True, f"{skill_name}: Would add related-skills (dry-run)"

    skill_md.write_text(new_content)
    return True, f"{skill_name}: Added related-skills"


def migrate_skill(skill_dir: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Migrate a single skill's frontmatter.

    Returns (success, message).
    """
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return False, f"{skill_name}: SKILL.md not found"

    content = skill_md.read_text()
    fm, body = parse_frontmatter(content)

    if fm is None:
        return False, f"{skill_name}: No valid frontmatter found"

    # Check if already migrated (has metadata key)
    if "metadata" in fm:
        return True, f"{skill_name}: Already migrated (skipped)"

    # Validate required fields exist
    for field in ["name", "description", "triggers"]:
        if field not in fm:
            return False, f"{skill_name}: Missing required field '{field}'"

    # Build new frontmatter
    new_frontmatter = build_new_frontmatter(fm, skill_name)
    new_content = new_frontmatter + body

    if dry_run:
        print(f"\n{'='*60}")
        print(f"  {skill_name}")
        print(f"{'='*60}")
        print(new_frontmatter)
        return True, f"{skill_name}: Would migrate (dry-run)"

    skill_md.write_text(new_content)
    return True, f"{skill_name}: Migrated"


def main():
    parser = argparse.ArgumentParser(
        description="Migrate skill frontmatter to Agent Skills spec-compliant structure.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--skill",
        help="Migrate only the specified skill",
    )
    parser.add_argument(
        "--related-skills",
        action="store_true",
        help="Add related-skills metadata extracted from ## Related Skills body section",
    )
    args = parser.parse_args()

    if not SKILLS_DIR.exists():
        print(f"Error: Skills directory not found: {SKILLS_DIR}")
        sys.exit(1)

    # Find skill directories
    skill_dirs = sorted(
        [d for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )

    if args.skill:
        skill_dirs = [d for d in skill_dirs if d.name == args.skill]
        if not skill_dirs:
            print(f"Error: Skill not found: {args.skill}")
            sys.exit(1)

    # Build set of all valid skill directory names
    all_skill_dirs = {
        d.name
        for d in SKILLS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    }

    # Related-skills migration pass
    if args.related_skills:
        success_count = 0
        skip_count = 0
        fail_count = 0

        for skill_dir in skill_dirs:
            ok, msg = migrate_related_skills(
                skill_dir,
                all_skill_dirs,
                dry_run=args.dry_run,
            )
            if ok:
                if "skipped" in msg:
                    skip_count += 1
                else:
                    success_count += 1
            else:
                fail_count += 1
                print(f"  FAIL: {msg}", file=sys.stderr)

        print()
        print(f"Related-skills migration {'preview' if args.dry_run else 'complete'}:")
        print(f"  Updated:  {success_count}")
        print(f"  Skipped:  {skip_count}")
        print(f"  Failed:   {fail_count}")
        print(f"  Total:    {len(skill_dirs)}")

        if fail_count > 0:
            sys.exit(1)
        return

    # Check domain map coverage
    unmapped = []
    for d in skill_dirs:
        if d.name not in SKILL_DOMAIN_MAP:
            unmapped.append(d.name)
    if unmapped:
        print(f"Warning: Skills without domain mapping: {', '.join(unmapped)}")
        print("These will get domain 'unknown'.")
        print()

    # Migrate
    success_count = 0
    skip_count = 0
    fail_count = 0

    for skill_dir in skill_dirs:
        ok, msg = migrate_skill(skill_dir, dry_run=args.dry_run)
        if ok:
            if "skipped" in msg:
                skip_count += 1
            else:
                success_count += 1
        else:
            fail_count += 1
            print(f"  FAIL: {msg}", file=sys.stderr)

    # Summary
    print()
    print(f"Migration {'preview' if args.dry_run else 'complete'}:")
    print(f"  Migrated: {success_count}")
    print(f"  Skipped:  {skip_count}")
    print(f"  Failed:   {fail_count}")
    print(f"  Total:    {len(skill_dirs)}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
