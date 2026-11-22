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
# An escaped pipe inside a cell stays in that cell, unescaped, and does not shift the columns after it
got=$(cd "$REPO_ROOT/scripts" && python3 - <<'PY'
from eval_common_ground_run import tables
from eval_workflow_run import cells
report = """| Doc | Claim | Verdict | Evidence |
|-----|-------|---------|----------|
| docs/configuration.md | "Payment or mail credentials \\| None exist in the repo" | stale | `src/config.ts` |
"""
row = tables(report, {"doc", "claim"})[0][0]
ok = row["claim"] == '"Payment or mail credentials | None exist in the repo"' and row["verdict"] == "stale"
split = cells(r"| a \| b | c |")
print("ok" if ok and split == ["a | b", "c"] else f"{row} {split}")
PY
)
if [ "$got" = ok ]; then pass "table rows split on unescaped pipes only"; else fail "table rows split on unescaped pipes only: $got"; fi

# discovery:approve records "Created as <ID>" next to the proposed ticket: in its table row or under its ### heading
R2="$WORK/disc2"
T2="$R2/docs/specs/todo/discovery/billing"
mkdir -p "$T2"
cat >"$T2/discovery.md" <<'MD'
# Billing

## Features

| # | Item | Route | Feature Forge file |
|---|------|-------|--------------------|
| F1 | CSV export of invoices | Clear | - |
| F3 | Tax rules per country | Research | - |

## Proposed tickets

| # | Title | Item | Depends on | Blocked by decisions |
|---|-------|------|------------|----------------------|
| P1 | Export invoices as CSV (Created as ENG-1) | F1 | - | - |
| P4 | Tax rate table per country | F3 | - | - |
| P5 | Refund export | F1 | - | - |

### P4: Tax rate table per country

Store a rate per country.

Created as ENG-2.

### P5: Refund export

Not created yet.
MD
cat >"$WORK/disc2-gold.json" <<'JSON'
{"topic": "billing", "routes": {"csv export": "Clear"}, "decisions": [], "tickets": ["export.*csv", "tax rate"]}
JSON
set +e
out=$(python3 "$DISC" --repo "$R2" --topic billing --gold "$WORK/disc2-gold.json" 2>&1)
set -e
if has "$out" approved-tickets 1; then pass "discovery reads Created as in a ticket's row or under its heading"; else fail "discovery reads Created as in a ticket's row or under its heading: $out"; fi
printf '{"topic": "billing", "routes": {}, "decisions": [], "tickets": ["refund export"]}\n' >"$WORK/disc3-gold.json"
set +e
out=$(python3 "$DISC" --repo "$R2" --topic billing --gold "$WORK/disc3-gold.json" 2>&1)
set -e
if has "$out" approved-tickets 0; then pass "discovery: a ticket with no Created as is not created"; else fail "discovery: a ticket with no Created as is not created: $out"; fi

# common-ground prints the table again after an owner answer: the last one is the report. Gold rows that hold must
# be reported as holding.
cat >"$WORK/cg-twice.md" <<'MD'
| ID | Verdict | Spec | Assumption | Source | Fix |
|----|---------|------|------------|--------|-----|
| sso:A3 | conflicts | sso | The API is wired | components: API | spec:create sso |

Owner answered; checked again:

| ID | Verdict | Spec | Assumption | Source | Fix |
|----|---------|------|------------|--------|-----|
| billing-v2:A1 | conflicts | billing-v2 | The export worker is wired | components: Exporter (built, not wired) | spec:create billing-v2 |
| sso:A2 | **conflicts** | sso | F-001 is fixed | findings: F-001 (open) | spec:create sso |
| sso:A3 | holds | sso | The API is wired | components: API | - |
MD
cat >"$WORK/cg-holds-gold.json" <<'JSON'
{"conflicts": [{"spec": "billing-v2", "match": "export worker"}, {"spec": "sso", "match": "F-001"}],
 "holds": [{"spec": "sso", "match": "API is wired"}]}
JSON
set +e
out=$(python3 "$CG" --report "$WORK/cg-twice.md" --gold "$WORK/cg-holds-gold.json" 2>&1)
set -e
for c in conflict-recall no-false-flags right-spec holds-recognized; do
    if has "$out" "$c" 1; then pass "common-ground $c reads the last table"; else fail "common-ground $c reads the last table: $out"; fi
done
sed -i 's/| sso:A3 | holds |/| sso:A3 | unknown |/' "$WORK/cg-twice.md"
set +e
out=$(python3 "$CG" --report "$WORK/cg-twice.md" --gold "$WORK/cg-holds-gold.json" 2>&1)
set -e
if has "$out" holds-recognized 0; then pass "common-ground: a gold hold reported unknown fails holds-recognized"; else fail "common-ground: a gold hold reported unknown fails holds-recognized: $out"; fi

# gold_edit <src> <dst> <python statement on d>: a copy of a gold file with one change
gold_edit() {
    python3 - "$1" "$2" "$3" <<'PY'
import json, sys
src, dst, stmt = sys.argv[1:]
d = json.load(open(src)); exec(stmt); json.dump(d, open(dst, "w"))
PY
}

echo "spec:current and spec:diff scorer"

SCD="$REPO_ROOT/scripts/eval_spec_current_diff_run.py"
R3="$WORK/current"
git init -q -b main "$R3"
git -C "$R3" config user.email t@example.com
git -C "$R3" config user.name t
mkdir -p "$R3/docs"
desc() { # desc <sha> <history row>: the system description, last updated at <sha>
    printf -- '---\nverified: %s\n---\n# System Description\n\n**Last updated:** 2026-11-20 at %s\n\n## 2. Components\n\nAPI, Exporter.\n\n## Change history\n\n| Spec | Folded in | Sections changed |\n|------|-----------|------------------|\n| baseline | 2026-11-01 | all |\n%s\n' "$1" "$1" "$2" >"$R3/docs/system-description.md"
}
desc 0000000 ""
printf '{}\n' >"$R3/docs/current-state.json"
git -C "$R3" add -A && git -C "$R3" commit -qm base
START3=$(git -C "$R3" rev-parse HEAD)
desc abc1234 "| billing-v2 | 2026-11-21 | 2 |"
git -C "$R3" add -A && git -C "$R3" commit -qm "docs(system): fold billing-v2 into the system description" -m "Intake: intake:create-system-description"
cat >"$R3/docs/current-state.json" <<'JSON'
{"schema": 1, "built_at": {"head": "abc1234def", "system_description": "abc1234", "date": "2026-11-20"},
 "components": [
   {"name": "API", "does": "serves requests", "status": "wired", "source": "docs/system-description.md#2"},
   {"name": "Exporter", "does": "exports invoices", "status": "wired", "source": "docs/system-description.md#2"},
   {"name": "Plans", "does": "the plan table", "status": "planned", "source": "docs/system-description.md#2"}],
 "findings": [{"id": "F-001", "finding": "Any user sees any invoice", "severity": "High", "area": "access", "status": "open", "source": "docs/intake-findings.md"}],
 "drift": [{"doc": "docs/architecture/api-reference.md", "verified": "abc1234", "reasons": ["src/api.ts changed"], "source": "guard docs-drift"}]}
JSON
git -C "$R3" add -A && git -C "$R3" commit -qm "docs(system): compile current state"
cat >"$WORK/diff-report.md" <<'MD'
## Spec diff: billing-v2, sso (in this order)

> A plan, not the current state. Built at abc1234 from the specs' overviews.

### billing-v2

| Adds, changes or removes | Component or flow | Source |
|--------------------------|-------------------|--------|
| changes | Exporter: called by the API | overview.md |

### sso

| Adds, changes or removes | Component or flow | Source |
|--------------------------|-------------------|--------|
| adds | Single sign-on | overview.md |

### Overlaps

| Specs | Component or assumption | What collides |
|-------|-------------------------|---------------|
| billing-v2, sso | API | both change the router |

### Assumptions

| ID | Spec | Kind | Assumption | Quoted from | Checked against |
|----|------|------|------------|-------------|-----------------|
| billing-v2:A1 | billing-v2 | component | The export worker is built | overview.md, "Approach" | components: Exporter |
MD
printf 'abc1234\n' >"$WORK/diff-before.txt"
cp "$WORK/diff-before.txt" "$WORK/diff-after.txt"
cat >"$WORK/current-gold.json" <<JSON
{"fixture_start": "$START3",
 "spec_current": {
   "commits": {"description": {"subject": "^docs\\\\(system\\\\): fold", "trailer": "Intake: intake:create-system-description", "files_only": ["docs/system-description.md"]},
               "state": {"subject": "compile current state", "files_only": ["docs/current-state.json"]}},
   "description": {"change_history_row": {"spec": "billing-v2"}, "last_updated_not": "0000000", "verified_not": "0000000"},
   "current_state": {"built_at_system_description_not": "0000000",
     "components": {"count": [2, 3], "required": [{"match": "export", "status": ["wired"]}], "planned_allowed": "plan",
                    "others": "wired", "forbidden": [{"match": "^API", "does_not": "invoice"}]},
     "findings": {"ids": ["F-001"]},
     "drift": {"docs": ["docs/architecture/api-reference.md"], "absent": ["docs/README.md"]}}},
 "spec_diff": {"specs": ["billing-v2", "sso"], "banner": "A plan, not the current state", "writes_nothing": true,
   "assumptions": [{"spec": "billing-v2", "match": "export worker", "kind": "component", "checked_against": "Exporter"}],
   "overlaps": [{"specs": ["billing-v2", "sso"], "match": "router"}],
   "changes": {"billing-v2": ["Exporter"]}, "not_changed": {"sso": ["Exporter"]}}}
JSON
CD_CHECKS="current-commits description-folded state-fresh components findings drift diff-coverage diff-assumptions diff-overlaps diff-changes diff-read-only"
cd_score() { # cd_score <gold> [after file]
    python3 "$SCD" --repo "$R3" --diff-report "$WORK/diff-report.md" --diff-before "$WORK/diff-before.txt" \
        --diff-after "${2:-$WORK/diff-after.txt}" --gold "$1" 2>&1
}
set +e
out=$(cd_score "$WORK/current-gold.json")
rc=$?
set -e
for c in $CD_CHECKS; do
    if has "$out" "$c" 1; then pass "spec-current-diff $c passes on a matching run"; else fail "spec-current-diff $c passes on a matching run: $out"; fi
done
[ "$rc" -eq 0 ] && pass "spec-current-diff exits 0 when every check passes" || fail "spec-current-diff exits 0 (got $rc)"
printf 'abc1234\n M docs/system-description.md\n' >"$WORK/diff-after-dirty.txt"
for case in \
    'current-commits|d["spec_current"]["commits"]["description"]["files_only"] = ["docs/other.md"]' \
    'description-folded|d["spec_current"]["description"]["last_updated_not"] = "abc1234"' \
    'state-fresh|d["spec_current"]["current_state"]["built_at_system_description_not"] = "abc1234"' \
    'components|d["spec_current"]["current_state"]["components"]["required"][0]["status"] = ["planned"]' \
    'components|d["spec_current"]["current_state"]["components"]["forbidden"][0]["does_not"] = "requests"' \
    'findings|d["spec_current"]["current_state"]["findings"]["ids"] = ["F-002"]' \
    'drift|d["spec_current"]["current_state"]["drift"]["absent"] = ["docs/architecture/api-reference.md"]' \
    'diff-coverage|d["spec_diff"]["specs"].append("ledger")' \
    'diff-assumptions|d["spec_diff"]["assumptions"][0]["kind"] = "interface"' \
    'diff-overlaps|d["spec_diff"]["overlaps"][0]["match"] = "ledger"' \
    'diff-changes|d["spec_diff"]["not_changed"]["billing-v2"] = ["Exporter"]'; do
    c=${case%%|*}
    gold_edit "$WORK/current-gold.json" "$WORK/current-gold-bad.json" "${case#*|}"
    set +e
    out=$(cd_score "$WORK/current-gold-bad.json")
    rc=$?
    set -e
    if has "$out" "$c" 0 && [ "$rc" -eq 1 ]; then pass "spec-current-diff $c fails: ${case#*|}"; else fail "spec-current-diff $c fails: ${case#*|}: $out"; fi
done
set +e
out=$(cd_score "$WORK/current-gold.json" "$WORK/diff-after-dirty.txt")
set -e
if has "$out" diff-read-only 0; then pass "spec-current-diff diff-read-only fails when spec:diff changed the tree"; else fail "spec-current-diff diff-read-only fails when spec:diff changed the tree: $out"; fi
set +e
out=$(python3 "$SCD" --diff-report "$WORK/diff-report.md" --gold "$WORK/current-gold.json" 2>&1)
set -e
if has "$out" diff-assumptions 1 && ! printf '%s' "$out" | grep -q '"current-commits"\|"diff-read-only"'; then
    pass "spec-current-diff scores only the inputs it is given"
else
    fail "spec-current-diff scores only the inputs it is given: $out"
fi

echo "spec:complete docs scorer"

SCO="$REPO_ROOT/scripts/eval_spec_complete_docs_run.py"
sd_file() { # sd_file <path> <section 2> <section 3> <history row>
    printf '# System Description\n\n**Last updated:** 2026-11-20 at abc1234\n\n## 1. Purpose and scope\n\nInvoices.\n\n## 2. Components\n\n%s\n\n## 3. Data flow\n\n%s\n\n## Change history\n\n| Spec | Folded in | Sections changed |\n|------|-----------|------------------|\n| baseline | 2026-11-01 | all |\n%s\n' "$2" "$3" "$4" >"$1"
}
sd_file "$WORK/sd-before.md" "API (wired). The Exporter is not wired." "Requests reach the API." ""
sd_file "$WORK/sd-after.md" "API (wired). Exporter (wired), called by the API." "Requests reach the API." "| billing-v2 | 2026-11-21 | 2. Components |"
cat >"$WORK/verify.md" <<'MD'
| Doc | Claim | Verdict | Evidence |
|-----|-------|---------|----------|
| docs/architecture/api-reference.md, Exports | "Exports run nightly from cron" | fixed | `src/export.ts::schedule` |
| docs/README.md | "The API serves invoices" | holds | `src/api.ts::invoices` |
| docs/specs/todo/billing-v2/overview.md | "The old plan" | stale | the diff |
MD
cat >"$WORK/complete-gold.json" <<'JSON'
{"spec": "billing-v2",
 "system_description": {
   "sections": [
     {"section": "2", "heading": "Components", "must_change": true, "stale": ["Exporter is not wired"], "expect": ["Exporter \\(wired\\)"]},
     {"section": "3", "heading": "Data flow", "must_change": false},
     {"section": "1", "heading": "Purpose", "must_change": "optional", "stale": ["Invoices\\."], "expect": ["exports"]}],
   "change_history_row": {"spec": "billing-v2", "sections_include": ["2"]}},
 "docs_verify": {
   "stale_claims": [{"id": "S1", "doc": "docs/architecture/api-reference.md", "match": "nightly", "required": true},
                    {"id": "S2", "doc": "docs/README.md", "match": "manual export", "required": false}],
   "not_stale": [{"id": "N1", "doc": "docs/README.md", "match": "serves invoices", "why": "still true"}],
   "excluded_docs": ["docs/specs/"]}}
JSON
CO_CHECKS="sd-changed sd-unchanged change-history verify-recall verify-false-flags"
co_score() { python3 "$SCO" --before "$WORK/sd-before.md" --after "$1" --verify "$2" --gold "$WORK/complete-gold.json" 2>&1; }
set +e
out=$(co_score "$WORK/sd-after.md" "$WORK/verify.md")
rc=$?
set -e
for c in $CO_CHECKS; do
    if has "$out" "$c" 1; then pass "spec-complete-docs $c passes on a matching run"; else fail "spec-complete-docs $c passes on a matching run: $out"; fi
done
[ "$rc" -eq 0 ] && pass "spec-complete-docs exits 0 when every check passes" || fail "spec-complete-docs exits 0 (got $rc)"
if printf '%s' "$out" | grep -q 'optional S2 not flagged' && printf '%s' "$out" | grep -q 'optional section 1 unchanged'; then
    pass "spec-complete-docs reports optional sections and claims without failing on them"
else
    fail "spec-complete-docs reports optional sections and claims without failing on them: $out"
fi
# Section 2 kept its stale sentence, section 3 changed, the row names section 3 only, the stale claim held, a true one flagged
sd_file "$WORK/sd-bad.md" "API (wired). The Exporter is not wired." "Requests reach the API, then the Exporter." "| billing-v2 | 2026-11-21 | 3 |"
sed 's/| fixed |/| holds |/; s/| holds | `src\/api/| stale | `src\/api/' "$WORK/verify.md" >"$WORK/verify-bad.md"
set +e
out=$(co_score "$WORK/sd-bad.md" "$WORK/verify-bad.md")
rc=$?
set -e
for c in $CO_CHECKS; do
    if has "$out" "$c" 0; then pass "spec-complete-docs $c fails on a wrong run"; else fail "spec-complete-docs $c fails on a wrong run: $out"; fi
done
[ "$rc" -eq 1 ] && pass "spec-complete-docs exits 1 when a check fails" || fail "spec-complete-docs exits 1 (got $rc)"
# docs:verify found nothing: an empty table and its line, so a required stale claim is missed
printf '| Doc | Claim | Verdict | Evidence |\n|-----|-------|---------|----------|\n\nNo doc names what this diff changed.\n' >"$WORK/verify-empty.md"
set +e
out=$(co_score "$WORK/sd-after.md" "$WORK/verify-empty.md")
set -e
if has "$out" verify-recall 0 && has "$out" verify-false-flags 1; then
    pass "spec-complete-docs: an empty docs:verify table misses the required claims and flags nothing"
else
    fail "spec-complete-docs: an empty docs:verify table misses the required claims and flags nothing: $out"
fi

echo "coverage matrix"

# Every command the workflow manifest ships has a row in evals/README.md's coverage matrix
missing=$(python3 - "$REPO_ROOT/plugin/commands/workflow-manifest.yaml" "$REPO_ROOT/evals/README.md" <<'PY'
import re, sys
manifest, readme = (open(p, encoding="utf-8").read() for p in sys.argv[1:])
commands = re.findall(r"^\s*-?\s*command:\s*\"?([\w:-]+)\"?\s*$", manifest, re.M)
section = re.search(r"^## Coverage\s*$(.*?)(?=^## |\Z)", readme, re.M | re.S)
rows = {m.group(1) for m in re.finditer(r"^\|\s*`([\w:-]+)`\s*\|", section.group(1) if section else "", re.M)}
print(" ".join(c for c in commands if c not in rows) if commands else "no commands parsed")
PY
)
if [ -z "$missing" ]; then pass "every workflow-manifest command has a row in the eval coverage matrix"; else fail "commands missing from the eval coverage matrix in evals/README.md: $missing"; fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
