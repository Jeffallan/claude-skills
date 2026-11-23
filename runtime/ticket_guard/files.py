"""Which files are tests, what changed since the start SHA, and digests of both."""

from __future__ import annotations

from collections.abc import Callable
from fnmatch import fnmatch
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

from ticket_guard import settings
from ticket_guard.gitutil import git, top

TEST_DIRS = frozenset({"tests", "test", "__tests__", "spec"})
TEST_NAMES = (
    "test_*.py",
    "*_test.py",
    "*_test.go",
    "*.test.*",
    "*.spec.*",
    "*_spec.rb",
)


def test_matcher(cwd: Path) -> Callable[[str], bool]:
    """Default convention; `guard.testPatterns` (fnmatch on the repo path) replaces it."""
    patterns = settings.get(cwd, "guard.testPatterns")
    if patterns:
        return lambda rel: any(fnmatch(rel, p) for p in patterns)

    def default(rel: str) -> bool:
        parts = rel.split("/")
        return bool(TEST_DIRS & set(parts[:-1])) or any(fnmatch(parts[-1], n) for n in TEST_NAMES)

    return default


def changed_since(cwd: Path, sha: str) -> list[str]:
    """Tracked files changed against `sha` (committed or not) plus untracked files."""
    tracked = git(cwd, "diff", "--name-only", "--no-renames", sha).splitlines()
    untracked = git(cwd, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted({p for p in (*tracked, *untracked) if p})


def all_tests(cwd: Path) -> list[str]:
    listed = git(cwd, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    root, is_test = top(cwd), test_matcher(cwd)
    return sorted(p for p in listed if p and is_test(p) and (root / p).is_file())


def digest(cwd: Path, rels: list[str]) -> str:
    """sha256 over each path and its content (a missing file counts as deleted)."""
    root = top(cwd)
    h = hashlib.sha256()
    for rel in sorted(rels):
        path = root / rel
        content = path.read_bytes() if path.is_file() else b"<deleted>"
        h.update(rel.encode() + b"\0" + hashlib.sha256(content).digest())
    return h.hexdigest()


def tree_hash(cwd: Path) -> str:
    """The git tree of the working tree as it is now, through a throwaway index."""
    root = top(cwd)
    fd, index = tempfile.mkstemp(prefix="guard-index-")
    os.close(fd)
    os.unlink(index)
    env = {**os.environ, "GIT_INDEX_FILE": index}
    try:
        subprocess.run(["git", "add", "-A"], cwd=root, env=env, check=True, capture_output=True)
        out = subprocess.run(
            ["git", "write-tree"],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        return out.stdout.strip()
    finally:
        Path(index).unlink(missing_ok=True)
