#!/usr/bin/env bash
#
# Test the plugin tree under plugin/, which the marketplace entry ships
# ("source": "./plugin").
#
# Usage: bash scripts/test-plugin-tree.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

PASS=0
FAIL=0
CLEANUP_DIRS=()

cleanup() {
    for dir in "${CLEANUP_DIRS[@]}"; do
        rm -rf "$dir"
    done
}
trap cleanup EXIT

# Helpers
pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

assert_exists() {
    if [ -e "$1" ]; then pass "$2"; else fail "$2 (missing)"; fi
}

assert_not_exists() {
    if [ ! -e "$1" ]; then pass "$2"; else fail "$2 (should not be shipped)"; fi
}

assert_exit_zero() {
    if [ "$1" -eq 0 ]; then pass "$2"; else fail "$2 (expected exit 0, got $1)"; fi
}

assert_equal() {
    if [ "$1" = "$2" ]; then pass "$3"; else fail "$3 (expected $2, got $1)"; fi
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO_ROOT/plugin"

echo "plugin tree"

assert_equal "$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['plugins'][0]['source'])" "$REPO_ROOT/.claude-plugin/marketplace.json" 2>/dev/null)" "./plugin" "the marketplace entry ships ./plugin"

# Shipped content
assert_exists "$OUT/.claude-plugin/plugin.json" "ships plugin.json"
assert_exists "$OUT/skills" "ships skills/"
assert_exists "$OUT/commands" "ships commands/"
assert_exists "$OUT/references/common-ground" "ships references/common-ground/"
# Claude Code names a command after its path, so this registers as /fullstack-dev-skills:common-ground
assert_exists "$OUT/commands/common-ground.md" "ships commands/common-ground.md"
assert_equal "$(find "$OUT/commands" -name 'COMMAND.md' | wc -l | tr -d ' ')" "0" "ships no commands named COMMAND"
assert_exists "$OUT/references/adapters/operations.md" "ships references/adapters/"
assert_exists "$OUT/references/specs/launch.md" "ships references/specs/"
assert_exists "$OUT/references/review/verifier.md" "ships references/review/"

# The workflow companion skill ships; its hooks live in the plugin's hooks.json (F11),
# so a resumed session keeps them, and the skill no longer declares copies that would run twice
GUARD="$OUT/skills/ticket-guard/SKILL.md"
assert_exists "$GUARD" "ships the ticket-guard companion skill"
if grep -q '^hooks:' "$GUARD" 2>/dev/null; then fail "ticket-guard declares no frontmatter hooks"; else pass "ticket-guard declares no frontmatter hooks"; fi

PHOOKS="$OUT/hooks/hooks.json"
assert_exists "$PHOOKS" "ships hooks/hooks.json"
for spec in "PreToolUse:pre-tool-use" "PostToolUse:post-tool-use" "Stop:stop" "SessionStart:session-start"; do
    event=${spec%%:*}; sub=${spec#*:}
    if python3 -c "import json,sys; h=json.load(open(sys.argv[1]))['hooks'].get(sys.argv[2],[]); c=[x['command'] for g in h for x in g['hooks']]; want='exec \"\$u\" run -q --no-project --python \">=3.11\" \"\${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz\" hook '+sys.argv[3]; gate='ticket-guard/marker.json\"; [ -f \"\$m\" ] || exit 0;'; sys.exit(0 if len(c)==1 and c[0].endswith(want) and gate in c[0] and c[0].index(gate) < c[0].index('command -v uv') else 1)" "$PHOOKS" "$event" "$sub" 2>/dev/null; then
        pass "hooks.json has one marker-gated $event hook"
    else
        fail "hooks.json has one marker-gated $event hook"
    fi
done
if python3 -c "import json,sys; h=json.load(open(sys.argv[1]))['hooks']; sys.exit(0 if h['SessionStart'][0].get('matcher')=='compact' and h['PreToolUse'][0].get('matcher')=='Write|Edit|MultiEdit|NotebookEdit|Bash' and h['PostToolUse'][0].get('matcher')=='Write|Edit|MultiEdit|NotebookEdit' else 1)" "$PHOOKS" 2>/dev/null; then
    pass "hooks.json keeps the compact and edit-tool matchers"
else
    fail "hooks.json keeps the compact and edit-tool matchers"
fi

hook_cmd() { python3 -c "import json,sys; print([x['command'] for g in json.load(open(sys.argv[1]))['hooks'][sys.argv[2]] for x in g['hooks']][0])" "$PHOOKS" "$1"; }

# Without a marker, every hook exits 0 at once and prints nothing
NOGIT=$(mktemp -d)
CLEANUP_DIRS+=("$NOGIT")
git -C "$NOGIT" init -q
for event in PreToolUse PostToolUse Stop SessionStart; do
    set +e
    hook_out=$(cd "$NOGIT" && CLAUDE_PROJECT_DIR="$NOGIT" bash -c "$(hook_cmd "$event")" </dev/null 2>&1)
    rc=$?
    set -e
    assert_exit_zero "$rc" "the $event hook exits 0 without a marker"
    assert_equal "$hook_out" "" "the $event hook prints nothing without a marker"
done

# The guard ships as one runnable file, without its source tree or tests
assert_exists "$OUT/runtime/guard.pyz" "ships the bundled guard"
assert_not_exists "$OUT/runtime/tests" "excludes the guard tests"
assert_not_exists "$OUT/runtime/ticket_guard" "excludes the guard source tree"

# A resumed session keeps its session id, so the plugin hook still denies a frozen-test edit
export CLAUDE_PLUGIN_ROOT="$OUT"
{
    sl() { python3 "$OUT/runtime/guard.pyz" "${@:2}"; }
    pre=$(hook_cmd PreToolUse)
    RES=$(mktemp -d)
    CLEANUP_DIRS+=("$RES")
    git -C "$RES" init -q
    git -C "$RES" -c user.email=t@t -c user.name=t commit -q --allow-empty -m base
    (cd "$RES" && sl guard marker start pilot T1 --mode goal >/dev/null 2>&1)
    mkdir -p "$RES/tests" && echo 'raise SystemExit(1)' > "$RES/tests/test_guard.py"
    (cd "$RES" && sl guard run red -- python3 tests/test_guard.py >/dev/null 2>&1 || true)
    edit() { printf '{"session_id":"%s","tool_name":"Edit","tool_input":{"file_path":"%s/tests/test_guard.py"},"cwd":"%s"}' "$1" "$RES" "$RES"; }
    (cd "$RES" && edit S1 | CLAUDE_PROJECT_DIR="$RES" bash -c "$pre" >/dev/null 2>&1 || true)
    resumed=$(cd "$RES" && edit S1 | CLAUDE_PROJECT_DIR="$RES" bash -c "$pre" 2>/dev/null || true)
    if printf '%s' "$resumed" | grep -q '"permissionDecision": "deny"'; then
        pass "a resumed session's hook still denies a frozen-test edit"
    else
        fail "a resumed session's hook still denies a frozen-test edit (got: $resumed)"
    fi
    other=$(cd "$RES" && edit S2 | CLAUDE_PROJECT_DIR="$RES" bash -c "$pre" 2>/dev/null || true)
    assert_equal "$other" "" "another session's hook stands down"
}

# With a ticket in progress and no uv on the hooks' PATH, every hook fails closed (exit 2, a reason on
# stderr) instead of exiting 127, which Claude Code treats as "nothing to block". A uv in ~/.local/bin
# is found when the PATH lacks it (Claude Code launched without the shell profile that adds it).
{
    NOUV=$(mktemp -d)
    CLEANUP_DIRS+=("$NOUV")
    mkdir -p "$NOUV/bin" "$NOUV/home"
    for tool in sh git cat; do ln -s "$(command -v "$tool")" "$NOUV/bin/$tool"; done
    for event in PreToolUse PostToolUse Stop SessionStart; do
        set +e
        err=$(cd "$RES" && edit S1 | env -i PATH="$NOUV/bin" HOME="$NOUV/home" CLAUDE_PROJECT_DIR="$RES" CLAUDE_PLUGIN_ROOT="$OUT" "$NOUV/bin/sh" -c "$(hook_cmd "$event")" 2>&1 >/dev/null)
        rc=$?
        set -e
        if [ "$rc" -eq 2 ] && printf '%s' "$err" | grep -q "uv not found"; then
            pass "the $event hook fails closed without uv while a ticket is in progress"
        else
            fail "the $event hook fails closed without uv while a ticket is in progress (rc $rc: $err)"
        fi
    done
    # A Stop hook that already blocked once (stop_hook_active true) lets the stop through, saying the
    # guard did not run, so a run that can't install uv doesn't loop on the block.
    stopin() { printf '{"session_id":"S1","hook_event_name":"Stop","stop_hook_active":%s,"cwd":"%s"}' "$1" "$RES"; }
    nouv_stop() { stopin "$1" | (cd "$RES" && env -i PATH="$NOUV/bin" HOME="$NOUV/home" CLAUDE_PROJECT_DIR="$RES" CLAUDE_PLUGIN_ROOT="$OUT" "$NOUV/bin/sh" -c "$(hook_cmd Stop)" 2>"$NOUV/err"); }
    for active in true " true"; do
        set +e
        out=$(nouv_stop "$active")
        rc=$?
        set -e
        if [ "$rc" -eq 0 ] && grep -q "uv not found" "$NOUV/err" && printf '%s' "$out" | python3 -c "import json,sys; m=json.load(sys.stdin)['systemMessage']; sys.exit(0 if 'uv not found' in m and 'did not run' in m else 1)"; then
            pass "a Stop hook without uv lets the stop through once it has blocked (\"stop_hook_active\":$active), and says the guard did not run"
        else
            fail "a Stop hook without uv lets the stop through once it has blocked (\"stop_hook_active\":$active), and says the guard did not run (rc $rc, out: $out, err: $(cat "$NOUV/err"))"
        fi
    done
    set +e
    nouv_stop " false" >/dev/null
    rc=$?
    set -e
    if [ "$rc" -eq 2 ] && grep -q "uv not found" "$NOUV/err"; then
        pass "a Stop hook without uv blocks when stop_hook_active is false"
    else
        fail "a Stop hook without uv blocks when stop_hook_active is false (rc $rc)"
    fi
    mkdir -p "$NOUV/home/.local/bin"
    ln -s "$(command -v uv)" "$NOUV/home/.local/bin/uv"
    mkdir -p "$NOUV/py" && ln -s "$(command -v python3)" "$NOUV/py/python3"
    found=$(cd "$RES" && edit S1 | env -i PATH="$NOUV/bin:$NOUV/py" HOME="$NOUV/home" CLAUDE_PROJECT_DIR="$RES" CLAUDE_PLUGIN_ROOT="$OUT" "$NOUV/bin/sh" -c "$pre" 2>/dev/null || true)
    if printf '%s' "$found" | grep -q '"permissionDecision": "deny"'; then
        pass "the hook finds uv in ~/.local/bin when the PATH lacks it"
    else
        fail "the hook finds uv in ~/.local/bin when the PATH lacks it (got: $found)"
    fi
    set +e
    (cd "$NOUV" && git init -q . && env -i PATH="$NOUV/bin" HOME="$NOUV/home" CLAUDE_PROJECT_DIR="$NOUV" "$NOUV/bin/sh" -c "$pre" </dev/null >/dev/null 2>&1)
    rc=$?
    set -e
    assert_exit_zero "$rc" "without a marker the hook needs no uv"
}
assert_exists "$OUT/LICENSE" "ships LICENSE"

# The main session runs the full suite itself at phase boundaries, not after every item
if grep -q "Full suite at phase boundaries" "$OUT/commands/intake.md" && grep -q "after \`document-codebase\`" "$OUT/commands/intake.md"; then pass "intake runs the full suite at phase boundaries"; else fail "intake runs the full suite at phase boundaries"; fi

# Parallel testing writers: each procedure says how it reports tracker edits in a batch; agents know the item report
for p in testing-features testing-authorization testing-owasp; do
    if grep -q "Parallel testing writers" "$OUT/references/intake/procedures/$p.md"; then pass "$p explains its batch tracker edits"; else fail "$p explains its batch tracker edits"; fi
done
for a in doc-writer test-writer security-prober architect; do
    if grep -q "item report" "$OUT/agents/$a.md"; then pass "agent $a ends with the item report"; else fail "agent $a ends with the item report"; fi
done

# The assumptions loop: spec:current, spec:diff and common-ground, with the ground file in the repo
for c in current diff; do assert_exists "$OUT/commands/spec/$c.md" "ships spec:$c"; done
assert_exists "$OUT/references/specs/assumptions.md" "ships the shared assumptions reference"
MENU="common-ground discovery:approve discovery:create intake spec:complete spec:create spec:current spec:diff spec:review spec:status spec:triage ticket:complete ticket:execute"
assert_equal "$(python3 -c "import json,sys; print(' '.join(sorted(json.load(open(sys.argv[1]))['commands'])))" "$OUT/.claude-plugin/plugin.json" 2>/dev/null)" "$MENU" "plugin.json maps exactly the 13 menu commands"
assert_equal "$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['workflowCount'])" "$REPO_ROOT/version.json" 2>/dev/null)" "13" "version.json counts all 13 commands, intake and common-ground included"
if grep -qF "plus \`intake\` and \`common-ground\`" "$REPO_ROOT/QUICKSTART.md"; then fail "QUICKSTART's command count already includes intake and common-ground"; else pass "QUICKSTART's command count already includes intake and common-ground"; fi
CG="$OUT/commands/common-ground.md"
if grep -q 'argument-hint: "\[--list\] \[--check\] \[--graph\] \[spec ...\]"' "$CG"; then pass "common-ground takes spec names"; else fail "common-ground takes spec names"; fi
if grep -rqE "~/.claude/common-ground/\{project" "$CG" "$OUT/references/common-ground" "$OUT/commands/common-ground.yaml"; then fail "the ground file lives in the repo"; else pass "the ground file lives in the repo"; fi
for f in "$CG" "$OUT/commands/spec/diff.md"; do
    if grep -q "references/specs/assumptions.md" "$f" 2>/dev/null; then pass "$(basename "$f") lists assumptions through the shared reference"; else fail "$(basename "$f") lists assumptions through the shared reference"; fi
done
if grep -q "guard.pyz\" current-state\|guard current-state" "$OUT/commands/spec/current.md" 2>/dev/null; then pass "spec:current compiles the current state"; else fail "spec:current compiles the current state"; fi
if grep -q -- "--roadmap" "$OUT/references/intake/procedures/create-system-description.md"; then fail "create-system-description drops --roadmap"; else pass "create-system-description drops --roadmap"; fi

# discovery:approve absorbs discovery:synthesize
assert_not_exists "$OUT/commands/discovery/synthesize.md" "ships no discovery:synthesize"
assert_equal "$(python3 -c "import json,sys; print('discovery:synthesize' in json.load(open(sys.argv[1]))['commands'])" "$OUT/.claude-plugin/plugin.json" 2>/dev/null)" "False" "plugin.json maps no discovery:synthesize"
if grep -q "synthesis.md" "$OUT/commands/discovery/approve.md" && ! grep -q "suggest \`discovery:synthesize" "$OUT/commands/discovery/approve.md"; then
    pass "discovery:approve synthesizes instead of refusing"
else
    fail "discovery:approve synthesizes instead of refusing"
fi

# The eight capability agents (decision 1); plugin agents ignore frontmatter hooks, so none carry any (decision 5a)
AGENTS="architect assumption-checker code-reader doc-writer reviewer security-prober test-writer verifier"
assert_equal "$(cd "$OUT/agents" 2>/dev/null && ls *.md | sed 's/\.md$//' | LC_ALL=C sort | tr '\n' ' ')" "$AGENTS " "ships exactly the eight agents"
fm() { sed -n '2,/^---$/p' "$OUT/agents/$1.md" 2>/dev/null | grep "^$2:" | cut -d: -f2- | sed 's/^ *//'; }
for a in $AGENTS; do
    assert_equal "$(fm "$a" name)" "$a" "agent $a names itself"
    if [ -n "$(fm "$a" description)" ]; then pass "agent $a has a description"; else fail "agent $a has a description"; fi
    case " $(fm "$a" tools | tr -d ',') " in *" Skill "*) pass "agent $a can load skills" ;; *) fail "agent $a can load skills" ;; esac
    if grep -q '^hooks:' "$OUT/agents/$a.md" 2>/dev/null; then fail "agent $a carries no hooks"; else pass "agent $a carries no hooks"; fi
done
# Intake goal runs write each item in one pass: the brief may turn a stop into a Checkpoint draft
for a in $AGENTS; do
    if grep -qF "In a goal run the brief may tell you not to stop there" "$OUT/agents/$a.md" 2>/dev/null && grep -qF "Checkpoint draft:" "$OUT/agents/$a.md"; then
        pass "agent $a records a Checkpoint draft when a goal-run brief says to keep going"
    else
        fail "agent $a records a Checkpoint draft when a goal-run brief says to keep going"
    fi
done
if grep -qF "A fact-pass brief may name no procedure" "$OUT/agents/code-reader.md" 2>/dev/null; then pass "code-reader takes a fact-pass brief with no procedure"; else fail "code-reader takes a fact-pass brief with no procedure"; fi
for a in code-reader assumption-checker; do
    case " $(fm "$a" tools | tr -d ',') " in *" Write "* | *" Edit "* | *" Bash "*) fail "agent $a only reads" ;; *) pass "agent $a only reads" ;; esac
done

# One intake command over the 21 procedures under references/intake/procedures/
PROCS="create-onboarding create-system-description document-analytics document-api document-authorization document-codebase document-config document-data-model document-features document-file-tree document-glossary document-integrations document-security document-user-flow document-user-model existing-docs testing-authorization testing-features testing-owasp testing-setup testing-user-flows"
assert_equal "$(cd "$OUT/references/intake/procedures" 2>/dev/null && ls *.md | sed 's/\.md$//' | LC_ALL=C sort | tr '\n' ' ')" "$PROCS " "ships the 21 intake procedures"
assert_exists "$OUT/commands/intake.md" "ships commands/intake.md"
assert_not_exists "$OUT/commands/intake" "ships no intake:* commands"
# git reads trailers only from the last paragraph: Claude Code appends Co-Authored-By after a blank line
if grep -q "no blank line between them" "$OUT/commands/intake.md"; then pass "intake keeps its Intake: trailer in the last paragraph"; else fail "intake keeps its Intake: trailer in the last paragraph"; fi
assert_equal "$(python3 -c "import json,sys; print(sorted(k for k in json.load(open(sys.argv[1]))['commands'] if k.startswith('intake')))" "$OUT/.claude-plugin/plugin.json" 2>/dev/null)" "['intake']" "plugin.json maps intake and no intake:* command"

# The intake flow: what the text tells the main session and the agents to do
has() { if grep -qF -- "$2" "$1" 2>/dev/null; then pass "$3"; else fail "$3"; fi; }
hasnt() { if grep -qF -- "$2" "$1" 2>/dev/null; then fail "$3"; else pass "$3"; fi; }
INTAKE="$OUT/commands/intake.md"
IREF="$OUT/references/intake"
# Goal runs: one agent per item runs discovery and write in one pass; attended runs keep pause and resume
has "$INTAKE" "Goal run: one pass" "intake runs a goal-run item in one pass"
has "$INTAKE" "Checkpoint draft:" "the goal-run agent reports its checkpoint draft"
has "$INTAKE" "Attended: discovery, then resume" "intake keeps pause and resume for attended runs"
hasnt "$INTAKE" "every checkpoint resumes an agent" "intake no longer resumes at every checkpoint"
has "$IREF/rules.md" "In a goal run there is no stop" "rules: a goal-run checkpoint doesn't stop the agent"
hasnt "$IREF/goal-prompt.md" "every checkpoint resumes an agent" "goal prompt no longer resumes at every checkpoint"
# The main session doesn't read the procedure: it takes the skills list with sed, and every brief names the path,
# where the intake eval opens the item's window (scripts/eval_intake_run.py, item_opens)
hasnt "$INTAKE" "**Read the procedure** in this session" "intake doesn't read the whole procedure in the main session"
has "$INTAKE" "sed -n '/^## Skills to load/,/^## /p'" "intake takes the procedure's skills list with sed"
has "$INTAKE" "Procedure: <plugin root>/references/intake/procedures/<procedure>.md" "the brief names the procedure path"
# Read-only work runs in parallel; writers stay one at a time (decision 5a)
has "$INTAKE" "### Read-only work in parallel" "intake runs read-only work in parallel"
has "$INTAKE" "start the next item's \`code-reader\` fact pass" "intake starts the next item's fact pass while the current item writes"
has "$INTAKE" "in one message" "intake starts independent code-readers in one message"
has "$INTAKE" "never a procedure path" "an early fact brief opens no eval window"
has "$INTAKE" "Start the next writer only after the current item is committed" "intake keeps one writer at a time"
has "$IREF/rules.md" "\`code-reader\` agents may run beside the writer" "rules: readers run beside the writer"
has "$IREF/procedures/document-authorization.md" "all in one message" "authorization's blind batches start together"
# A repo with no git remote has unknown visibility, so High security detail goes to the restricted file
has "$IREF/findings.md" "A repo with no git remote counts as unknown" "findings: no remote means visibility unknown"
# testing-owasp rates a dependency advisory by the reach shown in this app, not by the advisory's score
has "$IREF/procedures/testing-owasp.md" "With no exposure path shown in this app, the finding is Low" "testing-owasp: an advisory with no exposure path is Low"
# The findings-tracker item carries a fixed trailer; the eval still sees no `intake:<cmd>` item on its line
TRACKER_ITEM=$(grep -F -- '- [ ] Start the findings tracker:' "$IREF/checklist.md")
case "$TRACKER_ITEM" in *'commit trailer `Intake: intake:findings-tracker`') pass "the tracker item names its fixed trailer" ;; *) fail "the tracker item names its fixed trailer" ;; esac
case "$TRACKER_ITEM" in *'`intake:'*) fail "the tracker item stays a no-procedure item for the eval" ;; *) pass "the tracker item stays a no-procedure item for the eval" ;; esac
has "$INTAKE" "the trailer its checklist line names" "intake commits a no-procedure item with the trailer its line names"
has "$IREF/goal-prompt.md" "the trailer its checklist line names" "the goal prompt commits a no-procedure item with the trailer its line names"
for p in $PROCS; do
    if [ "$(grep -c '^## Skills to load$' "$IREF/procedures/$p.md")" = 1 ]; then pass "$p has one Skills to load heading"; else fail "$p has one Skills to load heading"; fi
done
# A lean main-session step: the agent runs the item's checks and drafts the note and commit message;
# the main session reviews the diff, reruns a check only with a reason, pastes the note and commits
has "$IREF/rules.md" "## The item report" "rules: the agent ends with a fixed item report"
for k in "Changed files:" "Checks:" "Checklist note:" "Commit message:"; do
    has "$IREF/rules.md" "$k" "rules: the item report carries $k"
done
has "$INTAKE" "the item report in rules.md" "the brief asks for the item report"
has "$INTAKE" "Rerun a check the agent ran only when" "intake reruns an agent's check only with a reason"
hasnt "$INTAKE" "and the project's test command for a testing item, and read the fresh output" "intake no longer reruns every item's checks"
has "$INTAKE" "Paste the drafted note" "intake pastes the agent's drafted note"
has "$INTAKE" "Agents never commit" "agents still never commit"
hasnt "$IREF/goal-prompt.md" "run-and-verify phase, then \`<test:all command>\`" "the goal prompt doesn't rerun test:all after every item"
has "$IREF/goal-prompt.md" "counted from docs/intake-findings.md" "the final report counts findings by severity from the tracker, not from memory"
# Parallel testing writers: the three Phase 3 items after testing-setup write at once; the command assigns ids
has "$INTAKE" "### Parallel testing writers" "intake runs the three testing writers in parallel"
has "$INTAKE" "\`F-901\`" "parallel writers use provisional finding ids"
has "$INTAKE" "in checklist order (\`testing-features\`, \`testing-authorization\`, \`testing-owasp\`)" "intake assigns ids and commits in checklist order"
has "$INTAKE" "Fall back to serial" "intake falls back to serial on a shared file"
has "$INTAKE" "each brief names its own procedure path" "each parallel brief names its procedure for the eval"
has "$IREF/rules.md" "except the three parallel testing items" "rules: writers run one at a time except the testing trio"
has "$IREF/findings.md" "the \`intake\` command writes their tracker edits" "findings: the command writes the parallel items' tracker edits"

# Repo-only content stays out
for path in .claude-plugin/marketplace.json CLAUDE.md site docs scripts assets research specs evals .serena .github version.json pyproject.toml; do
    assert_not_exists "$OUT/$path" "excludes $path"
done

# Only these top-level entries ship
assert_equal "$(cd "$OUT" 2>/dev/null && ls -A | LC_ALL=C sort | tr '\n' ' ')" ".claude-plugin LICENSE README.md agents commands hooks references runtime skills " "ships only the plugin's own entries"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
