"""Compile `<docs root>/current-state.json` from the system description, the findings tracker and docs drift.

The file is compiled, never hand-edited: common-ground, the assumption-checker agent and the evals read it.
Every row names its source. A malformed table or an unknown status raises instead of writing a guess.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from ticket_guard import docs
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import git, top

SCHEMA = 1
STATUSES = ("wired", "built, not wired", "planned")
CLOSED = ("fixed", "invalid")  # findings that no longer describe the system
FINDING_COLUMNS = ("id", "finding", "severity", "area", "status")
LAST_UPDATED = re.compile(r"\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})\s+at\s+([0-9a-f]{7,40})")


def _section(text: str, heading: re.Pattern[str]) -> str | None:
    """The body of the first `## ` section whose heading matches, up to the next `## `."""
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = bool(heading.match(line[3:].strip()))
            continue
        if inside:
            out.append(line)
    return "\n".join(out) if inside else None


def _tables(text: str) -> list[list[list[str]]]:
    """Each Markdown table outside code fences, as rows of stripped cells, separator rows dropped."""
    tables, cur, fenced = [], [], False
    for line in [*text.splitlines(), ""]:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                cur.append(cells)
        elif cur:
            tables.append(cur)
            cur = []
    return tables


def _plain(cell: str) -> str:
    """The cell without a code span that wraps all of it (`` `wired` ``); code at one edge keeps its backticks."""
    c = cell.strip()
    return c[1:-1].strip() if len(c) > 1 and c[0] == c[-1] == "`" and "`" not in c[1:-1] else c


def components(sd_path: str, text: str) -> list[dict[str, str]]:
    body = _section(text, re.compile(r"(2\.\s*)?Components\b", re.I))
    if body is None:
        raise GuardError(f"{sd_path}: no '## 2. Components' section")
    for table in _tables(body):
        head = [h.lower() for h in table[0]]
        if "component" in head and "status" in head:
            name, status = head.index("component"), head.index("status")
            does = next((i for i, h in enumerate(head) if i not in (name, status)), None)
            out, bad = [], []
            for row in table[1:]:
                if len(row) != len(head):
                    bad.append(f"{sd_path}: component row has {len(row)} cells, the header has {len(head)}: {row}")
                    continue
                st = _plain(row[status])
                if st not in STATUSES:
                    bad.append(f"{_plain(row[name])}: unknown status '{st}' (one of: {', '.join(STATUSES)})")
                    continue
                out.append(
                    {
                        "name": _plain(row[name]),
                        "does": row[does] if does is not None else "",
                        "status": st,
                        "source": f"{sd_path}#2-components",
                    }
                )
            if bad:
                raise GuardError("\n".join(bad))
            return out
    raise GuardError(f"{sd_path}: no component table (Component and Status columns) in section 2")


def findings(path: str, text: str) -> list[dict[str, str]]:
    body = _section(text, re.compile(r"Summary$", re.I))
    tables = _tables(body or "")
    if not tables:
        raise GuardError(f"{path}: no findings table under '## Summary'")
    head = [h.lower() for h in tables[0][0]]
    missing = [c for c in FINDING_COLUMNS if c not in head]
    if missing:
        raise GuardError(f"{path}: the Summary table lacks columns {missing}")
    out = []
    for row in tables[0][1:]:
        if len(row) != len(head):
            raise GuardError(f"{path}: findings row has {len(row)} cells, the header has {len(head)}: {row}")
        rec = {c: _plain(row[head.index(c)]) for c in FINDING_COLUMNS}
        if rec["status"].lower() in CLOSED:
            continue
        out.append({**rec, "source": f"{path}#{rec['id']}"})
    return out


def build(cwd: Path) -> dict[str, Any]:
    repo, base = top(cwd), docs.root(cwd).rstrip("/")
    sd_path, f_path = f"{base}/system-description.md", f"{base}/intake-findings.md"
    if not (repo / sd_path).is_file():
        raise GuardError(f"{sd_path} is missing: run `intake create-system-description` first")
    sd = (repo / sd_path).read_text(encoding="utf-8")
    m = LAST_UPDATED.search(sd)
    if not m:
        raise GuardError(f"{sd_path}: no '**Last updated:** <YYYY-MM-DD> at <short-sha>' line")
    f_file = repo / f_path
    data = {
        "schema": SCHEMA,
        "built_at": {"head": git(cwd, "rev-parse", "HEAD"), "system_description": m.group(2), "date": m.group(1)},
        "components": components(sd_path, sd),
        "findings": findings(f_path, f_file.read_text(encoding="utf-8")) if f_file.is_file() else [],
        "drift": [{**r, "source": "guard docs-drift"} for r in docs.drift(cwd)],
    }
    problems = validate(data)
    if problems:
        raise GuardError("\n".join(problems))
    return data


def validate(data: Any) -> list[str]:
    """Shape errors in a current-state document; empty when it matches schema 1."""
    shape = {
        "components": ("name", "does", "status", "source"),
        "findings": (*FINDING_COLUMNS, "source"),
        "drift": ("doc", "verified", "reasons", "source"),
    }
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        return [f"schema is not {SCHEMA}"]
    out = []
    built = data.get("built_at")
    if not isinstance(built, dict) or any(not built.get(k) for k in ("head", "system_description", "date")):
        out.append("built_at needs head, system_description and date")
    for key, fields in shape.items():
        rows = data.get(key)
        if not isinstance(rows, list):
            out.append(f"{key} is not a list")
            continue
        for i, row in enumerate(rows):
            if not isinstance(row, dict) or any(f not in row for f in fields) or not row.get("source"):
                out.append(f"{key}[{i}] needs {', '.join(fields)} and a source")
            elif key == "components" and row["status"] not in STATUSES:
                out.append(f"components[{i}]: unknown status '{row['status']}'")
    return out


def write(cwd: Path) -> Path:
    data = build(cwd)
    path = top(cwd) / docs.root(cwd).rstrip("/") / "current-state.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
