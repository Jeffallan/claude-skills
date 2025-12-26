# Skill Trigger Logging System

> Research document for testing skill invocation accuracy via Claude Code hooks.

---

## Problem Statement

Skills are "model-invoked" - Claude decides internally when to activate them. There's no direct `PreSkillLoad` or `SkillActivation` hook event. This makes it difficult to:

- Verify correct skills activate for given prompts
- Detect trigger phrase regressions after updates
- Identify skill overlap/competition
- Measure skill invocation accuracy

## Solution: Indirect Observation via Hooks

Claude Code hooks can observe file reads and user prompts. By correlating these, we can reconstruct which skills were invoked for which prompts.

---

## Hook Configuration

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$(date -u +%Y-%m-%dT%H:%M:%SZ)|PROMPT|$(pwd)|$(jq -r '.prompt' | tr '\\n' ' ' | cut -c1-200)\" >> ~/.claude/logs/skill-triggers.log"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | grep -E '(SKILL\\.md|/references/)' | while read f; do echo \"$(date -u +%Y-%m-%dT%H:%M:%SZ)|READ|$(pwd)|$f\"; done >> ~/.claude/logs/skill-triggers.log 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### Log Format

```
TIMESTAMP|EVENT_TYPE|WORKING_DIR|CONTENT
```

**Example output:**
```
2024-12-21T14:30:00Z|PROMPT|~/Projects/myapp|debug this null pointer exception
2024-12-21T14:30:01Z|READ|~/Projects/myapp|~/Projects/claude-skills/skills/debugging-wizard/SKILL.md
2024-12-21T14:30:02Z|READ|~/Projects/myapp|~/Projects/claude-skills/skills/debugging-wizard/references/common-patterns.md
```

---

## Setup Instructions

### 1. Create Log Directory

```bash
mkdir -p ~/.claude/logs
```

### 2. Add Hooks to Settings

```bash
# Edit or create settings file
nano ~/.claude/settings.json
```

Paste the hook configuration above.

### 3. Verify Hooks Are Active

```bash
# Start a new Claude Code session and check logs
tail -f ~/.claude/logs/skill-triggers.log
```

---

## Analysis Scripts

### View Recent Activity

```bash
# Last 20 skill-related events
tail -20 ~/.claude/logs/skill-triggers.log | column -t -s'|'
```

### Correlate Prompts to Skills

```bash
#!/bin/bash
# ~/.claude/scripts/analyze-triggers.sh

LOG=~/.claude/logs/skill-triggers.log

echo "=== Prompt → Skill Mapping ==="
echo ""

# Group reads that follow each prompt
awk -F'|' '
  /\|PROMPT\|/ {
    if (prompt != "") print prompt " → " skills
    prompt = $4
    skills = ""
  }
  /\|READ\|.*SKILL\.md/ {
    match($4, /skills\/([^\/]+)\//, arr)
    if (arr[1] != "") skills = skills " " arr[1]
  }
  END { if (prompt != "") print prompt " → " skills }
' "$LOG"
```

### Filter by Project

```bash
# Only show triggers from a specific project
grep "/Projects/claude-skills|" ~/.claude/logs/skill-triggers.log
```

### Skill Invocation Frequency

```bash
# Count which skills are invoked most often
grep "|READ|" ~/.claude/logs/skill-triggers.log \
  | grep "SKILL.md" \
  | sed 's|.*/skills/||; s|/SKILL.md||' \
  | sort | uniq -c | sort -rn
```

---

## Test Harness

### Test Case Format

Create `~/.claude/tests/skill-trigger-tests.json`:

```json
[
  {
    "prompt": "debug this null pointer exception",
    "expected_skills": ["debugging-wizard"],
    "not_expected": ["test-master"]
  },
  {
    "prompt": "optimize this PostgreSQL query",
    "expected_skills": ["postgres-pro", "database-optimizer"],
    "not_expected": ["sql-pro"]
  },
  {
    "prompt": "review this NestJS controller for security issues",
    "expected_skills": ["nestjs-expert", "secure-code-guardian"],
    "not_expected": ["django-expert"]
  }
]
```

### Run Tests and Compare

```bash
#!/bin/bash
# ~/.claude/scripts/test-skill-triggers.sh

TESTS=~/.claude/tests/skill-trigger-tests.json
LOG=~/.claude/logs/skill-triggers.log
RESULTS=~/.claude/logs/test-results-$(date +%Y%m%d).log

echo "Skill Trigger Test Results - $(date)" > "$RESULTS"
echo "=================================" >> "$RESULTS"

jq -c '.[]' "$TESTS" | while read test; do
  prompt=$(echo "$test" | jq -r '.prompt')
  expected=$(echo "$test" | jq -r '.expected_skills[]' | tr '\n' ' ')

  # Find skills invoked after this prompt
  actual=$(grep -A5 "$prompt" "$LOG" | grep "SKILL.md" | sed 's|.*/skills/||; s|/SKILL.md||' | tr '\n' ' ')

  if [[ "$actual" == *"$expected"* ]]; then
    echo "[PASS] $prompt → $actual" >> "$RESULTS"
  else
    echo "[FAIL] $prompt" >> "$RESULTS"
    echo "       Expected: $expected" >> "$RESULTS"
    echo "       Actual:   $actual" >> "$RESULTS"
  fi
done

cat "$RESULTS"
```

---

## Insights From Working Directory

The `pwd` field enables:

1. **Project-specific analysis** - Which skills activate in which codebases?
2. **Context correlation** - Does the same prompt trigger different skills in different projects?
3. **Skill relevance** - Are certain skills only useful in certain project types?

### Example: Project-Skill Heatmap

```bash
# Which skills are used in which projects?
awk -F'|' '/\|READ\|.*SKILL\.md/ {
  split($3, path, "/")
  project = path[5]  # Assumes /Users/user/Projects/name structure
  match($4, /skills\/([^\/]+)\//, skill)
  print project, skill[1]
}' ~/.claude/logs/skill-triggers.log | sort | uniq -c | sort -rn
```

---

## Limitations

| Capability | Status |
|------------|--------|
| Log skill file reads | Supported |
| Log reference file reads | Supported |
| Log working directory | Supported |
| Correlate prompt → skill | Manual/scripted |
| Block incorrect skill | Not possible |
| Real-time alerts | Not built-in |

---

## Future Enhancements

1. **Structured logging** - Output JSON for easier parsing
2. **Dashboard** - Visual display of skill invocation patterns
3. **Regression CI** - Run test suite on skill changes
4. **Overlap detection** - Alert when multiple skills compete for same prompt

---

## References

- Claude Code hooks documentation
- [obra/superpowers](https://github.com/obra/superpowers) - Verification discipline patterns
- [claude-code-plugins-plus-skills](https://github.com/jeremylongshore/claude-code-plugins-plus-skills) - Verification script patterns
