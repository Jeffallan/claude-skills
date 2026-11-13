#!/usr/bin/env bash
#
# Print the verification evidence for the current branch in one run: each
# check's command, its output and its exit code against the expected one.
# Goal prompts can name `make evidence` in <done_when>.
#
# Usage: bash scripts/evidence.sh   (or: make evidence)
#   EXPECT_UPSTREAM=0  the branch has no upstream (default, local-only work)
#   EXPECT_UPSTREAM=1  the branch has an upstream and is in sync with it
#   RETIRED='a\|b'     grep pattern for names no shipped file may mention
# Needs: jq, and claude on PATH (one short Haiku call to list loaded commands)
# Exit codes: 0 = every check exited as expected, 1 = at least one did not

set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2

EXPECT_UPSTREAM=${EXPECT_UPSTREAM:-0}
RETIRED=${RETIRED:-'spec:reopen\|create-epic\|complete-sprint\|execute-ticket'}

CHECKS=0
FAILED=0
BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT

# check <expected exit> <command>
check() {
    local want=$1 cmd=$2 rc
    echo ""
    echo "\$ $cmd"
    eval "$cmd"
    rc=$?
    CHECKS=$((CHECKS + 1))
    if [ "$rc" -eq "$want" ]; then
        echo "exit=$rc (expected $want) ok"
    else
        echo "exit=$rc (expected $want) FAIL"
        FAILED=$((FAILED + 1))
    fi
}

check 0 "make --no-print-directory validate 2>&1 | tail -3"
check 0 "make --no-print-directory test 2>&1 | grep -E 'Results|FAIL'"
check 0 "git status --short; test -z \"\$(git status --short)\" && echo clean"
check 0 "git branch -vv | grep '^\*'"
if [ "$EXPECT_UPSTREAM" = 1 ]; then
    check 0 "git rev-parse --abbrev-ref --symbolic-full-name '@{u}' && test \"\$(git rev-list --count '@{u}...HEAD')\" = 0 && echo 'in sync with upstream'"
else
    check 0 "! git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1 && echo 'no upstream'"
fi
check 0 "git log --oneline origin/main..HEAD"
# grep finds nothing: exit 1 is the pass
check 1 "grep -rn '$RETIRED' commands references skills/*/SKILL.md"
for plan in docs/specs/todo/*/implementation-plan.md; do
    check 0 "sed -n '/^## Completion Status/,/^---/p' $plan | grep '^| ' | tail -n +3 | cut -d'|' -f2-3"
done
check 0 "bash scripts/build-plugin-dist.sh $BUILD"
# The session's init event lists the commands that loaded and the plugin they came from
check 0 "claude --plugin-dir $BUILD -p ok --model haiku --setting-sources project --output-format stream-json --verbose </dev/null 2>/dev/null | head -1 | jq -re '(.slash_commands[] | select(test(\"^fullstack-dev-skills:(intake|discovery|spec|ticket):\"))), (.plugins[] | select(.name == \"fullstack-dev-skills\") | [.source, .path, .version] | join(\" \"))'"

echo ""
echo "Evidence: $CHECKS checks, $FAILED failed"
[ "$FAILED" -eq 0 ]
