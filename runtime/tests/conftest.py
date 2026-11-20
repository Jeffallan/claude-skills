from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

PLAN = """# Demo plan

**Spec:** demo

## Completion Status

| Ticket | Status | Completed Date | Notes |
|--------|--------|----------------|-------|
| T1 | Pending | - | - |
| T2 | Pending | - | - |
| T3 | Pending | - | - |

## Execution Order

| # | Ticket | Summary | Risk | Dependencies |
|---|--------|---------|------|--------------|
| 1 | T1 | One | Low | None |
| 2 | T2 | Two | Low | T1 |
| 3 | T3 | Three | Low | None |

## Open questions

| # | Ticket | Question | Asked by |
|---|--------|----------|----------|
"""


class GitRepo:
    """A throwaway git repo with one commit, a demo spec plan and a src/tests layout."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "T")
        self.git("config", "commit.gpgsign", "false")
        self.write("docs/specs/todo/demo/implementation-plan.md", PLAN)
        self.write("src/app.py", "def add(a, b):\n    return a + b\n")
        self.write(
            "tests/test_app.py",
            "from src.app import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        )
        self.write("src/__init__.py", "")
        self.commit("init")

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.head()

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    @property
    def guard(self) -> Path:
        return self.root / ".git" / "ticket-guard"


@pytest.fixture
def git_repo(tmp_path, monkeypatch) -> GitRepo:
    repo = GitRepo(tmp_path / "work")
    monkeypatch.chdir(repo.root)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    return repo
