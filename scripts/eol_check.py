"""Check product version baselines against the endoflife.date v1 API."""

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

WINDOW_DAYS = 90
API_BASE = "https://endoflife.date/api/v1/products"
USER_AGENT = "claude-skills-baseline-check"
REPORT_SECTIONS = ("past end of support", "inside warning window", "not checked")
ATTENTION_STATUSES = frozenset({"past end of support", "inside warning window"})


@dataclass(frozen=True)
class Baseline:
    source: str
    product: str
    version: str


@dataclass(frozen=True)
class Result:
    baseline: Baseline
    status: str
    eol: date | None
    note: str = ""


def _retry_after_seconds(exc: urllib.error.HTTPError) -> float:
    raw = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw is None:
        return 30.0
    try:
        seconds = float(raw)
    except ValueError:
        return 30.0
    return max(0.0, min(seconds, 120.0))


def fetch_releases(slug: str) -> list[dict[str, Any]] | None:
    url = f"{API_BASE}/{urllib.parse.quote(slug, safe='')}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code != 429:
            raise
        time.sleep(_retry_after_seconds(exc))
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    return payload["result"]["releases"]


def find_release(releases: list[dict[str, Any]], version: str) -> dict[str, Any] | None:
    match = next((r for r in releases if r.get("name") == version), None)
    if match is not None:
        return match
    if version.endswith(".0"):
        trimmed = version.removesuffix(".0")
        return next((r for r in releases if r.get("name") == trimmed), None)
    return None


def evaluate(
    baseline: Baseline,
    slug: str | None,
    releases: list[dict[str, Any]] | None,
    today: date,
    window_days: int = WINDOW_DAYS,
) -> Result:
    if slug is None:
        return Result(baseline, "not checked", None, "no slug mapping")
    if releases is None:
        return Result(baseline, "not checked", None, "unknown product at endoflife.date")
    release = find_release(releases, baseline.version)
    if release is None:
        return Result(baseline, "not checked", None, f"version {baseline.version} not listed")

    eol_raw = release.get("eolFrom")
    eol = date.fromisoformat(eol_raw) if isinstance(eol_raw, str) else None

    if release.get("isEol") is True or (eol is not None and eol <= today):
        return Result(baseline, "past end of support", eol)
    if eol is not None and eol <= today + timedelta(days=window_days):
        return Result(baseline, "inside warning window", eol)

    note = "no end date published" if eol is None else ""
    return Result(baseline, "supported", eol, note)


def check(
    baselines: list[Baseline],
    slugs: dict[str, str],
    today: date,
    fetch: Callable[[str], list[dict[str, Any]] | None] = fetch_releases,
    window_days: int = WINDOW_DAYS,
) -> list[Result]:
    cache: dict[str, list[dict[str, Any]] | None] = {}
    results: list[Result] = []
    for baseline in baselines:
        slug = slugs.get(baseline.product)
        releases: list[dict[str, Any]] | None = None
        if slug is not None:
            if slug not in cache:
                cache[slug] = fetch(slug)
            releases = cache[slug]
        results.append(evaluate(baseline, slug, releases, today, window_days=window_days))
    return results


def render_report(results: list[Result], today: date) -> str:
    header = (
        f"Checked {len(results)} baselines on {today.isoformat()} "
        f"against endoflife.date (warning window: {WINDOW_DAYS} days)."
    )
    lines = [header]
    for status in REPORT_SECTIONS:
        group = [r for r in results if r.status == status]
        if not group:
            continue
        lines.append("")
        lines.append(f"## {status.capitalize()} ({len(group)})")
        lines.append("")
        lines.append("| Skill | Product | Version | End of support | Note |")
        lines.append("| --- | --- | --- | --- | --- |")
        for r in group:
            eol_str = r.eol.isoformat() if r.eol is not None else "-"
            row = f"| {r.baseline.source} | {r.baseline.product} | {r.baseline.version} | {eol_str} | {r.note} |"
            lines.append(row)

    supported_count = sum(1 for r in results if r.status == "supported")
    lines.append("")
    lines.append(f"{supported_count} supported.")
    return "\n".join(lines) + "\n"


def needs_attention(results: list[Result]) -> bool:
    return any(r.status in ATTENTION_STATUSES for r in results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check baselines against endoflife.date.")
    parser.add_argument("--input", required=True, type=Path, help="Path to baselines JSON file.")
    parser.add_argument("--slugs", required=True, type=Path, help="Path to product-to-slug JSON mapping.")
    parser.add_argument("--today", type=date.fromisoformat, default=None, help="Override today's date (YYYY-MM-DD).")
    parser.add_argument("--report", type=Path, default=None, help="Write Markdown report to this path.")
    args = parser.parse_args(argv)

    try:
        raw_pairs = json.loads(args.input.read_text(encoding="utf-8"))
        slugs: dict[str, str] = json.loads(args.slugs.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error reading input: {exc}", file=sys.stderr)
        return 1

    today = args.today or date.today()
    baselines = [
        Baseline(source=item["source"], product=item["product"], version=item["version"]) for item in raw_pairs
    ]
    results = check(baselines, slugs, today)
    report = render_report(results, today)

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(report)

    flag = "true" if needs_attention(results) else "false"
    print(f"attention={flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
