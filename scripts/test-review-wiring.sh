#!/usr/bin/env bash
#
# Test that the review references match the bundled guard runtime:
# the example verdicts in references/review/rollup.md build a rollup, and
# the gate refuses open blocking and PR-feedback rows until the owner's
# decisions are logged.
#
# Usage: bash scripts/test-review-wiring.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }
assert_equal() {
    if [ "$1" = "$2" ]; then pass "$3"; else fail "$3 (expected $2, got $1)"; fi
}
assert_contains() {
    if grep -qF -- "$2" "$1" 2>/dev/null; then pass "$3"; else fail "$3 ('$2' missing from $1)"; fi
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD=(python3 "$REPO_ROOT/runtime")  # the guard source runs as a directory; the plugin ships it as plugin/runtime/guard.pyz
VERIFIER="$REPO_ROOT/plugin/references/review/verifier.md"
ROLLUP_REF="$REPO_ROOT/plugin/references/review/rollup.md"

echo "review references"

# The verifier brief carries the rules the gate and rollup rely on
for s in "debugging-wizard" "Reproduce, Isolate and Hypothesize" "one verifier per merged blocking or warning finding" \
    "acceptance criteria" "git worktree add --detach" "no gitignored files" "review/repro/" "unresolved" \
    "second look" "writes its own RED test" "refactor"; do
    assert_contains "$VERIFIER" "$s" "verifier brief covers '$s'"
done
for hidden in "reviewer" "tier" "reasoning"; do
    assert_contains "$VERIFIER" "Never in the packet" "verifier brief lists what the packet hides ($hidden)"
done
for s in "Tokens" "Minutes" "fixed-verified" "wontfix" "rejection-accepted" "guard gate" "guard decide" "--transcripts"; do
    assert_contains "$ROLLUP_REF" "$s" "rollup reference covers '$s'"
done

echo "runtime wiring"

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
git -C "$WORK" init -q
git -C "$WORK" config user.email test@example.com
git -C "$WORK" config user.name test
SPEC="$WORK/docs/specs/todo/demo"
mkdir -p "$SPEC/review"
printf '# Demo\n\n**Spec:** demo\n\n## Readiness\n\n| Ticket | Readiness | Evidence or question |\n|---|---|---|\n| T1 | Ready | - |\n' >"$SPEC/overview.md"
printf '# Demo plan\n\n## Completion Status\n\n| Ticket | Status | Completed Date | Notes |\n|---|---|---|---|\n| T1 | Done | 2026-11-10 | - |\n' >"$SPEC/implementation-plan.md"
git -C "$WORK" add -A
git -C "$WORK" commit -qm init

# The example verdicts block in the rollup reference, as documented
sed -n '/<!-- example-verdicts:start -->/,/<!-- example-verdicts:end -->/p' "$ROLLUP_REF" | sed '1,2d;$d' | sed '$d' >"$WORK/verdicts.jsonl"
assert_equal "$(wc -l <"$WORK/verdicts.jsonl" | tr -d ' ')" "3" "the reference holds three example verdicts"

set +e
(cd "$WORK" && "${GUARD[@]}" rollup demo --verdicts "$WORK/verdicts.jsonl" >/dev/null 2>&1)
rc=$?
set -e
assert_equal "$rc" "0" "guard rollup accepts the documented verdict format"
assert_contains "$SPEC/review/rollup.md" "| ID | Tier | Suggested | Sources | Location | Claim | Verdict | Proof | Evidence | Reason | Tokens | Minutes | Status |" "rollup has the documented columns"
for id in F1 F2 F3; do assert_contains "$SPEC/review/rollup.md" "| $id |" "rollup lists $id"; done

gate() {
    set +e
    (cd "$WORK" && "${GUARD[@]}" gate demo >/dev/null 2>&1)
    echo $?
    set -e
}
assert_equal "$(gate)" "1" "gate refuses an open blocking row"
(cd "$WORK" && "${GUARD[@]}" decide F1 wontfix --spec demo --session test >/dev/null)
assert_equal "$(gate)" "0" "gate passes once the blocking row is wontfix"

printf '# PR feedback, round 1\n\n| ID | Tier | Suggested | Sources | Location | Claim | Verdict | Proof | Evidence | Reason | Tokens | Minutes | Status |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|\n| P1 | advisory | - | reviewer | src/a.py:1 | Why this name? | - | - | - | - | - | - | open |\n' >"$SPEC/review/pr-feedback-1.md"
assert_equal "$(gate)" "1" "gate refuses an open PR-feedback row whatever its tier"
(cd "$WORK" && "${GUARD[@]}" decide P1 answered --spec demo --session test >/dev/null)
assert_equal "$(gate)" "0" "gate passes once the question is answered"

printf '| T2 | Pending | - | - |\n' >>"$SPEC/implementation-plan.md"
assert_equal "$(gate)" "1" "gate refuses a Pending ticket"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
