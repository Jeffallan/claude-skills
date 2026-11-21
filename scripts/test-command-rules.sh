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

echo "guard decide rules: a help call never asks, every decision does, the goal deny stays broad"
# Bash's [[ == ]] glob gives `*` the meaning Claude Code gives it: any text, spaces included.
matches_any() { # $1 = command, $2 = rules, one Bash(...) per line
    local rule
    while IFS= read -r rule; do
        rule=${rule#Bash(}; rule=${rule%)}
        # shellcheck disable=SC2053
        [[ $1 == $rule ]] && return 0
    done <<< "$2"
    return 1
}
ask_decide=$(printf '%s\n' "$ask_block" | grep -oE 'Bash\([^"]* decide [^"]*\)' || true)
deny_decide=$(sed -n '/^```bash$/,/^```$/p' "$REF/specs/launch.md" | grep -oE "Bash\([^']* decide [^']*\)" || true)
G='uv run -q --no-project --python ">=3.11" "/p/runtime/guard.pyz"'
real=("$G decide F3 wontfix --spec demo" "$G decide F3 rejection-accepted --spec demo" "$G decide T2 accepted --spec demo"
      "$G decide P1 answered --spec demo" "$G decide F3 revoke --spec demo" "$G decide --spec demo T2 accepted"
      "$G decide T2 accepted" "python -m ticket_guard decide F3 \"wontfix\" --spec=demo" "/p/runtime decide F3 revoke")
helps=("$G decide --help" "$G decide -h" "python -m ticket_guard decide --help")
for c in "${real[@]}"; do
    if matches_any "$c" "$ask_decide"; then pass "an ask rule matches: $c"; else fail "an ask rule matches: $c"; fi
    if matches_any "$c" "$deny_decide"; then pass "a goal deny rule matches: $c"; else fail "a goal deny rule matches: $c"; fi
done
for c in "${helps[@]}"; do
    if matches_any "$c" "$ask_decide"; then fail "no ask rule matches: $c"; else pass "no ask rule matches: $c"; fi
    if matches_any "$c" "$deny_decide"; then pass "a goal deny rule still matches: $c"; else fail "a goal deny rule still matches: $c"; fi
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

echo "missing metrics: exit 3 and the missing list"
for s in "guard metrics <spec-name> --json" "exits 3" "\`missing\`"; do
    if printf '%s\n' "$step1" | grep -qF -- "$s"; then pass "spec:review Step 1 keys the warning on the JSON run ($s)"; else fail "spec:review Step 1 keys the warning on the JSON run ($s)"; fi
done
if printf '%s\n' "$step6" | grep -qF "\`missing\`"; then pass "spec:review refuses a refactor ticket whose tool is missing"; else fail "spec:review refuses a refactor ticket whose tool is missing"; fi
for s in "Not installed, so unmeasured:" "No metric tool ran (not installed:"; do
    if printf '%s\n' "$step4" | grep -qF -- "$s"; then pass "ticket:execute reads the missing line in metrics.md ($s)"; else fail "ticket:execute reads the missing line in metrics.md ($s)"; fi
done

echo "verifier: a refactor fix whose proving tool is missing is never proven"
VER="$REF/review/verifier.md"
for s in "guard metrics <spec-name> --json" "\`missing\`" "exits 3" "never claimed proven"; do
    assert_contains "$VER" "$s" "verifier.md refuses a refactor proof without its tool ($s)"
done

echo "docs the diff adds or changes"
for s in "added in the diff" "changed in the diff"; do
    assert_contains "$CMD/spec/review.md" "$s" "spec:review says docs-affected lists a doc $s"
    assert_contains "$CMD/spec/complete.md" "$s" "spec:complete says docs-affected lists a doc $s"
done
doc_row=$(grep -F '| Docs under the docs root | `code-documenter` |' "$CMD/spec/review.md")
case "$doc_row" in *'`updated`'*) pass "the code-documenter reviews the docs the diff updated" ;; *) fail "the code-documenter reviews the docs the diff updated" ;; esac
assert_contains "$CMD/spec/complete.md" "each doc listed \`added in the diff\`" "spec:complete adds each added doc to the docs index"

echo "specs that live only on the current branch"
assert_contains "$CMD/spec/status.md" "| Unbranched (on <branch>) |" "spec:status explains the Unbranched state"
for f in spec/diff common-ground; do
    assert_contains "$CMD/$f.md" "\`Unbranched\` (any branch)" "$f counts an Unbranched spec as outstanding"
done

echo "owner revokes a decision"
assert_contains "$CMD/spec/review.md" "guard decide <F-id> revoke --spec <spec-name>" "spec:review lists revoke with the owner statuses"
if printf '%s\n' "$step6" | grep -qF "revoke that row first"; then pass "spec:review revokes a recorded decision before turning it into a fix ticket"; else fail "spec:review revokes a recorded decision before turning it into a fix ticket"; fi

echo "config wizard"
OPS="$REF/adapters/operations.md"
assert_not_contains "$OPS" "MCP server among the session's tools: recommend" "a connected MCP server alone never makes the recommendation"
assert_contains "$OPS" "never the recommendation on its own" "the wizard lists a connected MCP server as available only"
for s in "existing config" "tickets/" "ticket CLI" "remote"; do
    assert_contains "$OPS" "$s" "the wizard recommends from the repo signal '$s'"
done

echo "triage keeps every ticket"
TRIAGE="$CMD/spec/triage.md"
assert_contains "$TRIAGE" "Keep every ticket the owner asked about" "spec:triage groups every ticket the owner asked about"
assert_contains "$TRIAGE" "Contradictions are \`spec:create\`'s job" "spec:triage leaves contradictions to spec:create"
assert_contains "$TRIAGE" "a suggestion the owner can take" "spec:triage proposes splits only as a suggestion"
assert_not_contains "$TRIAGE" "| Real unknowns (nobody can write acceptance criteria yet) | Left ungrouped;" "spec:triage never leaves an asked-about unknown out"

echo "ticket evidence lives in the repo"
for f in ticket/execute ticket/complete; do
    assert_contains "$CMD/$f.md" "never a scratch path" "$f keeps RED and GREEN scripts in the repo"
done
assert_contains "$CMD/ticket/execute.md" "review/repro/" "ticket:execute runs a fix ticket's reproduction from review/repro/"

echo "intake procedure pages: the checkpoint stops only attended runs"
n=0
for f in "$PLUGIN"/../docs/workflow/intake-*.md; do
    case "$f" in */intake-phase.md) continue ;; esac
    grep -qF "checkpoint" "$f" || continue
    n=$((n + 1))
    assert_contains "$f" "as a draft in the checklist note and goes on" "$(basename "$f") says a goal run drafts the scope and goes on"
done
if [ "$n" -eq 19 ]; then pass "19 procedure pages name the checkpoint"; else fail "19 procedure pages name the checkpoint (found $n)"; fi

# a blocked layer keeps exit 0 but is reported: the count and reason in Checks, never read as green
assert_contains "$REF/intake/rules.md" "blocked count and its reason" "rules: a blocked layer's count and reason are reported"
assert_contains "$REF/intake/rules.md" "exit 0 with blocked tests is not a green suite" "rules: exit 0 with blocked tests is not green"
assert_contains "$CMD/intake.md" "blocked count" "intake: the phase-boundary suite reads the blocked count"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
