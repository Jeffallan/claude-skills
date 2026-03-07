# Suggested Commands

## Validation
```bash
# Full skill validation (YAML, descriptions, references, counts)
python scripts/validate-skills.py

# Single skill
python scripts/validate-skills.py --skill react-expert

# YAML checks only
python scripts/validate-skills.py --check yaml

# Reference checks only
python scripts/validate-skills.py --check references

# JSON output for CI
python scripts/validate-skills.py --format json
```

## Markdown Validation
```bash
python scripts/validate-markdown.py
python scripts/validate-markdown.py --path FILE    # Single file
python scripts/validate-markdown.py --check        # CI mode
```

## Version & Docs Updates
```bash
# Update version in version.json first, then:
python scripts/update-docs.py

# Check files are in sync (CI)
python scripts/update-docs.py --check

# Preview changes
python scripts/update-docs.py --dry-run
```

## Social Preview
```bash
npm install --no-save puppeteer && node ./assets/capture-screenshot.js
```

## Git / System
```bash
git status
git log --oneline -10
gh pr view NUMBER
gh pr merge NUMBER --merge
```
