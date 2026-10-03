#!/usr/bin/env bash
#
# Assemble the plugin distribution tree published to the `plugin` branch.
# Only the files the plugin needs ship; the docs site, scripts, research,
# and contributor files stay on main. Content comes from committed HEAD
# via `git archive`, so untracked and uncommitted files never ship.
#
# Usage: bash scripts/build-plugin-dist.sh <empty-output-dir>
# Exit codes: 0 = success, 1 = usage error

set -euo pipefail

OUT="${1:-}"
if [ -z "$OUT" ]; then
    echo "usage: $0 <empty-output-dir>" >&2
    exit 1
fi

mkdir -p "$OUT"
if [ -n "$(ls -A "$OUT")" ]; then
    echo "error: output directory is not empty: $OUT" >&2
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

git -C "$REPO_ROOT" archive --format=tar HEAD -- \
    .claude-plugin \
    ':(exclude).claude-plugin/marketplace.json' \
    skills \
    commands \
    references \
    README.md \
    LICENSE \
    | tar -x -C "$OUT"

echo "Built plugin distribution in $OUT"
