# Task Completion Checklist

When a task is completed, run the following before committing:

1. **Validate skills**: `python scripts/validate-skills.py`
   - Must pass with 0 errors (warnings OK)

2. **Validate markdown** (if markdown files changed): `python scripts/validate-markdown.py`

3. **Update docs** (if version/counts changed):
   - Edit `version.json` with new version/counts
   - Run `python scripts/update-docs.py`

4. **Pre-commit hooks** run automatically on `git commit`:
   - ruff (lint)
   - ruff-format (format)
   - prettier (JSON/JS)
   - pyright (type check)

5. **Changelog**: Update CHANGELOG.md under [Unreleased] or new version section

6. **For releases**: Follow the full Release Checklist in CLAUDE.md
