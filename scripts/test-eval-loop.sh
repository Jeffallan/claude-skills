#!/usr/bin/env bash
#
# Test the discovery and common-ground scorers on synthetic runs: a topic folder
# scored against a gold routing, decision and ticket set, and a common-ground
# report scored against gold conflicts.
#
# Usage: bash scripts/test-eval-loop.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }
# has <json> <check id> <1|0>: the check passed (1) or failed (0)
has() { printf '%s' "$1" | python3 -c "import json,sys; d=json.load(sys.stdin); c={x['id']:x['pass'] for x in d['checks']}; sys.exit(0 if c.get(sys.argv[1]) is (sys.argv[2]=='1') else 1)" "$2" "$3"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DISC="$REPO_ROOT/scripts/eval_discovery_run.py"
CG="$REPO_ROOT/scripts/eval_common_ground_run.py"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "discovery scorer"

R="$WORK/disc"
T="$R/docs/specs/todo/discovery/billing"
mkdir -p "$T"
cat >"$T/discovery.md" <<'MD'
# Billing

**Topic:** billing

## Features

| # | Item | Route | Feature Forge file |
|---|------|-------|--------------------|
| F1 | CSV export of invoices | Clear | - |
| F2 | Plan upgrades | Feature Forge | plan-upgrades.md |
| F3 | Tax rules per country | Research | - |

## Blocking decisions

| # | Decision | Options | Recommendation | Blocks |
|---|----------|---------|----------------|--------|
| D1 | Proration on upgrade | A) daily, B) none | A | P2 |

## Proposed tickets

| # | Title | Item | Depends on | Blocked by decisions |
|---|-------|------|------------|----------------------|
| P1 | Export invoices as CSV | F1 | - | - |
| P2 | Upgrade a plan mid-cycle | F2 | - | D1 |

Created as ENG-1: P1
MD
cat >"$T/synthesis.md" <<'MD'
# Billing: synthesis

## Blocking decisions

| # | Decision | Options | Recommendation | Blocks |
|---|----------|---------|----------------|--------|
| D2 | VAT registration threshold | A) per country, B) EU-wide | A | P4 |

## Proposed tickets

| # | Title | Item | Depends on | Blocked by decisions |
|---|-------|------|------------|----------------------|
| P4 | Tax rate table per country | F3 | - | D2 |

Created as ENG-2: P4
MD
cat >"$WORK/disc-gold.json" <<'JSON'
{"topic": "billing",
 "routes": {"csv export": "Clear", "plan upgrade": "Feature Forge", "tax rules": "Research"},
 "decisions": ["prorat", "VAT"],
 "tickets": ["export.*csv", "tax rate"]}
JSON
set +e
out=$(python3 "$DISC" --repo "$R" --topic billing --gold "$WORK/disc-gold.json" 2>&1)
set -e
for c in routing blocking-decisions approved-tickets; do
    if has "$out" "$c" 1; then pass "discovery $c passes on a matching run"; else fail "discovery $c passes on a matching run: $out"; fi
done
sed -i 's/| F3 | Tax rules per country | Research |/| F3 | Tax rules per country | Clear |/; s/^Created as ENG-1: P1$//' "$T/discovery.md"
sed -i 's/| D2 | VAT registration threshold/| D2 | Invoice numbering/' "$T/synthesis.md"
set +e
out=$(python3 "$DISC" --repo "$R" --topic billing --gold "$WORK/disc-gold.json" 2>&1)
set -e
for c in routing blocking-decisions approved-tickets; do
    if has "$out" "$c" 0; then pass "discovery $c fails on a wrong run"; else fail "discovery $c fails on a wrong run: $out"; fi
done

echo "common-ground scorer"

cat >"$WORK/cg-report.md" <<'MD'
## Assumptions check

| ID | Verdict | Spec | Assumption | Source | Fix |
|----|---------|------|------------|--------|-----|
| billing-v2:A1 | conflicts | billing-v2 | The export worker is wired | components: Exporter (built, not wired) | spec:create billing-v2 |
| sso:A2 | conflicts | sso | F-001 is fixed | findings: F-001 (open) | spec:create sso |
| sso:A1 | holds | sso | The API is wired | components: API | - |
MD
cat >"$WORK/cg-gold.json" <<'JSON'
{"conflicts": [{"spec": "billing-v2", "match": "export worker"}, {"spec": "sso", "match": "F-001"}]}
JSON
set +e
out=$(python3 "$CG" --report "$WORK/cg-report.md" --gold "$WORK/cg-gold.json" 2>&1)
set -e
for c in conflict-recall no-false-flags right-spec; do
    if has "$out" "$c" 1; then pass "common-ground $c passes on a matching report"; else fail "common-ground $c passes on a matching report: $out"; fi
done
cat >"$WORK/cg-bad.md" <<'MD'
| ID | Verdict | Spec | Assumption | Source | Fix |
|----|---------|------|------------|--------|-----|
| sso:A1 | conflicts | sso | The export worker is wired | components: Exporter | spec:create sso |
| sso:A3 | conflicts | sso | The API is wired | components: API | spec:create sso |
MD
set +e
out=$(python3 "$CG" --report "$WORK/cg-bad.md" --gold "$WORK/cg-gold.json" 2>&1)
set -e
for c in conflict-recall no-false-flags right-spec; do
    if has "$out" "$c" 0; then pass "common-ground $c fails on a wrong report"; else fail "common-ground $c fails on a wrong report: $out"; fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
