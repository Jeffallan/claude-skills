"""Boundary checks for ticket:complete: clean re-run, RED replay, tamper scan, evidence summary."""

from __future__ import annotations

import ast
from collections.abc import Iterator
import contextlib
from fnmatch import fnmatch
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

from ticket_guard import docs, evidence, files, marker, runs, settings
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import git, top

SKIP = re.compile(
    r"@pytest\.mark\.(skip|skipif|xfail)|pytest\.(skip|xfail)\(|@unittest\.(skip|expectedFailure)"
    r"|\.(skip|only|todo)\(|\b(xit|xdescribe|xtest|fit|fdescribe)\(|t\.Skip(Now|f)?\("
    r"|#\[ignore\]|@(Disabled|Ignore)\b"
)
ASSERTION = re.compile(r"\bassert|\bexpect\(|\bshould\b|\.toBe|t\.(Error|Fatal)|require\.|\braises\(")
# A file that defines no test case (a shared helper under tests/) is not held to the assertion rule.
TEST_CASE = re.compile(r"\b(it|test|specify)(\.\w+)*\s*\(|\bit\s+['\"]|\bdef test_|\bfunc Test\w*\(|@Test\b|#\[test\]")
SNAPSHOTS = ("*__snapshots__/*", "*.snap", "*.golden", "*/golden/*", "*/snapshots/*")
MOCK_ASSERT = re.compile(r"^assert_(not_)?(called|any_call|has_calls|awaited)")


def context(cwd: Path, ticket: str | None = None) -> dict[str, Any]:
    """Ticket, start SHA and mode from the marker, or from the evidence when the marker is gone."""
    data = marker.read(cwd)
    if data is not None and ticket in (None, data["ticket"]):
        return {
            "ticket": data["ticket"],
            "start_sha": data["start_sha"],
            "mode": data["mode"],
            "marker": True,
        }
    if ticket is None:
        raise GuardError("no marker: pass --ticket")
    starts = [r for r in evidence.records(cwd, ticket) if r["event"] == "marker_start"]
    if not starts:
        raise GuardError(f"no evidence record of a start for ticket {ticket}")
    return {
        "ticket": ticket,
        "start_sha": starts[-1]["start_sha"],
        "mode": starts[-1]["mode"],
        "marker": False,
    }


@contextlib.contextmanager
def worktree(cwd: Path, sha: str) -> Iterator[Path]:
    base = Path(tempfile.mkdtemp(prefix="guard-wt-"))
    path = base / "wt"
    git(cwd, "worktree", "add", "-q", "--detach", str(path), sha)
    try:
        yield path
    finally:
        git(cwd, "worktree", "remove", "--force", str(path), check=False)
        shutil.rmtree(base, ignore_errors=True)
        git(cwd, "worktree", "prune", check=False)


def _copy(src_root: Path, dst_root: Path, rels: list[str]) -> None:
    for rel in rels:
        src = src_root / rel
        dst = dst_root / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        else:
            dst.unlink(missing_ok=True)


def _record(cwd: Path, ticket: str, check: str, run: dict[str, Any], passed: bool, **extra: Any) -> dict[str, Any]:
    run.pop("output", None)
    return evidence.append(cwd, ticket, "boundary", check=check, passed=passed, **run, **extra)


def _setup_commands(cwd: Path) -> list[str]:
    value = settings.get(cwd, "setup") or []
    if not isinstance(value, list) or not all(isinstance(c, str) for c in value):
        raise GuardError("setup must be a list of shell strings in the workflow config")
    return value


def _run_setup(cwd: Path, ticket: str, check: str, wt: Path, commands: list[str]) -> dict[str, Any] | None:
    """Run `setup` in the worktree (GH4: a fresh worktree has no node_modules). A failure's record."""
    for cmd in commands:
        run = runs.execute(cwd, ticket, f"{check}-setup", [cmd], run_in=wt)
        if run["exit_code"] != 0:
            return _record(cwd, ticket, check, run, False, reason=f"setup command failed: {cmd}")
    return None


def rerun(
    cwd: Path, command: list[str] | None = None, ticket: str | None = None, spec: str | None = None
) -> dict[str, Any]:
    """Run the verification commands on HEAD plus the uncommitted work, in a fresh worktree.

    With `spec`, no ticket is needed: the spec-level recheck records under `<spec>-recheck`.
    """
    if spec is not None:
        if not settings.spec_dir(cwd, spec).is_dir():
            raise GuardError(f"no spec {spec} under the specs root")
        ctx = {"ticket": f"{spec}-recheck"}
    else:
        ctx = context(cwd, ticket)
    commands = [command] if command else [[c] for c in settings.get(cwd, "verify") or []]
    if not commands and spec is not None:
        raise GuardError("nothing to run: give a command or set `verify` in the workflow config")
    if not commands:
        green = runs.latest(evidence.current(cwd, ctx["ticket"]), "green", valid_only=False)
        if green is None:
            raise GuardError("nothing to run: give a command, set `verify` in the workflow config, or record GREEN")
        commands = [green.get("argv") or [green["command"]]]
    setup = _setup_commands(cwd)
    root = top(cwd)
    diff = git(cwd, "diff", "--binary", "HEAD")
    untracked = [p for p in git(cwd, "ls-files", "--others", "--exclude-standard").splitlines() if p]
    with worktree(cwd, "HEAD") as wt:
        if diff:
            subprocess.run(
                ["git", "apply", "--whitespace=nowarn"],
                cwd=wt,
                input=diff + "\n",
                text=True,
                check=True,
            )
        _copy(root, wt, untracked)
        failed = _run_setup(cwd, ctx["ticket"], "rerun", wt, setup)
        if failed is not None:
            return failed
        result = None
        for cmd in commands:
            run = runs.execute(cwd, ctx["ticket"], "rerun", cmd, echo=True, run_in=wt)
            result = _record(cwd, ctx["ticket"], "rerun", run, run["exit_code"] == 0)
            if not result["passed"]:
                break
    assert result is not None
    return result


def red_replay(cwd: Path, ticket: str | None = None) -> dict[str, Any]:
    """Only the ticket's test files, applied to the start SHA, must fail."""
    ctx = context(cwd, ticket)
    red = runs.latest(evidence.current(cwd, ctx["ticket"]), "red")
    if red is None:
        raise GuardError("no valid RED record to replay")
    if red.get("red_type") == "refactor":
        return evidence.append(
            cwd,
            ctx["ticket"],
            "boundary",
            check="red-replay",
            passed=True,
            skipped="refactor ticket (answer 102)",
        )
    setup = _setup_commands(cwd)
    with worktree(cwd, ctx["start_sha"]) as wt:
        _copy(top(cwd), wt, red["test_files"])
        failed = _run_setup(cwd, ctx["ticket"], "red-replay", wt, setup)
        if failed is not None:
            return failed
        run = runs.execute(
            cwd,
            ctx["ticket"],
            "red-replay",
            red.get("argv") or [red["command"]],
            run_in=wt,
        )
    passed = run["exit_code"] != 0
    return _record(
        cwd,
        ctx["ticket"],
        "red-replay",
        run,
        passed,
        reason=None if passed else "the new tests passed against the start SHA",
    )


def _python_flags(rel: str, text: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    flags = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) or not node.name.startswith("test"):
            continue
        asserts = any(isinstance(n, ast.Assert) for n in ast.walk(node))
        calls = [
            n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            for n in ast.walk(node)
            if isinstance(n, ast.Call)
        ]
        mock_asserts = [c for c in calls if MOCK_ASSERT.match(c)]
        other_asserts = [
            c for c in calls if c not in mock_asserts and (c.startswith("assert") or c in ("raises", "warns"))
        ]
        if not asserts and not other_asserts:
            kind = "mock-only" if mock_asserts else "no-assertion"
            detail = "asserts only on mocks" if mock_asserts else "has no assertion"
            flags.append(
                {
                    "kind": kind,
                    "file": rel,
                    "line": node.lineno,
                    "detail": f"{node.name} {detail}",
                }
            )
    return flags


def scan(cwd: Path, start_sha: str) -> list[dict[str, Any]]:
    root = top(cwd)
    is_test = files.test_matcher(cwd)
    status = git(cwd, "diff", "--name-status", "--no-renames", start_sha).splitlines()
    changes = {line.split("\t", 1)[1]: line[0] for line in status if "\t" in line}
    for rel in git(cwd, "ls-files", "--others", "--exclude-standard").splitlines():
        if rel:
            changes[rel] = "A"
    flags: list[dict[str, Any]] = []
    for rel, kind in sorted(changes.items()):
        snapshot = any(fnmatch(rel, p) for p in SNAPSHOTS)
        if snapshot:
            if kind in "MD":
                flags.append(
                    {
                        "kind": "snapshot-changed",
                        "file": rel,
                        "detail": "snapshot or golden output changed",
                    }
                )
            continue
        if not is_test(rel):
            continue
        if kind == "D":
            flags.append({"kind": "deleted-test", "file": rel, "detail": "test file deleted"})
            continue
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        if kind == "A":
            added = list(enumerate(text.splitlines(), 1))
        else:
            diff = git(cwd, "diff", "-U0", start_sha, "--", rel).splitlines()
            added = [(0, line[1:]) for line in diff if line.startswith("+") and not line.startswith("+++")]
        for line_no, line in added:
            if SKIP.search(line):
                flags.append(
                    {
                        "kind": "skip-added",
                        "file": rel,
                        "line": line_no or None,
                        "detail": line.strip(),
                    }
                )
        if rel.endswith(".py"):
            flags.extend(_python_flags(rel, text))
        elif TEST_CASE.search(text) and not ASSERTION.search(text):
            flags.append(
                {
                    "kind": "no-assertion",
                    "file": rel,
                    "detail": "no assertion in the file",
                }
            )
    for index, flag in enumerate(flags, 1):
        flag["id"] = f"TS{index}"
    return flags


def tamper_scan(cwd: Path, reasons: dict[str, str], ticket: str | None = None) -> dict[str, Any]:
    ctx = context(cwd, ticket)
    if ctx["mode"] == "goal":
        reasons = {}  # the agent must not clear its own flags (answer 101); block the ticket instead
    flags = scan(cwd, ctx["start_sha"])
    for flag in flags:
        flag["reason"] = reasons.get(flag["id"])
    passed = all(f["reason"] for f in flags)
    return evidence.append(cwd, ctx["ticket"], "tamper_scan", flags=flags, passed=passed, mode=ctx["mode"])


def _last(recs: list[dict[str, Any]], event: str, check: str | None = None) -> dict[str, Any] | None:
    for rec in reversed(recs):
        if rec["event"] == event and (check is None or rec.get("check") == check):
            return rec
    return None


def summary(cwd: Path, ticket: str | None = None, accept_lost: bool = False) -> tuple[str, list[str]]:
    """(notes line for the Completion Status table, missing evidence). Missing evidence fails."""
    ctx = context(cwd, ticket)
    recs = evidence.current(cwd, ctx["ticket"])
    missing: list[str] = []
    parts: list[str] = []
    red = runs.latest(recs, "red")
    green = runs.latest(recs, "green", valid_only=False)
    if red is None:
        missing.append("RED: no valid RED record")
    else:
        parts.append(f"RED `{red['command']}` exit {red['exit_code']}")
    if green is None or green["exit_code"] != 0 or green.get("tests_changed"):
        missing.append("GREEN: no passing GREEN record with the RED tests unchanged")
    else:
        parts.append(f"GREEN `{green['command']}` exit 0")
        if green.get("amended_tests"):
            parts.append(f"tests amended after RED with approval: {', '.join(green['amended_tests'])}")
    if red is not None:
        parts.append(f"tests sha256 {red['test_files_digest'][:12]} ({len(red['test_files'])} files)")
    for check, label in (("rerun", "clean re-run"), ("red-replay", "RED replay")):
        rec = _last(recs, "boundary", check)
        if rec is None or not rec["passed"]:
            missing.append(f"{label}: no passing record")
        elif rec.get("skipped"):
            parts.append(f"{label} skipped ({rec['skipped']})")
        else:
            parts.append(f"{label} exit {rec['exit_code']}")
    scan_rec = _last(recs, "tamper_scan")
    if scan_rec is None or not scan_rec["passed"]:
        missing.append("tamper scan: not run, or flags without a reason")
    else:
        flags = scan_rec["flags"]
        parts.append(
            "tamper scan: "
            + ("; ".join(f"{f['id']} {f['kind']} {f['file']} ({f['reason']})" for f in flags) or "no flags")
        )
    docs_text, docs_missing = docs.summary_part(docs.statuses(cwd, ctx["start_sha"], recs))
    missing += docs_missing
    if docs_text:
        parts.append(docs_text)
    lifecycle = [r["event"] for r in recs if r["event"].startswith("marker_")]
    if not ctx["marker"] and lifecycle[-1:] != ["marker_clear"]:
        if ctx["mode"] == "goal":
            missing.append("marker lost (no logged clear): in goal mode, block the ticket with `guard block`")
        elif not accept_lost:
            missing.append(
                "marker lost (no logged clear): the owner may pass --accept-lost-marker once the boundary checks pass"
            )
        else:
            parts.append("marker lost, accepted by the owner")
    return "; ".join(parts), missing
