#!/usr/bin/env bash
#
# Test that the user docs keep up with the commands: each command's inputs,
# flags and output paths appear on its docs/workflow page, its argument hint
# matches the Command reference in WORKFLOW_COMMANDS.md. Links in the user
# docs are checked by scripts/test-doc-links.sh.
#
# Usage: bash scripts/test-command-docs.sh
# Exit codes: 0 = all tests pass, 1 = failure

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT" <<'EOF'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
passed = failed = 0


def check(ok, msg):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS: {msg}")
    else:
        failed += 1
        print(f"  FAIL: {msg}")


def scalar(text, key):
    # top-level `key: value` in a command yaml; the yamls hold plain scalars, so no parser is needed
    m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', text, re.M)
    return m.group(1) if m else None


def items(text, section):
    # the `- name:` entries of a top-level list, each with its optional `path:`
    block = re.search(rf"^{section}:\n((?:  .*\n|\n)*)", text, re.M)
    out = []
    for entry in re.split(r"^  - ", block.group(1) if block else "", flags=re.M)[1:]:
        name = re.search(r"^name:\s*(\S+)", entry, re.M)
        path = re.search(r'^\s*path:\s*"?([^"\n]+)"?', entry, re.M)
        out.append((name.group(1), path.group(1) if path else None))
    return out


def literal(path):
    # the longest piece of a templated path, e.g. {specsRoot}/todo/{topic}/synthesis.md -> synthesis.md
    parts = [p.strip("/") or p for p in re.split(r"\{[^}]+\}", path)]
    return max(parts, key=len)


wc = (root / "docs/WORKFLOW_COMMANDS.md").read_text()
ref_rows = {}
for line in wc[wc.index("## Command reference") :].splitlines():
    m = re.match(r"\|\s*`([^`]+)`\s*\|(.*?)\|", line.replace("\\|", "\x00"))
    if m:
        ref_rows[m.group(1)] = m.group(2).replace("\x00", "|")

print("command docs")
yamls = sorted(p for p in (root / "plugin/commands").rglob("*.yaml") if p.name != "workflow-manifest.yaml")
check(len(yamls) == 13, f"13 command yamls (found {len(yamls)})")
for y in yamls:
    text = y.read_text()
    cmd = scalar(text, "command")
    page_rel = scalar(text, "description")
    page = root / page_rel
    check(page.is_file(), f"{cmd}: its page {page_rel} exists")
    if not page.is_file():
        continue
    doc = page.read_text()
    md = (root / scalar(text, "path")).read_text()
    hint = scalar(text, "argument-hint")
    md_hint = re.search(r'^argument-hint:\s*"(.*)"\s*$', md, re.M)
    check(md_hint is not None and md_hint.group(1) == hint, f"{cmd}: the yaml's argument hint matches the command file's")
    for flag in re.findall(r"--[a-z][a-z-]*", hint):
        check(flag in doc, f"{cmd}: its page names the flag {flag}")
    for name, _ in items(text, "inputs"):
        check(f"`{name}`" in doc or f"--{name}" in doc, f"{cmd}: its page names the input {name}")
    for name, path in items(text, "outputs"):
        if path:
            check(literal(path) in doc, f"{cmd}: its page names the output path {literal(path)} ({name})")
    cell = ref_rows.get(cmd)
    check(cell is not None, f"{cmd}: WORKFLOW_COMMANDS.md's Command reference has a row")
    if cell is not None:
        want = "none" if hint == "" else f"`{hint}`"
        check(want in cell, f"{cmd}: the Command reference row shows {want}")

print("")
print(f"Results: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
EOF
