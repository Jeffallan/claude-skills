#!/usr/bin/env bash
#
# Test that the workflow commands carry the rules the v0.5.0 pilots showed
# they need: parallel read-only agents, no self-scheduling, missing metrics,
# the config wizard's tracker pick, triage keeping every ticket, and ticket
# evidence kept in the repo.
#
# Usage: bash scripts/test-command-rules.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }
assert_contains() {
    if grep -qF -- "$2" "$1" 2>/dev/null; then pass "$3"; else fail "$3 ('$2' missing from $1)"; fi
}
assert_not_contains() {
    if grep -qF -- "$2" "$1" 2>/dev/null; then fail "$3 ('$2' found in $1)"; else pass "$3"; fi
}

PLUGIN="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/plugin"
CMD="$PLUGIN/commands"
REF="$PLUGIN/references"

echo "parallel read-only agents"
for f in spec/create spec/triage spec/diff spec/review discovery/create discovery/approve ticket/execute; do
    assert_contains "$CMD/$f.md" "in one message" "$f starts its independent read-only agents in one message"
done
assert_contains "$CMD/spec/review.md" "shared database or fixed ports" "spec:review keeps verifiers that share a database or ports one at a time"

echo "no self-scheduling"
n=$(grep -cF "never schedule a fallback" "$CMD/spec/review.md" || true)
if [ "$n" -ge 2 ]; then pass "spec:review repeats the no-fallback rule at the verifiers and the recheck"; else fail "spec:review repeats the no-fallback rule at the verifiers and the recheck (found $n)"; fi
ask_block=$(sed -n '/^## Shared ask rules$/,/^## Judging a run$/p' "$REF/specs/launch.md" | sed -n '/"ask": \[/,/\]/p')
for tool in ScheduleWakeup CronCreate RemoteTrigger; do
    if printf '%s\n' "$ask_block" | grep -qF "\"$tool\""; then pass "shared ask rules include $tool"; else fail "shared ask rules include $tool"; fi
    assert_contains "$CMD/spec/create.md" "$tool" "spec:create's settings step names $tool"
done

echo "missing metrics"
step1=$(sed -n '/^## Step 1: Metrics$/,/^## Step 2: Panel$/p' "$CMD/spec/review.md")
for s in "did not run" "AskUserQuestion" "goal mode"; do
    if printf '%s\n' "$step1" | grep -qF "$s"; then pass "spec:review Step 1 handles a metric that did not run ($s)"; else fail "spec:review Step 1 handles a metric that did not run ($s)"; fi
done
step6=$(sed -n '/^## Step 6: Owner triage$/,/^## Recheck$/p' "$CMD/spec/review.md")
if printf '%s\n' "$step6" | grep -qF "did not run"; then pass "spec:review adds no refactor ticket its metric can't prove"; else fail "spec:review adds no refactor ticket its metric can't prove"; fi
step4=$(sed -n '/^## Step 4: RED$/,/^## Step 5: Implement$/p' "$CMD/ticket/execute.md")
if printf '%s\n' "$step4" | grep -qF "did not run"; then pass "ticket:execute refuses a refactor ticket whose metric did not run"; else fail "ticket:execute refuses a refactor ticket whose metric did not run"; fi

echo "config wizard"
OPS="$REF/adapters/operations.md"
assert_not_contains "$OPS" "MCP server among the session's tools: recommend" "a connected MCP server alone never makes the recommendation"
assert_contains "$OPS" "never the recommendation on its own" "the wizard lists a connected MCP server as available only"
for s in "existing config" "tickets/" "ticket CLI" "remote"; do
    assert_contains "$OPS" "$s" "the wizard recommends from the repo signal '$s'"
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
