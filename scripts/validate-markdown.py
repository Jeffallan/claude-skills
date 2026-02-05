#!/usr/bin/env python3
"""
Validate markdown files for common parsing errors.

Checks for:
- HTML comments breaking tables
- Unclosed code blocks
- Missing table separator rows
- Inconsistent column counts in tables

Usage:
    python scripts/validate-markdown.py [--check] [--path PATH]
"""

from dataclasses import dataclass
from pathlib import Path
from enum import StrEnum
import argparse
import re
import sys


class IssueType(StrEnum):
    HTML_IN_TABLE = "html-in-table"
    UNCLOSED_CODE_BLOCK = "unclosed-code-block"
    MISSING_SEPARATOR = "missing-table-separator"
    COLUMN_MISMATCH = "column-count-mismatch"


@dataclass
class MarkdownIssue:
    file: Path
    line: int
    issue_type: IssueType
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: [{self.issue_type}] {self.message}"


def count_columns(line: str) -> int:
    """Count table columns, accounting for escaped pipes."""
    cleaned = line.strip().replace("\\|", "\x00")
    return cleaned.count("|") - 1


def is_table_row(line: str) -> bool:
    """Check if a line is a table row."""
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 2


def is_separator_row(line: str) -> bool:
    """Check if a line is a table separator row."""
    stripped = line.strip()
    return bool(re.match(r"^\|[\s\-:|]+\|$", stripped))


def is_html_comment(line: str) -> bool:
    """Check if a line contains an HTML comment."""
    return "<!--" in line


def validate_file(path: Path) -> list[MarkdownIssue]:
    """Validate a single markdown file for issues."""
    issues: list[MarkdownIssue] = []

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    # Check for unclosed code blocks
    in_code_block = False
    last_fence_line = 0

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            if not in_code_block:
                last_fence_line = i
            in_code_block = not in_code_block

    if in_code_block:
        issues.append(
            MarkdownIssue(
                file=path,
                line=last_fence_line,
                issue_type=IssueType.UNCLOSED_CODE_BLOCK,
                message=f"Code block opened at line {last_fence_line} is never closed",
            )
        )

    # Check tables
    in_code_block = False
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            i += 1
            continue

        if in_code_block:
            i += 1
            continue

        # Check for table
        if is_table_row(line):
            table_start = i
            header_cols = count_columns(line)

            # Check next line
            i += 1
            if i >= len(lines):
                break

            next_line = lines[i]

            # Check for HTML comment between header and separator
            if is_html_comment(next_line):
                issues.append(
                    MarkdownIssue(
                        file=path,
                        line=i + 1,
                        issue_type=IssueType.HTML_IN_TABLE,
                        message="HTML comment interrupts table structure",
                    )
                )
                i += 1
                continue

            # Check for separator row
            if not is_separator_row(next_line):
                issues.append(
                    MarkdownIssue(
                        file=path,
                        line=i + 1,
                        issue_type=IssueType.MISSING_SEPARATOR,
                        message="Table header not followed by separator row",
                    )
                )
                i += 1
                continue

            # Check data rows
            i += 1
            while i < len(lines):
                data_line = lines[i]
                data_stripped = data_line.strip()

                # Check for HTML comment in table
                if is_html_comment(data_line):
                    issues.append(
                        MarkdownIssue(
                            file=path,
                            line=i + 1,
                            issue_type=IssueType.HTML_IN_TABLE,
                            message="HTML comment interrupts table structure",
                        )
                    )

                # End of table
                if data_stripped == "" or not is_table_row(data_line):
                    break

                # Check column count
                cols = count_columns(data_line)
                if cols != header_cols:
                    issues.append(
                        MarkdownIssue(
                            file=path,
                            line=i + 1,
                            issue_type=IssueType.COLUMN_MISMATCH,
                            message=f"Expected {header_cols} columns, got {cols}",
                        )
                    )

                i += 1
        else:
            i += 1

    return issues


def validate_directory(root: Path) -> list[MarkdownIssue]:
    """Validate all markdown files in a directory."""
    all_issues: list[MarkdownIssue] = []

    for md_file in sorted(root.rglob("*.md")):
        issues = validate_file(md_file)
        all_issues.extend(issues)

    return all_issues


def main() -> int:
    """Main entry point. Returns exit code."""
    parser = argparse.ArgumentParser(
        description="Validate markdown files for parsing errors"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check only, don't output suggestions (for CI)",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("skills"),
        help="Path to validate (default: skills/)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        return 1

    if args.path.is_file():
        issues = validate_file(args.path)
    else:
        issues = validate_directory(args.path)

    if args.format == "json":
        import json

        output = [
            {
                "file": str(i.file),
                "line": i.line,
                "type": str(i.issue_type),
                "message": i.message,
            }
            for i in issues
        ]
        print(json.dumps(output, indent=2))
    else:
        # Group by issue type
        by_type: dict[IssueType, list[MarkdownIssue]] = {}
        for issue in issues:
            by_type.setdefault(issue.issue_type, []).append(issue)

        if issues:
            for issue_type, type_issues in sorted(by_type.items()):
                print(f"\n{issue_type.upper()} ({len(type_issues)} issues):")
                for issue in type_issues:
                    print(f"  {issue}")

            print(f"\nTotal: {len(issues)} issues found")
        else:
            print("No markdown issues found.")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
