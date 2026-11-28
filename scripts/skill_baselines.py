"""Extract product/version baseline pairs from skill SKILL.md frontmatter."""

import argparse
import json
from pathlib import Path
import re
import sys

DEFAULT_SKILLS_DIR = Path("plugin/skills")
BASELINE_RE = re.compile(r"^\s+baseline:\s*(.+)$")


def _extract_frontmatter(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:idx]
    return []


def _parse_baseline_value(raw: str) -> list[tuple[str, str]]:
    cleaned = raw.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        cleaned = cleaned[1:-1].strip()
    pairs: list[tuple[str, str]] = []
    for item in cleaned.split(","):
        entry = item.strip()
        if not entry:
            continue
        parts = entry.rsplit(maxsplit=1)
        if len(parts) == 2:
            pairs.append((parts[0], parts[1]))
        else:
            pairs.append((parts[0], ""))
    return pairs


def read_baselines(skills_dir: Path = DEFAULT_SKILLS_DIR) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md"), key=lambda p: p.parent.name):
        source = skill_md.parent.name
        frontmatter = _extract_frontmatter(skill_md.read_text(encoding="utf-8"))
        for line in frontmatter:
            match = BASELINE_RE.match(line)
            if match is None:
                continue
            for product, version in _parse_baseline_value(match.group(1)):
                records.append({"source": source, "product": product, "version": version})
            break
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract skill baselines as JSON.")
    parser.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR, help="Path to skills directory.")
    parser.add_argument("--output", type=Path, default=None, help="Write JSON output to this path.")
    args = parser.parse_args(argv)

    payload = json.dumps(read_baselines(args.skills_dir), indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
