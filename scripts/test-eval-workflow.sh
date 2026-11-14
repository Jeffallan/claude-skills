#!/usr/bin/env bash
#
# Test scripts/eval_workflow_run.py on two synthetic spec runs: a good one that
# keeps every workflow guarantee, and a bad one that breaks four of them
# (a Done ticket without RED, a second commit for one ticket, an amend after the
# run started, and a goal session that asked a question and ran git reset).
#
# Usage: bash scripts/test-eval-workflow.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVAL="$REPO_ROOT/scripts/eval_workflow_run.py"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# make_run <dir>: a spec run with two Done tickets, T1 and T2, and full evidence
make_run() {
    local d=$1
    git init -q -b main "$d"
    git -C "$d" config user.email t@example.com
    git -C "$d" config user.name t
    mkdir -p "$d/docs/specs/todo/demo"
    printf '# Demo\n\n**Spec:** demo\n\n## Readiness\n\n| Ticket | Readiness | Evidence or question |\n|---|---|---|\n| T1 | Ready | - |\n| T2 | Ready | - |\n| T3 | Already done | abc123 |\n' >"$d/docs/specs/todo/demo/overview.md"
    printf '# Plan\n\n## Completion Status\n\n| Ticket | Status | Completed Date | Notes |\n|---|---|---|---|\n| T1 | Done | 2026-11-10 | - |\n| T2 | Done | 2026-11-10 | - |\n' >"$d/docs/specs/todo/demo/implementation-plan.md"
    git -C "$d" add -A
    git -C "$d" commit -qm "docs(demo): plan the spec"
    git -C "$d" checkout -qb spec/demo
    local ev="$d/.git/ticket-guard/evidence"
    mkdir -p "$ev"
    sleep 1
    local t
    for t in T1 T2; do
        local now
        now=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
        printf '{"at":"%s","event":"marker_start","mode":"goal"}\n{"at":"%s","event":"run","phase":"red","exit_code":1,"valid":true}\n{"at":"%s","event":"run","phase":"green","exit_code":0,"valid":true}\n{"at":"%s","event":"marker_clear"}\n' "$now" "$now" "$now" "$now" >"$ev/$t.jsonl"
        echo "$t" >"$d/$t.txt"
        git -C "$d" add -A
        git -C "$d" commit -qm "feat: $t" -m "Ticket: $t"
    done
}

echo "workflow run eval"

GOOD="$WORK/good"
make_run "$GOOD"
GOLD="$WORK/gold.json"
printf '{"demo": {"T1": "Done", "T2": "Done", "T3": "Already done"}}\n' >"$GOLD"
T0=$(date -u -d '-1 min' +%Y-%m-%dT%H:%M:%SZ)
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '{"type":"user","timestamp":"%s","message":{"role":"user","content":"/goal Every condition in <done_when> holds"}}\n{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"git log --oneline"}}]}}\n{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"text","text":"done_when evidence: git log shows 2 commits"}]}}\n' "$T0" "$T1" "$T1" >"$WORK/good.jsonl"
# An attended command amends its own commit after the goal session ended: allowed
sleep 2
git -C "$GOOD" commit -q --amend -m "feat: T2" -m "Ticket: T2"

set +e
out=$(python3 "$EVAL" --repo "$GOOD" --spec demo --gold "$GOLD" --transcript "$WORK/good.jsonl" 2>&1)
rc=$?
set -e
if [ "$rc" -eq 0 ]; then pass "the good run passes (exit 0)"; else fail "the good run passes (exit $rc): $out"; fi
if printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d["score"]==d["total"] and d["total"]>=8 else 1)'; then pass "the good run scores every check"; else fail "the good run scores every check: $out"; fi

# An eval directory: eval.json names the gold file and the run's repo, spec and transcripts
ED="$WORK/evaldir"
mkdir -p "$ED"
cp "$GOLD" "$ED/gold.json"
cp "$WORK/good.jsonl" "$ED/good.jsonl"
printf '{"gold": "gold.json", "runs": [{"run": "good", "repo": "%s", "spec": "demo", "plugin": "abc1234", "transcripts": ["good.jsonl"]}]}\n' "$GOOD" >"$ED/eval.json"
set +e
out=$(python3 "$EVAL" --eval "$ED" --run good 2>&1)
rc=$?
set -e
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q '"version": "abc1234"' && printf '%s' "$out" | grep -q '"gold-outcomes"'; then
    pass "--eval and --run read the repo, spec, gold and transcripts from eval.json"
else
    fail "--eval and --run read every input from eval.json (exit $rc): $out"
fi

BAD="$WORK/bad"
make_run "$BAD"
# T2 loses its RED, T1 gets a second commit, the last commit is amended after the run started
grep -v '"phase":"red"' "$BAD/.git/ticket-guard/evidence/T2.jsonl" >"$WORK/t2" && mv "$WORK/t2" "$BAD/.git/ticket-guard/evidence/T2.jsonl"
echo more >>"$BAD/T1.txt"
git -C "$BAD" commit -qam "fix: T1 again" -m "Ticket: T1"
git -C "$BAD" commit -q --amend -m "fix: T1 again, amended" -m "Ticket: T1"
B0=$(date -u -d '-1 min' +%Y-%m-%dT%H:%M:%SZ)
B1=$(date -u -d '+1 min' +%Y-%m-%dT%H:%M:%SZ)
printf '{"type":"user","timestamp":"%s","message":{"role":"user","content":"/goal Every condition in <done_when> holds"}}\n{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"tool_use","name":"AskUserQuestion","input":{}}]}}\n{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"echo prep && git reset --soft HEAD~1"}}]}}\n{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"text","text":"All done."}]}}\n' "$B0" "$B0" "$B1" "$B1" >"$WORK/bad.jsonl"

set +e
out=$(python3 "$EVAL" --repo "$BAD" --spec demo --gold "$GOLD" --transcript "$WORK/bad.jsonl" 2>&1)
rc=$?
set -e
if [ "$rc" -eq 1 ]; then pass "the bad run fails (exit 1)"; else fail "the bad run fails (exit $rc)"; fi
if printf '%s' "$out" | grep -q 'git reset --soft'; then pass "the denied-git detail shows the matching command"; else fail "the denied-git detail shows the matching command"; fi
for check in one-commit-per-ticket red-before-green no-history-rewrite no-question-in-goal no-denied-git final-message-evidence; do
    if printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); c=[x for x in d['checks'] if x['id']=='$check']; sys.exit(0 if c and not c[0]['pass'] else 1)"; then
        pass "the bad run fails $check"
    else
        fail "the bad run fails $check"
    fi
done
if printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); c=[x for x in d['checks'] if x['id']=='launch-delivered']; sys.exit(0 if c and c[0]['pass'] else 1)"; then
    pass "the bad run still passes launch-delivered"
else
    fail "the bad run still passes launch-delivered"
fi

# A pruned reflog must not pass the rewrite check silently
SNAP="$WORK/bad-reflog.txt"
git -C "$BAD" reflog --date=iso-strict --format='%gd%x00%gs' >"$SNAP"
git -C "$BAD" reflog expire --expire=now --all
set +e
out=$(python3 "$EVAL" --repo "$BAD" --spec demo 2>&1)
set -e
if printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); c=[x for x in d['checks'] if x['id']=='no-history-rewrite'][0]; sys.exit(0 if not c['pass'] and 'reflog' in c['detail'] else 1)"; then
    pass "a pruned reflog fails no-history-rewrite and says why"
else
    fail "a pruned reflog fails no-history-rewrite and says why"
fi
set +e
out=$(python3 "$EVAL" --repo "$BAD" --spec demo --reflog "$SNAP" 2>&1)
set -e
if printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); c=[x for x in d['checks'] if x['id']=='no-history-rewrite'][0]; sys.exit(0 if not c['pass'] and 'amend' in c['detail'] else 1)"; then
    pass "a saved reflog snapshot still finds the amend"
else
    fail "a saved reflog snapshot still finds the amend"
fi

# final-message-evidence: an evidence message counts even when later turns follow it,
# unless a git commit comes after the last evidence message
for case in trailing:1 commit-after:0 commit-before:1; do
    name=${case%%:*}
    want=${case##*:}
    G='{"type":"user","timestamp":"2026-11-10T10:00:00Z","message":{"role":"user","content":"/goal Every condition in <done_when> holds"}}'
    E='{"type":"assistant","timestamp":"2026-11-10T10:01:00Z","message":{"content":[{"type":"text","text":"done_when evidence: git log shows 2 commits"}]}}'
    C='{"type":"assistant","timestamp":"2026-11-10T10:02:00Z","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"git add -A && git commit -m more"}}]}}'
    L='{"type":"assistant","timestamp":"2026-11-10T10:03:00Z","message":{"content":[{"type":"text","text":"Stop hook fired again; nothing left to do."}]}}'
    case $name in
    trailing) printf '%s\n' "$G" "$E" "$L" >"$WORK/fme-$name.jsonl" ;;
    commit-after) printf '%s\n' "$G" "$E" "$C" "$L" >"$WORK/fme-$name.jsonl" ;;
    commit-before) printf '%s\n' "$G" "$C" "$E" "$L" >"$WORK/fme-$name.jsonl" ;;
    esac
    if PYTHONPATH="$REPO_ROOT/scripts" python3 -c "
from pathlib import Path
from eval_workflow_run import transcript_checks
c = [x for x in transcript_checks([Path('$WORK/fme-$name.jsonl')])[0] if x['id'] == 'final-message-evidence'][0]
raise SystemExit(0 if c['pass'] == bool($want) else 1)"; then
        pass "final-message-evidence on $name gives pass=$want"
    else
        fail "final-message-evidence on $name gives pass=$want"
    fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
