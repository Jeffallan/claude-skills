"""Settings from the project's `.claude/workflow-config.json` (missing file or key: defaults)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ticket_guard.errors import GuardError
from ticket_guard.gitutil import top

CONFIG = ".claude/workflow-config.json"
DEFAULTS: dict[str, Any] = {
    "specsRoot": "docs/specs",
    "guard.markerWarnHours": 24,
    "guard.greenFailLimit": 3,  # provisional key: answer 84 says "about 3"
    "goal.batchSize": 3,
    # Pre-approves the guard skill in `claude -p`, where a denied Skill call leaves batches unguarded.
    "goal.allow": ["Skill(fullstack-dev-skills:ticket-guard)"],
    # A bare `claude -p` refuses every edit (pilot F6).
    "goal.permissionMode": "auto",
}


def load(cwd: Path) -> dict[str, Any]:
    path = top(cwd) / CONFIG
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GuardError(f"{CONFIG} does not parse: {exc}") from exc
    return data if isinstance(data, dict) else {}


def get(cwd: Path, key: str) -> Any:
    """A dotted key such as 'guard.markerWarnHours', falling back to DEFAULTS."""
    value: Any = load(cwd)
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return DEFAULTS.get(key)
        value = value[part]
    return value


def spec_dir(cwd: Path, spec: str) -> Path:
    """The spec's folder under todo/, or completed/ when it has moved there."""
    root = top(cwd) / get(cwd, "specsRoot")
    todo = root / "todo" / spec
    done = root / "completed" / spec
    return done if done.is_dir() and not todo.is_dir() else todo
