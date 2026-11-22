#!/usr/bin/env bash
#
# Test the intake severity scorer on synthetic gold sets, mappings and trackers:
# per-finding agreement, the scale match for runs without Critical, miss classes,
# weighted kappa and AC2, gates, and pooling over eval directories.
#
# Usage: bash scripts/test-eval-severity.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }
# check <name> <json> <python expression over d>: the expression holds for the parsed JSON
check() {
    if printf '%s' "$2" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if ($3) else 1)" 2>/dev/null; then
        pass "$1"
    else
        fail "$1: $2"
    fi
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEV="$REPO_ROOT/scripts/eval_intake_severity.py"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "severity scorer"

cat >"$WORK/gold.md" <<'MD'
# Gold set: synthetic

- **Version:** 7 (test)

## Findings (8)

| Gold id | Verdict | Severity | Area | Source | What |
|---------|---------|----------|------|--------|------|
| F-001 | valid | Critical | profile | seeded | role change |
| F-002 | valid | High (floor) | records | seeded | other accounts' records |
| F-003 | valid | Medium | invites | seeded | invite expiry |
| F-004 | valid | Medium or Low (contested) | search | seeded | search side channel |
| F-005 | valid | Low | feed | seeded | feed escaping |
| F-006 | valid | Medium | booking | seeded | party size |
| ADDED-1 | valid | Low | errors | run 9 | 500 on bad body |
| MISSED-1 | valid | Medium | export | review | export leak |

## Decoys (0)
MD
cat >"$WORK/map.json" <<'JSON'
{"run": "run 9", "found": {"F-001": "F-011 (e)", "F-002": "F-012 (e)", "F-003": "F-013", "F-004": "F-014 (e)",
 "F-005": "F-015 (e)", "F-006": "F-016 (e)", "ADDED-1": "F-019 (e)", "MISSED-1": "docs/api.md (OP-015, F-099 named in prose) (d)"}, "given": []}
JSON
cat >"$WORK/findings.md" <<'MD'
# Intake Findings

## Findings

### F-011 Any user can change their role
- **Severity:** High (accounts)

### F-012 Another account's records are readable
- **Severity:** Medium (records). Row: Medium, reads another account's ordinary data; no adjustment

### F-013 Invites never expire
- **Severity:** Low (invites)

### F-014 Search matches hidden notes
- **Severity:** Low (search)

### F-015 Feed escaping
- **Severity:** High (feed)

### F-016 Party size unchecked
- **Severity:** Low (booking)

### F-017 An extra
- **Severity:** Medium (misc)

### F-018 Another extra
- **Severity:** Low (misc)

### F-019 Bad body answers 500
- **Severity:** Low (errors)
MD

out=$(python3 "$SEV" "$WORK/gold.md" "$WORK/map.json" "$WORK/findings.md" --no-critical --json)
check "matched findings leave out null, given and the run's own rows" "$out" "d['n'] == 6"
check "a docs-only (d) match has no run severity and is listed apart" "$out" "d['docs_only'] == ['MISSED-1']"
check "exact agreement counts the scale match only in the normalized score" "$out" "d['exact_raw'] == 0.167 and d['exact'] == 0.333"
check "a contested gold row counts exact when the run picks either level" "$out" "any(m['gold_id'] == 'F-004' for m in d['matches'] if m['error'] == 0)"
check "within-one, signed error and over/under use the normalized scale" "$out" "d['within_one'] == 0.833 and d['signed_error'] == -0.167 and d['over'] == 1 and d['under'] == 3"
check "a miss by two levels is counted" "$out" "d['two_plus'] == 1"
check "each miss gets one class" "$out" "{m['gold_id']: m['class'] for m in d['misses']} == {'F-001': 'scale', 'F-002': 'floor', 'F-003': 'unexplained', 'F-005': 'unexplained', 'F-006': 'unexplained'}"
check "the stated-row check counts Severity lines that name a rubric row" "$out" "d['stated_row'] == [1, 6]"
check "the confusion matrix keeps raw levels (gold Critical, run High)" "$out" "d['confusion']['Critical']['High'] == 1 and d['confusion']['Medium']['Low'] == 2"
check "unmatched run findings are counted by level" "$out" "d['extras'] == {'Medium': 1, 'Low': 1}"
check "per-run gates fail on floor, two-level, exact, within-one and signed error" "$out" "{g['gate']: g['result'] for g in d['gates']} == {'floor': 'fail', 'two_plus': 'fail', 'exact': 'fail', 'within_one': 'fail', 'signed_error': 'pass', 'unexplained': 'report-only', 'stated_row': 'report-only'}"
check "the scale is reported with where it came from" "$out" "d['scale'] == {'critical': False, 'source': 'flag'}"

out=$(python3 "$SEV" "$WORK/gold.md" "$WORK/map.json" "$WORK/findings.md" --critical --json)
check "on a scale with Critical, run High against gold Critical is an under-rating" "$out" "d['exact'] == 0.167 and d['under'] == 4 and {m['gold_id']: m['class'] for m in d['misses']}['F-001'] == 'unexplained'"

set +e
python3 "$SEV" "$WORK/gold.md" "$WORK/map.json" "$WORK/findings.md" --no-critical >"$WORK/report.md"
rc_plain=$?
python3 "$SEV" "$WORK/gold.md" "$WORK/map.json" "$WORK/findings.md" --no-critical --gate >/dev/null
rc_gate=$?
set -e
if [ "$rc_plain" -eq 0 ] && [ "$rc_gate" -eq 1 ]; then
    pass "gates are advisory unless --gate, which exits 1 on a failed gate"
else
    fail "gates are advisory unless --gate, which exits 1 on a failed gate (exit $rc_plain, $rc_gate)"
fi
if grep -q '| F-013 | F-003 | Low | Medium | invites | unexplained |' "$WORK/report.md" && grep -q '| Exact, normalized | 33.3%' "$WORK/report.md"; then
    pass "the markdown report lists metrics and each miss by id, level, area and class"
else
    fail "the markdown report lists metrics and each miss by id, level, area and class: $(cat "$WORK/report.md")"
fi

# Weighted agreement, checked by hand: pairs (gold, run) = (High, High), (Medium, Medium), (Medium, Low), (Low, Low)
cat >"$WORK/gold-k.md" <<'MD'
# Gold

## Findings (4)

| Gold id | Verdict | Severity | Area | Source | What |
|---------|---------|----------|------|--------|------|
| F-001 | valid | High | a | seeded | x |
| F-002 | valid | Medium | a | seeded | x |
| F-003 | valid | Medium | a | seeded | x |
| F-004 | valid | Low | a | seeded | x |
MD
printf '{"run": "r", "found": {"F-001": "F-001", "F-002": "F-002", "F-003": "F-003", "F-004": "F-004"}}\n' >"$WORK/map-k.json"
printf '## Findings\n\n### F-001 a\n- **Severity:** High (a)\n\n### F-002 b\n- **Severity:** Medium (a)\n\n### F-003 c\n- **Severity:** Low (a)\n\n### F-004 d\n- **Severity:** Low (a)\n' >"$WORK/findings-k.md"
out=$(python3 "$SEV" "$WORK/gold-k.md" "$WORK/map-k.json" "$WORK/findings-k.md" --critical --json)
check "linear- and quadratic-weighted kappa and Gwet's AC2 match hand-computed values" "$out" "d['kappa_linear'] == 0.714 and d['kappa_quadratic'] == 0.8 and d['ac2_linear'] == 0.83"
check "recall per gold level" "$out" "d['recall'] == {'High': 1.0, 'Medium': 0.5, 'Low': 1.0}"

set +e
printf '{"run": "r", "found": {"F-001": "F-099"}}\n' >"$WORK/map-bad.json"
python3 "$SEV" "$WORK/gold-k.md" "$WORK/map-bad.json" "$WORK/findings-k.md" --critical >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 2 ]; then pass "a mapped run id the tracker lacks is bad input"; else fail "a mapped run id the tracker lacks is bad input (exit $rc)"; fi

# Pooling: two eval directories, the scale taken from eval.json or from the plugin commit
PLUG="$WORK/plugin-repo"
git init -q "$PLUG"
mkdir -p "$PLUG/plugin/references/intake"
printf '| Severity | Use it for |\n| High | x |\n' >"$PLUG/plugin/references/intake/findings.md"
git -C "$PLUG" add -A
git -C "$PLUG" -c user.name=t -c user.email=t@t commit -qm old
OLD=$(git -C "$PLUG" rev-parse --short HEAD)
printf '| Severity | Use it for |\n| Critical | x |\n| High | x |\n' >"$PLUG/plugin/references/intake/findings.md"
git -C "$PLUG" -c user.name=t -c user.email=t@t commit -qam new
NEW=$(git -C "$PLUG" rev-parse --short HEAD)

make_eval() { # make_eval <dir> <run entry extra JSON> <findings file>
    local dir="$1" proj="$1/proj"
    mkdir -p "$dir/r1" "$proj/docs"
    cp "$WORK/gold-k.md" "$dir/gold.md"
    cp "$WORK/map-k.json" "$dir/r1/map.json"
    cp "$3" "$proj/docs/intake-findings.md"
    git init -q -b intake/r1 "$proj"
    git -C "$proj" add -A
    git -C "$proj" -c user.name=t -c user.email=t@t commit -qm run
    git -C "$proj" bundle create -q "$dir/r1/repo.bundle" intake/r1
    local sha
    sha=$(git -C "$proj" rev-parse --short HEAD)
    printf '{"eval": "intake", "gold": "gold.md", "runs": [{"run": "r1", "bundle": "r1/repo.bundle", "branch": "intake/r1", "scored_at": "%s", "accuracy": "r1/map.json", %s}, {"run": "unmapped", "bundle": "x", "branch": "y", "plugin": "%s"}]}\n' "$sha" "$2" "$OLD" >"$dir/eval.json"
    rm -rf "$proj"
}
printf '## Findings\n\n### F-001 a\n- **Severity:** High (a)\n\n### F-002 b\n- **Severity:** Medium (a)\n\n### F-003 c\n- **Severity:** Medium (a)\n\n### F-004 d\n- **Severity:** Low (a)\n' >"$WORK/findings-ok.md"
make_eval "$WORK/evalA" "\"plugin\": \"$OLD\"" "$WORK/findings-k.md"
make_eval "$WORK/evalB" "\"plugin\": \"$NEW-variant\"" "$WORK/findings-ok.md"
out=$(python3 "$SEV" --pool "$WORK/evalA" "$WORK/evalB" --plugin-repo "$PLUG" --json)
check "--pool scores every mapped run of every eval directory and skips unmapped runs" "$out" "[r['run'] for r in d['runs']] == ['r1', 'r1'] and d['pooled']['n'] == 8"
check "the scale comes from the plugin commit when eval.json has no flag" "$out" "[r['scale'] for r in d['runs']] == [{'critical': False, 'source': 'plugin $OLD'}, {'critical': True, 'source': 'plugin $NEW-variant'}]"
check "pooled metrics and calibration gates" "$out" "d['pooled']['exact'] == 0.875 and {g['gate']: g['result'] for g in d['pooled']['gates']}['exact'] == 'pass' and d['pooled']['signed_error'] == -0.125"

make_eval "$WORK/evalC" '"critical": true, "plugin": "deadbee"' "$WORK/findings-ok.md"
out=$(python3 "$SEV" --pool "$WORK/evalC" --plugin-repo "$PLUG" --json)
check "a critical flag in eval.json wins over the plugin commit" "$out" "d['runs'][0]['scale'] == {'critical': True, 'source': 'eval.json'}"
make_eval "$WORK/evalD" '"plugin": "deadbee"' "$WORK/findings-ok.md"
out=$(python3 "$SEV" --pool "$WORK/evalD" --plugin-repo "$PLUG" --json)
check "an unknown plugin commit is assumed to predate Critical, and says so" "$out" "d['runs'][0]['scale'] == {'critical': False, 'source': 'assumed (plugin deadbee unknown)'}"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
