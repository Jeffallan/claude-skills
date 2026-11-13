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
import fnmatch
import json
from pathlib import Path
import re
import subprocess
import sys

import eval_dir
from eval_workflow_run import REWRITE, check, git, transcript_checks, when

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
LINE_CITE = re.compile(r"`[\w./-]+\.\w+:\d+(-\d+)?`")
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


def bug_tests_check(repo: Path, start: str, ids: set[str], globs: list[str]) -> dict:
    """Every skipped or expected-fail test written by intake names a finding id the tracker knows.

    A helper that wraps a marker is checked where it is called, not where it is defined.
    """
    bad, unknown, seen = [], [], 0
    files = {}
    for rel in changed(repo, start):
        p = repo / rel
        if is_test(rel, globs) and p.exists():
            files[rel] = p.read_text(encoding="utf-8", errors="replace").splitlines()
    helpers = {
        n
        for lines in files.values()
        for i, line in enumerate(lines)
        if SKIP_MARK.search(line) and (n := marker_helper(lines, i))
    }
    call = re.compile(r"\b(" + "|".join(map(re.escape, sorted(helpers))) + r")\s*\(") if helpers else None
    for rel, lines in files.items():
        for i, line in enumerate(lines):
            if SKIP_MARK.search(line):
                if marker_helper(lines, i):
                    continue
            elif not (call and call.search(line) and not HELPER_DEF.search(line)):
                continue
            seen += 1
            near = " ".join(lines[max(0, i - 2) : i + 4])
            found = {m.group(1) for m in FINDING.finditer(near)}
            if not found:
                bad.append(f"{rel}:{i + 1}")
            unknown += [f"F-{f} ({rel}:{i + 1})" for f in found - ids]
    ok = not bad and not unknown
    detail = (
        f"{seen} skipped or expected-fail tests, each naming a tracked finding"
        if ok
        else f"no finding id: {bad}; not in the tracker: {unknown}"
    )
    return check("bug-tests-cite-findings", ok, detail)


def suite_check(repo: Path, cmd: str | None) -> dict:
    if not cmd:
        return check("characterization-green", False, "not run: pass --test-cmd with the project's test:all command")
    r = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    return check("characterization-green", r.returncode == 0, f"`{cmd}` exit {r.returncode}: {tail[0][:160]}")


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


def package_json_ok(repo: Path, start: str, rel: str) -> bool:
    """package.json may change only its scripts and devDependencies; a new one may also carry inert metadata."""
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
            if (repo / rel).exists() and package_json_ok(repo, start, rel):
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


def skills_check(repo: Path, paths: list[Path]) -> dict:
    """Every skill a checklist note names was loaded with the Skill tool in the goal session or its subagents."""
    path = repo / "docs/intake-checklist.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    claimed = {m.split(":", 1)[1] for m in SKILL_NAME.findall(text)}
    # bare names count too ("the test-master skill"): any skill this plugin ships, as a whole word
    for name in (d.name for d in (Path(__file__).resolve().parent.parent / "skills").iterdir() if d.is_dir()):
        if re.search(rf"(?<![\w:/-]){re.escape(name)}(?![\w-])", text):
            claimed.add(name)
    loaded = set()
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            if '"Skill"' not in line:
                continue
            m = json.loads(line)
            content = m.get("message", {}).get("content") if isinstance(m.get("message"), dict) else None
            for c in content if isinstance(content, list) else []:
                if c.get("type") == "tool_use" and c.get("name") == "Skill":
                    loaded.add(str(c.get("input", {}).get("skill", "")).split(":")[-1])
    missing = sorted(claimed - loaded)
    return check(
        "skills-loaded",
        not missing,
        f"{len(claimed)} skills named in checklist notes, all loaded"
        if not missing
        else f"named but never loaded: {missing}",
    )


VOICE_SKILL = "writing-with-agents:human-voice"


def voice_check(repo: Path, paths: list[Path]) -> dict:
    """Each checked documentation item's note records its human-voice pass; a note naming the skill needs a Skill call."""
    path = repo / "docs/intake-checklist.md"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    missing, claimed = [], False
    for i, line in enumerate(lines):
        m = re.search(r"`intake:([a-z-]+)`", line)
        if not (m and line.lstrip().startswith("- [x]") and m.group(1) in DOCS):
            continue
        note = [line]
        for nxt in lines[i + 1 :]:
            if not nxt.startswith("  "):
                break
            note.append(nxt)
        text = " ".join(note)
        if re.search(r"not present|\bN/A\b", text, re.I):
            continue
        if "human-voice" not in text.lower():
            missing.append(m.group(1))
        claimed |= VOICE_SKILL in text
    loaded = any(
        f'"{VOICE_SKILL}"' in line and '"Skill"' in line
        for p in paths
        for line in p.read_text(encoding="utf-8").splitlines()
    )
    unbacked = claimed and paths and not loaded
    ok = not missing and not unbacked
    detail = (
        "every documentation item's note records its human-voice pass"
        if ok
        else "; ".join(
            x
            for x in (
                f"no human-voice record in: {missing}" if missing else "",
                f"notes name {VOICE_SKILL} but no transcript loads it" if unbacked else "",
            )
            if x
        )
    )
    return check("human-voice-pass", ok, detail)


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


def evidence_check(repo: Path) -> dict:
    """Every finding not invalid names a real test (`path::name`), or says why none can and names its evidence command."""
    rows, bad = findings(repo), []
    for f in rows:
        if f["status"].startswith("invalid"):
            continue
        cited = guard_docs.citations(f["tests"])
        if cited:
            gone = [
                f"{path}::{name}"
                for path, name in cited
                if not (repo / path).is_file()
                or not re.search(rf"\b{re.escape(name.split('.')[-1])}\b", (repo / path).read_text(encoding="utf-8"))
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
    for p in sorted((repo / "docs").rglob("*.md")):
        rel = str(p.relative_to(repo))
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
        if "related" not in re.findall(r"^(\w+):", text.split("\n---", 1)[0] if text.startswith("---") else "", re.M):
            problems.append(f"{rel}: no related: frontmatter")
        for other in guard_docs.related(text):
            target = repo / "docs" / other
            if not target.is_file():
                problems.append(f"{rel}: related {other} does not exist")
            elif rel not in guard_docs.related(target.read_text(encoding="utf-8")):
                problems.append(f"{rel} lists {other}, which does not list it back")
        for path, symbol in guard_docs.citations(text):
            target = repo / path
            word = symbol.split(".")[-1]
            if not target.is_file() or not re.search(
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


CHECKS_VERSION = (
    5  # 2: empty-module docstring; 3: subagents feed skills-loaded only; 4: human-voice-pass; 5: docs and evidence
)


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
        sessions = [t for t in a.transcript if not is_subagent(t)]  # subagents feed skills-loaded only
        t_checks, windows = transcript_checks(sessions) if sessions else ([], [])
        ids = tracker_ids(a.repo)
        globs = a.test_path + declared_test_paths(a.repo)
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
            evidence_check(a.repo),
            citations_check(a.repo),
            index_check(a.repo),
            pristine_check(a.repo),
            check("characterization-green", True, "green in the run's saved test output (--suite-green)")
            if a.suite_green and not a.test_cmd
            else suite_check(a.repo, a.test_cmd),
            diff_check(a.repo, start, globs),
            commits_check(a.repo, start),
            voice_check(a.repo, a.transcript),
            rewrite_check(a.repo, start, windows, a.reflog),
            *t_checks,
        ]
        if a.transcript:
            checks.append(skills_check(a.repo, a.transcript))
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
