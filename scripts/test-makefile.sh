#!/usr/bin/env bash
#
# Test the Makefile dev-link, dev-unlink, and validate targets.
# Uses a temporary directory to simulate the plugin cache — does not
# touch the real ~/.claude/plugins/ directory.
#
# Usage: bash scripts/test-makefile.sh
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

assert_symlink() {
    if [ -L "$1" ]; then pass "$2"; else fail "$2 (not a symlink)"; fi
}

assert_dir() {
    if [ -d "$1" ] && [ ! -L "$1" ]; then pass "$2"; else fail "$2 (not a real directory)"; fi
}

assert_not_exists() {
    if [ ! -e "$1" ]; then pass "$2"; else fail "$2 (still exists)"; fi
}

assert_exit_nonzero() {
    if [ "$1" -ne 0 ]; then pass "$2"; else fail "$2 (expected failure, got exit 0)"; fi
}

assert_exit_zero() {
    if [ "$1" -eq 0 ]; then pass "$2"; else fail "$2 (expected exit 0, got $1)"; fi
}

# Setup: create a temp directory simulating the plugin cache structure
TMPDIR=$(mktemp -d)
CLEANUP_DIRS+=("$TMPDIR")

VERSION=$(python -c "import json; print(json.load(open('version.json'))['version'])")
FAKE_CACHE="$TMPDIR/fullstack-dev-skills"
CACHE_DIR="$FAKE_CACHE/$VERSION"

mkdir -p "$CACHE_DIR"
echo "placeholder" > "$CACHE_DIR/SKILL.md"

echo ""
echo "========================================"
echo "Makefile Target Tests"
echo "========================================"
echo "Temp cache: $FAKE_CACHE"
echo "Version:    $VERSION"
echo ""

# ─── Test 1: dev-link creates symlink and backup ─────────────────────
echo "--- Test 1: dev-link creates symlink and backup ---"

make dev-link CACHE_BASE="$FAKE_CACHE" > /dev/null 2>&1
EXIT=$?

assert_exit_zero $EXIT "dev-link exits 0"
assert_symlink "$CACHE_DIR" "cache dir is now a symlink"
assert_dir "$CACHE_DIR.bak" "backup directory exists"

# ─── Test 2: dev-link guard — already linked ─────────────────────────
echo "--- Test 2: dev-link guard (already symlinked) ---"

EXIT=0
make dev-link CACHE_BASE="$FAKE_CACHE" > /dev/null 2>&1 || EXIT=$?

assert_exit_nonzero $EXIT "dev-link fails when already symlinked"

# ─── Test 3: dev-unlink restores backup ──────────────────────────────
echo "--- Test 3: dev-unlink restores backup ---"

EXIT=0
make dev-unlink CACHE_BASE="$FAKE_CACHE" > /dev/null 2>&1 || EXIT=$?

assert_exit_zero $EXIT "dev-unlink exits 0"
assert_dir "$CACHE_DIR" "cache dir is a real directory again"
assert_not_exists "$CACHE_DIR.bak" "backup removed after restore"

# ─── Test 4: dev-unlink guard — no symlink ───────────────────────────
echo "--- Test 4: dev-unlink guard (no symlink) ---"

EXIT=0
make dev-unlink CACHE_BASE="$FAKE_CACHE" > /dev/null 2>&1 || EXIT=$?

assert_exit_nonzero $EXIT "dev-unlink fails when not symlinked"

# ─── Test 5: dev-link guard — backup already exists ──────────────────
echo "--- Test 5: dev-link guard (backup already exists) ---"

mkdir -p "$CACHE_DIR.bak"

EXIT=0
make dev-link CACHE_BASE="$FAKE_CACHE" > /dev/null 2>&1 || EXIT=$?

assert_exit_nonzero $EXIT "dev-link fails when backup already exists"

rmdir "$CACHE_DIR.bak"

# ─── Test 6: dev-link guard — cache dir missing ─────────────────────
echo "--- Test 6: dev-link guard (cache dir missing) ---"

mv "$CACHE_DIR" "$CACHE_DIR.tmp"

EXIT=0
make dev-link CACHE_BASE="$FAKE_CACHE" > /dev/null 2>&1 || EXIT=$?

assert_exit_nonzero $EXIT "dev-link fails when cache dir missing"

mv "$CACHE_DIR.tmp" "$CACHE_DIR"

# ─── Test 7: dev-unlink guard — no backup ────────────────────────────
echo "--- Test 7: dev-unlink guard (no backup) ---"

# Create a symlink without a backup to test the guard
mv "$CACHE_DIR" "$CACHE_DIR.hold"
ln -s /nonexistent "$CACHE_DIR"

EXIT=0
make dev-unlink CACHE_BASE="$FAKE_CACHE" > /dev/null 2>&1 || EXIT=$?

assert_exit_nonzero $EXIT "dev-unlink fails when no backup exists"

rm "$CACHE_DIR"
mv "$CACHE_DIR.hold" "$CACHE_DIR"

# ─── Test 8: validate runs without error ─────────────────────────────
echo "--- Test 8: validate ---"

EXIT=0
make validate > /dev/null 2>&1 || EXIT=$?

assert_exit_zero $EXIT "validate exits 0"

# ─── Summary ─────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "Results: $PASS passed, $FAIL failed"
echo "========================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
