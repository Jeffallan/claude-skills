"""An eval directory: `eval.json` names the gold set and every run, with paths relative to the directory.

Eval data (gold sets, run bundles, transcripts, baselines) lives in a private results repo, never in this
one; the scorers here take the directory's path. The format is in evals/README.md.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def path(eval_dir: Path, rel: str) -> Path:
    """`rel` resolved from the eval directory; absolute and `~` paths are kept."""
    return eval_dir / Path(rel).expanduser()


def manifest(eval_dir: Path) -> dict[str, Any]:
    return json.loads((eval_dir / "eval.json").read_text(encoding="utf-8"))


def run(eval_dir: Path, name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """(manifest, run entry). LookupError when eval.json has no run of that name."""
    data = manifest(eval_dir)
    for entry in data["runs"]:
        if entry["run"] == name:
            return data, entry
    raise LookupError(f'no run "{name}" in {eval_dir / "eval.json"}')
