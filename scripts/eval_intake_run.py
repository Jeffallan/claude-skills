#!/usr/bin/env python3
"""Score one finished intake run against the intake guarantees.

Reads the intake docs, the findings tracker, the checklist, the tests and the
git history since the run's start SHA, runs the characterization suite and,
optionally, reads the goal-session transcripts. Prints a JSON result in the
eval intake shape (eval, version, model, checks, score) and exits 0 when every
check passes, 1 when one fails, 2 on bad input.

Usage:
    python3 scripts/eval_intake_run.py --repo <path> --start <sha>
        [--test-cmd "<cmd>"] [--transcript <jsonl> ...] [--reflog <file>]
        [--version V] [--model M]
"""

from __future__ import annotations

import argparse
import ast
from datetime import datetime
import fnmatch
import json
from pathlib import Path
import re
import subprocess
import sys

import eval_dir
from eval_workflow_run import REWRITE, check, git, text_of, transcript_checks, when

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runtime"))
from ticket_guard import docs as guard_docs

# Each documentation command and the doc it owns (references/intake/rules.md)
DOCS = {
    "document-data-model": "docs/architecture/data-model.md",
    "document-file-tree": "docs/architecture/file-tree.md",
    "document-integrations": "docs/architecture/external-integrations.md",
    "document-api": "docs/architecture/api-reference.md",
    "document-user-model": "docs/domain/user-model.md",
    "document-features": "docs/domain/features.md",
    "document-glossary": "docs/domain/glossary.md",
    "document-security": "docs/security/security.md",
    "document-authorization": "docs/security/authorization.md",
    "document-user-flow": "docs/flows/user-flow.md",
    "document-config": "docs/operations/configuration.md",
    "document-analytics": "docs/operations/analytics-events.md",
    "create-onboarding": "docs/README.md",
    "existing-docs": "docs/intake-existing-docs.md",
}
# Docs intake writes beyond DOCS; owner-written docs are never checked for style
INTAKE_DOCS = (*DOCS.values(), "docs/system-description.md")
# a file path (a separator, or an extension starting with a letter) then :line; `0.0.0.0:8080` and `localhost:5432` are not
LINE_CITE = re.compile(r"`(?:[\w./-]*/[\w.-]+|[\w.-]*\.[A-Za-z]\w*):\d+(-\d+)?`")
REPEAT_WORDS = 12  # a sentence this long, word for word in two docs, is a repeated fact
# Letters or digits may not touch the id; `_` may, so test_F012_name counts
FINDING = re.compile(r"(?<![A-Za-z0-9])F-?(\d{3})(?!\d)")
# Markers that make a test skipped or expected-fail: the intended-behavior twin of a finding
SKIP_MARK = re.compile(
    r"(pytest\.mark\.(skip|xfail)|@(unittest\.)?(skip\w*|expectedFailure)\b|\b(it|test|describe)\.(skip|failing|fails|fail|fixme|todo)\b"
    r"|\bx(it|test|describe)\(|@Disabled\b|\bt\.Skip\(|\$this->markTestSkipped|\bskip\s*\()"
)
# Test files by name, the fallback when the run declares no test paths. Folder names that also
# hold shipped code (spec/, fixtures/, testing/) count only inside one of these trees.
TEST_PATH = re.compile(
    r"(^|/)([Tt]ests?|__tests__|__mocks__|e2e|cypress|playwright|androidTest|[^/]+\.Tests)(/|$)"
    r"|(^|/)(test_[^/]+|tests\.py|[^/]+_test\.[a-z]+|[^/]+_spec\.rb|[^/]+\.(test|spec)\.[a-z]+|conftest\.py)$"
)
TEST_CONFIG = re.compile(
    r"(^|/)(pytest\.ini|tox\.ini|\.coveragerc|setup\.cfg|phpunit\.xml(\.dist)?|karma\.conf\.[a-z]+"
    r"|(jest|vitest|playwright|cypress)\.config\.[a-z]+|babel\.config\.[a-z]+|requirements[-_](dev|test)[^/]*\.txt"
    r"|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|CLAUDE\.md)$"
)
COMMENT_LINE = re.compile(r"^\s*(#|//|/\*|\*|\*/|<!--|-->|--|;|\"\"\"|'''|$)")


def declared_test_paths(repo: Path) -> list[str]:
    """Globs from `Test paths:` notes in the checklist, written by intake:testing-setup."""
    path = repo / "docs/intake-checklist.md"
    if not path.exists():
        return []
    found = re.findall(r"(?<!`)Test paths:\s*([^\n]+)", path.read_text(encoding="utf-8"))
    return [g.strip().strip("`") for line in found for g in line.split(",") if g.strip()]


def is_test(rel: str, globs: list[str]) -> bool:
    return bool(TEST_PATH.search(rel)) or any(fnmatch.fnmatch(rel, g) for g in globs)


def checklist_excuses(repo: Path) -> dict[str, str]:
    """Commands whose checklist item says the aspect is not present, so their doc may be absent."""
    path = repo / "docs/intake-checklist.md"
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    out = {}
    for i, line in enumerate(lines):
        m = re.search(r"intake:([a-z-]+)", line)
        if m and line.lstrip().startswith("- [x]"):
            note = " ".join([line] + [x for x in lines[i + 1 : i + 3] if x.startswith("  ")])
            if re.search(r"not present|\bN/A\b", note, re.I):
                out[m.group(1)] = "not present"
    return out


def docs_check(repo: Path) -> dict:
    excused = checklist_excuses(repo)
    missing, unaudited, noted = [], [], []
    for cmd, rel in DOCS.items():
        rel = intake_path(repo, rel)
        p = repo / rel
        if not p.exists():
            (noted if cmd in excused else missing).append(cmd if cmd not in excused else f"{cmd}: not present")
        elif not re.search(r"^#{2,3} Accuracy audit\b", p.read_text(encoding="utf-8"), re.M):
            unaudited.append(rel)
    ok = not missing and not unaudited
    detail = "every doc exists with an Accuracy audit section" if ok else f"missing: {missing}; no audit: {unaudited}"
    if noted:
        detail += f"; excused: {noted}"
    return check("docs-with-audit", ok, detail)


def tracker_ids(repo: Path) -> set[str] | None:
    p = repo / "docs/intake-findings.md"
    if not p.exists():
        return None
    return {m.group(1) for m in FINDING.finditer(p.read_text(encoding="utf-8"))}


def changed(repo: Path, start: str) -> list[str]:
    return [x for x in git(repo, "diff", "--name-only", f"{start}..HEAD").splitlines() if x]


# A function, not a test, defined just above a marker wraps it: `function intended(test, reason) { test.fail(...) }`
HELPER_DEF = re.compile(
    r"(?:\bfunction\s+(\w+)\s*\(|\b(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(|\bdef\s+(\w+)\s*\()"
)


def marker_helper(lines: list[str], i: int) -> str | None:
    """The name of the non-test function whose body holds the marker on line i, if it starts within 3 lines above."""
    for line in reversed(lines[max(0, i - 3) : i + 1]):
        m = HELPER_DEF.search(line)
        if m:
            name = next(g for g in m.groups() if g)
            return None if name.lower().startswith("test") else name
    return None


# Where prose starts: a docstring or block comment opening, or a line comment after whitespace (never `http://`)
PROSE_START = re.compile(r"\"\"\"|'''|/\*|(?<!\S)(?:#|//)")


def code_text(lines: list[str]) -> list[str]:
    """Each line with its comments, docstrings and block comments removed, so prose naming a marker is not one."""
    out, close = [], ""
    for line in lines:
        kept, pos = "", 0
        while True:
            if close:
                end = line.find(close, pos)
                if end < 0:
                    break
                pos, close = end + len(close), ""
            m = PROSE_START.search(line, pos)
            if not m:
                kept += line[pos:]
                break
            kept += line[pos : m.start()]
            if m.group() in ("#", "//"):
                break
            close, pos = ("*/" if m.group() == "/*" else m.group()), m.end()
        out.append(kept)
    return out


# A named table a test is generated from: `.each(cases)`, `for (const c of cases)`, `for c in cases`,
# `parametrize("a,b", cases)`. An inline table's first rows sit within the marker's reach already.
TABLE_REF = re.compile(
    r"\.each\(\s*(\w+)|\bfor\b.*?\b(?:of|in)\s+(\w+)"
    r"|parametrize\(\s*(?:\"[^\"]*\"|'[^']*'|\[[^\]]*\]|\([^)]*\))\s*,\s*(\w+)"
)


def table_rows(text: str, start: int) -> list[str]:
    """The top-level rows of the bracketed table that opens at text[start]."""
    rows, depth, quote, begin, k = [], 0, "", start + 1, start
    while k < len(text):
        ch = text[k]
        if quote:
            quote = "" if ch == quote and text[k - 1] != "\\" else quote
        elif text.startswith(("#", "//"), k) and text[k - 1].isspace():
            k = text.find("\n", k)  # a comment runs to the line end
            if k < 0:
                break
            continue
        elif ch in "'\"`":
            quote = ch
        elif ch in "[({":
            depth += 1
        elif ch in "])}":
            depth -= 1
            if depth == 0:
                rows.append(text[begin:k])
                break
        elif ch == "," and depth == 1:
            # a row keeps the comment that ends its line: `("op1", "x"),  # F-001`
            eol = len(text) if (eol := text.find("\n", k)) < 0 else eol
            rest = text[k + 1 : eol].strip()
            end = eol if not rest or rest.startswith(("#", "//")) else k
            rows.append(text[begin:end])
            begin = end + 1
        k += 1
    return [r for r in rows if r.strip()]


def driving_rows(lines: list[str], i: int) -> list[str]:
    """The rows of the table the marked test on line i is generated from, if a table drives it."""
    text = "\n".join(lines)
    for j in range(max(0, i - 3), min(len(lines), i + 2)):
        m = TABLE_REF.search(lines[j])
        if not m:
            continue
        ref = next(g for g in m.groups() if g)
        if d := re.search(rf"\b{re.escape(ref)}\b\s*(?::[^=\n]+)?=\s*\[", text):
            return table_rows(text, d.end() - 1)
    return []


def bug_tests_check(repo: Path, start: str, ids: set[str], globs: list[str]) -> dict:
    """Every skipped or expected-fail test written by intake names a finding id the tracker knows.

    A helper that wraps a marker is checked where it is called, not where it is defined. Markers count only in
    code: a comment or docstring that names one is prose. A test generated from a table cites through its rows.
    """
    bad, unknown, seen = [], [], 0
    files = {}
    for rel in changed(repo, start):
        p = repo / rel
        if is_test(rel, globs) and p.exists():
            files[rel] = p.read_text(encoding="utf-8", errors="replace").splitlines()
    codes = {rel: code_text(lines) for rel, lines in files.items()}
    helpers = {
        n
        for rel, lines in files.items()
        for i, line in enumerate(codes[rel])
        if SKIP_MARK.search(line) and (n := marker_helper(lines, i))
    }
    call = re.compile(r"\b(" + "|".join(map(re.escape, sorted(helpers))) + r")\s*\(") if helpers else None
    for rel, lines in files.items():
        for i, line in enumerate(codes[rel]):
            if SKIP_MARK.search(line):
                if marker_helper(lines, i):
                    continue
            elif not (call and call.search(line) and not HELPER_DEF.search(line)):
                continue
            seen += 1
            near = " ".join(lines[max(0, i - 2) : i + 4])
            found = {m.group(1) for m in FINDING.finditer(near)}
            rows = [] if found else driving_rows(lines, i)
            if rows:  # a table-driven twin: every row it is generated from names its finding
                found = {m.group(1) for r in rows for m in FINDING.finditer(r)}
                if any(not FINDING.search(r) for r in rows):
                    bad.append(f"{rel}:{i + 1} (a table row)")
            elif not found:
                bad.append(f"{rel}:{i + 1}")
            unknown += [f"F-{f} ({rel}:{i + 1})" for f in found - ids]
    ok = not bad and not unknown
    detail = (
        f"{seen} skipped or expected-fail tests, each naming a tracked finding"
        if ok
        else f"no finding id: {bad}; not in the tracker: {unknown}"
    )
    return check("bug-tests-cite-findings", ok, detail)


def suite_check(repo: Path, cmd: str | None) -> tuple[dict, str]:
    """The suite's verdict plus its output, which lists the titles table-driven tests build at runtime."""
    if not cmd:
        return check(
            "characterization-green", False, "not run: pass --test-cmd with the project's test:all command"
        ), ""
    r = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True)
    out = r.stdout + r.stderr
    tail = out.strip().splitlines()[-1:] or [""]
    return check("characterization-green", r.returncode == 0, f"`{cmd}` exit {r.returncode}: {tail[0][:160]}"), out


def jest_titles(out: str) -> str:
    """Each test's full name and title from `jest --json`, one per line; nothing when the output isn't its JSON."""
    try:
        data = json.loads(out)
    except ValueError:
        return ""
    if not isinstance(data, dict):
        return ""
    return "\n".join(
        f"{a.get('fullName', '')}\n{a.get('title', '')}"
        for r in data.get("testResults", [])
        for a in r.get("assertionResults", [])
    )


def node_test_runs(package_json: str, cmd: str) -> list[str]:
    """The package's `node --test` scripts the test command doesn't reach by `npm run`, each with the spec reporter."""
    try:
        scripts = json.loads(package_json).get("scripts") or {}
    except (ValueError, AttributeError):
        return []
    reached, todo = set(), [cmd]
    while todo:
        for n in re.findall(r"\b(?:npm|pnpm|yarn)\s+(?:run(?:-script)?\s+)?([\w:.-]+)", todo.pop()):
            if n in scripts and n not in reached:
                reached.add(n)
                todo.append(str(scripts[n]))
    return [
        re.sub(r"(\bnode\b[^&|;]*?\s--test)(?![\w=-])", r"\1 --test-reporter=spec", str(body), count=1)
        for name, body in scripts.items()
        if name not in reached
        and re.search(r"\bnode\b[^&|;]*?\s--test(?![\w=-])", str(body))
        and "--test-reporter" not in str(body)
    ]


def node_titles(out: str) -> str:
    """The spec reporter's titles, each also joined to its enclosing describe titles by indent, as a cited full name."""
    lines, stack = [], []
    for m in re.finditer(r"^( *)[▶✔✖﹣] (.+?)(?: \([\d.]+ms\))?(?: # \w+.*)?$", out, re.M):
        stack = [*stack[: len(m.group(1)) // 2], m.group(2)]
        lines += [m.group(2), " ".join(stack)]
    return "\n".join(lines)


def test_listing(repo: Path, cmd: str | None) -> str:
    """Test titles as the runners list them, so names built at runtime and e2e titles outside `cmd` are found.

    pytest collects through the test command's own invocation, and Django's runner reruns it at verbosity 2, which
    prints each test id. vitest and Playwright list from each tracked package.json naming vitest or
    playwright.config.*, e2e suites the test command skips included. Jest has no listing with titles
    (`--listTests` prints files), so each package naming jest runs once with `--json`. A package script running
    `node --test` that the test command doesn't reach through `npm run` runs with the spec reporter. A runner that
    fails or times out adds nothing, which leaves the file-text match as before.
    """
    if not cmd:
        return ""
    runs: list[tuple[Path, str, str]] = []  # (cwd, command, how to read its output)
    if m := re.match(r"(.*?\bpytest)\b", cmd):
        runs.append((repo, f"{m.group(1)} --collect-only -q", "stdout"))
    if m := re.match(r"(.*?\bmanage\.py\s+test\b[^&|;]*)", cmd):
        runs.append((repo, f"{m.group(1).rstrip()} -v 2", "both"))  # a later -v wins
    for rel in git(repo, "ls-files").splitlines():
        name, cwd = Path(rel).name, (repo / rel).parent
        if name == "package.json":
            text = (repo / rel).read_text(encoding="utf-8", errors="replace")
            if '"vitest"' in text:
                runs.append((cwd, "npx --no vitest list", "stdout"))
            elif '"jest"' in text:
                runs.append((cwd, "npx --no jest --json", "jest"))
            runs += [(cwd, run, "node") for run in node_test_runs(text, cmd)]
        elif re.fullmatch(r"playwright\.config\.[cm]?[jt]s", name):
            runs.append((cwd, "npx --no playwright test --list", "stdout"))
        elif re.fullmatch(r"jest\.config\.[cm]?[jt]s", name):
            runs.append((cwd, "npx --no jest --json", "jest"))
    out = []
    for cwd, run, how in dict.fromkeys(runs):
        try:
            r = subprocess.run(run, shell=True, cwd=cwd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            continue
        if how == "jest":  # a red test still prints its JSON; no JSON means jest never ran
            out.append(jest_titles(r.stdout))
        elif r.returncode == 0:
            out.append({"stdout": r.stdout, "both": r.stdout + r.stderr, "node": node_titles(r.stdout)}[how])
    text = "\n".join(out)
    # vitest joins describe and title with " > ", Playwright with " \u203a "; a cited full name joins them with a space
    return text + "\n" + re.sub(" (?:>|\u203a) ", " ", text)


def strip_docstrings(src: str) -> str:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                # a module may be empty; a class or function body needs a statement
                node.body = node.body[1:] or ([] if isinstance(node, ast.Module) else [ast.Pass()])
    return ast.dump(tree)


def comment_only(repo: Path, start: str, rel: str) -> bool:
    """True when every change to a source file is a comment or a docstring."""
    try:
        before = git(repo, "show", f"{start}:{rel}")
    except subprocess.CalledProcessError:
        return False  # a new application file is never comment-only
    p = repo / rel
    if not p.exists():
        return False
    if rel.endswith(".py"):
        try:
            return strip_docstrings(before) == strip_docstrings(p.read_text(encoding="utf-8"))
        except SyntaxError:
            return False
    diff = git(repo, "diff", "-U0", start, "--", rel).splitlines()
    body = [x[1:] for x in diff if x[:1] in "+-" and not x.startswith(("+++", "---"))]
    return all(COMMENT_LINE.match(x) for x in body)


def package_json_ok(repo: Path, start: str, rel: str, globs: list[str]) -> bool:
    """package.json may change only its scripts and devDependencies; a new one may also carry inert metadata.

    A new manifest below the root under a declared test glob may also set "type" for its test files.
    """
    try:
        after = json.loads((repo / rel).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    try:
        before = json.loads(git(repo, "show", f"{start}:{rel}"))
        keep = {"scripts", "devDependencies"}
    except subprocess.CalledProcessError:
        before = {}  # a manifest intake created for its test scripts
        keep = {"scripts", "devDependencies", "name", "description", "private", "version", "license"}
        if "/" in rel and any(fnmatch.fnmatch(rel, g) for g in globs):
            keep.add("type")
    except json.JSONDecodeError:
        return False
    return {k: v for k, v in before.items() if k not in keep} == {k: v for k, v in after.items() if k not in keep}


def lockfile_ok(repo: Path, start: str, rel: str) -> bool:
    """package-lock.json may add or change dev entries only; every runtime entry stays as it was."""
    try:
        after = json.loads((repo / rel).read_text(encoding="utf-8"))
        before = json.loads(git(repo, "show", f"{start}:{rel}"))
    except subprocess.CalledProcessError:
        before = {}  # a lockfile intake created beside a test-only manifest
    except json.JSONDecodeError:
        return False
    # lockfileVersion 2 and 3 key "packages"; version 1 keys "dependencies"
    key = "packages" if "packages" in after or "packages" in before else "dependencies"

    def runtime(lock: dict) -> dict:
        out = {}
        for name, entry in (lock.get(key) or {}).items():
            if name == "":  # the root: only its runtime dependency lists count
                deps = {
                    k: v for k, v in entry.items() if k in ("dependencies", "optionalDependencies", "peerDependencies")
                }
                if deps:
                    out[name] = deps
            elif not entry.get("dev"):
                out[name] = entry
        return out

    return runtime(before) == runtime(after)


def diff_check(repo: Path, start: str, globs: list[str]) -> dict:
    """The diff since the start touches only docs, tests, test config and docstrings."""
    bad = []
    for rel in changed(repo, start):
        # A manifest is judged by its keys whatever a declared glob says
        if rel.endswith("package.json"):
            if (repo / rel).exists() and package_json_ok(repo, start, rel, globs):
                continue
            bad.append(rel)
            continue
        # shortcut: yarn.lock and pnpm-lock.yaml carry no dev flag, so they stay excused; parse them if a run abuses that
        if rel.endswith("package-lock.json"):
            if (repo / rel).exists() and lockfile_ok(repo, start, rel):
                continue
            bad.append(rel)
            continue
        if rel.startswith("docs/") or is_test(rel, globs) or TEST_CONFIG.search(rel):
            continue
        if not comment_only(repo, start, rel):
            bad.append(rel)
    return check(
        "characterize-dont-fix",
        not bad,
        ("only docs, tests, test config and docstrings changed" if not bad else f"code changed: {bad}")
        + (f"; declared test paths: {globs}" if globs else ""),
    )


def checked_commands(text: str) -> set[str]:
    """The `intake:<command>` items checked in a checklist's text."""
    return {
        m.group(1)
        for line in text.splitlines()
        if line.lstrip().startswith("- [x]")
        for m in [re.search(r"`(intake:[a-z-]+)`", line)]
        if m
    }


def commits_check(repo: Path, start: str) -> dict:
    """Every commit carries one Intake: trailer, and every item checked since the start has a commit naming it.

    BLOCKED notes, unblocking and follow-up fixes are commits like any other: each names its item.
    """
    bad, named = [], set()
    for sha in git(repo, "rev-list", "--reverse", f"{start}..HEAD").splitlines():
        msg = git(repo, "log", "-1", "--format=%B", sha)
        # git's own trailer parse: an Intake: line counts only in the final trailer block
        trailers = [
            t.strip()
            for t in git(repo, "log", "-1", "--format=%(trailers:key=Intake,valueonly)", sha).splitlines()
            if t.strip()
        ]
        if len(trailers) != 1:
            bad.append(f"{sha[:7]} {msg.splitlines()[0]} ({len(trailers)} trailers)")
        named.update(
            t.removeprefix("intake:") for t in trailers
        )  # `Intake: document-api` and `Intake: intake:document-api` name the same item
    try:
        before = checked_commands(git(repo, "show", f"{start}:docs/intake-checklist.md"))
    except subprocess.CalledProcessError:
        before = set()
    path = repo / "docs/intake-checklist.md"
    after = checked_commands(path.read_text(encoding="utf-8")) if path.exists() else set()
    orphans = sorted(c for c in after - before if c.removeprefix("intake:") not in named)
    ok = not bad and not orphans
    detail = (
        "every commit carries one Intake: trailer and every newly checked item has a commit"
        if ok
        else "; ".join(
            x
            for x in (f"bad commits: {bad}" if bad else "", f"checked with no commit: {orphans}" if orphans else "")
            if x
        )
    )
    return check("one-commit-per-item", ok, detail)


def rewrite_check(repo: Path, start: str, windows, reflog: Path | None) -> dict:
    """No rebase, reset or amend after the run started (or inside a goal session, given transcripts)."""
    since = when(git(repo, "log", "-1", "--format=%cI", start).strip())
    text = (
        reflog.read_text(encoding="utf-8")
        if reflog
        else git(repo, "reflog", "--date=iso-strict", "--format=%gd%x00%gs")
    )
    entries = []
    for line in text.splitlines():
        ref, _, subject = line.partition("\x00")
        m = re.search(r"\{(.+)\}", ref)
        if m:
            entries.append((when(m.group(1)), subject))
    if not any(t >= since for t, _ in entries):
        return check(
            "no-history-rewrite", False, "the reflog has no entries since the start; save a snapshot with --reflog"
        )
    hits = [
        s
        for t, s in entries
        if t >= since
        and REWRITE.match(s)
        and s != "reset: moving to HEAD"
        and (not windows or any(a <= t <= b for a, b in windows))
    ]
    return check("no-history-rewrite", not hits, "no rebase, reset or amend in the run" if not hits else f"ran: {hits}")


SKILL_NAME = re.compile(r"\bfullstack-dev-skills:[a-z][a-z0-9-]*\b")
# A decline claims nothing: "javascript-pro not loaded", "vue-expert/vue-expert-js not loaded", "vue-expert and
# vue-expert-js skipped (Vue 2 app)", or a clause whose verdict follows a semicolon ("vue-expert targets Vue 3; not
# loaded"). "skipped" and "declined" count only where the clause ends, so "skipped tests cite F-001" declines nothing.
_VERDICT = r"(?:not loaded|(?:skipped|declined)(?=\s*(?:$|[;.,(])))"
DECLINED = re.compile(
    rf"[\w:-]+(?:\s*(?:/|,|&|\band\b)\s*[\w:-]+)*\s+(?:skills?\s+)?(?:(?:was|were)\s+)?{_VERDICT}"
    rf"|(?:^|(?<=;)|(?<=: )|(?<=\())[^;\n]*;\s*{_VERDICT}",
    re.M,
)
ITEM_SKILL = "fullstack-dev-skills:intake:"  # the pre-0.5.0 layout: one command per item
ITEM_READ = re.compile(r"/references/intake/procedures/([a-z-]+)\.md$")  # 0.5.0: the intake command reads the procedure
ITEM_BRIEF = re.compile(r"/references/intake/procedures/([a-z-]+)\.md")  # 0.5.0: or names it in the agent's brief
CONTINUED = "This session is being continued from a previous conversation"


def checklist_items(repo: Path) -> list[tuple[str, bool, str]]:
    """Each `intake:<cmd>` item of the checklist: its command, whether it is checked, and its line plus note."""
    path = repo / "docs/intake-checklist.md"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    out = []
    for i, line in enumerate(lines):
        m = re.search(r"`intake:([a-z-]+)`", line)
        if not (m and line.lstrip().startswith("- [")):
            continue
        note = [line]
        for nxt in lines[i + 1 :]:
            if not nxt.startswith("  "):
                break
            note.append(nxt)
        out.append((m.group(1), line.lstrip().startswith("- [x]"), " ".join(note)))
    return out


def named_skills(text: str) -> set[str]:
    """Skills a note claims: `fullstack-dev-skills:<name>`, or a bare name this plugin ships, as a whole word."""
    text = DECLINED.sub("", text)  # "javascript-pro not loaded (no call sites)" claims nothing
    claimed = {m.split(":", 1)[1] for m in SKILL_NAME.findall(text)}
    for name in (
        d.name for d in (Path(__file__).resolve().parent.parent / "plugin" / "skills").iterdir() if d.is_dir()
    ):
        if re.search(rf"(?<![\w:/-]){re.escape(name)}(?![\w-])", text):
            claimed.add(name)
    return claimed


def item_opens(m: dict) -> list[str]:
    """Items whose window this record opens: a Skill call to an intake command, a Read of a procedure file, or an
    Agent call whose brief names one."""
    content = m.get("message", {}).get("content") if isinstance(m.get("message"), dict) else None
    out = []
    for c in content if isinstance(content, list) else []:
        if c.get("type") != "tool_use":
            continue
        if c.get("name") == "Skill" and str(c.get("input", {}).get("skill", "")).startswith(ITEM_SKILL):
            out.append(str(c["input"]["skill"]).removeprefix(ITEM_SKILL))
        else:
            pattern, field = {
                "Read": (ITEM_READ, "file_path"),
                "Agent": (ITEM_BRIEF, "prompt"),
                "Task": (ITEM_BRIEF, "prompt"),
            }.get(str(c.get("name")), (None, ""))
            if pattern and (r := pattern.search(str(c.get("input", {}).get(field, "")))):
                out.append(r.group(1))
    return out


def skill_uses(m: dict) -> list[str]:
    content = m.get("message", {}).get("content") if isinstance(m.get("message"), dict) else None
    return [
        str(c.get("input", {}).get("skill", ""))
        for c in (content if isinstance(content, list) else [])
        if c.get("type") == "tool_use" and c.get("name") == "Skill"
    ]


def timeline(
    paths: list[Path],
) -> tuple[list[tuple[str, datetime, datetime]], list[tuple[datetime, str]], list[datetime]]:
    """Item windows (cmd, start, end), Skill loads (time, skill) and compaction times from the goal sessions.

    A window opens at a Skill call to `fullstack-dev-skills:intake:<cmd>`, a Read of
    `references/intake/procedures/<cmd>.md`, or an Agent call whose brief names that file, and runs to the next
    one or the session's end. A subagent's loads count when their time falls inside a window.
    """
    windows, loads, compactions, side = [], [], [], []
    for p in paths:
        msgs = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        timed = [(when(m["timestamp"]), m) for m in msgs if m.get("timestamp")]
        if is_subagent(p):
            side += [(t, s) for t, m in timed for s in skill_uses(m)]
            continue
        opened = None
        for t, m in timed:
            content = m["message"].get("content", "") if isinstance(m.get("message"), dict) else ""
            if m.get("type") == "user" and (m.get("isCompactSummary") or text_of(content).startswith(CONTINUED)):
                compactions.append(t)
            loads += [(t, s) for s in skill_uses(m)]
            for cmd in item_opens(m):
                if opened:
                    windows.append((*opened, t))
                opened = (cmd, t)
        if opened:
            windows.append((*opened, timed[-1][0]))
    loads += [(t, s) for t, s in side if any(a <= t <= b for _, a, b in windows)]
    return windows, loads, compactions


def skills_check(repo: Path, tl) -> dict:
    """A skill a checklist note names is loaded by the end of the first naming item's window, and again after a compaction.

    The reload is due by the end of the next naming item's window after the compaction.
    """
    windows, loads, compactions = tl
    by_skill: dict[str, set[str]] = {}
    for cmd, _, note in checklist_items(repo):
        for name in named_skills(note):
            by_skill.setdefault(name, set()).add(cmd)
    bad = []
    for name, cmds in sorted(by_skill.items()):
        spans = sorted((a, b, c) for c, a, b in windows if c in cmds)
        times = [t for t, s in loads if s.split(":")[-1] == name]
        if not spans:
            bad.append(f"{name}: named by {sorted(cmds)}, which have no window in the transcripts")
        elif not any(t <= spans[0][1] for t in times):
            bad.append(f"{name}: not loaded by the end of intake:{spans[0][2]}")
        else:
            for c in compactions:
                nxt = next((s for s in spans if s[0] > c), None)  # the first naming item to start after it
                if nxt and not any(c < t <= nxt[1] for t in times):
                    bad.append(
                        f"{name}: not reloaded after the compaction at {c.isoformat()} by the end of intake:{nxt[2]}"
                    )
    return check(
        "skills-loaded",
        not bad,
        f"{len(by_skill)} skills named in checklist notes, each loaded before use" if not bad else f"{bad[:10]}",
    )


VOICE_SKILL = "writing-with-agents:human-voice"


def voice_check(repo: Path, tl) -> dict:
    """Each checked documentation item's note records its human-voice pass; a note naming the skill needs a call in its window."""
    missing, unbacked = [], []
    for cmd, checked, text in checklist_items(repo):
        if not checked or cmd not in DOCS or re.search(r"not present|\bN/A\b", text, re.I):
            continue
        if "human-voice" not in text.lower():
            missing.append(cmd)
        if VOICE_SKILL in text and tl:
            windows, loads, _ = tl
            spans = [(a, b) for c, a, b in windows if c == cmd]
            if not any(a <= t <= b for t, s in loads if s == VOICE_SKILL for a, b in spans):
                unbacked.append(cmd)
    ok = not missing and not unbacked
    detail = (
        "every documentation item's note records its human-voice pass"
        if ok
        else "; ".join(
            x
            for x in (
                f"no human-voice record in: {missing}" if missing else "",
                f"notes name {VOICE_SKILL} with no call in the item's window: {unbacked}" if unbacked else "",
            )
            if x
        )
    )
    return check("human-voice-pass", ok, detail)


TELL = re.compile(r"\u2014|(?:^[\s>*#-]*|[.!?][\"')\]]*\s+)(?:And|But)\s")


def tells_check(repo: Path) -> dict:
    """The prose of every intake doc carries no em dash and no sentence starting with "And " or "But ".

    Prose is outside frontmatter, fenced code and table rows, with inline code removed.
    """
    hits = []
    for rel, text in intake_docs(repo).items():
        fence = front = False
        for n, line in enumerate(text.splitlines(), 1):
            if n == 1 and line.strip() == "---":
                front = True
                continue
            if front:
                front = line.strip() != "---"
                continue
            if line.lstrip().startswith(("```", "~~~")):
                fence = not fence
                continue
            if fence or line.lstrip().startswith("|"):
                continue
            if TELL.search(re.sub(r"`[^`]*`", "", line)):
                hits.append(f"{rel}:{n}")
    return check(
        "human-voice-tells",
        not hits,
        "no em dash or sentence opening with And or But in intake prose" if not hits else f"tells at: {hits[:10]}",
    )


RECOVERY_FILES = ("intake-checklist.md", "intake-goal-prompt.md")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def compaction_check(paths: list[Path]) -> dict | None:
    """After each compaction in a goal session, the run re-reads the checklist and goal prompt before its next edit.

    None when no goal session compacted: the check only counts when a run exercised it.
    """
    seen, bad = 0, []
    for p in paths:
        msgs = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        pending = None  # files still to re-read since the last compaction
        for m in msgs:
            if m.get("type") == "system" and m.get("subtype") == "compact_boundary":
                seen += 1
                pending = set(RECOVERY_FILES)
                continue
            if pending is None or m.get("type") != "assistant":
                continue
            content = m["message"].get("content") if isinstance(m.get("message"), dict) else None
            for c in content if isinstance(content, list) else []:
                if c.get("type") != "tool_use":
                    continue
                inp = c.get("input", {})
                target = (
                    inp.get("file_path", "")
                    if c.get("name") == "Read"
                    else inp.get("command", "")
                    if c.get("name") == "Bash"
                    else ""
                )
                pending -= {f for f in pending if f in target}
                if not pending:
                    pending = None
                    break
                if c.get("name") in EDIT_TOOLS:
                    bad.append(f"{p.name[:8]}: edited before re-reading {sorted(pending)}")
                    pending = None
                    break
    if not seen:
        return None
    return check(
        "compaction-recovery",
        not bad,
        f"{seen} compaction(s), each followed by re-reading the checklist and goal prompt before any edit"
        if not bad
        else f"{bad}",
    )


def is_subagent(path: Path) -> bool:
    """A subagent transcript marks its records `isSidechain`; it never starts with the /goal prompt."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                return bool(json.loads(line).get("isSidechain"))
    return False


# The check set a score is out of. Bump it whenever a scored check is added, removed or changes its
# rule, then re-score every baseline run (scripts/eval_intake_baseline.py) before comparing runs.
def intake_path(repo: Path, rel: str) -> str:
    """`rel`, or `<name>-intake.md` beside it when an owner doc holds the path (references/intake/rules.md)."""
    beside = rel.removesuffix(".md") + "-intake.md"
    return beside if (repo / beside).is_file() else rel


def intake_docs(repo: Path) -> dict[str, str]:
    paths = (intake_path(repo, rel) for rel in INTAKE_DOCS)
    return {rel: (repo / rel).read_text(encoding="utf-8") for rel in paths if (repo / rel).is_file()}


def citations_check(repo: Path) -> dict:
    texts = intake_docs(repo)
    tracker = repo / "docs/intake-findings.md"
    if tracker.is_file():
        texts[str(tracker.relative_to(repo))] = tracker.read_text(encoding="utf-8")
    hits = [f"{rel}: {m.group(0)}" for rel, text in texts.items() for m in LINE_CITE.finditer(text)]
    return check(
        "symbol-citations",
        not hits,
        "every citation names a symbol" if not hits else f"line citations: {hits[:5]}",
    )


def findings(repo: Path) -> list[dict]:
    """Each `### F-NNN` section of the tracker: id, status and Tests: value."""
    p = repo / "docs/intake-findings.md"
    if not p.is_file():
        return []
    out = []
    for block in re.split(r"^### ", p.read_text(encoding="utf-8"), flags=re.M)[1:]:
        m = FINDING.match(block)
        if not m:
            continue
        status = re.search(r"\*\*Status:\*\*\s*([^\n]*)", block)
        tests = re.search(r"\*\*Tests:\*\*\s*([^\n]*)", block)
        out.append(
            {
                "id": f"F-{m.group(1)}",
                "status": status.group(1).strip() if status else "",
                "tests": tests.group(1).strip() if tests else "",
            }
        )
    return out


# a test id: a pytest node id (`path::Class::test`), `path::Class.method`, or a JS test title (`path::title`)
TEST_ID = re.compile(r"`([\w./-]+\.\w+)::([^`]+)`")


SETATTR = re.compile(r"""setattr\(\s*\w+\s*,\s*f(["'])(.*?)\1""")


PLACEHOLDER = re.compile(r"<[\w-]+>|\$\{[^}]*\}")


def placeholder_title(name: str) -> re.Pattern[str] | None:
    """A title cited with placeholders (`a <status> member`, `a ${status} member`) as a pattern, else None."""
    parts = PLACEHOLDER.split(name)
    return re.compile(r"(?:\$\{[^}]*\}|[^\n`'\"]+?)".join(map(re.escape, parts))) if len(parts) > 1 else None


def test_exists(path: Path, name: str) -> bool:
    if not path.is_file():
        return False
    last, text = name.split("::")[-1], path.read_text(encoding="utf-8")
    if (pattern := placeholder_title(last)) and pattern.search(text):
        return True  # a parameterized test, cited with its parameter left as a placeholder
    if re.fullmatch(r"[\w.]+", last):
        if re.search(rf"\b{re.escape(last.split('.')[-1])}\b", text):
            return True
    elif last in text:  # a title with spaces appears as written
        return True
    # a Python name built at runtime: setattr(Class, f"test_{op}_current", ...)
    for _, f in SETATTR.findall(text):
        if re.fullmatch(".+".join(map(re.escape, re.split(r"\{[^}]*\}", f))), last):
            return True
    # Jest's full name: a describe title and a test title joined by one space
    plain = text.replace("\\'", "'").replace('\\"', '"')
    q = "['\"`]"
    return any(
        re.search(rf"\bdescribe(?:\.\w+)*\(\s*{q}{re.escape(last[:i])}{q}", plain)
        and re.search(rf"\b(?:it|test)(?:\.\w+)*\(\s*{q}{re.escape(last[i + 1 :])}{q}", plain)
        for i, ch in enumerate(last)
        if ch == " "
    )


def evidence_check(repo: Path, suite_out: str = "") -> dict:
    """Every finding not invalid names a real test (`path::name`), or says why none can and names its evidence command.

    A name absent from its file still counts when the suite run or a runner's test listing printed it (a title
    built at runtime).
    """
    rows, bad = findings(repo), []
    for f in rows:
        if f["status"].startswith("invalid"):
            continue
        cited = TEST_ID.findall(f["tests"])
        if cited:
            gone = [
                f"{path}::{name}"
                for path, name in cited
                if not (
                    test_exists(repo / path, name)
                    or (suite_out and name.split("::")[-1] in suite_out)
                    or (
                        suite_out and (pattern := placeholder_title(name.split("::")[-1])) and pattern.search(suite_out)
                    )
                )
            ]
            if gone:
                bad.append(f"{f['id']} names missing tests {gone}")
        elif not re.match(r"none:.*evidence:\s*`[^`]+`", f["tests"]):
            bad.append(f"{f['id']} has no test and no evidence command")
    ok = bool(rows) and not bad
    detail = (
        f"{len(rows)} findings, each with its evidence" if ok else (f"{bad[:5]}" if rows else "no findings sections")
    )
    return check("findings-evidence", ok, detail)


OP_ROW = re.compile(r"^\|\s*(OP-\d+)\s*\|(.*)$", re.M)


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def matrix_check(repo: Path) -> dict:
    """The access matrix has a row per inventory operation and no unexamined cell (references/intake/access-control.md)."""
    if "document-api" in checklist_excuses(repo):
        return check("access-matrix", True, "no API: document-api is checked not present")
    api, authz = (
        repo / intake_path(repo, rel)
        for rel in ("docs/architecture/api-reference.md", "docs/security/authorization.md")
    )
    ops = section(api.read_text(encoding="utf-8"), "Operations") if api.is_file() else ""
    matrix = section(authz.read_text(encoding="utf-8"), "Access matrix") if authz.is_file() else ""
    inventory = [m[0] for m in OP_ROW.findall(ops) if "removed" not in m[1].lower()]
    rows = {m[0]: m[1] for m in OP_ROW.findall(matrix)}
    problems = []
    if not inventory:
        problems.append("no ## Operations inventory with OP-NNN rows")
    listed = re.search(r"\((\d+) routes?\b", ops)
    # more rows than the listing is fine: JOB/EVENT rows, a static mount, an expanded catch-all
    if listed and int(listed.group(1)) > len(inventory):
        problems.append(
            f"route listing counts {listed.group(1)}, inventory has only {len(inventory)}: a listed route is missing"
        )
    if not rows:
        problems.append("no ## Access matrix with OP-NNN rows")
    if missing := [op for op in inventory if op not in rows]:
        problems.append(f"operations missing from the matrix: {missing[:10]}")
    if unexamined := [op for op, cells in rows.items() if "[x]" in cells]:
        problems.append(f"rows with unexamined [x] cells: {unexamined[:10]}")
    detail = f"{len(inventory)} operations, each in the matrix, every cell examined"
    return check("access-matrix", not problems, detail if not problems else "; ".join(problems))


def index_check(repo: Path) -> dict:
    """The docs index links every doc, and the checklist and tracker name the same base commit.

    The index is docs/README.md, or docs/README-intake.md when the project has its own docs/README.md;
    then the owner's README is one of the docs the index must link.
    """
    problems = []
    index = intake_path(repo, "docs/README.md")
    readme = repo / index
    links = set(re.findall(r"\]\(([^)#\s]+)", readme.read_text(encoding="utf-8"))) if readme.is_file() else set()
    skip = {index, "docs/intake-checklist.md", "docs/intake-goal-prompt.md"}
    # git's view of docs/, so a file the run keeps out of git (a restricted findings file) isn't required
    listed = git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "--", "docs").splitlines()
    for rel in sorted(p for p in listed if p.endswith(".md")):
        if rel in skip or (rel.startswith("docs/specs/") and rel != "docs/specs/INDEX.md"):
            continue
        if rel.removeprefix("docs/") not in links:
            problems.append(f"{index} misses {rel}")
    sha = re.compile(r"\bat\s+(?:\S+\s+)?`?([0-9a-f]{7,40})`?")
    heads = []
    for rel in ("docs/intake-checklist.md", "docs/intake-findings.md"):
        p = repo / rel
        m = sha.search(p.read_text(encoding="utf-8")) if p.is_file() else None
        heads.append(m.group(1) if m else None)
    if None in heads:
        problems.append("checklist or tracker header names no base commit")
    elif not (heads[0].startswith(heads[1]) or heads[1].startswith(heads[0])):
        problems.append(f"checklist says {heads[0]}, tracker says {heads[1]}")
    return check(
        "docs-index", not problems, "README links every doc; one base commit" if not problems else f"{problems[:5]}"
    )


def prose_sentences(text: str) -> set[str]:
    """Normalized sentences of REPEAT_WORDS words or more, outside frontmatter, code, tables and the audit."""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.split(r"^#{2,3} Accuracy audit\b", text, flags=re.M)[0]
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith(("|", "#"))]
    out = set()
    for sentence in re.split(r"(?<=[.!?])\s+", " ".join(lines)):
        words = re.findall(r"[\w'`-]+", sentence.lower())
        if len(words) >= REPEAT_WORDS:
            out.add(" ".join(words))
    return out


def pristine_check(repo: Path) -> dict:
    """Intake docs: two-way related: links, citations that resolve, no sentence repeated across docs."""
    texts = intake_docs(repo)
    by_root = {rel.removeprefix("docs/"): text for rel, text in texts.items()}
    problems = []
    for rel, text in by_root.items():
        fm = guard_docs.frontmatter(text)
        missing = [k for k in ("command", "verified", "sources", "related") if k not in fm]
        if missing:
            problems.append(f"{rel}: frontmatter lacks {', '.join(missing)}")
        verified = fm.get("verified")
        if (
            verified
            and subprocess.run(
                ["git", "rev-parse", "--verify", "-q", f"{verified}^{{commit}}"], cwd=repo, capture_output=True
            ).returncode
        ):
            problems.append(f"{rel}: verified {verified} is not a commit")
        for other in guard_docs.related(text):
            target = repo / "docs" / other
            if not target.is_file():
                problems.append(f"{rel}: related {other} does not exist")
            elif rel not in guard_docs.related(target.read_text(encoding="utf-8")):
                problems.append(f"{rel} lists {other}, which does not list it back")
        cited = guard_docs.citations(text)
        vendored = guard_docs._ignored(repo, sorted({p for p, _ in cited if (repo / p).is_file()}))
        for path, symbol in cited:
            target = repo / path
            word = symbol.split(".")[-1]
            if path in vendored:
                problems.append(f"{rel}: {path}::{symbol} cites vendored or git-ignored code")
            elif not target.is_file() or not re.search(
                rf"\b{re.escape(word)}\b", target.read_text(encoding="utf-8", errors="replace")
            ):
                problems.append(f"{rel}: {path}::{symbol} does not resolve")
    seen: dict[str, str] = {}
    for rel, text in sorted(by_root.items()):
        for sentence in prose_sentences(text):
            if sentence in seen and seen[sentence] != rel:
                problems.append(f"repeated in {seen[sentence]} and {rel}: {sentence[:60]}")
            seen.setdefault(sentence, rel)
    return check("docs-pristine", not problems, "intake docs consistent" if not problems else f"{problems[:5]}")


CHECKS_VERSION = 15  # 2: empty-module docstring; 3: subagents feed skills-loaded only; 4: human-voice-pass; 5: docs and evidence; 6: test ids and declined skills; 7: access matrix; 8: runtime test titles from suite output; 9: skill and human-voice claims per item window, human-voice-tells, setattr and Jest full test names; 10: evidence before trailing turns, type in new test manifests; 11: access matrix allows more inventory rows than the route listing; 12: docs-pristine fails a citation into vendored or git-ignored code; 13: findings-evidence reads the runners' test listings, bug-tests-cite-findings ignores markers named in comments and docstrings and follows table-driven twins to their rows; 14: symbol-citations skips addresses (`0.0.0.0:8080`, `localhost:5432`), skills-loaded reads joined and semicolon declines, findings-evidence lists Jest, Django and node --test titles; 15: a test title cited with a <placeholder> or ${...} matches the parameterized test


def main() -> int:
    ap = argparse.ArgumentParser(description="Score one finished intake run against the intake guarantees.")
    ap.add_argument("--eval", type=Path, help="eval directory: every input below defaults to its eval.json")
    ap.add_argument("--run", help="the run's name in eval.json")
    ap.add_argument("--repo", type=Path)
    ap.add_argument("--start", help="the commit the intake run started from")
    ap.add_argument("--test-cmd", help="the characterization suite command, run in the repo")
    ap.add_argument(
        "--suite-green",
        action="store_true",
        help="count the suite as green from the run's saved test output, for re-scoring a run whose services are gone",
    )
    ap.add_argument(
        "--test-path",
        action="append",
        default=[],
        help="glob of a test tree beyond the built-in names, matched with fnmatch (`*` crosses folders)",
    )
    ap.add_argument("--transcript", type=Path, action="append", default=[])
    ap.add_argument("--reflog", type=Path, help="saved `git reflog --date=iso-strict --format=%%gd%%x00%%gs` output")
    ap.add_argument("--version", default="unknown", help="plugin version or commit the run used")
    ap.add_argument("--model", default="unknown")
    a = ap.parse_args()
    if a.eval:
        try:
            data, run = eval_dir.run(a.eval, a.run)
        except (OSError, LookupError, json.JSONDecodeError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        a.repo = a.repo or (eval_dir.path(a.eval, run["repo"]) if run.get("repo") else None)
        a.start = a.start or run.get("start")
        a.transcript = a.transcript or [eval_dir.path(a.eval, t) for t in run.get("transcripts", [])]
        a.reflog = a.reflog or (eval_dir.path(a.eval, run["reflog"]) if run.get("reflog") else None)
        a.test_cmd = a.test_cmd or run.get("test_cmd") or data.get("test_cmd")
        a.test_path += run.get("test_paths", data.get("test_paths", []))
        a.suite_green = a.suite_green or bool(run.get("suite_green"))
        a.version = run.get("plugin", a.version) if a.version == "unknown" else a.version
        a.model = run.get("model", a.model) if a.model == "unknown" else a.model
    if not a.repo or not a.start:
        ap.error("give --repo and --start, or --eval and --run with both in eval.json")
    try:
        start = git(a.repo, "rev-parse", "--verify", f"{a.start}^{{commit}}").strip()
        sessions = [
            t for t in a.transcript if not is_subagent(t)
        ]  # subagents feed the per-item skill and human-voice claims only
        t_checks, windows = transcript_checks(sessions) if sessions else ([], [])
        tl = timeline(a.transcript) if a.transcript else None
        ids = tracker_ids(a.repo)
        globs = a.test_path + declared_test_paths(a.repo)
        suite, suite_out = (
            (check("characterization-green", True, "green in the run's saved test output (--suite-green)"), "")
            if a.suite_green and not a.test_cmd
            else suite_check(a.repo, a.test_cmd)
        )
        checks = [
            docs_check(a.repo),
            check(
                "findings-tracker",
                bool(ids),
                f"docs/intake-findings.md holds {len(ids)} finding ids"
                if ids
                else "docs/intake-findings.md missing or holds no F-NNN ids",
            ),
            bug_tests_check(a.repo, start, ids or set(), globs),
            evidence_check(a.repo, suite_out + test_listing(a.repo, a.test_cmd)),
            citations_check(a.repo),
            index_check(a.repo),
            matrix_check(a.repo),
            pristine_check(a.repo),
            suite,
            diff_check(a.repo, start, globs),
            commits_check(a.repo, start),
            voice_check(a.repo, tl),
            tells_check(a.repo),
            rewrite_check(a.repo, start, windows, a.reflog),
            *t_checks,
        ]
        if a.transcript:
            checks.append(skills_check(a.repo, tl))
        # Optional checks run only when the run exercised them; they never enter the score
        optional = [c for c in (compaction_check(sessions),) if c]
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    score = sum(c["pass"] for c in checks)
    print(
        json.dumps(
            {
                "eval": "intake-run",
                "checks_version": CHECKS_VERSION,
                "workflow": "claude-skills intake",
                "start": a.start,
                "version": a.version,
                "model": a.model,
                "score": score,
                "total": len(checks),
                "checks": checks,
                "optional": optional,
            },
            indent=2,
        )
    )
    return 0 if score == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
