#!/usr/bin/env python3
"""
Update documentation files with version and counts from version.json.

This script:
1. Reads the version from version.json
2. Computes counts (skills, references, workflows) from filesystem
3. Updates version.json with computed counts
4. Updates all documentation files with version and counts

Usage:
    python scripts/update-docs.py           # Update all files
    python scripts/update-docs.py --check   # Check if files are in sync (no changes)
    python scripts/update-docs.py --dry-run # Show what would change

Exit codes:
    0 = Success (or in sync for --check)
    1 = Files out of sync (--check) or error
"""

import argparse
import json
import re
import sys
from pathlib import Path


# =============================================================================
# Configuration
# =============================================================================

VERSION_FILE = "version.json"
SKILLS_DIR = "skills"
COMMANDS_DIR = "commands/project"

# Files to update and their patterns
FILES_TO_UPDATE = {
    ".claude-plugin/plugin.json": "json",
    ".claude-plugin/marketplace.json": "json",
    "README.md": "markdown",
    "QUICKSTART.md": "markdown",
    "ROADMAP.md": "markdown",
    "assets/social-preview.html": "html",
}


# =============================================================================
# Count Functions
# =============================================================================

def count_skills(base_path: Path) -> int:
    """Count skill directories that contain a SKILL.md file."""
    skills_dir = base_path / SKILLS_DIR
    if not skills_dir.exists():
        return 0
    return sum(
        1 for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )


def count_references(base_path: Path) -> int:
    """Count reference markdown files."""
    skills_dir = base_path / SKILLS_DIR
    if not skills_dir.exists():
        return 0
    return sum(1 for _ in skills_dir.rglob("references/*.md"))


def count_workflows(base_path: Path) -> int:
    """Count workflow command markdown files."""
    commands_dir = base_path / COMMANDS_DIR
    if not commands_dir.exists():
        return 0
    return sum(1 for _ in commands_dir.rglob("*.md"))


# =============================================================================
# Update Functions
# =============================================================================

def update_json_file(file_path: Path, version: str, counts: dict, dry_run: bool) -> bool:
    """Update JSON files (plugin.json, marketplace.json)."""
    if not file_path.exists():
        print(f"  Skipping {file_path} (not found)")
        return False

    content = file_path.read_text()
    original = content

    # Update version
    content = re.sub(
        r'"version":\s*"[^"]*"',
        f'"version": "{version}"',
        content
    )

    # Update skill count in description
    content = re.sub(
        r'(\d+)\s+specialized\s+skills',
        f'{counts["skillCount"]} specialized skills',
        content
    )

    # Update workflow count in description
    content = re.sub(
        r'(\d+)\s+project\s+workflow\s+commands',
        f'{counts["workflowCount"]} project workflow commands',
        content
    )

    if content != original:
        if dry_run:
            print(f"  Would update {file_path}")
        else:
            file_path.write_text(content)
            print(f"  Updated {file_path}")
        return True
    return False


def update_markdown_file(file_path: Path, version: str, counts: dict, dry_run: bool) -> bool:
    """Update Markdown files (README.md, QUICKSTART.md, ROADMAP.md)."""
    if not file_path.exists():
        print(f"  Skipping {file_path} (not found)")
        return False

    content = file_path.read_text()
    original = content

    # Update version badge (e.g., version-0.4.1-blue.svg)
    content = re.sub(
        r'version-[\d.]+-blue\.svg',
        f'version-{version}-blue.svg',
        content
    )

    # Update "**Version:** vX.Y.Z" pattern
    content = re.sub(
        r'\*\*Version:\*\*\s*v[\d.]+',
        f'**Version:** v{version}',
        content
    )

    # Update skill counts (various patterns)
    # "65 Skills" or "65 skills"
    content = re.sub(
        r'(\d+)\s+[Ss]kills',
        f'{counts["skillCount"]} Skills',
        content
    )

    # "65 specialized skills"
    content = re.sub(
        r'(\d+)\s+specialized\s+skills',
        f'{counts["skillCount"]} specialized skills',
        content
    )

    # Update workflow counts
    # "9 Workflows" or "9 workflows"
    content = re.sub(
        r'(\d+)\s+[Ww]orkflows',
        f'{counts["workflowCount"]} Workflows',
        content
    )

    # "9 project workflow commands"
    content = re.sub(
        r'(\d+)\s+project\s+workflow\s+commands',
        f'{counts["workflowCount"]} project workflow commands',
        content
    )

    # Update reference file counts
    # "355 Reference Files" or "355 reference files"
    content = re.sub(
        r'(\d+)\s+[Rr]eference\s+[Ff]iles',
        f'{counts["referenceFileCount"]} Reference Files',
        content
    )

    if content != original:
        if dry_run:
            print(f"  Would update {file_path}")
        else:
            file_path.write_text(content)
            print(f"  Updated {file_path}")
        return True
    return False


def update_html_file(file_path: Path, version: str, counts: dict, dry_run: bool) -> bool:
    """Update HTML files (social-preview.html)."""
    if not file_path.exists():
        print(f"  Skipping {file_path} (not found)")
        return False

    content = file_path.read_text()
    original = content

    # Update counts in spans or text
    content = re.sub(
        r'>(\d+)\s+[Ss]kills<',
        f'>{counts["skillCount"]} Skills<',
        content
    )

    content = re.sub(
        r'>(\d+)\s+[Ww]orkflows<',
        f'>{counts["workflowCount"]} Workflows<',
        content
    )

    content = re.sub(
        r'>(\d+)\s+[Rr]eference\s+[Ff]iles<',
        f'>{counts["referenceFileCount"]} Reference Files<',
        content
    )

    if content != original:
        if dry_run:
            print(f"  Would update {file_path}")
        else:
            file_path.write_text(content)
            print(f"  Updated {file_path}")
        return True
    return False


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Update documentation files with version and counts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if files are in sync (exit 1 if not)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without making changes",
    )
    args = parser.parse_args()

    base_path = Path(".")
    version_path = base_path / VERSION_FILE

    # Read version.json
    if not version_path.exists():
        print(f"Error: {VERSION_FILE} not found")
        sys.exit(1)

    with open(version_path) as f:
        version_data = json.load(f)

    version = version_data.get("version", "0.0.0")

    # Compute counts
    print("Computing counts...")
    counts = {
        "skillCount": count_skills(base_path),
        "workflowCount": count_workflows(base_path),
        "referenceFileCount": count_references(base_path),
    }
    print(f"  Skills: {counts['skillCount']}")
    print(f"  Workflows: {counts['workflowCount']}")
    print(f"  Reference files: {counts['referenceFileCount']}")

    # Update version.json with computed counts
    needs_update = (
        version_data.get("skillCount") != counts["skillCount"] or
        version_data.get("workflowCount") != counts["workflowCount"] or
        version_data.get("referenceFileCount") != counts["referenceFileCount"]
    )

    if needs_update:
        version_data.update(counts)
        if args.dry_run:
            print(f"\nWould update {VERSION_FILE}")
        elif not args.check:
            with open(version_path, "w") as f:
                json.dump(version_data, f, indent=2)
                f.write("\n")
            print(f"\nUpdated {VERSION_FILE}")

    # Update documentation files
    print(f"\nUpdating files with version {version}...")
    files_changed = 0

    update_funcs = {
        "json": update_json_file,
        "markdown": update_markdown_file,
        "html": update_html_file,
    }

    for file_path, file_type in FILES_TO_UPDATE.items():
        update_func = update_funcs.get(file_type)
        if update_func:
            changed = update_func(
                base_path / file_path,
                version,
                counts,
                dry_run=args.dry_run or args.check,
            )
            if changed:
                files_changed += 1

    # Summary
    print(f"\n{'Would update' if args.dry_run or args.check else 'Updated'} {files_changed} files")

    if args.check and (files_changed > 0 or needs_update):
        print("\nFiles are out of sync. Run 'python scripts/update-docs.py' to update.")
        sys.exit(1)

    print("\nDone!")


if __name__ == "__main__":
    main()
