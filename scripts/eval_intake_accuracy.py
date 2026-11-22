"""Tally an intake run's accuracy against a gold set.

An accuracy pass (an agent, checked by a person) writes a mapping file: for each gold row, the run's
finding id that covers it, or null. This script checks the mapping against the gold file and prints
found/total, leaving out the rows the run's setup gave away.

Usage: python3 scripts/eval_intake_accuracy.py <gold.md> <mapping.json>
mapping.json: {"run": "run 2", "found": {"F-005": "F-012", "MISSED-1": null, ...}, "given": ["F-002", "F-003"]}
"run" names the scored run as the gold file's Source column does; rows from that source are left out.
"""

import json
from pathlib import Path
import re
import sys


def findings_table(text: str) -> dict[str, dict[str, str]]:
    """Each finding row of the gold file's Findings table, by id, as {column header: cell}."""
    lines = [ln for ln in text.split("## Findings", 1)[1].split("\n## ", 1)[0].splitlines() if ln.startswith("|")]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = {}
    for line in lines[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if re.fullmatch(r"(?:F|MISSED|ADDED)-\d+", cells[0]):
            rows[cells[0]] = dict(zip(header, cells, strict=False))
    return rows


def gold_rows(text: str) -> tuple[str, dict[str, str]]:
    """The gold version and each finding row's id with its Source (empty when the table has none)."""
    version = re.search(r"\*\*Version:\*\* (\d+)", text)
    rows = {i: row.get("Source", "") for i, row in findings_table(text).items()}
    return (version.group(1) if version else "?"), rows


def main(argv: list[str]) -> int:
    version, rows = gold_rows(Path(argv[0]).read_text(encoding="utf-8"))
    ids = list(rows)
    mapping = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    found, given = mapping.get("found", {}), set(mapping.get("given", []))
    # A run is never scored on rows it was the source of: those are found by construction
    own = {i for i, src in rows.items() if src and src == mapping.get("run")}
    unknown = sorted(set(found) - set(ids))
    unmapped = sorted(set(ids) - set(found) - given - own)
    if unknown or unmapped:
        print(f"mapping doesn't match gold v{version}: unknown {unknown}, unmapped {unmapped}", file=sys.stderr)
        return 2
    scored = [i for i in ids if i not in given and i not in own]
    hit = [i for i in scored if found.get(i)]
    missed = [i for i in scored if not found.get(i)]
    print(
        json.dumps(
            {
                "gold_version": version,
                "found": len(hit),
                "total": len(scored),
                "given": sorted(given),
                "own": sorted(own),
                "missed": missed,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
