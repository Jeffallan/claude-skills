#!/usr/bin/env bash
#
# Test scripts/eval_intake_run.py on two synthetic intake runs over a small
# Python project: a good one that keeps every intake guarantee, and a bad one
# that breaks them (a doc without its accuracy audit, a missing doc, a skipped
# test with no finding id, a red suite, an application-code fix, a commit
# without its Intake: trailer, an amend, and a goal session that asked a
# question).
#
# Usage: bash scripts/test-eval-intake.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVAL="$REPO_ROOT/scripts/eval_intake_run.py"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

DOCS="architecture/data-model architecture/file-tree architecture/external-integrations architecture/api-reference domain/user-model domain/features domain/glossary security/security security/authorization flows/user-flow operations/configuration"

# commit_item <dir> <command> <message>: one checklist item, one commit
commit_item() {
    git -C "$1" add -A
    git -C "$1" commit -qm "$3" -m "Intake: $2"
}

# make_run <dir>: a finished intake run; prints the start SHA
make_run() {
    local d=$1
    git init -q -b main "$d"
    git -C "$d" config user.email t@example.com
    git -C "$d" config user.name t
    cat >"$d/app.py" <<'EOF'
def total(items):
    return sum(i["price"] for i in items)


def visible(user, profile):
    return True
EOF
    mkdir -p "$d/tests"
    printf 'from app import total\n\n\ndef test_total():\n    assert total([{"price": 2}]) == 2\n' >"$d/tests/test_total.py"
    git -C "$d" add -A
    git -C "$d" commit -qm "initial"
    git -C "$d" checkout -qb intake/demo
    mkdir -p "$d/docs"
    local base
    base=$(git -C "$d" rev-parse --short HEAD)
    printf '# Intake Checklist\n\nStarted 2026-11-12 on branch intake/demo at %s.\n\n- [x] `intake:document-analytics`\n  not present: no analytics in the code\n' "$base" >"$d/docs/intake-checklist.md"
    printf 'Run intake.\n' >"$d/docs/intake-goal-prompt.md"
    git -C "$d" add -A
    git -C "$d" commit -qm "docs(intake): checklist and goal prompt"
    git -C "$d" rev-parse --short HEAD >"$d.start"
    sleep 1
    # Docstrings only: the AST without docstrings is unchanged
    cat >"$d/app.py" <<'EOF'
"""Order totals and profile visibility."""


def total(items):
    """Sum the price of each item; raises KeyError when one has no price."""
    return sum(i["price"] for i in items)


def visible(user, profile):
    """Return True for every pair: no ownership check (F-001)."""
    return True
EOF
    commit_item "$d" intake:document-codebase "docs(intake): document-codebase"
    printf '# Intake Findings\n\nIssues found while running intake on 2026-11-12, at intake/demo %s.\n\n## Summary\n\n| ID | Finding | Severity | Area | Status | Surfaced by |\n|----|---|---|---|---|---|\n| F-001 | Any user sees any profile | High | access | open | intake:document-codebase |\n\n## Findings\n\n### F-001 Any user sees any profile\n- **Severity:** High (access)\n- **Status:** open\n- **Location:** `app.py::visible`\n- **Tests:** none\n\n## Test coverage\n\n| ID | Characterization test | Intended-behavior test |\n|----|---|---|\n' "$base" >"$d/docs/intake-findings.md"
    local doc
    for doc in $DOCS existing-docs; do
        mkdir -p "$d/docs/$(dirname "$doc")"
        printf -- '---\ncommand: intake:document-x\nverified: %s\nsources: [app.py]\nrelated: []\n---\n# Doc %s\n\nBody citing `app.py::total`.\n\n## Accuracy audit\n\nChecked against the code.\n' "$base" "$doc" >"$d/docs/$doc.md"
    done
    mv "$d/docs/existing-docs.md" "$d/docs/intake-existing-docs.md"
    {
        printf -- '---\ncommand: intake:create-onboarding\nverified: %s\nsources: []\nrelated: []\n---\n# Docs\n\n' "$base"
        for doc in $DOCS; do printf -- '- [%s](%s.md)\n' "$doc" "$doc"; done
        printf -- '- [Findings](intake-findings.md)\n- [Existing docs](intake-existing-docs.md)\n\n## Accuracy audit\n\nLinks checked.\n'
    } >"$d/docs/README.md"
    commit_item "$d" intake:document-data-model "docs(intake): reference docs"
    cat >"$d/tests/test_visible.py" <<'EOF'
import pytest

from app import visible


def test_F001_any_user_sees_any_profile_current():
    assert visible("a", "b") is True


@pytest.mark.xfail(strict=True, reason="F-001")
def test_F001_other_profiles_hidden_intended():
    assert visible("a", "b") is False
EOF
    printf '[pytest]\naddopts = -q\n' >"$d/pytest.ini"
    sed -i 's|- \*\*Tests:\*\* none|- **Tests:** `tests/test_visible.py::test_F001_any_user_sees_any_profile_current`, `tests/test_visible.py::test_F001_other_profiles_hidden_intended`|' "$d/docs/intake-findings.md"
    printf '| F-001 | `tests/test_visible.py::test_F001_any_user_sees_any_profile_current` | `tests/test_visible.py::test_F001_other_profiles_hidden_intended` |\n' >>"$d/docs/intake-findings.md"
    commit_item "$d" intake:testing-authorization "test(intake): testing-authorization"
    mkdir -p "$d/apps/clients"
    printf 'import pytest\n\n\n@pytest.mark.xfail(strict=True, reason="F-001")\ndef test_F001_clients_hidden_intended():\n    assert False\n' >"$d/apps/clients/tests.py"
    commit_item "$d" intake:testing-features "test(intake): testing-features"
}

TEST_CMD="python3 -c 'import sys; sys.exit(0)'"

score() { # score <dir> [extra args...]
    local d=$1
    shift
    python3 "$EVAL" --repo "$d" --start "$(cat "$d.start")" --test-cmd "$TEST_CMD" "$@" 2>&1
}

has() { # has <json> <check id> <pass: 1|0>
    printf '%s' "$1" | python3 -c "import json,sys; d=json.load(sys.stdin); c=[x for x in d['checks']+d.get('optional',[]) if x['id']=='$2']; sys.exit(0 if c and c[0]['pass']==bool($3) else 1)"
}

echo "intake run eval"

GOOD="$WORK/good"
make_run "$GOOD"
G0=$(date -u -d '-1 min' +%Y-%m-%dT%H:%M:%SZ)
G1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '{"type":"user","timestamp":"%s","message":{"role":"user","content":"/goal Every condition in <done_when> holds"}}\n{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"text","text":"done_when evidence: git log shows 3 commits"}]}}\n' "$G0" "$G1" >"$WORK/good.jsonl"

set +e
out=$(score "$GOOD" --transcript "$WORK/good.jsonl")
rc=$?
set -e
if [ "$rc" -eq 0 ]; then pass "the good run passes (exit 0)"; else fail "the good run passes (exit $rc): $out"; fi
if printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d["score"]==d["total"] and d["total"]>=11 else 1)'; then
    pass "the good run scores every check"
else
    fail "the good run scores every check: $out"
fi
if has "$out" docs-with-audit 1 && printf '%s' "$out" | grep -q 'document-analytics: not present'; then
    pass "a doc marked not present in the checklist is excused"
else
    fail "a doc marked not present in the checklist is excused"
fi

BAD="$WORK/bad"
make_run "$BAD"
# Break the doc audit, drop a doc, skip a test with no finding id, fix the app, commit without a trailer, amend
printf '# Glossary\n\nNo audit here.\n' >"$BAD/docs/domain/glossary.md"
git -C "$BAD" rm -q docs/flows/user-flow.md
printf 'import pytest\n\n\n@pytest.mark.skip(reason="later")\ndef test_total_rounding():\n    assert False\n' >"$BAD/tests/test_rounding.py"
sed -i 's/    return True/    return user == profile/' "$BAD/app.py"
git -C "$BAD" add -A
git -C "$BAD" commit -qm "fix: hide other profiles"
git -C "$BAD" commit -q --amend -m "fix: hide other profiles, amended"
B0=$(date -u -d '-1 min' +%Y-%m-%dT%H:%M:%SZ)
B1=$(date -u -d '+1 min' +%Y-%m-%dT%H:%M:%SZ)
printf '{"type":"user","timestamp":"%s","message":{"role":"user","content":"/goal Every condition in <done_when> holds"}}\n{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"tool_use","name":"AskUserQuestion","input":{}}]}}\n{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"text","text":"All done."}]}}\n' "$B0" "$B0" "$B1" >"$WORK/bad.jsonl"

set +e
out=$(python3 "$EVAL" --repo "$BAD" --start "$(cat "$BAD.start")" --test-cmd "python3 -c 'import sys; sys.exit(3)'" --transcript "$WORK/bad.jsonl" 2>&1)
rc=$?
set -e
if [ "$rc" -eq 1 ]; then pass "the bad run fails (exit 1)"; else fail "the bad run fails (exit $rc): $out"; fi
for check in docs-with-audit bug-tests-cite-findings characterization-green characterize-dont-fix one-commit-per-item no-history-rewrite no-question-in-goal final-message-evidence; do
    if has "$out" "$check" 0; then pass "the bad run fails $check"; else fail "the bad run fails $check"; fi
done
for check in findings-tracker launch-delivered no-denied-git; do
    if has "$out" "$check" 1; then pass "the bad run still passes $check"; else fail "the bad run still passes $check"; fi
done
if printf '%s' "$out" | grep -q 'app.py'; then pass "the diff detail names the changed application file"; else fail "the diff detail names the changed application file"; fi
if printf '%s' "$out" | grep -q 'glossary.md'; then pass "the audit detail names the doc without an audit"; else fail "the audit detail names the doc without an audit"; fi

# No test command: the suite check fails rather than passing silently
set +e
out=$(python3 "$EVAL" --repo "$GOOD" --start "$(cat "$GOOD.start")" 2>&1)
set -e
if has "$out" characterization-green 0; then pass "a missing test command fails characterization-green"; else fail "a missing test command fails characterization-green"; fi

# Test-path detection: broad folder names no longer excuse app files
for f in spec/openapi.yaml fixtures/seed.json; do
    D="$WORK/path-$(basename "$f" | cut -d. -f1)"
    make_run "$D"
    mkdir -p "$D/$(dirname "$f")"
    echo "changed: true" >"$D/$f"
    commit_item "$D" intake:testing-setup "test(intake): $f"
    set +e
    out=$(score "$D")
    set -e
    if has "$out" characterize-dont-fix 0 && printf '%s' "$out" | grep -q "$f"; then
        pass "an app file under $(dirname "$f")/ fails characterize-dont-fix"
    else
        fail "an app file under $(dirname "$f")/ fails characterize-dont-fix: $out"
    fi
done

# A test tree outside the built-in names counts once declared: by flag, or by the checklist's Test paths note
QA="$WORK/qa"
make_run "$QA"
mkdir -p "$QA/qa"
printf 'def check_total():\n    assert True\n' >"$QA/qa/check_total.py"
commit_item "$QA" intake:testing-setup "test(intake): qa harness"
set +e
out=$(score "$QA")
set -e
if has "$out" characterize-dont-fix 0; then pass "an undeclared qa/ tree counts as app code"; else fail "an undeclared qa/ tree counts as app code"; fi
set +e
out=$(score "$QA" --test-path 'qa/*')
set -e
if has "$out" characterize-dont-fix 1; then pass "--test-path qa/* makes qa/ a test tree"; else fail "--test-path qa/* makes qa/ a test tree: $out"; fi
printf -- '- [x] `intake:testing-setup`\n  2026-11-11: smoke tests ran. Test paths: qa/*\n' >>"$QA/docs/intake-checklist.md"
commit_item "$QA" intake:testing-setup "docs(intake): record test paths"
set +e
out=$(score "$QA")
set -e
if has "$out" characterize-dont-fix 1; then pass "the checklist's Test paths note makes qa/ a test tree"; else fail "the checklist's Test paths note makes qa/ a test tree: $out"; fi

# A declared glob never excuses package.json beyond scripts and devDependencies,
# and the template's own "`Test paths:` line" wording is not read as a glob
PK="$WORK/pkg"
make_run "$PK"
printf '{"name": "demo", "dependencies": {}}\n' >"$PK/package.json"
git -C "$PK" add -A
git -C "$PK" commit -qm "chore: add manifest before intake" -m "Intake: setup"
git -C "$PK" rev-parse --short HEAD >"$PK.start"
printf -- '- [x] `intake:testing-setup`: scripts wired (its note ends with the `Test paths:` line the command prints)\n  2026-11-11: Test paths: tests/*, package.json\n' >>"$PK/docs/intake-checklist.md"
printf '{"name": "demo", "dependencies": {"leftpad": "1.0.0"}}\n' >"$PK/package.json"
commit_item "$PK" intake:testing-setup "test(intake): harness"
set +e
out=$(score "$PK")
set -e
if has "$out" characterize-dont-fix 0 && printf '%s' "$out" | grep -q 'package.json'; then
    pass "a declared package.json glob doesn't excuse a dependency change"
else
    fail "a declared package.json glob doesn't excuse a dependency change: $out"
fi
if printf '%s' "$out" | grep -q 'line the command prints'; then
    fail "the template's Test paths wording is not read as a glob: $out"
else
    pass "the template's Test paths wording is not read as a glob"
fi

# A new manifest may carry inert metadata beside scripts and devDependencies; never runtime keys
for case in ok:pass deps:fail; do
    name=${case%%:*}
    want=${case##*:}
    NM="$WORK/newpkg-$name"
    make_run "$NM"
    mkdir -p "$NM/tests/e2e"
    printf '{"name": "e2e", "private": true, "scripts": {"e2e": "playwright test"}, "devDependencies": {"@playwright/test": "1.0.0"}}\n' >"$NM/tests/e2e/package.json"
    if [ "$name" = ok ]; then
        printf '{"name": "root", "description": "test scripts", "private": true, "scripts": {"test:all": "pytest"}}\n' >"$NM/package.json"
    else
        printf '{"name": "root", "private": true, "scripts": {}, "dependencies": {"leftpad": "1.0.0"}}\n' >"$NM/package.json"
    fi
    commit_item "$NM" intake:testing-setup "test(intake): harness"
    set +e
    out=$(score "$NM")
    set -e
    if [ "$want" = pass ] && has "$out" characterize-dont-fix 1; then
        pass "new manifests with metadata, scripts and devDependencies pass"
    elif [ "$want" = fail ] && has "$out" characterize-dont-fix 0 && printf '%s' "$out" | grep -qF "code changed: ['package.json']"; then
        pass "a new manifest with dependencies fails characterize-dont-fix"
    else
        fail "new manifest case $name expected $want: $out"
    fi
done

# package-lock.json may gain dev entries; its runtime entries stay identical
for case in dev:pass runtime:fail; do
    name=${case%%:*}
    want=${case##*:}
    LK="$WORK/lock-$name"
    make_run "$LK"
    printf '{"name": "app", "dependencies": {"vue": "2.6.0"}}\n' >"$LK/package.json"
    printf '{"lockfileVersion": 3, "packages": {"": {"dependencies": {"vue": "2.6.0"}}, "node_modules/vue": {"version": "2.6.0"}}}\n' >"$LK/package-lock.json"
    git -C "$LK" add -A
    git -C "$LK" commit -qm "chore: app before intake" -m "Intake: setup"
    git -C "$LK" rev-parse --short HEAD >"$LK.start"
    printf '{"name": "app", "dependencies": {"vue": "2.6.0"}, "devDependencies": {"@vue/test-utils": "1.3.0"}}\n' >"$LK/package.json"
    if [ "$name" = dev ]; then
        printf '{"lockfileVersion": 3, "packages": {"": {"dependencies": {"vue": "2.6.0"}, "devDependencies": {"@vue/test-utils": "1.3.0"}}, "node_modules/vue": {"version": "2.6.0"}, "node_modules/@vue/test-utils": {"version": "1.3.0", "dev": true}}}\n' >"$LK/package-lock.json"
    else
        printf '{"lockfileVersion": 3, "packages": {"": {"dependencies": {"vue": "2.6.0"}, "devDependencies": {"@vue/test-utils": "2.4.0"}}, "node_modules/vue": {"version": "3.4.0"}, "node_modules/@vue/test-utils": {"version": "2.4.0", "dev": true}}}\n' >"$LK/package-lock.json"
    fi
    commit_item "$LK" intake:testing-setup "test(intake): harness"
    set +e
    out=$(score "$LK")
    set -e
    if [ "$want" = pass ] && has "$out" characterize-dont-fix 1; then
        pass "a lockfile that only adds dev entries passes"
    elif [ "$want" = fail ] && has "$out" characterize-dont-fix 0 && printf '%s' "$out" | grep -qF "package-lock.json"; then
        pass "a lockfile that changes a runtime entry fails characterize-dont-fix"
    else
        fail "lockfile case $name expected $want: $out"
    fi
done

# A finding id inside a snake_case test name counts, with no other mention nearby
SN="$WORK/snake"
make_run "$SN"
printf 'import unittest\n\n\nclass T(unittest.TestCase):\n    @unittest.expectedFailure\n    def test_F001_profiles_hidden_intended(self):\n        self.fail()\n' >"$SN/tests/test_snake.py"
commit_item "$SN" intake:testing-owasp "test(intake): testing-owasp"
set +e
out=$(score "$SN")
set -e
if has "$out" bug-tests-cite-findings 1; then pass "a snake_case test_F001_ name cites its finding"; else fail "a snake_case test_F001_ name cites its finding: $out"; fi

# Playwright's in-body test.fail() and Vitest's it.fails are expected-fail markers too
PW="$WORK/pw"
make_run "$PW"
mkdir -p "$PW/e2e"
printf "test('logout revokes the token', async () => {\n  test.fail();\n  expect(1).toBe(2);\n});\n\nit.fails('rounds totals', () => {\n  expect(1).toBe(2);\n});\n" >"$PW/e2e/auth.spec.js"
commit_item "$PW" intake:testing-user-flows "test(intake): testing-user-flows"
set +e
out=$(score "$PW")
set -e
if has "$out" bug-tests-cite-findings 0 && printf '%s' "$out" | grep -q 'auth.spec.js:2' && printf '%s' "$out" | grep -q 'auth.spec.js:6'; then
    pass "test.fail() and it.fails without a finding id fail bug-tests-cite-findings"
else
    fail "test.fail() and it.fails without a finding id fail bug-tests-cite-findings: $out"
fi

# A helper that wraps an expected-fail marker is judged at its call sites, not its definition
HL="$WORK/helper"
make_run "$HL"
mkdir -p "$HL/e2e"
printf "export function intended(test, reason) {\n  test.fail(true, reason);\n}\n" >"$HL/e2e/helpers.mjs"
printf "import { intended } from './helpers.mjs';\n\ntest('F-001 profiles are hidden', async () => {\n  intended(test, 'F-001');\n});\n\ntest('totals round', async () => {\n  intended(test, 'later');\n});\n" >"$HL/e2e/profile.spec.js"
commit_item "$HL" intake:testing-user-flows "test(intake): testing-user-flows"
set +e
out=$(score "$HL")
set -e
if has "$out" bug-tests-cite-findings 0 && printf '%s' "$out" | grep -q 'profile.spec.js:8' && ! printf '%s' "$out" | grep -q 'helpers.mjs'; then
    pass "a marker helper is checked at its call sites, not its definition"
else
    fail "a marker helper is checked at its call sites, not its definition: $out"
fi

# A new test-only lockfile carries a root entry with no dev flag; only runtime packages count
NL="$WORK/newlock"
make_run "$NL"
mkdir -p "$NL/tests/e2e"
printf '{"name": "e2e", "private": true, "devDependencies": {"@playwright/test": "1.0.0"}}\n' >"$NL/tests/e2e/package.json"
printf '{"name": "e2e", "lockfileVersion": 3, "packages": {"": {"name": "e2e", "devDependencies": {"@playwright/test": "1.0.0"}}, "node_modules/@playwright/test": {"version": "1.0.0", "dev": true}}}\n' >"$NL/tests/e2e/package-lock.json"
commit_item "$NL" intake:testing-setup "test(intake): harness"
set +e
out=$(score "$NL")
set -e
if has "$out" characterize-dont-fix 1; then pass "a new test-only lockfile passes"; else fail "a new test-only lockfile passes: $out"; fi

# git stash resets to the same HEAD, which rewrites nothing
ST="$WORK/stash"
make_run "$ST"
echo "scratch" >>"$ST/docs/domain/glossary.md"
git -C "$ST" stash -q
git -C "$ST" stash pop -q
git -C "$ST" checkout -q -- docs/domain/glossary.md
set +e
out=$(score "$ST")
set -e
if has "$out" no-history-rewrite 1; then pass "a stash's reset to HEAD is not a rewrite"; else fail "a stash's reset to HEAD is not a rewrite: $out"; fi

# The Intake: trailer counts only inside the final trailer block, as git parses it
TR="$WORK/trailer"
make_run "$TR"
echo "- note" >>"$TR/docs/domain/glossary.md"
git -C "$TR" add -A
git -C "$TR" commit -qm "docs(intake): glossary" -m "Intake: intake:document-glossary" -m "Co-Authored-By: A <a@example.com>"
set +e
out=$(score "$TR")
set -e
if has "$out" one-commit-per-item 0; then pass "an Intake: line outside the trailer block fails one-commit-per-item"; else fail "an Intake: line outside the trailer block fails one-commit-per-item: $out"; fi

# unittest markers imported bare (from unittest import expectedFailure) count too
BM="$WORK/bare"
make_run "$BM"
printf 'import unittest\nfrom unittest import expectedFailure, skip\n\n\nclass T(unittest.TestCase):\n    @expectedFailure\n    def test_rounding_intended(self):\n        self.fail()\n\n    @skip("later")\n    def test_other(self):\n        pass\n' >"$BM/tests/test_bare.py"
commit_item "$BM" intake:testing-features "test(intake): testing-features"
set +e
out=$(score "$BM")
set -e
if has "$out" bug-tests-cite-findings 0 && printf '%s' "$out" | grep -q 'test_bare.py:6' && printf '%s' "$out" | grep -q 'test_bare.py:10'; then
    pass "bare @expectedFailure and @skip count as markers"
else
    fail "bare @expectedFailure and @skip count as markers: $out"
fi

# Accuracy tally: found/total against a gold file, given rows left out, mismatched mappings refused
ACC="$REPO_ROOT/scripts/eval_intake_accuracy.py"
printf '# Gold\n\n- **Version:** 3 (test)\n\n## Findings (4)\n\n| Gold id | Verdict | Source |\n|---|---|---|\n| F-001 | valid | review |\n| F-002 | valid | review |\n| MISSED-1 | valid | review |\n| ADDED-1 | valid | run 2 |\n\n## Docs (0)\n' >"$WORK/gold.md"
printf '{"run": "run 2", "found": {"F-001": "F-004", "MISSED-1": null, "ADDED-1": "F-009"}, "given": ["F-002"]}\n' >"$WORK/map.json"
out=$(python3 "$ACC" "$WORK/gold.md" "$WORK/map.json")
if printf '%s' "$out" | grep -q '"gold_version": "3", "found": 1, "total": 2' && printf '%s' "$out" | grep -q '"missed": \["MISSED-1"\]' && printf '%s' "$out" | grep -q '"own": \["ADDED-1"\]'; then
    pass "the accuracy tally counts found rows and leaves given rows and the run's own rows out"
else
    fail "the accuracy tally counts found rows and leaves given rows and the run's own rows out: $out"
fi
printf '{"run": "run 2", "found": {"F-001": "F-004"}, "given": []}\n' >"$WORK/map-short.json"
set +e
python3 "$ACC" "$WORK/gold.md" "$WORK/map-short.json" >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 2 ]; then pass "the accuracy tally refuses a mapping that skips gold rows"; else fail "the accuracy tally refuses a mapping that skips gold rows (exit $rc)"; fi

# Compaction recovery: after a compaction, the goal session re-reads the checklist and goal prompt before editing
CP="$WORK/compact"
make_run "$CP"
T0=$(date -u -d '-1 min' +%Y-%m-%dT%H:%M:%SZ)
goal_line="{\"type\":\"user\",\"timestamp\":\"$T0\",\"message\":{\"role\":\"user\",\"content\":\"/goal Every condition in <done_when> holds\"}}"
boundary="{\"type\":\"system\",\"subtype\":\"compact_boundary\",\"timestamp\":\"$T0\"}"
read_of() { printf '{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/r/docs/%s"}}]}}' "$T0" "$1"; }
edit_line="{\"type\":\"assistant\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"tool_use\",\"name\":\"Edit\",\"input\":{\"file_path\":\"/r/docs/domain/glossary.md\"}}]}}"
final_line="{\"type\":\"assistant\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"text\",\"text\":\"git log shows every done_when check\"}]}}"
printf '%s\n' "$goal_line" "$boundary" "$(read_of intake-checklist.md)" "$(read_of intake-goal-prompt.md)" "$edit_line" "$final_line" >"$WORK/compact-good.jsonl"
printf '%s\n' "$goal_line" "$boundary" "$edit_line" "$(read_of intake-checklist.md)" "$final_line" >"$WORK/compact-bad.jsonl"
printf '%s\n' "$goal_line" "$edit_line" "$final_line" >"$WORK/compact-none.jsonl"
for case in good:1 bad:0; do
    name=${case%%:*}; want=${case##*:}
    set +e
    out=$(python3 "$EVAL" --repo "$CP" --start "$(cat "$CP.start")" --transcript "$WORK/compact-$name.jsonl" 2>&1)
    set -e
    if has "$out" compaction-recovery "$want"; then pass "compaction recovery case $name"; else fail "compaction recovery case $name: $out"; fi
done
set +e
out=$(python3 "$EVAL" --repo "$CP" --start "$(cat "$CP.start")" --transcript "$WORK/compact-none.jsonl" 2>&1)
set -e
if printf '%s' "$out" | grep -q '"compaction-recovery"'; then fail "a run with no compaction has no compaction-recovery check"; else pass "a run with no compaction has no compaction-recovery check"; fi

# Every commit carries one Intake: trailer (BLOCKED notes included); every item checked since the start has a commit
for case in blocked:1 untrailered:0 nocommit:0 barename:1; do
    name=${case%%:*}; want=${case##*:}
    CM="$WORK/commits-$name"
    make_run "$CM"
    case $name in
    blocked)
        printf -- '- [ ] `intake:testing-owasp`\n  BLOCKED: no browser in this environment\n' >>"$CM/docs/intake-checklist.md"
        commit_item "$CM" intake:testing-owasp "docs(intake): testing-owasp blocked" ;;
    untrailered)
        printf -- '- [ ] `intake:testing-owasp`\n  BLOCKED: no browser in this environment\n' >>"$CM/docs/intake-checklist.md"
        git -C "$CM" add -A && git -C "$CM" commit -qm "docs(intake): testing-owasp blocked" ;;
    nocommit)
        printf -- '- [x] `intake:document-glossary`\n  2026-11-12: written\n' >>"$CM/docs/intake-checklist.md"
        commit_item "$CM" intake:document-features "docs(intake): document-features" ;;
    barename)
        printf -- '- [x] `intake:document-glossary`\n  2026-11-12: written\n' >>"$CM/docs/intake-checklist.md"
        commit_item "$CM" document-glossary "docs(intake): document-glossary" ;;
    esac
    set +e
    out=$(score "$CM")
    set -e
    if has "$out" one-commit-per-item "$want"; then pass "commit rule case $name"; else fail "commit rule case $name: $out"; fi
done

# Skills a checklist note claims must appear as Skill calls in the goal transcripts
SK="$WORK/skills"
make_run "$SK"
printf -- '- [x] `intake:document-glossary`\n  2026-11-12: written with fullstack-dev-skills:code-documenter and the test-master skill\n' >>"$SK/docs/intake-checklist.md"
commit_item "$SK" intake:document-glossary "docs(intake): document-glossary"
T0=$(date -u -d '-1 min' +%Y-%m-%dT%H:%M:%SZ)
g="{\"type\":\"user\",\"timestamp\":\"$T0\",\"message\":{\"role\":\"user\",\"content\":\"/goal Every condition in <done_when> holds\"}}"
f="{\"type\":\"assistant\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"text\",\"text\":\"git log shows every done_when check\"}]}}"
sk="{\"type\":\"assistant\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"tool_use\",\"name\":\"Skill\",\"input\":{\"skill\":\"fullstack-dev-skills:code-documenter\"}}]}}"
sk2="{\"type\":\"assistant\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"tool_use\",\"name\":\"Skill\",\"input\":{\"skill\":\"fullstack-dev-skills:test-master\"}}]}}"
printf '%s\n' "$g" "$sk" "$sk2" "$f" >"$WORK/skills-loaded.jsonl"
printf '%s\n' "$g" "$sk" "$f" >"$WORK/skills-bare.jsonl"
printf '%s\n' "$g" "$f" >"$WORK/skills-missing.jsonl"
for case in loaded:1 missing:0 bare:0; do
    name=${case%%:*}; want=${case##*:}
    set +e
    out=$(python3 "$EVAL" --repo "$SK" --start "$(cat "$SK.start")" --transcript "$WORK/skills-$name.jsonl" 2>&1)
    set -e
    if has "$out" skills-loaded "$want"; then pass "skills check case $name"; else fail "skills check case $name: $out"; fi
done

# A fixed check set: the output names its version, optional checks sit outside the score, a saved suite result counts
set +e
out=$(python3 "$EVAL" --repo "$CP" --start "$(cat "$CP.start")" --transcript "$WORK/compact-good.jsonl" --suite-green 2>&1)
set -e
if printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); ids=[c['id'] for c in d['checks']]; opt=[c['id'] for c in d['optional']]; sys.exit(0 if d['checks_version']>=1 and 'compaction-recovery' in opt and 'compaction-recovery' not in ids and d['total']==len(ids) else 1)"; then
    pass "the output names its checks version and keeps optional checks out of the score"
else
    fail "the output names its checks version and keeps optional checks out of the score: $out"
fi
if has "$out" characterization-green 1; then pass "--suite-green counts a saved green suite"; else fail "--suite-green counts a saved green suite: $out"; fi

# An empty module that only gains a docstring is comment-only
EM="$WORK/emptymod"
make_run "$EM"
mkdir -p "$EM/pkg" && : >"$EM/pkg/__init__.py"
git -C "$EM" add -A && git -C "$EM" commit -qm "chore: package" -m "Intake: setup"
git -C "$EM" rev-parse --short HEAD >"$EM.start"
printf '"""The package that holds the demo app."""\n' >"$EM/pkg/__init__.py"
commit_item "$EM" intake:document-codebase "docs(intake): document-codebase"
set +e
out=$(score "$EM")
set -e
if has "$out" characterize-dont-fix 1; then pass "a docstring added to an empty module is comment-only"; else fail "a docstring added to an empty module is comment-only: $out"; fi

# Subagent transcripts feed skills-loaded but not the goal-session checks
SA="$WORK/subagent"
make_run "$SA"
printf -- '- [x] `intake:document-glossary`\n  2026-11-12: written with the test-master skill\n' >>"$SA/docs/intake-checklist.md"
commit_item "$SA" intake:document-glossary "docs(intake): document-glossary"
T0=$(date -u -d '-1 min' +%Y-%m-%dT%H:%M:%SZ)
printf '%s\n' "{\"type\":\"user\",\"timestamp\":\"$T0\",\"message\":{\"role\":\"user\",\"content\":\"/goal Every condition in <done_when> holds\"}}" "{\"type\":\"assistant\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"text\",\"text\":\"git log shows every done_when check\"}]}}" >"$WORK/sa-main.jsonl"
printf '%s\n' "{\"type\":\"user\",\"isSidechain\":true,\"agentId\":\"a1\",\"timestamp\":\"$T0\",\"message\":{\"role\":\"user\",\"content\":\"Review this diff\"}}" "{\"type\":\"assistant\",\"isSidechain\":true,\"agentId\":\"a1\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"tool_use\",\"name\":\"Skill\",\"input\":{\"skill\":\"fullstack-dev-skills:test-master\"}}]}}" >"$WORK/sa-agent.jsonl"
set +e
out=$(python3 "$EVAL" --repo "$SA" --start "$(cat "$SA.start")" --transcript "$WORK/sa-main.jsonl" --transcript "$WORK/sa-agent.jsonl" 2>&1)
set -e
if has "$out" launch-delivered 1 && has "$out" final-message-evidence 1 && has "$out" skills-loaded 1; then
    pass "subagent transcripts count for skills-loaded only"
else
    fail "subagent transcripts count for skills-loaded only: $out"
fi

# Each documentation item's note records its human-voice pass; a note naming the skill needs a Skill call
HV="$WORK/voice"
make_run "$HV"
printf -- '- [x] `intake:document-glossary`\n  2026-11-12: written; human-voice: writing-with-agents:human-voice\n' >>"$HV/docs/intake-checklist.md"
commit_item "$HV" intake:document-glossary "docs(intake): document-glossary"
T0=$(date -u -d '-1 min' +%Y-%m-%dT%H:%M:%SZ)
gl="{\"type\":\"user\",\"timestamp\":\"$T0\",\"message\":{\"role\":\"user\",\"content\":\"/goal Every condition in <done_when> holds\"}}"
fl="{\"type\":\"assistant\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"text\",\"text\":\"git log shows every done_when check\"}]}}"
hv="{\"type\":\"assistant\",\"timestamp\":\"$T0\",\"message\":{\"content\":[{\"type\":\"tool_use\",\"name\":\"Skill\",\"input\":{\"skill\":\"writing-with-agents:human-voice\"}}]}}"
printf '%s\n' "$gl" "$hv" "$fl" >"$WORK/hv-loaded.jsonl"
printf '%s\n' "$gl" "$fl" >"$WORK/hv-missing.jsonl"
for case in loaded:1 missing:0; do
    name=${case%%:*}; want=${case##*:}
    set +e
    out=$(python3 "$EVAL" --repo "$HV" --start "$(cat "$HV.start")" --transcript "$WORK/hv-$name.jsonl" 2>&1)
    set -e
    if has "$out" human-voice-pass "$want"; then pass "human-voice case $name"; else fail "human-voice case $name: $out"; fi
done
HN="$WORK/voice-none"
make_run "$HN"
printf -- '- [x] `intake:document-features`\n  2026-11-12: written\n' >>"$HN/docs/intake-checklist.md"
commit_item "$HN" intake:document-features "docs(intake): document-features"
set +e
out=$(score "$HN")
set -e
if has "$out" human-voice-pass 0 && printf '%s' "$out" | grep -q 'document-features'; then pass "a documentation note without a human-voice record fails"; else fail "a documentation note without a human-voice record fails: $out"; fi

# Version 5: symbol citations, findings with evidence, the docs index, pristine docs
fresh() { # fresh <name>: a good run plus one more commit made by the caller
    local d="$WORK/$1"
    make_run "$d"
    printf '%s' "$d"
}
v5() { # v5 <dir> <check> <want> <label>
    local out
    set +e
    out=$(score "$1")
    set -e
    if has "$out" "$2" "$3"; then pass "$4"; else fail "$4: $out"; fi
}
V=$(fresh v5-good)
for c in symbol-citations findings-evidence docs-index docs-pristine; do v5 "$V" "$c" 1 "the good run passes $c"; done

V=$(fresh v5-line)
printf '\nSee `app.py:5`.\n' >>"$V/docs/domain/glossary.md"
commit_item "$V" intake:document-glossary "docs(intake): glossary"
v5 "$V" symbol-citations 0 "a path:line citation fails symbol-citations"

V=$(fresh v5-tests-none)
sed -i 's|- \*\*Tests:\*\* `.*|- **Tests:** none|' "$V/docs/intake-findings.md"
commit_item "$V" intake:testing-features "test(intake): fix"
v5 "$V" findings-evidence 0 "a finding left Tests: none fails findings-evidence"

V=$(fresh v5-tests-missing)
sed -i 's|test_F001_any_user_sees_any_profile_current`, |test_F001_gone`, |' "$V/docs/intake-findings.md"
commit_item "$V" intake:testing-features "test(intake): fix"
v5 "$V" findings-evidence 0 "a Tests: entry naming no real test fails findings-evidence"

V=$(fresh v5-evidence)
sed -i 's|- \*\*Tests:\*\* `.*|- **Tests:** none: dead code, no behavior to pin; evidence: `python3 -m vulture app.py`|' "$V/docs/intake-findings.md"
commit_item "$V" intake:testing-features "test(intake): fix"
v5 "$V" findings-evidence 1 "a finding no test can express passes with its evidence command"

V=$(fresh v5-invalid)
sed -i 's|- \*\*Tests:\*\* `.*|- **Tests:** none|; s|- \*\*Status:\*\* open|- **Status:** invalid|' "$V/docs/intake-findings.md"
commit_item "$V" intake:testing-features "test(intake): fix"
v5 "$V" findings-evidence 1 "an invalid finding needs no evidence"

V=$(fresh v5-index)
sed -i '/glossary.md/d' "$V/docs/README.md"
commit_item "$V" intake:create-onboarding "docs(intake): onboarding"
v5 "$V" docs-index 0 "a doc missing from docs/README.md fails docs-index"

V=$(fresh v5-header)
sed -i 's|at intake/demo [0-9a-f]*\.|at intake/demo 0000000.|' "$V/docs/intake-findings.md"
commit_item "$V" intake:testing-features "test(intake): fix"
v5 "$V" docs-index 0 "a tracker base that differs from the checklist header fails docs-index"

V=$(fresh v5-dup)
s='Every request to the profile endpoint returns the profile whatever the caller owns today.'
sed -i "/^Body citing/a $s" "$V/docs/domain/features.md" "$V/docs/security/authorization.md"
commit_item "$V" intake:document-authorization "docs(intake): authorization"
v5 "$V" docs-pristine 0 "a sentence repeated in two docs fails docs-pristine"

V=$(fresh v5-related)
sed -i 's|^related: \[\]|related: [security/authorization.md]|' "$V/docs/domain/features.md"
commit_item "$V" intake:document-features "docs(intake): features"
v5 "$V" docs-pristine 0 "a one-sided related: link fails docs-pristine"

V=$(fresh v5-cite)
printf '\nAlso `app.py::nowhere`.\n' >>"$V/docs/domain/features.md"
commit_item "$V" intake:document-features "docs(intake): features"
v5 "$V" docs-pristine 0 "a citation whose symbol is gone fails docs-pristine"

V=$(fresh v5-beside)
git -C "$V" mv docs/domain/glossary.md docs/domain/glossary-intake.md
printf '# Our glossary\n\nOwner text, no audit.\n' >"$V/docs/domain/glossary.md"
sed -i 's|(domain/glossary.md)|(domain/glossary-intake.md)\n- [Owner glossary, owner-written](domain/glossary.md)|' "$V/docs/README.md"
commit_item "$V" intake:document-glossary "docs(intake): glossary beside the owner's"
set +e
out=$(score "$V")
set -e
if has "$out" docs-with-audit 1 && has "$out" docs-index 1 && has "$out" docs-pristine 1; then pass "an intake doc beside an owner doc counts, and the owner doc is never checked for style"; else fail "an intake doc beside an owner doc counts: $out"; fi

# An eval directory: eval.json names the gold set and each run; --eval/--run read every input from it
ED="$WORK/evaldir"
mkdir -p "$ED/runs/good"
cp "$WORK/good.jsonl" "$ED/runs/good/goal.jsonl"
cp "$WORK/gold.md" "$ED/gold.md"
printf '{"run": "good", "found": {"F-001": "F-001", "F-002": null, "MISSED-1": null, "ADDED-1": null}, "given": []}\n' >"$ED/runs/good/map.json"
git -C "$GOOD" bundle create -q "$ED/runs/good/repo.bundle" --all
python3 - "$ED" "$GOOD" "$(cat "$GOOD.start")" "$TEST_CMD" <<'PY'
import json, sys
d, repo, start, cmd = sys.argv[1:]
json.dump({"gold": "gold.md", "test_cmd": cmd, "runs": [{
    "run": "good", "repo": repo, "bundle": "runs/good/repo.bundle", "branch": "intake/demo", "start": start,
    "plugin": "abc1234", "transcripts": ["runs/good/goal.jsonl"], "accuracy": "runs/good/map.json"}]},
    open(f"{d}/eval.json", "w"))
PY
set +e
out=$(python3 "$EVAL" --eval "$ED" --run good 2>&1)
rc=$?
set -e
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q '"version": "abc1234"' && has "$out" final-message-evidence 1; then
    pass "--eval and --run read the repo, start, transcripts, plugin and test command from eval.json"
else
    fail "--eval and --run read every input from eval.json (exit $rc): $out"
fi
set +e
out=$(python3 "$EVAL" --eval "$ED" --run nope 2>&1)
rc=$?
set -e
if [ "$rc" -eq 2 ] && printf '%s' "$out" | grep -q 'no run "nope"'; then pass "an unknown run name exits 2"; else fail "an unknown run name exits 2 (got $rc): $out"; fi
set +e
out=$(python3 "$REPO_ROOT/scripts/eval_intake_baseline.py" "$ED" 2>&1)
rc=$?
set -e
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q '| good | `abc1234` |' && printf '%s' "$out" | grep -q '1 of 4'; then
    pass "the baseline re-scores every run in the eval directory against its own gold set"
else
    fail "the baseline re-scores every run in the eval directory (exit $rc): $out"
fi

# An owner docs/README.md: the intake index is docs/README-intake.md, and it lists the owner's README
V=$(fresh v5-owner-readme)
git -C "$V" mv docs/README.md docs/README-intake.md
printf '# Our docs\n\nOwner text.\n' >"$V/docs/README.md"
printf -- '- [Owner README, owner-written](README.md)\n' >>"$V/docs/README-intake.md"
commit_item "$V" intake:create-onboarding "docs(intake): index beside the owner README"
set +e
out=$(score "$V")
set -e
if has "$out" docs-index 1 && has "$out" docs-with-audit 1 && has "$out" docs-pristine 1; then pass "with an owner docs/README.md, docs/README-intake.md is the index"; else fail "with an owner docs/README.md, docs/README-intake.md is the index: $out"; fi
sed -i '/Owner README/d' "$V/docs/README-intake.md"
commit_item "$V" intake:create-onboarding "docs(intake): index drops the owner README"
set +e
out=$(score "$V")
set -e
if has "$out" docs-index 0 && printf '%s' "$out" | grep -q 'misses docs/README.md'; then pass "an intake index that leaves out the owner README fails docs-index"; else fail "an intake index that leaves out the owner README fails docs-index: $out"; fi

V=$(fresh v5-no-verified)
sed -i '/^verified:/d' "$V/docs/domain/features.md"
commit_item "$V" intake:document-features "docs(intake): features"
v5 "$V" docs-pristine 0 "an intake doc without verified: fails docs-pristine"

V=$(fresh v5-bad-verified)
sed -i 's/^verified: .*/verified: 0000000/' "$V/docs/domain/features.md"
commit_item "$V" intake:document-features "docs(intake): features"
v5 "$V" docs-pristine 0 "a verified: that is not a commit fails docs-pristine"

V=$(fresh v5-no-command)
sed -i '/^command:/d; /^sources:/d' "$V/docs/domain/features.md"
commit_item "$V" intake:document-features "docs(intake): features"
v5 "$V" docs-pristine 0 "an intake doc without command: or sources: fails docs-pristine"

# A bad start SHA is bad input
set +e
python3 "$EVAL" --repo "$GOOD" --start deadbeef >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 2 ]; then pass "an unknown start SHA exits 2"; else fail "an unknown start SHA exits 2 (got $rc)"; fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
