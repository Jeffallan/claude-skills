#!/usr/bin/env bash
#
# Test scripts/build-plugin-dist.sh, which assembles the plugin
# distribution tree published to the `plugin` branch.
#
# Usage: bash scripts/test-build-plugin-dist.sh
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

assert_exit_nonzero() {
    if [ "$1" -ne 0 ]; then pass "$2"; else fail "$2 (expected failure, got exit 0)"; fi
}

assert_exit_zero() {
    if [ "$1" -eq 0 ]; then pass "$2"; else fail "$2 (expected exit 0, got $1)"; fi
}

assert_equal() {
    if [ "$1" = "$2" ]; then pass "$3"; else fail "$3 (expected $2, got $1)"; fi
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$REPO_ROOT/scripts/build-plugin-dist.sh"

echo "build-plugin-dist.sh"

# Missing output argument fails
set +e
bash "$BUILD" >/dev/null 2>&1
rc=$?
set -e
assert_exit_nonzero "$rc" "fails without an output directory"

# Non-empty output directory is refused
OUT=$(mktemp -d)
CLEANUP_DIRS+=("$OUT")
touch "$OUT/existing"
set +e
bash "$BUILD" "$OUT" >/dev/null 2>&1
rc=$?
set -e
assert_exit_nonzero "$rc" "refuses a non-empty output directory"

# Successful build into an empty directory
OUT=$(mktemp -d)
CLEANUP_DIRS+=("$OUT")
set +e
bash "$BUILD" "$OUT" >/dev/null 2>&1
rc=$?
set -e
assert_exit_zero "$rc" "builds into an empty directory"

# Shipped content
assert_exists "$OUT/.claude-plugin/plugin.json" "ships plugin.json"
assert_exists "$OUT/skills" "ships skills/"
assert_exists "$OUT/commands" "ships commands/"
assert_exists "$OUT/references/common-ground" "ships references/common-ground/"
assert_exists "$OUT/README.md" "ships README.md"
assert_exists "$OUT/LICENSE" "ships LICENSE"

# Repo-only content stays out
for path in .claude-plugin/marketplace.json CLAUDE.md site docs scripts assets research specs .serena .github version.json; do
    assert_not_exists "$OUT/$path" "excludes $path"
done

# Untracked files never ship
assert_equal "$(find "$OUT" -name 'v0.5.0-*' | wc -l | tr -d ' ')" "0" "excludes untracked files"

# Every tracked skill ships
src_count=$(cd "$REPO_ROOT" && git ls-files 'skills/*/SKILL.md' | wc -l | tr -d ' ')
dist_count=$(find "$OUT/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')
assert_equal "$dist_count" "$src_count" "ships every tracked skill"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
