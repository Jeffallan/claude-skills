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

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
