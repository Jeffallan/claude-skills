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
assert_contains "$CMD/spec/review.md" "A rollup and no \`<spec-name>-rv-<n>\` fix ticket in the plan: the last review is still waiting for triage" "spec:review takes an untriaged rollup straight to triage, not a new panel or a recheck"

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

echo "spec:complete docs:verify: the diff's stale doc claims, fixed one at a time on the owner's yes"
COMPLETE="$CMD/spec/complete.md"
step2=$(sed -n '/^## Step 2: Completion commit$/,/^## Step 3: PR$/p' "$COMPLETE")
verify=$(printf '%s\n' "$step2" | grep -F '**Docs verify (`docs:verify`)**' || true)
if [ -n "$verify" ]; then pass "spec:complete Step 2 has the docs:verify item"; else fail "spec:complete Step 2 has the docs:verify item"; fi
for s in "README" "docs/" "git diff" "fullstack-dev-skills:code-reader" "fullstack-dev-skills:spec-miner" "in one message" \
         "| Doc | Claim | Verdict | Evidence |" "\`holds\`" "\`stale\`" "\`unknown\`" "review/docs-verify.md" \
         "one at a time" "AskUserQuestion" "never edits a doc without" "<specsRoot>"; do
    case "$verify" in *"$s"*) pass "docs:verify names $s" ;; *) fail "docs:verify names $s" ;; esac
done
# it runs after the docs-affected item, so it checks the docs that item already updated
dv=$(printf '%s\n' "$step2" | grep -n 'docs:verify' | head -1 | cut -d: -f1 || true)
da=$(printf '%s\n' "$step2" | grep -n 'guard docs-affected' | head -1 | cut -d: -f1 || true)
if [ -n "$dv" ] && [ -n "$da" ] && [ "$dv" -gt "$da" ]; then pass "docs:verify runs after docs-affected"; else fail "docs:verify runs after docs-affected"; fi
assert_contains "$COMPLETE" "| Docs verify |" "the completion report has a Docs verify row"
assert_contains "$CMD/spec/complete.yaml" "review/docs-verify.md" "complete.yaml lists the docs:verify report"
assert_contains "$REF/specs/layout.md" "| \`review/docs-verify.md\` | \`spec:complete\`" "the spec layout lists who writes review/docs-verify.md"
assert_contains "$PLUGIN/../docs/workflow/spec-complete.md" "docs:verify" "the spec:complete page explains docs:verify"
assert_contains "$PLUGIN/../docs/workflow/spec-complete.md" "| Doc | Claim | Verdict | Evidence |" "the spec:complete page shows the docs:verify table"
assert_contains "$PLUGIN/../docs/WORKFLOW_COMMANDS.md" "docs:verify" "WORKFLOW_COMMANDS mentions docs:verify"
step7=$(sed -n '/^## Step 7: Close tickets and the group$/,/^## Report$/p' "$COMPLETE")
if printf '%s\n' "$step7" | grep -qF "filed them in Step 2"; then pass "Step 7 points at Step 2 for the text tracker's follow-ups"; else fail "Step 7 points at Step 2 for the text tracker's follow-ups"; fi

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
assert_contains "$OPS" "a ticket skill committed in the repo (\`.claude/skills/\`)" "a ticket skill counts only when the repo commits it"
assert_contains "$OPS" "Skills and MCP servers the session loaded from elsewhere" "the wizard ignores session-only skills and servers for the recommendation"

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
after_last=$(sed -n '/^## After the last item$/,/^## Rules$/p' "$CMD/intake.md")
final_report=$(sed -n '/^<final_report>$/,/^<\/final_report>$/p' "$REF/intake/goal-prompt.md")
for s in "blocked count" "each blocked layer"; do
    if printf '%s\n' "$after_last" | grep -qF "$s"; then pass "intake's final report states the suite's $s"; else fail "intake's final report states the suite's $s"; fi
    if printf '%s\n' "$final_report" | grep -qF "$s"; then pass "the goal prompt's final report states the suite's $s"; else fail "the goal prompt's final report states the suite's $s"; fi
done

assert_contains "$REF/intake/rules.md" "names its finding id in the row itself" "rules: a table-driven row names its finding id, never through a default"
# shared caches outside the repo are never pruned; a browser install skips Playwright's cleanup
assert_contains "$REF/intake/rules.md" "never deletes or prunes a shared cache outside the repo" "rules: intake never prunes a shared cache"
assert_contains "$REF/intake/procedures/testing-setup.md" "PLAYWRIGHT_SKIP_BROWSER_GC=1" "testing-setup: browser installs skip Playwright's cleanup"
# a matrix cell that can't apply skips with an n/a: reason, not as a bug test
assert_contains "$REF/intake/procedures/testing-authorization.md" "skips with an \`n/a: <reason>\` message" "testing-authorization: n/a cells skip with an n/a: reason"
echo "command text agrees with itself"
assert_not_contains "$CMD/spec/create.md" "No tracker write outside Step 6" "spec:create's rules name Step 5, where its tracker writes are"
assert_contains "$CMD/spec/create.md" "No tracker write outside Step 5" "spec:create keeps tracker writes in Step 5"
if grep -qE '[^ ] 1\. Read `\.claude/workflow-config\.json`' "$CMD/spec/create.md"; then fail "spec:create's Setup list starts on its own line"; else pass "spec:create's Setup list starts on its own line"; fi
step6=$(sed -n '/^## Step 6: Owner triage$/,/^## Recheck$/p' "$CMD/spec/review.md")
for s in "confirmed, unresolved or rejected" "fix (one of the four types below)" "for a rejected row, accept the rejection"; do
    if printf '%s\n' "$step6" | grep -qF "$s"; then pass "spec:review triage asks about every row the gate can block on ($s)"; else fail "spec:review triage asks about every row the gate can block on ($s)"; fi
done
assert_not_contains "$CMD/discovery/approve.md" "routed items to research (\`sources/\` holds files)" "discovery:approve's empty-sources stop is reachable"
assert_contains "$CMD/discovery/create.md" "**Status:** Proposed | Research | Ready for approval | Tickets created" "discovery:create's status list holds the status discovery:approve sets"
flow=$(sed -n '/^```mermaid$/,/^```$/p' "$CMD/intake.md")
case "$flow" in *"testing-features, testing-user-flows"*) fail "intake's flow runs testing-user-flows after the parallel batch" ;; *) pass "intake's flow runs testing-user-flows after the parallel batch" ;; esac
case "$flow" in *"--> uf[testing-user-flows"*) pass "intake's flow has a serial testing-user-flows node" ;; *) fail "intake's flow has a serial testing-user-flows node" ;; esac
assert_not_contains "$REF/intake/procedures/document-codebase.md" "This is the first item of the intake checklist" "document-codebase doesn't claim the first checklist item"
owasp_when=$(sed -n '/^## When to use$/,/^## Skills to load$/p' "$REF/intake/procedures/testing-owasp.md")
case "$owasp_when" in *"after \`intake:testing-setup\`, \`intake:testing-authorization\`"*) fail "testing-owasp runs beside testing-authorization, not after it" ;; *) pass "testing-owasp runs beside testing-authorization, not after it" ;; esac
assert_contains "$REF/intake/checklist.md" "One item per command, in order, except the parallel testing batch" "the checklist's in-order rule names the parallel testing batch"
assert_contains "$CMD/spec/current.md" "(\`wired\`, \`built, not wired\`, \`planned\`)" "spec:current quotes its three component statuses"
assert_contains "$CMD/ticket/execute.md" "added in the diff" "ticket:execute says docs-affected lists the docs the diff adds"

assert_not_contains "$CMD/spec/diff.md" "Run \`spec:current\` first, or" "spec:diff sends a repo with no description to intake, since spec:current stops too"
assert_not_contains "$REF/specs/templates/goal-prompt.md" "<pin>" "the goal-prompt template asks for no pin it doesn't hold"
assert_contains "$CMD/spec/triage.yaml" "a grouping" "triage.yaml's scope names the grouping form"
assert_not_contains "$CMD/ticket/complete.yaml" "ran in this session" "ticket:complete's id is optional while a marker exists, from any session"
assert_contains "$REF/intake/procedures/testing-setup.md" "plus the aggregate \`test:all\`" "testing-setup names the test:all script the checklist requires"

echo "common-ground is attended only"
CGC="$CMD/common-ground.md"
cg_guard=$(sed -n '/^## Unattended guard$/,/^---$/p' "$CGC")
for s in "BLOCKED: common-ground needs the owner" "wrong-session stop" "\`--list\`" "write nothing"; do
    if printf '%s\n' "$cg_guard" | grep -qF -- "$s"; then pass "common-ground's guard says $s"; else fail "common-ground's guard says $s"; fi
done
assert_contains "$CMD/common-ground.yaml" "unattended: false" "common-ground.yaml marks it attended only"
assert_contains "$CMD/discovery/create.yaml" "unattended: true" "discovery/create.yaml runs under a goal (it skips the interviews), as WORKFLOW_COMMANDS says"
attended_row=$(grep -F '| Attended-only commands |' "$REF/specs/unattended.md")
case "$attended_row" in *'`common-ground`'*) pass "unattended.md lists common-ground as attended only" ;; *) fail "unattended.md lists common-ground as attended only" ;; esac
assert_contains "$PLUGIN/../docs/workflow/common-ground.md" "BLOCKED: common-ground needs the owner" "the common-ground page explains its goal-run stop"

echo "assumptions.md extracts every present-tense claim and every uses-relation"
ASM="$REF/specs/assumptions.md"
assert_contains "$ASM" "Every sentence that says how the system works now is an assumption" "assumptions.md: present-tense claims are always listed"
assert_contains "$ASM" "list \"A can reach B\" as its own \`interface\` assumption" "assumptions.md: a uses-relation gets its own reach row"
assert_contains "$ASM" "When an open finding in \`docs/current-state.json\` touches the assumption, name it in **Checked against** as well" "assumptions.md: an open finding that touches an assumption is cited beside its code"
assert_contains "$CMD/spec/diff.md" "Print the banner line exactly as written" "spec:diff prints its plan banner verbatim"

echo "an assumption the spec relies on but neither exists nor gets built is a conflict"
rule="relies on something that doesn't exist and the spec doesn't build it, the verdict is \`conflicts\`"
assert_contains "$CGC" "$rule" "common-ground: unbuilt reliance is a conflict"
assert_contains "$PLUGIN/agents/assumption-checker.md" "$rule" "assumption-checker: unbuilt reliance is a conflict"

echo "common-ground reports every assumption as its own row with a bare verdict"
cg_report=$(sed -n '/^4\. \*\*Report\*\*/,/^The agent only reads/p' "$CGC")
for s in "every assumption as its own row" "holds included" "never group or elide" "exactly one of \`holds\`, \`conflicts\` or \`unknown\`" "a caveat goes in the Fix or Source column"; do
    if printf '%s\n' "$cg_report" | grep -qF -- "$s"; then pass "common-ground's report step says $s"; else fail "common-ground's report step says $s"; fi
done

echo "common-ground briefs the assumption-checker without verdict hints"
cg_check=$(sed -n '/^3\. \*\*Check them\.\*\*/,/^4\. \*\*Report\*\*/p' "$CGC")
s="carries only the assumption list and the checker's fixed rules, never hints about what a verdict should be"
if printf '%s\n' "$cg_check" | grep -qF -- "$s"; then pass "common-ground's check step keeps verdict hints out of the brief"; else fail "common-ground's check step keeps verdict hints out of the brief"; fi

echo "common-ground --graph lives in the index, so a regenerated ground file keeps it"
FM="$REF/common-ground/file-management.md"
schema=$(sed -n '/^### Schema$/,/^### Field Definitions$/p' "$FM")
case "$schema" in *'"graph": {'*'"mermaid":'*) pass "the index schema has a graph field" ;; *) fail "the index schema has a graph field" ;; esac
assert_contains "$FM" "| \`graph\` | object or null |" "the field table defines graph"
assert_contains "$FM" "renders \`graph\` as its \`## Reasoning Graph\` section" "regenerating COMMON-GROUND.md renders the stored graph"
graph_mode=$(sed -n '/^## --graph Mode$/,/^### Output Format$/p' "$CMD/common-ground.md")
for s in "ground.index.json" "\`graph\`" "regenerate"; do
    if printf '%s\n' "$graph_mode" | grep -qF -- "$s"; then pass "--graph stores the graph through the index ($s)"; else fail "--graph stores the graph through the index ($s)"; fi
done
if printf '%s\n' "$graph_mode" | grep -qF "Update \`COMMON-GROUND.md\` with embedded"; then fail "--graph never edits COMMON-GROUND.md directly"; else pass "--graph never edits COMMON-GROUND.md directly"; fi
assert_contains "$REF/common-ground/reasoning-graph.md" "stored in \`ground.index.json\`" "reasoning-graph.md keeps the graph in the index"

echo "spec:triage confirms each tracker write itself when no ask rules exist yet"
tri5=$(sed -n '/^## Step 5: Write$/,/^## /p' "$CMD/spec/triage.md" | sed '$d')
for s in ".claude/settings.json" "first triage" "its own \`AskUserQuestion\`" "before making it"; do
    if printf '%s\n' "$tri5" | grep -qF -- "$s"; then pass "spec:triage Step 5 handles missing ask rules ($s)"; else fail "spec:triage Step 5 handles missing ask rules ($s)"; fi
done
assert_contains "$PLUGIN/../docs/workflow/spec-triage.md" "its own question" "the spec:triage page says a first triage asks before each tracker write"

echo "command metadata matches what the commands do"
EXY="$CMD/ticket/execute.yaml"
if sed -n '/^requires:/,/^status:/p' "$EXY" | grep -qF "ticketing"; then fail "ticket:execute requires no tracker"; else pass "ticket:execute requires no tracker"; fi
assert_contains "$EXY" "adapter-operations: []" "ticket:execute uses no adapter operation"
assert_contains "$PLUGIN/../docs/workflow/workflow-definition-schema.md" "\`repeat\` and \`run_once\` count different things" "the schema explains repeat beside run_once"
grouping='argument-hint: "[ticket-ids | tracker-query | discovery:<topic> | grouping]"'
assert_contains "$CMD/spec/triage.md" "$grouping" "spec:triage's hint names the grouping form"
assert_contains "$CMD/spec/triage.yaml" "$grouping" "triage.yaml's hint names the grouping form"

echo "document-authorization's batch hand-back is an expected stop"
assert_contains "$REF/intake/procedures/document-authorization.md" "This stop is expected, in a goal run too" "document-authorization says its batch hand-back stop is expected and resumed"

echo "spec:current moves the description's verified: to the commit it was checked against"
cur2=$(sed -n '/^## Step 2: Update the system description$/,/^## Step 3: Compile the current state$/p' "$CMD/spec/current.md")
for s in "\`verified:\`" "git rev-parse --short HEAD" "guard docs-check"; do
    if printf '%s\n' "$cur2" | grep -qF -- "$s"; then pass "spec:current Step 2 bumps verified: ($s)"; else fail "spec:current Step 2 bumps verified: ($s)"; fi
done
assert_contains "$PLUGIN/../docs/workflow/spec-current.md" "\`verified:\`" "the spec:current page says the fold moves verified:"

echo "docs:verify also checks a doc's absolute statements against the diff"
verify=$(sed -n '/^## Step 2: Completion commit$/,/^## Step 3: PR$/p' "$CMD/spec/complete.md" | grep -F '**Docs verify (`docs:verify`)**' || true)
for s in "broad claims" "describe the components the diff touches" "none, no, only, never, always, exists" "calls no remote third-party service" "same table and verdicts"; do
    case "$verify" in *"$s"*) pass "docs:verify's broad-claims pass names $s" ;; *) fail "docs:verify's broad-claims pass names $s" ;; esac
done
assert_contains "$PLUGIN/../docs/workflow/spec-complete.md" "absolute statements" "the spec:complete page explains the broad-claims pass"

echo "security findings never commit reproduction detail, at any severity, in any repo"
FINDINGS="$REF/intake/findings.md"
RESTRICTED="docs/intake-findings-restricted.md"
assert_contains "$FINDINGS" "never goes in a committed file, at any severity, in any repo, private ones included" "findings: security reproduction detail never goes in a committed file"
assert_contains "$FINDINGS" "They are the exposure that remains" "findings: the committed tests are named as the remaining exposure"
assert_not_contains "$FINDINGS" "Private to the owner's team" "findings: no private-repo exception"
assert_not_contains "$FINDINGS" "gh repo view --json visibility" "findings: no visibility check"
for f in agents/security-prober.md commands/intake.md references/intake/access-control.md references/intake/procedures/testing-authorization.md references/intake/procedures/testing-owasp.md references/intake/procedures/document-security.md references/intake/procedures/document-authorization.md; do
    assert_contains "$PLUGIN/$f" "$RESTRICTED" "$f sends security reproduction detail to the restricted file"
done
assert_not_contains "$PLUGIN/agents/security-prober.md" "only in the test and the findings tracker" "security-prober no longer puts reproduction detail in the tracker"
assert_contains "$PLUGIN/../docs/INTAKE.md" "at any severity" "the Intake guide states the rule for every security finding"

echo "every attended-only guard ends with the BLOCKED line followed by git status --short (unattended.md)"
while IFS= read -r line; do
    f=${line%%:*}
    case "$line" in *'git status --short'*) pass "$(basename "$f") guard prints git status after BLOCKED" ;; *) fail "$(basename "$f") guard prints git status after BLOCKED" ;; esac
done < <(grep -rn 'needs the owner`' "$PLUGIN/commands")

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
