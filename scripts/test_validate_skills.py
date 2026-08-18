#!/usr/bin/env python3
"""Focused regression tests for skill validation behavior."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT_PATH = Path(__file__).with_name("validate-skills.py")
SPEC = importlib.util.spec_from_file_location("validate_skills", SCRIPT_PATH)
assert SPEC and SPEC.loader
validate_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_skills)


class DocumentationBacklinkCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skill_name = "example-skill"
        self.skill_dir = Path(self.temp_dir.name) / self.skill_name
        self.skill_dir.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_skill(self, body: str) -> None:
        content = f"""---
name: {self.skill_name}
description: Example capability. Use when testing validator behavior.
metadata:
  domain: quality
---

# Example Skill

{body}
"""
        (self.skill_dir / "SKILL.md").write_text(content)

    def issues_for(self, body: str):
        self.write_skill(body)
        checker = validate_skills.DocumentationBacklinkChecker()
        return checker.check(self.skill_dir, self.skill_name)

    def test_accepts_one_canonical_backlink_as_last_non_blank_line(self) -> None:
        issues = self.issues_for(
            "Guidance.\n\n[Documentation](https://jeffallan.github.io/claude-skills/skills/quality/example-skill/)\n"
        )

        self.assertEqual([], issues)

    def test_rejects_missing_backlink(self) -> None:
        issues = self.issues_for("Guidance.\n")

        self.assertEqual("documentation-backlink", issues[0].check)
        self.assertIn("missing", issues[0].message.lower())

    def test_rejects_backlink_with_wrong_domain_or_slug(self) -> None:
        issues = self.issues_for(
            "[Documentation](https://jeffallan.github.io/claude-skills/skills/security/other-skill/)\n"
        )

        self.assertEqual(1, len(issues))
        self.assertIn("expected", issues[0].message.lower())

    def test_rejects_content_after_backlink(self) -> None:
        issues = self.issues_for(
            "[Documentation](https://jeffallan.github.io/claude-skills/skills/quality/example-skill/)\n\nMore guidance.\n"
        )

        self.assertEqual(1, len(issues))
        self.assertIn("last non-blank line", issues[0].message)

    def test_rejects_an_extra_documentation_link(self) -> None:
        issues = self.issues_for(
            "[Documentation](https://example.com/old-docs)\n\n"
            "[Documentation](https://jeffallan.github.io/claude-skills/skills/quality/example-skill/)\n"
        )

        self.assertEqual(1, len(issues))
        self.assertIn("appear once", issues[0].message)

    def test_defers_invalid_metadata_shape_to_metadata_checker(self) -> None:
        (self.skill_dir / "SKILL.md").write_text(
            f"""---
name: {self.skill_name}
description: Example capability. Use when testing validator behavior.
metadata: invalid
---

# Example Skill
"""
        )

        checker = validate_skills.DocumentationBacklinkChecker()

        self.assertEqual([], checker.check(self.skill_dir, self.skill_name))


class ValidatorCompositionTests(unittest.TestCase):
    def test_registers_backlink_checker_without_changing_workflow_checker(self) -> None:
        with tempfile.TemporaryDirectory() as skills_dir:
            validator = validate_skills.SkillValidator(skills_dir=skills_dir)

        self.assertIn(
            "documentation-backlink",
            [checker.name for checker in validator.checkers],
        )
        self.assertTrue(hasattr(validate_skills.WorkflowDefinitionChecker, "_validate_definition"))


if __name__ == "__main__":
    unittest.main()
