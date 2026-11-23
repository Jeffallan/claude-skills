#!/usr/bin/env bash
#
# Test that every relative link and #anchor in the user docs resolves: the
# target file exists, and an anchor matches a heading in the target (GitHub
# slug rules) or an explicit <a id/name>. A fixture with known-bad links runs
# first, so a checker that stops catching them fails too.
#
# Usage: bash scripts/test-doc-links.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE="$(mktemp -d)"
trap 'rm -rf "$FIXTURE"' EXIT

cat >"$FIXTURE/target.md" <<'EOF'
# Target Page

## Setup & `Install` (v2)

## Setup & `Install` (v2)

<a id="custom-anchor"></a>

```bash
# not a heading
```
EOF
cat >"$FIXTURE/good.md" <<'EOF'
# Good

See [target](target.md), [setup](target.md#setup--install-v2), [dup](target.md#setup--install-v2-1),
[custom](target.md#custom-anchor), [self](#good), [ext](https://example.com/x), `[code](missing.md)`.

[ref]: target.md#target-page
EOF
cat >"$FIXTURE/bad.md" <<'EOF'
# Bad

[missing file](missing.md) and [bad anchor](target.md#nope) and [bad self](#absent)
and [fenced heading](target.md#not-a-heading).

[badref]: gone/index.md
EOF

python3 - "$ROOT" "$FIXTURE" <<'EOF'
import re
import sys
from pathlib import Path

root, fixture = Path(sys.argv[1]), Path(sys.argv[2])
passed = failed = 0


def check(ok, msg):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS: {msg}")
    else:
        failed += 1
        print(f"  FAIL: {msg}")


FENCE = re.compile(r"^\s*(```|~~~)")
LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)|^\s*\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)|(?:href|src)=\"([^\"]+)\"")


def prose(text):
    # (line number, line) outside fenced code blocks
    in_fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield n, line


def slug(heading):
    # GitHub: render inline markup to text, lowercase, drop punctuation but - and _, spaces to -
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    text = re.sub(r"<[^>]+>", "", text).replace("`", "").replace("*", "")
    return re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")


anchor_cache = {}


def anchors(path):
    if path not in anchor_cache:
        seen, out = {}, set()
        for _, line in prose(path.read_text()):
            m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
            if m:
                s = slug(m.group(1))
                out.add(s if s not in seen else f"{s}-{seen[s]}")
                seen[s] = seen.get(s, 0) + 1
            out.update(re.findall(r"<a\s+(?:id|name)=\"([^\"]+)\"", line))
        anchor_cache[path] = out
    return anchor_cache[path]


def broken_links(doc, lines=None):
    # lines: optional (start, end) line range to check, for the [Unreleased] part of the changelog
    out, count = [], 0
    for n, line in prose(doc.read_text()):
        if lines and not lines[0] <= n < lines[1]:
            continue
        for m in LINK.finditer(re.sub(r"`[^`]*`", "", line)):
            target = next(g for g in m.groups() if g)
            if re.match(r"^[a-z][a-z0-9+.-]*:|^//", target, re.I):
                continue
            count += 1
            path, _, frag = target.partition("#")
            dest = (doc.parent / path).resolve() if path else doc
            if not dest.exists():
                out.append(f"{n} -> {target} (no such file)")
            elif frag and dest.suffix == ".md" and frag not in anchors(dest):
                out.append(f"{n} -> {target} (no such anchor)")
    return out, count


print("the checker catches broken links (fixture)")
good, good_count = broken_links(fixture / "good.md")
check(good_count == 6 and not good, f"good fixture: 6 links, none broken (got {good_count}, {good})")
bad, _ = broken_links(fixture / "bad.md")
for want in ("missing.md", "target.md#nope", "#absent", "target.md#not-a-heading", "gone/index.md"):
    check(any(f"-> {want} " in b for b in bad), f"bad fixture: reports {want}")

print("relative links and anchors in the user docs resolve")
docs = [root / p for p in ("README.md", "QUICKSTART.md", "CONTRIBUTING.md", "SKILLS_GUIDE.md", "ROADMAP.md", "plugin/README.md")]
# planning notes record the layout of their day: history, not user docs. The v0.5.0 plan stays checked,
# since the site links it (site/scripts/sync-content.mjs linkMap), and so does the narrative it links.
planning = re.compile(r"^docs/(v\d+\.\d+\.\d+-restructure-plan\.md|ideas/|prompts/|skill-ideas/|specs/)")
docs += sorted(p for p in (root / "docs").rglob("*.md") if not planning.match(str(p.relative_to(root))))
docs += sorted((root / "examples").rglob("*.md"))
changelog = root / "CHANGELOG.md"
heads = [n for n, line in prose(changelog.read_text()) if line.startswith("## [")]
total = 0
for d, lines in [(d, None) for d in docs] + [(changelog, (heads[0], heads[1]))]:
    broken, count = broken_links(d, lines)
    total += count
    for b in broken:
        check(False, f"{d.relative_to(root)}:{b}")
check(total > 0, f"found relative links to check ({total})")
check(failed == 0, "every relative link and anchor resolves")

print("")
print(f"Results: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
EOF
