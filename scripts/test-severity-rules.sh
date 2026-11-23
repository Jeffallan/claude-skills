#!/usr/bin/env bash
#
# Test that the intake severity rubric carries the rules the v0.5.0 holdout
# runs showed it needs: four levels with a gated Critical, a re-rate rule,
# a change rated like a read, a Medium row for a field withheld from your own
# role, a closed list of downgrades, floors, data classes, over-rating guards,
# a Severity line that names its row, and synthetic anchors at each boundary.
# Every procedure and the intake command read the rubric before rating.
#
# Usage: bash scripts/test-severity-rules.sh
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
IREF="$PLUGIN/references/intake"
SEV="$IREF/severity.md"
FIND="$IREF/findings.md"

echo "the rubric file and its levels"
if [ -f "$SEV" ]; then pass "references/intake/severity.md exists"; else fail "references/intake/severity.md exists"; fi
for level in Critical High Medium Low; do
    assert_contains "$SEV" "| $level |" "severity.md defines $level"
done
assert_not_contains "$SEV" "Informational" "severity.md has no Informational level"
assert_contains "$SEV" "least-privileged actor" "Critical needs the least-privileged actor"
assert_contains "$SEV" "anyone who can register" "Critical names self-registration as the least privilege"
assert_contains "$SEV" "Reading another account's Sensitive data is High, not Critical" "a cross-account Sensitive read stays High"
assert_contains "$SEV" "rate it High and name the missing fact" "an uncited Critical claim is High"
for fact in "actor" "action" "target" "data class"; do
    assert_contains "$SEV" "the $fact" "the Critical gate cites the $fact"
done

echo "re-rating"
assert_not_contains "$FIND" "Severity is the finder's first guess; the owner adjusts it at close-out." "the first-guess line is gone"
assert_contains "$SEV" "re-rates it in the same commit" "a later procedure re-rates in the same commit"
assert_contains "$SEV" "says so in its item report" "a re-rate is reported in the item report"
assert_contains "$SEV" "The owner can still adjust any rating at close-out" "the owner still adjusts at close-out"
assert_contains "$SEV" "An Open question asking the owner to re-rate is not a re-rate" "an Open question never stands in for a re-rate"
assert_contains "$FIND" "| A finding's \`Severity:\` line after later evidence changes its reach |" "Who writes what has a re-rate row"
assert_contains "$CMD/intake.md" "its Severity: line" "parallel testers report a re-rate as a tracker edit"

echo "rows and rules"
assert_contains "$SEV" "Changing another account's Sensitive data rates the same as reading it" "a change rates like a read"
assert_contains "$SEV" "reads a field withheld from its own role" "Medium covers a field withheld from your own role"
assert_contains "$SEV" "through a search, filter or error" "the withheld-field row covers side channels"
assert_contains "$SEV" "Only these lower a rating" "the downgrade list is closed"
assert_contains "$SEV" "one level in total" "downgrades lower one level at most"
assert_contains "$SEV" "repeated guesses" "effort and repeated guesses are named as not a downgrade"
assert_contains "$SEV" "A link the app sent to the person holding it is not a leaked secret" "an own link is not a leaked secret"
assert_contains "$SEV" "## Floors" "floors section"
for class in Secret Sensitive Ordinary Public; do
    assert_contains "$SEV" "| $class |" "data class $class"
done
assert_contains "$SEV" "visit or appointment reasons" "Sensitive names visit or appointment reasons as health data"
assert_contains "$SEV" "Rate only what the code is shown to allow" "guard: rate only what the code allows"
assert_contains "$SEV" "every link" "guard: a chain needs evidence for every link"
assert_contains "$SEV" "An unknown only lowers" "guard: unknowns only lower"
assert_contains "$SEV" "Rate the reach you showed" "advisories rate by the reach shown"

echo "the Severity line names its row"
assert_contains "$FIND" "Row: <row>; <adjustment, or no adjustment>" "the finding template names the row and adjustment"
assert_contains "$SEV" "names the table row" "severity.md asks the Severity line to name its row"

echo "anchors"
anchors=$(sed -n '/^## Anchors$/,/^## /p' "$SEV" 2>/dev/null || true)
for level in Critical High Medium Low; do
    if printf '%s\n' "$anchors" | grep -qF "| $level |"; then pass "an anchor at $level"; else fail "an anchor at $level"; fi
done
if printf '%s\n' "$anchors" | grep -qiE 'clinic|patient|appointment|visit|doctor|medical'; then
    fail "anchors use no clinic, patient or appointment example"
else
    pass "anchors use no clinic, patient or appointment example"
fi

echo "owner decisions on calibration gaps"
critical_row=$(grep -F '| Critical |' "$SEV" | head -1 || true)
case "$critical_row" in *"deletes data of every account with no way back"*) pass "G1 Critical covers wiping every account" ;; *) fail "G1 Critical covers wiping every account" ;; esac
assert_contains "$SEV" "changed after the last backup counts as lost" "G2 data after the last backup counts as lost"
assert_contains "$SEV" "names the backup config" "G2 the finding names the backup config"
assert_contains "$SEV" "funds actually leave or are taken (a charge, refund or payout)" "G3 moving real money means funds leave"
assert_contains "$SEV" "fixed before any money moves is Medium" "G3 a wrong stored amount fixed first is Medium"
assert_contains "$SEV" "fitness, diet and sleep logs" "G4 fitness, diet and sleep logs are Sensitive"
assert_contains "$SEV" "every account is staff" "G5 no staff downgrade when every account is staff"
assert_contains "$SEV" "powers that were taken away" "G6 no staff downgrade for removed powers"
high_row=$(grep -F '| High |' "$SEV" | head -1 || true)
case "$high_row" in *"one account's Secret"*"a secret the app holds"*) pass "G7 High covers one account's Secret or an app-held secret" ;; *) fail "G7 High covers one account's Secret or an app-held secret" ;; esac
assert_contains "$SEV" "An email address or username counts as a known identifier" "G8 an email is a known identifier"
assert_contains "$SEV" "when an admin's identifier is shown or guessable" "G8 naming an admin makes takeover Critical"
assert_contains "$SEV" "Changing another account's login email" "G9 changing a login email is acting as the account"
assert_contains "$SEV" "A floor applies only when its outcome lands" "G10 a floor needs its outcome to land"
assert_contains "$SEV" "The no-way-back floor holds after the secret and unguessable-target adjustments" "G11 data-loss floor beats those downgrades"
assert_contains "$SEV" "Giving another account a higher role rates as gaining it" "G12 granting a role rates as gaining it"
assert_contains "$SEV" "A defect staff hit in normal use is rated by its harm" "G13 no staff downgrade for a defect in normal use"
assert_contains "$SEV" "salary and employment contracts" "G14 salary and contracts are Sensitive"
assert_contains "$SEV" "Changing another account's Public data rates as changing Ordinary data" "G15 changing Public data is Medium"

echo "the re-rate note field"
assert_contains "$IREF/rules.md" "Re-rated: <F-0xx <old> -> <new> (<reason>), or none>" "rules: the checklist note carries a Re-rated field"
assert_contains "$SEV" "\`Re-rated: F-0xx <old> -> <new> (<reason>)\`" "severity.md names the Re-rated field"
assert_contains "$FIND" "\`Re-rated:\`" "Who writes what names the Re-rated field"

echo "owner decisions on calibration residuals"
assert_contains "$SEV" "A defect that deletes data of every account with no way back, with no actor, rates as if the least-privileged actor did it" "R1 an actorless wipe of every account is Critical"
assert_contains "$SEV" "Medium when the app can correct it with a refund or credit, High when it cannot" "R2 a wrong amount on a real order depends on correction"
assert_contains "$SEV" "any role above the lowest counts as staff" "R3 roles above the lowest are staff in an all-staff app"
assert_contains "$SEV" "Plans someone writes for others are Ordinary" "R4 plans written for others are Ordinary"
assert_contains "$SEV" "Deleting one kind of data from every account (all trashed items, all attachments) counts as data of every account" "R5 a subset of every account is still every account"

echo "prose"
for f in "$SEV" "$FIND"; do
    if grep -qF "—" "$f"; then fail "$(basename "$f") has no em dash"; else pass "$(basename "$f") has no em dash"; fi
done
if grep -nE '(^|[.!?] )(And|But|So|Or|Yet) ' "$SEV" >/dev/null; then
    fail "severity.md starts no sentence with a conjunction"
else
    pass "severity.md starts no sentence with a conjunction"
fi

echo "the scale reaches every place that names it"
assert_not_contains "$FIND" "| High / Medium / Low |" "the Summary row drops the three-level scale"
assert_not_contains "$FIND" "<High / Medium / Low>" "the finding template drops the three-level scale"
n=$(grep -cF "Critical / High / Medium / Low" "$FIND" || true)
if [ "$n" -ge 2 ]; then pass "the Summary row and finding template name four levels"; else fail "the Summary row and finding template name four levels (found $n)"; fi
assert_contains "$FIND" "references/intake/severity.md" "findings.md points to severity.md"
for f in "$FIND" "$IREF/goal-prompt.md" "$CMD/intake.md"; do
    assert_contains "$f" "Critical or High security finding" "$(basename "$f") leads with Critical or High security findings"
done
assert_contains "$IREF/goal-prompt.md" "Critical, High, Medium and Low" "the goal-run final report counts four levels"
assert_contains "$CMD/intake.md" "Critical, High, Medium and Low" "the intake final report counts four levels"
assert_not_contains "$IREF/procedures/testing-authorization.md" "Broken access control is High." "no category sets a level"
assert_contains "$IREF/procedures/testing-authorization.md" "references/intake/severity.md" "testing-authorization rates by severity.md"
assert_contains "$IREF/procedures/testing-owasp.md" "\`severity.md\`" "testing-owasp rates advisories by severity.md"

echo "who reads the rubric"
assert_contains "$CMD/intake.md" "\${CLAUDE_PLUGIN_ROOT}/references/intake/severity.md" "the intake session reads severity.md before the first item"
brief=$(sed -n '/^### The brief$/,/^## After the last item$/p' "$CMD/intake.md")
if printf '%s\n' "$brief" | grep -qF "severity.md"; then pass "every agent brief names severity.md"; else fail "every agent brief names severity.md"; fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
