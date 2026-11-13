"""Small git helpers and the ticket-guard paths under the git directory."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from ticket_guard.errors import GuardError, NotARepo

GUARD_DIR = "ticket-guard"


def git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise GuardError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.rstrip()  # keep leading spaces: porcelain status columns


def git_dir(cwd: Path) -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def guard_dir(cwd: Path) -> Path:
    found = git_dir(cwd)
    if found is None:
        raise NotARepo(f"not a git repository: {cwd}")
    return found / GUARD_DIR


def top(cwd: Path) -> Path:
    return Path(git(cwd, "rev-parse", "--show-toplevel"))


def head(cwd: Path) -> str:
    return git(cwd, "rev-parse", "HEAD")


def branch(cwd: Path) -> str:
    return git(cwd, "branch", "--show-current")


def write_json(path: Path, data: Any) -> None:
    """Write to a temp file in the same folder, then rename, so readers never see half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
