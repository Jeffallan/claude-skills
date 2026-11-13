#!/usr/bin/env bash
#
# Test the goal launch command in references/specs/launch.md: the /goal prompt
# must survive the variadic --allowedTools/--disallowedTools options, the deny set
# must cover history rewrites, and, when claude is installed outside CI, the
# printed command must start a session that receives its prompt.
#
# Usage: bash scripts/test-launch-command.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCH="$REPO_ROOT/references/specs/launch.md"

echo "goal launch command"

# The whole-spec launch block, from "claude \" to the /goal line
block=$(sed -n '/^# Whole spec$/,/^```$/p' "$LAUNCH" | sed '1d;$d' | grep -v '^# Next batch')
goal_line=$(printf '%s\n' "$block" | grep -n '"/goal ' | cut -d: -f1)
prev_line=$(printf '%s\n' "$block" | sed -n "$((goal_line - 1))p")

if printf '%s\n' "$block" | sed -n "${goal_line}p" | grep -q '^  -- "/goal '; then
    pass "a -- separator ends the options before the /goal prompt"
else
    fail "a -- separator ends the options before the /goal prompt (variadic --disallowedTools swallows it)"
fi
case "$prev_line" in
    *"--disallowedTools"* | *"goal.deny"*) pass "the prompt is the last argument" ;;
    *) fail "the prompt is the last argument (line before it: $prev_line)" ;;
esac

for rule in 'Bash(git rebase:*)' 'Bash(git reset:*)' 'Bash(git commit --amend:*)' 'Bash(git push:*)' AskUserQuestion; do
    if printf '%s\n' "$block" | grep -qF -- "$rule"; then pass "launch denies $rule"; else fail "launch denies $rule"; fi
done

# Live check: the printed flags plus a short prompt, headless, on a small model
if [ -z "${CI:-}" ] && command -v claude >/dev/null 2>&1; then
    flags=$(printf '%s\n' "$block" | sed '1d' | grep -v '"/goal ' | grep -v 'goal.deny' | tr -d '\\\n')
    set +e
    out=$(cd "$(mktemp -d)" && eval "claude -p --model haiku --setting-sources project $flags -- 'Reply with exactly: PROMPT-OK'" </dev/null 2>&1)
    set -e
    if printf '%s' "$out" | grep -q 'PROMPT-OK'; then
        pass "a session started with the printed flags receives its prompt"
    else
        fail "a session started with the printed flags receives its prompt (got: $(printf '%s' "$out" | head -3))"
    fi
else
    echo "  SKIP: live launch check (CI, or claude not installed)"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
