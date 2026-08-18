#!/usr/bin/env python3
"""Behavior tests for the repository skill scaffold command."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("create-skill.py")


class CreateSkillTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            check=False,
            text=True,
        )

    def test_creates_repository_template_and_reference_directory(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            result = self.run_cli(
                "accessibility-auditor",
                "--domain",
                "quality",
                "--description",
                "Audits accessible interfaces. Use when checking WCAG conformance.",
                "--author",
                "octocat",
                "--output",
                output_dir,
            )

            skill_file = Path(output_dir) / "accessibility-auditor" / "SKILL.md"
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(skill_file.is_file())
            reference_file = skill_file.parent / "references" / "overview.md"
            self.assertTrue(reference_file.is_file())
            self.assertIn("# Accessibility Auditor Reference", reference_file.read_text())
            content = skill_file.read_text()
            self.assertIn("metadata:\n", content)
            self.assertIn("author: https://github.com/octocat", content)
            self.assertIn("## Core Workflow", content)
            self.assertTrue(
                content.rstrip().endswith(
                    "[Documentation](https://jeffallan.github.io/claude-skills/skills/quality/accessibility-auditor/)"
                )
            )

    def test_dry_run_does_not_create_files(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            result = self.run_cli(
                "api-auditor",
                "--domain",
                "quality",
                "--description",
                "Audits API contracts. Use when reviewing API changes.",
                "--author",
                "octocat",
                "--output",
                output_dir,
                "--dry-run",
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse((Path(output_dir) / "api-auditor").exists())
            self.assertIn("Would create", result.stdout)

    def test_rejects_invalid_name(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            result = self.run_cli(
                "Invalid_Name",
                "--domain",
                "quality",
                "--description",
                "Audits APIs. Use when reviewing API changes.",
                "--author",
                "octocat",
                "--output",
                output_dir,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("lowercase letters", result.stderr)

    def test_refuses_to_overwrite_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            skill_dir = Path(output_dir) / "api-auditor"
            skill_dir.mkdir()
            marker = skill_dir / "keep.txt"
            marker.write_text("keep")

            result = self.run_cli(
                "api-auditor",
                "--domain",
                "quality",
                "--description",
                "Audits APIs. Use when reviewing API changes.",
                "--author",
                "octocat",
                "--output",
                output_dir,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertEqual("keep", marker.read_text())

    def test_rejects_invalid_github_author(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            result = self.run_cli(
                "api-auditor",
                "--domain",
                "quality",
                "--description",
                "Audits APIs. Use when reviewing API changes.",
                "--author",
                "not/a-user",
                "--output",
                output_dir,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("GitHub username", result.stderr)

    def test_rejects_multiline_description(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            result = self.run_cli(
                "api-auditor",
                "--domain",
                "quality",
                "--description",
                "Audits APIs. Use when reviewing APIs.\nrole: injected",
                "--author",
                "octocat",
                "--output",
                output_dir,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("single line", result.stderr)


if __name__ == "__main__":
    unittest.main()
