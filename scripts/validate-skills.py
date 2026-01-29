#!/usr/bin/env python3
"""
Skill Validation Script for Claude Skills Repository

Validates skill structure, YAML frontmatter, and count consistency.
Run before releases to prevent broken skills from being published.

Usage:
    python scripts/validate-skills.py              # Run all checks
    python scripts/validate-skills.py --check yaml # YAML-related checks only
    python scripts/validate-skills.py --check references  # Reference checks only
    python scripts/validate-skills.py --skill react-expert  # Single skill
    python scripts/validate-skills.py --format json  # JSON for CI

Exit codes:
    0 = Success (warnings allowed)
    1 = Errors found
"""

import argparse
import json
import os
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# Try to import PyYAML, fall back to simple parser if not available
try:
    import yaml
    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False


def simple_yaml_parse(yaml_str: str) -> dict:
    """
    Simple YAML frontmatter parser for skill files.
    Handles the basic structure used in this project:
    - Simple key: value pairs
    - Lists with - prefix
    """
    result = {}
    current_key = None
    current_list = None

    for line in yaml_str.strip().split("\n"):
        # Skip empty lines
        if not line.strip():
            continue

        # Check for list item
        if line.startswith("  - ") or line.startswith("    - "):
            if current_key and current_list is not None:
                item = line.strip().lstrip("- ").strip()
                current_list.append(item)
            continue

        # Check for key: value pair
        if ":" in line and not line.startswith(" "):
            # Save previous list if any
            if current_key and current_list is not None:
                result[current_key] = current_list

            parts = line.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            # Check if this starts a list (empty value or just whitespace)
            if not value:
                current_key = key
                current_list = []
            else:
                result[key] = value
                current_key = None
                current_list = None

    # Save any remaining list
    if current_key and current_list is not None:
        result[current_key] = current_list

    return result


def parse_yaml(yaml_str: str) -> dict:
    """Parse YAML using PyYAML if available, otherwise use simple parser."""
    if HAS_PYYAML:
        return yaml.safe_load(yaml_str) or {}
    return simple_yaml_parse(yaml_str)


# =============================================================================
# Constants
# =============================================================================

SKILLS_DIR = "skills"
REQUIRED_FIELDS = ["name", "description", "triggers"]
MAX_DESCRIPTION_LENGTH = 1024
DESCRIPTION_PREFIX = "Use when"
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9-]+$")

# Files to check for count consistency
COUNT_FILES = [
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "README.md",
    "ROADMAP.md",
    "QUICKSTART.md",
    "assets/social-preview.html",
]


# =============================================================================
# Data Classes
# =============================================================================

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    skill: str
    check: str
    severity: Severity
    message: str
    file: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "check": self.check,
            "severity": self.severity.value,
            "message": self.message,
            "file": self.file,
        }


@dataclass
class ValidationResult:
    """Per-skill validation results."""
    skill: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == Severity.WARNING for i in self.issues)

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "issues": [i.to_dict() for i in self.issues],
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
        }


@dataclass
class ValidationReport:
    """Full validation report."""
    results: list[ValidationResult] = field(default_factory=list)
    count_issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(r.has_errors for r in self.results) or any(
            i.severity == Severity.ERROR for i in self.count_issues
        )

    @property
    def total_errors(self) -> int:
        count = sum(1 for r in self.results for i in r.issues if i.severity == Severity.ERROR)
        count += sum(1 for i in self.count_issues if i.severity == Severity.ERROR)
        return count

    @property
    def total_warnings(self) -> int:
        count = sum(1 for r in self.results for i in r.issues if i.severity == Severity.WARNING)
        count += sum(1 for i in self.count_issues if i.severity == Severity.WARNING)
        return count

    def to_dict(self) -> dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "count_issues": [i.to_dict() for i in self.count_issues],
            "summary": {
                "total_skills": len(self.results),
                "total_errors": self.total_errors,
                "total_warnings": self.total_warnings,
                "has_errors": self.has_errors,
            },
        }


# =============================================================================
# Checker Classes (Strategy Pattern)
# =============================================================================

class BaseChecker(ABC):
    """Abstract base class for skill checkers."""

    name: str = "base"
    category: str = "general"

    @abstractmethod
    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        """Run the check and return any issues found."""
        pass


class YamlChecker(BaseChecker):
    """Validates YAML frontmatter parsing."""

    name = "yaml"
    category = "yaml"

    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        issues = []
        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.ERROR,
                message="Missing SKILL.md file",
                file=str(skill_md),
            ))
            return issues

        content = skill_md.read_text()
        if not content.startswith("---"):
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.ERROR,
                message="SKILL.md does not start with YAML frontmatter (---)",
                file=str(skill_md),
            ))
            return issues

        parts = content.split("---", 2)
        if len(parts) < 3:
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.ERROR,
                message="Invalid YAML frontmatter structure (missing closing ---)",
                file=str(skill_md),
            ))
            return issues

        try:
            if HAS_PYYAML:
                yaml.safe_load(parts[1])
            else:
                parse_yaml(parts[1])
        except Exception as e:
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.ERROR,
                message=f"YAML parsing error: {e}",
                file=str(skill_md),
            ))

        return issues


class RequiredFieldsChecker(BaseChecker):
    """Validates required YAML fields are present."""

    name = "required-fields"
    category = "yaml"

    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        issues = []
        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            return issues  # YamlChecker will report this

        content = skill_md.read_text()
        if not content.startswith("---"):
            return issues  # YamlChecker will report this

        parts = content.split("---", 2)
        if len(parts) < 3:
            return issues  # YamlChecker will report this

        try:
            frontmatter = parse_yaml(parts[1])
            if frontmatter is None:
                frontmatter = {}
        except Exception:
            return issues  # YamlChecker will report this

        for field in REQUIRED_FIELDS:
            if field not in frontmatter:
                issues.append(ValidationIssue(
                    skill=skill_name,
                    check=self.name,
                    severity=Severity.ERROR,
                    message=f"Missing required field: {field}",
                    file=str(skill_md),
                ))
            elif field == "triggers" and not isinstance(frontmatter.get("triggers"), list):
                issues.append(ValidationIssue(
                    skill=skill_name,
                    check=self.name,
                    severity=Severity.ERROR,
                    message="'triggers' must be a list",
                    file=str(skill_md),
                ))

        return issues


class NameFormatChecker(BaseChecker):
    """Validates skill name format (letters, numbers, hyphens only)."""

    name = "name-format"
    category = "yaml"

    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        issues = []
        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            return issues

        content = skill_md.read_text()
        if not content.startswith("---"):
            return issues

        parts = content.split("---", 2)
        if len(parts) < 3:
            return issues

        try:
            frontmatter = parse_yaml(parts[1])
            if frontmatter is None:
                return issues
        except Exception:
            return issues

        name = frontmatter.get("name", "")
        if name and not NAME_PATTERN.match(name):
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.ERROR,
                message=f"Invalid name format: '{name}'. Use only letters, numbers, and hyphens.",
                file=str(skill_md),
            ))

        # Also check that directory name matches skill name
        if name and name != skill_name:
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.WARNING,
                message=f"Directory name '{skill_name}' doesn't match skill name '{name}'",
                file=str(skill_md),
            ))

        return issues


class DescriptionLengthChecker(BaseChecker):
    """Validates description is within max length."""

    name = "description-length"
    category = "yaml"

    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        issues = []
        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            return issues

        content = skill_md.read_text()
        if not content.startswith("---"):
            return issues

        parts = content.split("---", 2)
        if len(parts) < 3:
            return issues

        try:
            frontmatter = parse_yaml(parts[1])
            if frontmatter is None:
                return issues
        except Exception:
            return issues

        description = frontmatter.get("description", "")
        if description and len(description) > MAX_DESCRIPTION_LENGTH:
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.WARNING,
                message=f"Description exceeds {MAX_DESCRIPTION_LENGTH} chars ({len(description)} chars)",
                file=str(skill_md),
            ))

        return issues


class DescriptionFormatChecker(BaseChecker):
    """Validates description starts with 'Use when'."""

    name = "description-format"
    category = "yaml"

    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        issues = []
        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            return issues

        content = skill_md.read_text()
        if not content.startswith("---"):
            return issues

        parts = content.split("---", 2)
        if len(parts) < 3:
            return issues

        try:
            frontmatter = parse_yaml(parts[1])
            if frontmatter is None:
                return issues
        except Exception:
            return issues

        description = frontmatter.get("description", "")
        if description and not description.startswith(DESCRIPTION_PREFIX):
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.WARNING,
                message=f"Description should start with '{DESCRIPTION_PREFIX}' (trigger-only format)",
                file=str(skill_md),
            ))

        return issues


class ReferencesDirectoryChecker(BaseChecker):
    """Validates references/ directory exists."""

    name = "references-directory"
    category = "references"

    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        issues = []
        refs_dir = skill_path / "references"

        if not refs_dir.exists():
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.ERROR,
                message="Missing references/ directory",
                file=str(refs_dir),
            ))
        elif not refs_dir.is_dir():
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.ERROR,
                message="'references' exists but is not a directory",
                file=str(refs_dir),
            ))

        return issues


class ReferenceFileCountChecker(BaseChecker):
    """Validates skill has at least 1 reference file."""

    name = "reference-file-count"
    category = "references"

    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        issues = []
        refs_dir = skill_path / "references"

        if not refs_dir.exists() or not refs_dir.is_dir():
            return issues  # ReferencesDirectoryChecker will report this

        ref_files = list(refs_dir.glob("*.md"))
        if len(ref_files) == 0:
            issues.append(ValidationIssue(
                skill=skill_name,
                check=self.name,
                severity=Severity.WARNING,
                message="No reference files found in references/",
                file=str(refs_dir),
            ))

        return issues


class NonStandardHeadersChecker(BaseChecker):
    """Reports reference files with non-standard headers that should be removed.

    The official Agent Skills spec (https://agentskills.io/specification) does not
    require any specific headers in reference files. This checker identifies files
    that have the old project-specific 'Reference for:' and 'Load when:' headers
    so they can be cleaned up.
    """

    name = "non-standard-headers"
    category = "references"

    def check(self, skill_path: Path, skill_name: str) -> list[ValidationIssue]:
        issues = []
        refs_dir = skill_path / "references"

        if not refs_dir.exists() or not refs_dir.is_dir():
            return issues

        ref_files = list(refs_dir.glob("*.md"))
        for ref_file in ref_files:
            content = ref_file.read_text()
            lines = content.split("\n")[:10]  # Check first 10 lines
            header_text = "\n".join(lines)

            has_ref_for = "Reference for:" in header_text
            has_load_when = "Load when:" in header_text

            if has_ref_for or has_load_when:
                headers_found = []
                if has_ref_for:
                    headers_found.append("'Reference for:'")
                if has_load_when:
                    headers_found.append("'Load when:'")
                issues.append(ValidationIssue(
                    skill=skill_name,
                    check=self.name,
                    severity=Severity.ERROR,
                    message=f"Has non-standard headers ({', '.join(headers_found)}) - must be removed",
                    file=str(ref_file),
                ))

        return issues


# =============================================================================
# Count Consistency Checker
# =============================================================================

class CountConsistencyChecker:
    """Validates count consistency across documentation files."""

    def check(self, skills_dir: Path) -> list[ValidationIssue]:
        issues = []
        base_path = skills_dir.parent

        # Count actual skills
        skill_count = sum(
            1 for d in skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )

        # Count actual reference files
        ref_count = sum(
            1 for ref in skills_dir.rglob("references/*.md")
        )

        # Check each file for count mentions
        for file_path in COUNT_FILES:
            full_path = base_path / file_path
            if not full_path.exists():
                continue

            content = full_path.read_text()

            # Check for skill count mentions
            skill_patterns = [
                r"(\d+)\s*(?:specialized\s+)?skills",
                r"(\d+)\s*Skills",
            ]

            for pattern in skill_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    found_count = int(match)
                    if found_count != skill_count:
                        issues.append(ValidationIssue(
                            skill="__counts__",
                            check="count-consistency",
                            severity=Severity.WARNING,
                            message=f"Skill count mismatch: file says {found_count}, actual is {skill_count}",
                            file=str(full_path),
                        ))
                        break  # Only report once per file

            # Check for reference file count mentions
            ref_patterns = [
                r"(\d+)\s*[Rr]eference\s*[Ff]iles",
            ]

            for pattern in ref_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    found_count = int(match)
                    if found_count != ref_count:
                        issues.append(ValidationIssue(
                            skill="__counts__",
                            check="count-consistency",
                            severity=Severity.WARNING,
                            message=f"Reference count mismatch: file says {found_count}, actual is {ref_count}",
                            file=str(full_path),
                        ))
                        break

        return issues


# =============================================================================
# Formatters
# =============================================================================

class TableFormatter:
    """Human-readable table output."""

    def format(self, report: ValidationReport) -> str:
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("SKILL VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Skill issues
        skills_with_issues = [r for r in report.results if r.issues]
        if skills_with_issues:
            lines.append("SKILL ISSUES:")
            lines.append("-" * 80)
            for result in skills_with_issues:
                lines.append(f"\n  {result.skill}:")
                for issue in result.issues:
                    icon = "ERROR" if issue.severity == Severity.ERROR else "WARN "
                    file_info = f" ({issue.file})" if issue.file else ""
                    lines.append(f"    [{icon}] {issue.check}: {issue.message}{file_info}")

        # Count issues
        if report.count_issues:
            lines.append("")
            lines.append("COUNT CONSISTENCY ISSUES:")
            lines.append("-" * 80)
            for issue in report.count_issues:
                icon = "ERROR" if issue.severity == Severity.ERROR else "WARN "
                file_info = f" ({issue.file})" if issue.file else ""
                lines.append(f"  [{icon}] {issue.message}{file_info}")

        # Summary
        lines.append("")
        lines.append("=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        lines.append(f"  Skills validated: {len(report.results)}")
        lines.append(f"  Total errors:     {report.total_errors}")
        lines.append(f"  Total warnings:   {report.total_warnings}")
        lines.append("")

        if report.has_errors:
            lines.append("  STATUS: FAILED (errors found)")
        elif report.total_warnings > 0:
            lines.append("  STATUS: PASSED (with warnings)")
        else:
            lines.append("  STATUS: PASSED")

        lines.append("")
        return "\n".join(lines)


class JsonFormatter:
    """Machine-readable JSON output."""

    def format(self, report: ValidationReport) -> str:
        return json.dumps(report.to_dict(), indent=2)


# =============================================================================
# Validator
# =============================================================================

class SkillValidator:
    """Main validator that orchestrates checks."""

    def __init__(
        self,
        skills_dir: str = SKILLS_DIR,
        check_category: Optional[str] = None,
        skill_filter: Optional[str] = None,
    ):
        self.skills_dir = Path(skills_dir)
        self.check_category = check_category
        self.skill_filter = skill_filter

        # Register all checkers
        all_checkers = [
            YamlChecker(),
            RequiredFieldsChecker(),
            NameFormatChecker(),
            DescriptionLengthChecker(),
            DescriptionFormatChecker(),
            ReferencesDirectoryChecker(),
            ReferenceFileCountChecker(),
            NonStandardHeadersChecker(),
        ]

        # Filter by category if specified
        if check_category:
            self.checkers = [c for c in all_checkers if c.category == check_category]
        else:
            self.checkers = all_checkers

        self.count_checker = CountConsistencyChecker()

    def validate(self) -> ValidationReport:
        """Run all validations and return report."""
        report = ValidationReport()

        # Find all skill directories
        if not self.skills_dir.exists():
            print(f"Error: Skills directory not found: {self.skills_dir}")
            sys.exit(1)

        skill_dirs = sorted([
            d for d in self.skills_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ])

        # Filter to specific skill if requested
        if self.skill_filter:
            skill_dirs = [d for d in skill_dirs if d.name == self.skill_filter]
            if not skill_dirs:
                print(f"Error: Skill not found: {self.skill_filter}")
                sys.exit(1)

        # Run checks on each skill
        for skill_dir in skill_dirs:
            result = ValidationResult(skill=skill_dir.name)
            for checker in self.checkers:
                issues = checker.check(skill_dir, skill_dir.name)
                result.issues.extend(issues)
            report.results.append(result)

        # Run count consistency check (unless filtering to single skill or category)
        if not self.skill_filter and not self.check_category:
            report.count_issues = self.count_checker.check(self.skills_dir)

        return report


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validate skill structure and consistency for Claude Skills repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate-skills.py              # Run all checks
  python scripts/validate-skills.py --check yaml # YAML-related checks only
  python scripts/validate-skills.py --check references  # Reference checks only
  python scripts/validate-skills.py --skill react-expert  # Single skill
  python scripts/validate-skills.py --format json  # JSON for CI

Check categories:
  yaml        - YAML frontmatter validation (parsing, required fields, format)
  references  - Reference file validation (directory, count, headers)
""",
    )

    parser.add_argument(
        "--check",
        choices=["yaml", "references"],
        help="Run only checks in the specified category",
    )

    parser.add_argument(
        "--skill",
        help="Validate only the specified skill",
    )

    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument(
        "--skills-dir",
        default=SKILLS_DIR,
        help=f"Path to skills directory (default: {SKILLS_DIR})",
    )

    args = parser.parse_args()

    # Run validation
    validator = SkillValidator(
        skills_dir=args.skills_dir,
        check_category=args.check,
        skill_filter=args.skill,
    )
    report = validator.validate()

    # Format and output
    if args.format == "json":
        formatter = JsonFormatter()
    else:
        formatter = TableFormatter()

    print(formatter.format(report))

    # Exit with appropriate code
    sys.exit(1 if report.has_errors else 0)


if __name__ == "__main__":
    main()
