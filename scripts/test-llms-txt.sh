#!/usr/bin/env bash
#
# Test that every link in the generated site/public/llms.txt carries the
# /claude-skills base path and points at a generated markdown mirror.
# Requires site dependencies (cd site && npm ci).
#
# Usage: bash scripts/test-llms-txt.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

SITE_DIR="$(cd "$(dirname "$0")/../site" && pwd)"
LLMS="$SITE_DIR/public/llms.txt"

(cd "$SITE_DIR" && node scripts/sync-content.mjs > /dev/null)

links=$(grep -o '](/[^)]*)' "$LLMS" | sed 's/^](//; s/)$//')
[ -n "$links" ] || { echo "FAIL: no links found in llms.txt"; exit 1; }

fail=0
for link in $links; do
    case "$link" in
        /claude-skills/*) ;;
        *) echo "FAIL: missing base path: $link"; fail=1; continue ;;
    esac
    [ -f "$SITE_DIR/public/${link#/claude-skills/}" ] || { echo "FAIL: no mirror for $link"; fail=1; }
done

[ "$fail" -eq 0 ] && echo "PASS: $(echo "$links" | wc -l | tr -d ' ') llms.txt links resolve"
exit "$fail"
