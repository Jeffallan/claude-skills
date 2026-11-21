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
    if python3 -c "import json,sys; h=json.load(open(sys.argv[1]))['hooks'].get(sys.argv[2],[]); c=[x['command'] for g in h for x in g['hooks']]; want='ticket-guard/marker.json\"; [ -f \"\$m\" ] || exit 0; exec uv run -q --no-project --python \">=3.11\" \"\${CLAUDE_PLUGIN_ROOT}/runtime/guard.pyz\" hook '+sys.argv[3]; sys.exit(0 if len(c)==1 and c[0].endswith(want) else 1)" "$PHOOKS" "$event" "$sub" 2>/dev/null; then
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
assert_exists "$OUT/LICENSE" "ships LICENSE"

# The assumptions loop: spec:current, spec:diff and common-ground, with the ground file in the repo
for c in current diff; do assert_exists "$OUT/commands/spec/$c.md" "ships spec:$c"; done
assert_exists "$OUT/references/specs/assumptions.md" "ships the shared assumptions reference"
MENU="common-ground discovery:approve discovery:create intake spec:complete spec:create spec:current spec:diff spec:review spec:status spec:triage ticket:complete ticket:execute"
assert_equal "$(python3 -c "import json,sys; print(' '.join(sorted(json.load(open(sys.argv[1]))['commands'])))" "$OUT/.claude-plugin/plugin.json" 2>/dev/null)" "$MENU" "plugin.json maps exactly the 13 menu commands"
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
for a in code-reader assumption-checker; do
    case " $(fm "$a" tools | tr -d ',') " in *" Write "* | *" Edit "* | *" Bash "*) fail "agent $a only reads" ;; *) pass "agent $a only reads" ;; esac
done

# One intake command over the 21 procedures under references/intake/procedures/
PROCS="create-onboarding create-system-description document-analytics document-api document-authorization document-codebase document-config document-data-model document-features document-file-tree document-glossary document-integrations document-security document-user-flow document-user-model existing-docs testing-authorization testing-features testing-owasp testing-setup testing-user-flows"
assert_equal "$(cd "$OUT/references/intake/procedures" 2>/dev/null && ls *.md | sed 's/\.md$//' | LC_ALL=C sort | tr '\n' ' ')" "$PROCS " "ships the 21 intake procedures"
assert_exists "$OUT/commands/intake.md" "ships commands/intake.md"
assert_not_exists "$OUT/commands/intake" "ships no intake:* commands"
assert_equal "$(python3 -c "import json,sys; print(sorted(k for k in json.load(open(sys.argv[1]))['commands'] if k.startswith('intake')))" "$OUT/.claude-plugin/plugin.json" 2>/dev/null)" "['intake']" "plugin.json maps intake and no intake:* command"

# Repo-only content stays out
for path in .claude-plugin/marketplace.json CLAUDE.md site docs scripts assets research specs evals .serena .github version.json pyproject.toml; do
    assert_not_exists "$OUT/$path" "excludes $path"
done

# Only these top-level entries ship
assert_equal "$(cd "$OUT" 2>/dev/null && ls -A | LC_ALL=C sort | tr '\n' ' ')" ".claude-plugin LICENSE README.md agents commands hooks references runtime skills " "ships only the plugin's own entries"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
