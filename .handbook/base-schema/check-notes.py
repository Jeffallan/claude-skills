#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "jsonschema>=4.18"]
# ///
"""Check the YAML front matter of markdown notes against a Base Schema profile.

Usage: uv run check-notes.py [--schema FILE] PATH...
       uv run check-notes.py --from-answers [ANSWERS]

--from-answers reads notes_paths and notes_schema from a Copier answers file
(.copier-answers.yml by default) at run time, so a hook file written once never goes stale.

PATH is a file, a folder (searched for *.md) or a glob. A glob that matches nothing is fine;
a literal path that does not exist is an error. The rules all come from the schema
(envelope-lite.schema.json beside this script by default). Prints one line per error,
"file: field: message", and exits 1 when any note fails.
"""

import argparse
import glob
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE / "profiles" / "envelope-lite.schema.json"


class TextDates(yaml.SafeLoader):
    """SafeLoader that keeps dates as the text written, which is what the schemas describe."""


TextDates.yaml_implicit_resolvers = {
    k: [r for r in v if r[0] != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def validator(schema_path: Path) -> Draft202012Validator:
    schema = json.loads(schema_path.read_text())
    schema["$id"] = schema_path.as_uri()

    def retrieve(
        uri: str,
    ) -> Resource:  # sibling profiles, e.g. envelope-lite.schema.json
        return Resource.from_contents(
            json.loads(Path(uri.removeprefix("file://")).read_text())
        )

    return Draft202012Validator(schema, registry=Registry(retrieve=retrieve))


def notes(paths: list[str]) -> tuple[list[Path], list[str]]:
    found, missing = [], []
    for p in paths:
        if glob.has_magic(p):
            found += [
                Path(m)
                for m in sorted(glob.glob(p, recursive=True))
                if m.endswith(".md")
            ]
        elif Path(p).is_dir():
            found += sorted(Path(p).rglob("*.md"))
        elif Path(p).is_file():
            found.append(Path(p))
        else:
            missing.append(p)
    return found, missing


def front_matter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("no front matter")
    for i, line in enumerate(lines[1:], 1):
        if line.strip() in ("---", "..."):
            return yaml.load("\n".join(lines[1:i]), Loader=TextDates)
    raise ValueError("front matter is not closed with ---")


def errors(path: Path, check: Draft202012Validator) -> list[str]:
    try:
        data = front_matter(path.read_text(encoding="utf-8"))
    except (ValueError, yaml.YAMLError, UnicodeDecodeError) as e:
        return [f"{path}: {str(e).splitlines()[0]}"]
    if not isinstance(data, dict):
        return [f"{path}: front matter is not a mapping of fields"]
    return [
        f"{path}: {'.'.join(map(str, e.absolute_path)) or '(top)'}: {e.message}"
        for e in sorted(
            check.iter_errors(data), key=lambda e: list(map(str, e.absolute_path))
        )
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--schema", type=Path, default=DEFAULT_SCHEMA, help="profile to check against"
    )
    ap.add_argument(
        "--from-answers",
        nargs="?",
        const=".copier-answers.yml",
        metavar="ANSWERS",
        help="take notes_paths and notes_schema from a Copier answers file",
    )
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()

    schema, paths = args.schema, args.paths
    if args.from_answers:
        try:
            answers = yaml.safe_load(Path(args.from_answers).read_text()) or {}
        except (OSError, yaml.YAMLError) as e:
            ap.error(f"cannot read {args.from_answers}: {e}")
        paths = paths or answers.get("notes_paths") or []
        if not paths:
            ap.error(f"{args.from_answers} has no notes_paths")
        if schema == DEFAULT_SCHEMA:
            schema = (
                HERE
                / "profiles"
                / f"{answers.get('notes_schema', 'envelope-lite')}.schema.json"
            )
    if not paths:
        ap.error("name at least one path, or use --from-answers")

    check = validator(schema.resolve())
    found, missing = notes(paths)
    out = [f"{p}: no such file or folder" for p in missing]
    for path in found:
        out += errors(path, check)
    print("\n".join(out)) if out else None
    print(f"{len(found)} notes checked, {len(out)} errors", file=sys.stderr)
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main())
