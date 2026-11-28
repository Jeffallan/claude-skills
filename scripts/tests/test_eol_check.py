"""Tests for eol_check and skill_baselines."""

from collections.abc import Callable
from datetime import date
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import eol_check
import skill_baselines

TODAY = date(2026, 11, 28)

SLUGS = {
    "Python": "python",
    "PHP": "php",
    "Ghost": "ghost-unknown",
}

RELEASES: dict[str, list[dict[str, Any]]] = {
    "python": [
        {"name": "3.9", "isEol": True, "eolFrom": "2025-10-31"},
        {"name": "3.10", "isEol": False, "eolFrom": "2026-10-31"},
        {"name": "3.11", "isEol": False, "eolFrom": "2027-01-15"},
        {"name": "3.12", "isEol": False, "eolFrom": "2028-10-31"},
        {"name": "3.14", "isEol": False, "eolFrom": None},
    ],
    "php": [
        {"name": "8", "isEol": False, "eolFrom": "2028-12-31"},
        {"name": "8.3", "isEol": False, "eolFrom": "2027-12-31"},
    ],
}


def _make_fetcher() -> tuple[Callable[[str], list[dict[str, Any]] | None], list[str]]:
    calls: list[str] = []

    def fake_fetch(slug: str) -> list[dict[str, Any]] | None:
        calls.append(slug)
        return RELEASES.get(slug)

    return fake_fetch, calls


def test_past_eol_flag() -> None:
    fetch, _ = _make_fetcher()
    baselines = [eol_check.Baseline(source="py-old", product="Python", version="3.9")]
    [result] = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert result.status == "past end of support"
    assert result.eol == date(2025, 10, 31)


def test_past_eol_date_with_false_flag() -> None:
    fetch, _ = _make_fetcher()
    baselines = [eol_check.Baseline(source="py-stale", product="Python", version="3.10")]
    [result] = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert result.status == "past end of support"
    assert result.eol == date(2026, 10, 31)


def test_inside_warning_window() -> None:
    fetch, _ = _make_fetcher()
    baselines = [eol_check.Baseline(source="py-soon", product="Python", version="3.11")]
    [result] = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert result.status == "inside warning window"
    assert result.eol == date(2027, 1, 15)


def test_supported_far_ahead_and_null_eol() -> None:
    fetch, _ = _make_fetcher()
    baselines = [
        eol_check.Baseline(source="py-ok", product="Python", version="3.12"),
        eol_check.Baseline(source="py-new", product="Python", version="3.14"),
    ]
    res_ok, res_null = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert res_ok.status == "supported"
    assert res_ok.eol == date(2028, 10, 31)
    assert res_ok.note == ""
    assert res_null.status == "supported"
    assert res_null.eol is None
    assert res_null.note == "no end date published"


def test_unknown_product_not_checked() -> None:
    fetch, _ = _make_fetcher()
    baselines = [eol_check.Baseline(source="ghost-skill", product="Ghost", version="1.0")]
    [result] = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert result.status == "not checked"
    assert result.eol is None
    assert result.note == "unknown product at endoflife.date"


def test_unmapped_product_not_checked() -> None:
    fetch, calls = _make_fetcher()
    baselines = [eol_check.Baseline(source="custom-skill", product="CustomLang", version="2.0")]
    [result] = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert result.status == "not checked"
    assert result.eol is None
    assert result.note == "no slug mapping"
    assert calls == []


def test_version_not_listed_not_checked() -> None:
    fetch, _ = _make_fetcher()
    baselines = [eol_check.Baseline(source="py-missing", product="Python", version="9.9")]
    [result] = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert result.status == "not checked"
    assert result.eol is None
    assert result.note == "version 9.9 not listed"


def test_dot_zero_suffix_matching() -> None:
    fetch, _ = _make_fetcher()
    baselines = [eol_check.Baseline(source="php-major", product="PHP", version="8.0")]
    [result] = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert result.status == "supported"
    assert result.eol == date(2028, 12, 31)


def test_slug_fetched_once_when_shared() -> None:
    fetch, calls = _make_fetcher()
    baselines = [
        eol_check.Baseline(source="skill-a", product="Python", version="3.11"),
        eol_check.Baseline(source="skill-b", product="Python", version="3.12"),
    ]
    eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    assert calls == ["python"]


def test_render_report_and_needs_attention() -> None:
    fetch, _ = _make_fetcher()
    baselines = [
        eol_check.Baseline(source="skill-eol", product="Python", version="3.9"),
        eol_check.Baseline(source="skill-warn", product="Python", version="3.11"),
        eol_check.Baseline(source="skill-unmapped", product="CustomLang", version="1.0"),
        eol_check.Baseline(source="skill-ok-1", product="Python", version="3.12"),
        eol_check.Baseline(source="skill-ok-2", product="PHP", version="8.3"),
    ]
    results = eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)
    report = eol_check.render_report(results, TODAY)
    lines = report.splitlines()

    assert lines[0] == "Checked 5 baselines on 2026-11-28 against endoflife.date (warning window: 90 days)."
    assert "## Past end of support (1)" in report
    assert "## Inside warning window (1)" in report
    assert "## Not checked (1)" in report
    assert "skill-eol" in report
    assert "skill-warn" in report
    assert "skill-unmapped" in report
    assert "skill-ok-1" not in report
    assert "skill-ok-2" not in report
    assert lines[-1] == "2 supported."

    assert eol_check.needs_attention(results) is True
    assert eol_check.needs_attention([results[1]]) is True
    assert eol_check.needs_attention([results[2], results[3]]) is False


def test_read_baselines(tmp_path: Path) -> None:
    php_dir = tmp_path / "php-expert"
    php_dir.mkdir()
    (php_dir / "SKILL.md").write_text(
        '---\nname: php-expert\nmetadata:\n  baseline: "PHP 8.3, Laravel 11"\n---\n\n# PHP Expert\n',
        encoding="utf-8",
    )

    plain_dir = tmp_path / "plain-skill"
    plain_dir.mkdir()
    (plain_dir / "SKILL.md").write_text(
        "---\nname: plain-skill\nmetadata:\n  domain: specialized\n---\n\n# Plain\n",
        encoding="utf-8",
    )

    assert skill_baselines.read_baselines(tmp_path) == [
        {"source": "php-expert", "product": "PHP", "version": "8.3"},
        {"source": "php-expert", "product": "Laravel", "version": "11"},
    ]


def test_fetch_failure_is_not_checked_and_other_products_still_run() -> None:
    def flaky_fetch(slug: str) -> list[dict[str, Any]] | None:
        if slug == "php":
            raise OSError("network down")
        return RELEASES.get(slug)

    baselines = [
        eol_check.Baseline(source="php-skill", product="PHP", version="8.3"),
        eol_check.Baseline(source="py-old", product="Python", version="3.9"),
    ]
    failed, ok = eol_check.check(baselines, SLUGS, TODAY, fetch=flaky_fetch)
    assert failed.status == "not checked"
    assert failed.note == eol_check.FETCH_FAILED
    assert ok.status == "past end of support"


def test_attention_flag_is_unknown_when_a_fetch_failed_and_nothing_else_needs_attention() -> None:
    def down(slug: str) -> list[dict[str, Any]] | None:
        raise OSError("network down")

    baselines = [eol_check.Baseline(source="py-ok", product="Python", version="3.12")]
    results = eol_check.check(baselines, SLUGS, TODAY, fetch=down)
    assert eol_check.attention_flag(results) == "unknown"

    fetch, _ = _make_fetcher()
    assert eol_check.attention_flag(eol_check.check(baselines, SLUGS, TODAY, fetch=fetch)) == "false"
    old = [eol_check.Baseline(source="py-old", product="Python", version="3.9")]
    assert eol_check.attention_flag(eol_check.check(old, SLUGS, TODAY, fetch=fetch)) == "true"
