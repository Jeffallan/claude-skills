from datetime import UTC, datetime, timedelta
import json

import pytest
from ticket_guard import marker
from ticket_guard.__main__ import main
from ticket_guard.errors import GuardError


def test_start_writes_marker_with_r6_fields(git_repo):
    data = marker.start(git_repo.root, "demo", "T1", "goal")
    on_disk = json.loads((git_repo.guard / "marker.json").read_text())
    assert on_disk == data
    assert data["version"] == 1
    assert data["mode"] == "goal"
    assert (data["spec"], data["ticket"]) == ("demo", "T1")
    assert data["branch"] == "main"
    assert data["start_sha"] == git_repo.head()
    assert data["clean_start"] is True
    assert data["session_id"] == ""
    assert data["green_failures"] == 0
    assert datetime.fromisoformat(data["started_at"]).tzinfo is not None


def test_start_refuses_dirty_tree(git_repo):
    git_repo.write("src/app.py", "changed\n")
    with pytest.raises(GuardError, match="working tree is not clean"):
        marker.start(git_repo.root, "demo", "T1", "attended")
    assert not (git_repo.guard / "marker.json").exists()


def test_start_ignores_the_spec_plan(git_repo):
    """Blocked rows written by guard block stay uncommitted until the next ticket commits."""
    git_repo.write("docs/specs/todo/demo/implementation-plan.md", "edited by guard block\n")
    assert marker.start(git_repo.root, "demo", "T2", "goal")["clean_start"] is True


def test_start_refuses_another_ticket_and_resumes_the_same(git_repo):
    first = marker.start(git_repo.root, "demo", "T1", "goal")
    marker.claim(git_repo.root, "s1")
    git_repo.write("src/app.py", "work in progress\n")
    with pytest.raises(GuardError, match="T1"):
        marker.start(git_repo.root, "demo", "T2", "goal")
    again = marker.start(git_repo.root, "demo", "T1", "goal")
    assert again["start_sha"] == first["start_sha"]
    assert again["session_id"] == ""  # the next hook re-claims


def test_write_is_atomic_and_leaves_no_temp_files(git_repo):
    marker.start(git_repo.root, "demo", "T1", "goal")
    assert sorted(p.name for p in git_repo.guard.iterdir()) == [
        "evidence",
        "marker.json",
    ]


def test_hook_view_claims_then_stands_down_for_other_sessions(git_repo):
    marker.start(git_repo.root, "demo", "T1", "goal")
    assert marker.for_hook(git_repo.root, "s1")["session_id"] == "s1"
    assert marker.read(git_repo.root)["claimed_at"]
    assert marker.for_hook(git_repo.root, "s1") is not None
    assert marker.for_hook(git_repo.root, "s2") is None
    assert marker.read(git_repo.root)["session_id"] == "s1"


def test_hook_view_stands_down_on_another_branch(git_repo):
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.git("switch", "-q", "-c", "other")
    assert marker.for_hook(git_repo.root, "s1") is None
    assert marker.read(git_repo.root)["session_id"] == ""


def test_hook_view_without_marker_or_repo(git_repo, tmp_path):
    assert marker.for_hook(git_repo.root, "s1") is None
    outside = tmp_path / "plain"
    outside.mkdir()
    assert marker.for_hook(outside, "s1") is None


def test_claim_clears_blocked_stop(git_repo):
    marker.start(git_repo.root, "demo", "T1", "goal")
    marker.update(git_repo.root, blocked_at="x", blocked_stop="BLOCKED: env")
    marker.claim(git_repo.root, "s9")
    data = marker.read(git_repo.root)
    assert data["blocked_at"] is None and data["blocked_stop"] is None


def test_marker_events_go_to_the_evidence_record(git_repo):
    marker.start(git_repo.root, "demo", "T1", "goal")
    marker.for_hook(git_repo.root, "s1")
    marker.clear(git_repo.root)
    lines = (git_repo.guard / "evidence" / "T1.jsonl").read_text().splitlines()
    assert [json.loads(line)["event"] for line in lines] == [
        "marker_start",
        "marker_claim",
        "marker_clear",
    ]
    assert marker.read(git_repo.root) is None


def test_age_warning_uses_the_configured_threshold(git_repo):
    data = marker.start(git_repo.root, "demo", "T1", "goal")
    assert marker.age_warning(git_repo.root, data) is None
    old = (datetime.now(UTC) - timedelta(hours=30)).isoformat()
    data["started_at"] = old
    assert "older than 24 hours" in marker.age_warning(git_repo.root, data)
    git_repo.write(".claude/workflow-config.json", json.dumps({"guard": {"markerWarnHours": 48}}))
    assert marker.age_warning(git_repo.root, data) is None
    data["blocked_at"] = "set"
    data["started_at"] = (datetime.now(UTC) - timedelta(hours=99)).isoformat()
    assert marker.age_warning(git_repo.root, data) is None


def test_cli_start_status_clear(git_repo, capsys):
    assert main(["marker", "start", "demo", "T1", "--mode", "goal"]) == 0
    assert json.loads(capsys.readouterr().out)["ticket"] == "T1"
    assert main(["marker", "status"]) == 0
    assert json.loads(capsys.readouterr().out)["mode"] == "goal"
    assert main(["marker", "clear"]) == 0
    assert main(["marker", "status"]) == 1
    assert "no marker" in capsys.readouterr().err


def test_cli_start_refusal_exits_1(git_repo, capsys):
    git_repo.write("new.txt", "x")
    assert main(["marker", "start", "demo", "T1"]) == 1
    assert "not clean" in capsys.readouterr().err


def test_cli_outside_a_git_repo_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["marker", "status"]) == 2
    assert "not a git repository" in capsys.readouterr().err
