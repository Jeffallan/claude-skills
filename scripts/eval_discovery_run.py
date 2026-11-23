#!/usr/bin/env python3
"""Score one discovery run (`discovery:create`, then `discovery:approve`) against a gold set.

Reads the topic folder (`discovery.md`, and `synthesis.md` when research ran) and prints a JSON result:
whether each gold item got its route, each gold blocking decision was raised, and each gold ticket was
created. The gold set lives in a private eval directory (evals/README.md).

Usage: eval_discovery_run.py (--eval <dir> --run <name> | --repo <repo> --topic <topic> --gold <gold.json>)
Exit codes: 0 = every check passed, 1 = a check failed, 2 = bad input
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import eval_dir
from eval_workflow_run import cells, check, report, skip


def table(text: str, heading: str) -> list[dict[str, str]]:
    """Rows of the first table under `## <heading>`, keyed by lowercased header."""
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    lines = [ln.strip() for ln in (m.group(1) if m else "").splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    split = [cells(ln) for ln in lines]
    head = [h.lower() for h in split[0]]
    return [dict(zip(head, row, strict=False)) for row in split[2:]]


def topic_dir(repo: Path, topic: str) -> Path:
    cfg = repo / ".claude/workflow-config.json"
    root = json.loads(cfg.read_text()).get("specsRoot", "docs/specs") if cfg.exists() else "docs/specs"
    for state in ("todo", "completed"):
        d = repo / root / state / "discovery" / topic
        if d.is_dir():
            return d
    raise OSError(f"no discovery topic {topic} under {root}/todo or {root}/completed")


def created_ids(text: str) -> set[str]:
    """Proposed tickets the topic records as created: `discovery:approve` writes "Created as <ID>" next to the ticket,
    on a line that names it (its table row, or `Created as ENG-1: P1`) or under its `### P<n>:` heading."""
    out = {p for line in text.splitlines() if "Created as" in line for p in re.findall(r"\bP\d+\b", line)}
    for m in re.finditer(r"^###\s+(P\d+)\b(.*?)(?=^##|\Z)", text, re.M | re.S):
        if "Created as" in m.group(2):
            out.add(m.group(1))
    return out


def chosen(row: dict[str, str]) -> bool:
    """`discovery:approve` records the answer in the decision's row: "Chosen: B, ..." in a cell, or a Chosen column."""
    return bool(row.get("chosen", "").strip("-*` ")) or any(
        re.search(r"\bchosen\b\W*\w", v, re.I) for v in row.values()
    )


def approve_checks(folder: Path, gold: dict, texts: list[str], created_titles: list[str]) -> list[dict]:
    """Checks on what `discovery:approve` leaves behind; each is skipped when its gold key is absent."""
    out = []
    if "not_tickets" in gold:
        made = [p for p in gold["not_tickets"] if any(re.search(p, t, re.I) for t in created_titles)]
        out.append(
            check("dropped-not-created", not made, "no dropped ticket created" if not made else f"created: {made}")
        )
    else:
        out.append(skip("dropped-not-created", "no not_tickets in gold"))
    if "status" in gold:
        # approve's no-tickets path moves the topic to <specsRoot>/completed/discovery/; topic_dir prefers todo/
        done = folder.parent.parent.name == "completed"
        if gold["status"] == "completed":
            ok, got = done, "under completed/" if done else "still under todo/"
        else:
            topic = folder / "discovery.md"
            status = re.search(
                r"^\*\*Status:\*\*\s*Tickets created",
                topic.read_text(encoding="utf-8") if topic.exists() else "",
                re.M | re.I,
            )
            ok = not done and bool(status)
            got = "status Tickets created in todo/" if ok else "no Tickets created status in todo/"
        out.append(check("topic-status", ok, f"{got}, want {gold['status']}"))
    else:
        out.append(skip("topic-status", "no status in gold"))
    if "synthesis" in gold:
        syn = folder / "synthesis.md"
        if not gold["synthesis"]:
            out.append(
                check("synthesis", not syn.exists(), "no synthesis.md" if not syn.exists() else "synthesis.md written")
            )
        elif not syn.exists():
            out.append(check("synthesis", False, "no synthesis.md"))
        else:
            found = table(syn.read_text(encoding="utf-8"), "Findings")
            bare = [r.get("#", "?") for r in found if not re.search(r"\bsources/\S", r.get("sources", ""))]
            ok = bool(found) and not bare
            out.append(
                check(
                    "synthesis",
                    ok,
                    f"{len(found)} findings, each citing sources/" if ok else f"uncited: {bare or 'no findings'}",
                )
            )
    else:
        out.append(skip("synthesis", "no synthesis in gold"))
    if gold.get("decisions"):
        rows = [r for t in texts for r in table(t, "Blocking decisions")]
        open_ = [
            p
            for p in gold["decisions"]
            if not any(re.search(p, r.get("decision", ""), re.I) and chosen(r) for r in rows)
        ]
        out.append(
            check(
                "decisions-recorded",
                not open_,
                "every gold decision records its choice" if not open_ else f"no choice: {open_}",
            )
        )
    else:
        out.append(skip("decisions-recorded", "no decisions in gold"))
    return out


def score(folder: Path, gold: dict) -> list[dict]:
    texts = [
        (folder / f).read_text(encoding="utf-8") for f in ("discovery.md", "synthesis.md") if (folder / f).exists()
    ]
    items = table(texts[0], "Features") if texts else []
    wrong = []
    for pattern, route in gold.get("routes", {}).items():
        hit = [r for r in items if re.search(pattern, r.get("item", ""), re.I)]
        # The gold route is a regex so it can list alternatives ("Clear|Feature Forge"); the whole route must match.
        if not hit or not re.fullmatch(route, hit[0].get("route", "").strip(), re.I):
            wrong.append(f"{pattern}: {hit[0].get('route') if hit else 'missing'}, want {route}")
    decisions = [r.get("decision", "") for t in texts for r in table(t, "Blocking decisions")]
    missed = [p for p in gold.get("decisions", []) if not any(re.search(p, d, re.I) for d in decisions)]
    tickets = {r.get("#", ""): r.get("title", "") for t in texts for r in table(t, "Proposed tickets")}
    created = {p for t in texts for p in created_ids(t)}
    created_titles = [tickets.get(p, "") for p in created]
    not_created = [p for p in gold.get("tickets", []) if not any(re.search(p, t, re.I) for t in created_titles)]
    return [
        check("routing", not wrong, f"{len(gold.get('routes', {}))} items routed as gold" if not wrong else str(wrong)),
        # An empty gold list tests nothing, so the check is skipped rather than passed
        check("blocking-decisions", not missed, "every gold decision raised" if not missed else f"missing: {missed}")
        if gold.get("decisions")
        else skip("blocking-decisions", "no decisions in gold"),
        check(
            "approved-tickets",
            not not_created,
            "every gold ticket created" if not not_created else f"not created: {not_created}",
        )
        if gold.get("tickets")
        else skip("approved-tickets", "no tickets in gold"),
        *approve_checks(folder, gold, texts, created_titles),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Score one discovery run against a gold set.")
    ap.add_argument("--eval", type=Path, help="eval directory: every input below defaults to its eval.json")
    ap.add_argument("--run", help="the run's name in eval.json")
    ap.add_argument("--repo", type=Path)
    ap.add_argument("--topic")
    ap.add_argument("--gold", type=Path)
    a = ap.parse_args()
    try:
        if a.eval:
            data, run = eval_dir.run(a.eval, a.run)
            a.repo = a.repo or (eval_dir.path(a.eval, run["repo"]) if run.get("repo") else None)
            a.gold = a.gold or (eval_dir.path(a.eval, data["gold"]) if data.get("gold") else None)
            a.topic = a.topic or run.get("topic")
        if not (a.repo and a.gold):
            ap.error("give --repo and --gold, or --eval and --run with both in eval.json")
        gold = json.loads(a.gold.read_text())
        checks = score(topic_dir(a.repo, a.topic or gold["topic"]), gold)
    except (OSError, LookupError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return report("discovery", checks)


if __name__ == "__main__":
    sys.exit(main())
