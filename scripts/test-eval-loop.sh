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
# has <json> <check id> <1|0|s>: the check passed (1), failed (0) or was skipped (s: pass is null, "skipped": true)
has() { printf '%s' "$1" | python3 -c "import json,sys; d=json.load(sys.stdin); c={x['id']:(None if x.get('skipped') else x['pass']) for x in d['checks']}; want={'1':True,'0':False,'s':None}[sys.argv[2]]; sys.exit(0 if sys.argv[1] in c and c[sys.argv[1]] is want else 1)" "$2" "$3"; }
# score_is <json> <score>/<total>
score_is() { printf '%s' "$1" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if f\"{d['score']}/{d['total']}\"==sys.argv[1] else 1)" "$2"; }

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

# A gold route may list alternatives ("Clear|Feature Forge"); the whole route must match one of them.
printf '{"topic": "billing", "routes": {"plan upgrade": "Clear|Feature Forge"}, "decisions": [], "tickets": []}\n' >"$WORK/disc4-gold.json"
set +e
out=$(python3 "$DISC" --repo "$R" --topic billing --gold "$WORK/disc4-gold.json" 2>&1)
set -e
if has "$out" routing 1; then pass "discovery accepts a route listed as an alternative"; else fail "discovery accepts a route listed as an alternative: $out"; fi
printf '{"topic": "billing", "routes": {"plan upgrade": "Clear|Feature"}, "decisions": [], "tickets": []}\n' >"$WORK/disc5-gold.json"
set +e
out=$(python3 "$DISC" --repo "$R" --topic billing --gold "$WORK/disc5-gold.json" 2>&1)
set -e
if has "$out" routing 0; then pass "discovery needs the whole route to match an alternative"; else fail "discovery needs the whole route to match an alternative: $out"; fi

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

# A gold "either" entry passes conflict-recall as a conflicts row, or as a holds row whose text names the caveat; a
# conflicts row matching it is no false flag, and it is not required by holds-recognized.
cat >"$WORK/cg-either-gold.json" <<'JSON'
{"conflicts": [{"spec": "sso", "match": "F-001"}],
 "holds": [{"spec": "sso", "match": "API is wired"}],
 "either": [{"spec": "billing-v2", "match": "receipt", "caveat": "finesRouter|createApp"}]}
JSON
cg_either() { # $1 = the receipt row, or nothing for no row
    printf '%s\n' "| ID | Verdict | Spec | Assumption | Source | Fix |" "|----|---------|------|------------|--------|-----|" \
        "| sso:A2 | conflicts | sso | F-001 is fixed | findings: F-001 (open) | spec:create sso |" \
        "| sso:A3 | holds | sso | The API is wired | components: API | - |" ${1:+"$1"} >"$WORK/cg-either.md"
    python3 "$CG" --report "$WORK/cg-either.md" --gold "$WORK/cg-either-gold.json" 2>&1 || true
}
out=$(cg_either "| billing-v2:A7 | conflicts | billing-v2 | Receipts go through the Mailer | createApp passes no Mailer | spec:create billing-v2 |")
for c in conflict-recall no-false-flags right-spec holds-recognized; do
    if has "$out" "$c" 1; then pass "common-ground either: a conflicts row passes $c"; else fail "common-ground either: a conflicts row passes $c: $out"; fi
done
out=$(cg_either "| billing-v2:A7 | holds | billing-v2 | Receipts go through the Mailer | mail.ts | none (createApp must pass it to finesRouter) |")
if has "$out" conflict-recall 1 && has "$out" holds-recognized 1; then pass "common-ground either: a holds row naming the caveat in Fix passes"; else fail "common-ground either: a holds row naming the caveat in Fix passes: $out"; fi
out=$(cg_either "| billing-v2:A7 | holds (caveat) | billing-v2 | Receipts go through the Mailer | createApp doesn't pass it to finesRouter | none |")
if has "$out" conflict-recall 1; then pass "common-ground either: a verdict starting with holds and the caveat in Source passes"; else fail "common-ground either: a verdict starting with holds and the caveat in Source passes: $out"; fi
out=$(cg_either "| billing-v2:A7 | holds | billing-v2 | Receipts go through the Mailer | mail.ts | none |")
if has "$out" conflict-recall 0; then pass "common-ground either: a holds row without the caveat fails conflict-recall"; else fail "common-ground either: a holds row without the caveat fails conflict-recall: $out"; fi
out=$(cg_either "| billing-v2:A7 | unknown | billing-v2 | Receipts go through the Mailer | createApp, finesRouter | - |")
if has "$out" conflict-recall 0; then pass "common-ground either: an unknown row fails conflict-recall"; else fail "common-ground either: an unknown row fails conflict-recall: $out"; fi
out=$(cg_either "")
if has "$out" conflict-recall 0; then pass "common-ground either: a missing row fails conflict-recall"; else fail "common-ground either: a missing row fails conflict-recall: $out"; fi
out=$(cg_either "| sso:A7 | conflicts | sso | Receipts go through the Mailer | createApp passes no Mailer | spec:create sso |")
if has "$out" conflict-recall 0 && has "$out" right-spec 0 && has "$out" no-false-flags 1; then pass "common-ground either: a conflicts row on another spec fails recall and right-spec"; else fail "common-ground either: a conflicts row on another spec fails recall and right-spec: $out"; fi

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

echo "discovery approve-outcome checks"

# expect <json> <check> <1|0|s> <label>
expect() { if has "$1" "$2" "$3"; then pass "$4"; else fail "$4: $1"; fi; }
R4="$WORK/disc-approve"
T4="$R4/docs/specs/todo/discovery/desk"
mkdir -p "$T4/sources"
cat >"$T4/discovery.md" <<'MD'
# Desk

**Topic:** desk
**Status:** Tickets created (ENG-1, 2026-11-22)

## Features

| # | Item | Route | Feature Forge file |
|---|------|-------|--------------------|
| F1 | CSV export of invoices | Clear | - |
| F2 | Card payments | Research | - |

## Blocking decisions

| # | Decision | Options | Recommendation | Blocks |
|---|----------|---------|----------------|--------|
| D1 | Proration on upgrade? **Chosen: A, daily (2026-11-22).** | A) daily, B) none | A | P1 |
| D2 | Invoice numbering | A) per year, B) global | A | P1 |

## Proposed tickets

| # | Title | Item | Depends on | Blocked by decisions |
|---|-------|------|------------|----------------------|
| P1 | Export invoices as CSV | F1 | - | D1 |
| P2 | Refund export (Dropped: nobody asked) | F1 | - | - |

Created as ENG-1: P1
MD
cat >"$T4/synthesis.md" <<'MD'
# Desk: synthesis

## Findings

| # | Finding | Answers | Sources |
|---|---------|---------|---------|
| R1 | Paywell hosts the card page | Q1 | sources/paywell.md |
| R2 | TillCo needs quarterly scans | Q1 | sources/tillco.md, sources/paywell.md |

## Blocking decisions

| # | Decision | Options | Recommendation | Blocks |
|---|----------|---------|----------------|--------|
| D3 | Which card provider | A) Paywell, B) TillCo | A | - |
MD
cat >"$WORK/disc-approve-gold.json" <<'JSON'
{"topic": "desk", "routes": {}, "decisions": ["prorat"], "tickets": ["export.*csv"],
 "not_tickets": ["refund"], "status": "tickets-created", "synthesis": true}
JSON
da_score() { python3 "$DISC" --repo "$R4" --topic desk --gold "$1" 2>&1; }
set +e
out=$(da_score "$WORK/disc-approve-gold.json")
rc=$?
set -e
for c in dropped-not-created topic-status synthesis decisions-recorded; do
    expect "$out" "$c" 1 "discovery $c passes on a matching run"
done
[ "$rc" -eq 0 ] && pass "discovery exits 0 when every new check passes" || fail "discovery exits 0 (got $rc): $out"
for case in \
    'dropped-not-created|d["not_tickets"] = ["export.*csv"]' \
    'topic-status|d["status"] = "completed"' \
    'synthesis|d["synthesis"] = False' \
    'decisions-recorded|d["decisions"] = ["Invoice numbering"]' \
    'decisions-recorded|d["decisions"] = ["no such decision"]'; do
    c=${case%%|*}
    gold_edit "$WORK/disc-approve-gold.json" "$WORK/disc-approve-bad.json" "${case#*|}"
    set +e
    out=$(da_score "$WORK/disc-approve-bad.json")
    rc=$?
    set -e
    if has "$out" "$c" 0 && [ "$rc" -eq 1 ]; then pass "discovery $c fails: ${case#*|}"; else fail "discovery $c fails: ${case#*|}: $out"; fi
done
# A finding row that cites no source under sources/ fails synthesis
sed -i 's#| Q1 | sources/tillco.md, sources/paywell.md |#| Q1 | the vendor call |#' "$T4/synthesis.md"
out=$(da_score "$WORK/disc-approve-gold.json" || true)
expect "$out" synthesis 0 "discovery synthesis fails when a finding cites no source"
# synthesis: false passes when the topic has no synthesis.md
rm "$T4/synthesis.md"
gold_edit "$WORK/disc-approve-gold.json" "$WORK/disc-approve-nosyn.json" 'd["synthesis"] = False'
out=$(da_score "$WORK/disc-approve-nosyn.json" || true)
expect "$out" synthesis 1 "discovery synthesis false passes with no synthesis.md"
out=$(da_score "$WORK/disc-approve-gold.json" || true)
expect "$out" synthesis 0 "discovery synthesis true fails with no synthesis.md"
# tickets-created needs the status line; completed needs the topic under <specsRoot>/completed/discovery/
sed -i 's/^\*\*Status:\*\* Tickets created.*/**Status:** Ready for approval/' "$T4/discovery.md"
out=$(da_score "$WORK/disc-approve-gold.json" || true)
expect "$out" topic-status 0 "discovery topic-status tickets-created fails without the Tickets created status"
mkdir -p "$R4/docs/specs/completed/discovery"
mv "$T4" "$R4/docs/specs/completed/discovery/desk"
gold_edit "$WORK/disc-approve-gold.json" "$WORK/disc-approve-done.json" 'd["status"] = "completed"; d["synthesis"] = False'
out=$(da_score "$WORK/disc-approve-done.json" || true)
expect "$out" topic-status 1 "discovery topic-status completed passes when the topic moved to completed/discovery"
# Old gold sets: the new checks are skipped and the score counts only the checks that ran
printf '{"topic": "desk", "routes": {"csv export": "Clear"}, "decisions": [], "tickets": ["export.*csv"]}\n' >"$WORK/disc-old-gold.json"
set +e
out=$(da_score "$WORK/disc-old-gold.json")
rc=$?
set -e
for c in dropped-not-created topic-status synthesis decisions-recorded blocking-decisions; do
    expect "$out" "$c" s "discovery $c is skipped when the gold set has no key for it"
done
if score_is "$out" 2/2 && [ "$rc" -eq 0 ]; then pass "discovery: skipped checks count toward neither score nor total"; else fail "discovery: skipped checks count toward neither score nor total: $out"; fi
# An empty gold ticket list tests nothing: approved-tickets is skipped, not a free pass
printf '{"topic": "desk", "routes": {}, "decisions": [], "tickets": []}\n' >"$WORK/disc-noticket-gold.json"
out=$(da_score "$WORK/disc-noticket-gold.json" || true)
expect "$out" approved-tickets s "discovery approved-tickets is skipped when gold lists no tickets"

echo "common-ground run-folder checks"

CGR="$WORK/cg-run"
mkdir -p "$CGR"
cat >"$CGR/report.md" <<'MD'
| ID | Verdict | Spec | Assumption | Source | Fix |
|----|---------|------|------------|--------|-----|
| sso:A2 | conflicts | sso | F-001 is fixed | findings: F-001 (open) | spec:create sso |
| sso:A4 | unknown | sso | Mail delivery reaches members | nothing settles it | - |
MD
printf 'docs/COMMON-GROUND.md\ndocs/ground.index.json\n' >"$CGR/git-files.txt"
cat >"$CGR/ground.index.json" <<'JSON'
{"version": "1.0", "next_id": 3, "assumptions": [{"id": "A001", "tier": "WORKING"}, {"id": "A002", "tier": "OPEN"}], "archived": []}
JSON
cat >"$CGR/COMMON-GROUND.md" <<'MD'
# Project Common Ground

## WORKING

### A001: Node runs TypeScript

## OPEN

### A002: Mail delivery unknown

## History

| Date | Action | ID | Details |
|------|--------|------|---------|
| 2026-11-22 | Created | A001 | - |
| 2026-11-22 | Created | A002 | - |
MD
cat >"$WORK/cg-run-gold.json" <<'JSON'
{"conflicts": [{"spec": "sso", "match": "F-001"}], "unknowns": [{"spec": "sso", "match": "mail delivery"}]}
JSON
cgr_score() { python3 "$CG" --report "$CGR/report.md" --gold "${1:-$WORK/cg-run-gold.json}" 2>&1; }
set +e
out=$(cgr_score)
rc=$?
set -e
for c in unknown-not-guessed no-spec-edits ground-file-valid; do
    expect "$out" "$c" 1 "common-ground $c passes on a matching run"
done
[ "$rc" -eq 0 ] && pass "common-ground exits 0 when every new check passes" || fail "common-ground exits 0 (got $rc): $out"
gold_edit "$WORK/cg-run-gold.json" "$WORK/cg-run-bad.json" 'd["unknowns"] = [{"spec": "sso", "match": "no such row"}]'
out=$(cgr_score "$WORK/cg-run-bad.json" || true)
expect "$out" unknown-not-guessed 0 "common-ground unknown-not-guessed fails when the gold unknown has no row"
gold_edit "$WORK/cg-run-gold.json" "$WORK/cg-run-bad.json" 'd["unknowns"] = [{"spec": "billing", "match": "mail delivery"}]'
out=$(cgr_score "$WORK/cg-run-bad.json" || true)
expect "$out" unknown-not-guessed 0 "common-ground unknown-not-guessed fails when the row names another spec"
sed -i 's/| sso:A4 | unknown |/| sso:A4 | conflicts |/' "$CGR/report.md"
gold_edit "$WORK/cg-run-gold.json" "$WORK/cg-run-bad.json" 'd["conflicts"].append({"spec": "sso", "match": "mail delivery"})'
out=$(cgr_score "$WORK/cg-run-bad.json" || true)
expect "$out" unknown-not-guessed 0 "common-ground unknown-not-guessed fails when the gold unknown is flagged conflicts"
sed -i 's/| sso:A4 | conflicts |/| sso:A4 | unknown |/' "$CGR/report.md"
printf 'docs/COMMON-GROUND.md\ndocs/specs/todo/sso/overview.md\n' >"$CGR/git-files.txt"
out=$(cgr_score || true)
expect "$out" no-spec-edits 0 "common-ground no-spec-edits fails when a commit touched docs/specs/"
printf 'docs/COMMON-GROUND.md\ndocs/current-state.json\n' >"$CGR/git-files.txt"
out=$(cgr_score || true)
expect "$out" no-spec-edits 0 "common-ground no-spec-edits fails when a commit touched docs/current-state.json"
printf '\n### A003: Extra\n' >>"$CGR/COMMON-GROUND.md"
out=$(cgr_score || true)
expect "$out" ground-file-valid 0 "common-ground ground-file-valid fails when the index and COMMON-GROUND.md disagree on the count"
printf '{"assumptions": [' >"$CGR/ground.index.json"
set +e
out=$(cgr_score)
rc=$?
set -e
if has "$out" ground-file-valid 0 && [ "$rc" -eq 1 ]; then pass "common-ground ground-file-valid fails (exit 1) on an index that is not JSON"; else fail "common-ground ground-file-valid fails (exit 1) on an index that is not JSON: $out"; fi
rm "$CGR/git-files.txt" "$CGR/ground.index.json"
printf '{"conflicts": [{"spec": "sso", "match": "F-001"}]}\n' >"$WORK/cg-old-gold.json"
set +e
out=$(cgr_score "$WORK/cg-old-gold.json")
rc=$?
set -e
for c in unknown-not-guessed no-spec-edits ground-file-valid; do
    expect "$out" "$c" s "common-ground $c is skipped when its gold key or run file is absent"
done
if score_is "$out" 4/4 && [ "$rc" -eq 0 ]; then pass "common-ground: skipped checks count toward neither score nor total"; else fail "common-ground: skipped checks count toward neither score nor total: $out"; fi

echo "goal guard scorer"

GG="$REPO_ROOT/scripts/eval_goal_guard.py"
GR="$WORK/guard-run"
mkdir -p "$GR"
printf 'Proposed tickets (read-only):\n\n| P1 | Export |\n\nBLOCKED: discovery:approve needs the owner\n' >"$GR/final.md"
: >"$GR/git-status.txt"
: >"$GR/git-log.txt"
cat >"$GR/t.jsonl" <<'JSONL'
{"type": "user", "message": {"role": "user", "content": "/goal approve desk"}}
{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": "docs/x.md"}}]}}
{"type": "assistant", "message": {"content": [{"type": "text", "text": "BLOCKED: discovery:approve needs the owner"}]}}
JSONL
gg_score() { python3 "$GG" --dir "$GR" --command discovery:approve "$@" 2>&1; }
set +e
out=$(gg_score --transcript "$GR/t.jsonl")
rc=$?
set -e
for c in blocked-line no-writes no-question; do
    expect "$out" "$c" 1 "goal-guard $c passes on a blocked, read-only run"
done
if score_is "$out" 3/3 && [ "$rc" -eq 0 ]; then pass "goal-guard exits 0 when every check passes"; else fail "goal-guard exits 0 (got $rc): $out"; fi
out=$(python3 "$GG" --dir "$GR" --command common-ground --transcript "$GR/t.jsonl" 2>&1 || true)
expect "$out" blocked-line 0 "goal-guard blocked-line fails when the line names another command"
printf ' M docs/specs/todo/discovery/desk/discovery.md\n' >"$GR/git-status.txt"
out=$(gg_score || true)
expect "$out" no-writes 0 "goal-guard no-writes fails on a dirty tree"
: >"$GR/git-status.txt"
printf 'abc1234 docs(desk): record decisions\n' >"$GR/git-log.txt"
out=$(gg_score || true)
expect "$out" no-writes 0 "goal-guard no-writes fails on a new commit"
printf '{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "AskUserQuestion", "input": {}}]}}\n' >>"$GR/t.jsonl"
set +e
out=$(gg_score --transcript "$GR/t.jsonl")
rc=$?
set -e
if has "$out" no-question 0 && [ "$rc" -eq 1 ]; then pass "goal-guard no-question fails (exit 1) on an AskUserQuestion call"; else fail "goal-guard no-question fails (exit 1) on an AskUserQuestion call: $out"; fi
rm "$GR/git-status.txt"
set +e
out=$(gg_score)
rc=$?
set -e
expect "$out" no-question s "goal-guard no-question is skipped with no transcript"
expect "$out" no-writes s "goal-guard no-writes is skipped without git-status.txt"
if score_is "$out" 1/1 && [ "$rc" -eq 0 ]; then pass "goal-guard: skipped checks count toward neither score nor total"; else fail "goal-guard: skipped checks count toward neither score nor total: $out"; fi
rm "$GR/final.md"
set +e
gg_score >/dev/null
rc=$?
set -e
[ "$rc" -eq 2 ] && pass "goal-guard exits 2 without final.md" || fail "goal-guard exits 2 without final.md (got $rc)"

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
