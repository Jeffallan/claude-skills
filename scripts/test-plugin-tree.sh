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

# Repo-only content stays out
for path in .claude-plugin/marketplace.json CLAUDE.md site docs scripts assets research specs evals .serena .github version.json pyproject.toml; do
    assert_not_exists "$OUT/$path" "excludes $path"
done

# Only these top-level entries ship
assert_equal "$(cd "$OUT" 2>/dev/null && ls -A | LC_ALL=C sort | tr '\n' ' ')" ".claude-plugin LICENSE README.md commands hooks references runtime skills " "ships only the plugin's own entries"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
