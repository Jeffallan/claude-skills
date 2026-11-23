import io
import json
import sys

from ticket_guard import evidence, marker
from ticket_guard.__main__ import main

FAIL_TEST = "def test_sub():\n    assert False\n"
# Passes once a file named `ok` exists in the repo root.
CHECK = [
    sys.executable,
    "-c",
    "import pathlib, sys; sys.exit(0 if pathlib.Path('ok').exists() else 1)",
]


def stop(capsys, monkeypatch, git_repo, message="Done.", session="s1", active=True):
    payload = {
        "session_id": session,
        "hook_event_name": "Stop",
        "cwd": str(git_repo.root),
        "stop_hook_active": active,
        "last_assistant_message": message,
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert main(["hook", "stop"]) == 0
    out = capsys.readouterr().out
    return json.loads(out) if out else None


def ticket(git_repo, capsys, mode="goal"):
    marker.start(git_repo.root, "demo", "T1", mode)
    marker.claim(git_repo.root, "s1")
    git_repo.write("tests/test_sub.py", FAIL_TEST)
    assert main(["run", "red", "--", *CHECK]) == 0
    capsys.readouterr()


def test_blocks_while_green_fails_up_to_the_limit_then_allows_and_records(git_repo, capsys, monkeypatch):
    ticket(git_repo, capsys)
    for count in (1, 2, 3):
        out = stop(capsys, monkeypatch, git_repo)
        assert out["decision"] == "block"
        assert "pathlib" in out["reason"] and "guard block T1" in out["reason"]
        assert marker.read(git_repo.root)["green_failures"] == count
    assert stop(capsys, monkeypatch, git_repo) is None
    data = marker.read(git_repo.root)
    assert data["green_failures"] == 4 and data["green_failed_at"]
    events = [r["event"] for r in evidence.records(git_repo.root, "T1")]
    assert events.count("green_failure") == 1
    assert stop(capsys, monkeypatch, git_repo) is None
    assert [r["event"] for r in evidence.records(git_repo.root, "T1")].count("green_failure") == 1


def test_ignores_stop_hook_active(git_repo, capsys, monkeypatch):
    ticket(git_repo, capsys)
    assert stop(capsys, monkeypatch, git_repo, active=False)["decision"] == "block"
    assert stop(capsys, monkeypatch, git_repo, active=True)["decision"] == "block"


def test_passing_green_allows_and_resets_the_count(git_repo, capsys, monkeypatch):
    ticket(git_repo, capsys)
    stop(capsys, monkeypatch, git_repo)
    git_repo.write("ok", "")
    assert stop(capsys, monkeypatch, git_repo) is None
    assert marker.read(git_repo.root)["green_failures"] == 0
    rec = evidence.records(git_repo.root, "T1")[-1]
    assert (rec["phase"], rec["source"], rec["exit_code"]) == ("green", "stop-hook", 0)


def test_changed_tests_block_even_when_green_passes(git_repo, capsys, monkeypatch):
    ticket(git_repo, capsys)
    git_repo.write("ok", "")
    git_repo.write("tests/test_sub.py", "def test_sub():\n    pass\n")
    out = stop(capsys, monkeypatch, git_repo)
    assert out["decision"] == "block" and "changed since RED" in out["reason"]


def test_blocked_message_always_passes_and_is_recorded(git_repo, capsys, monkeypatch):
    ticket(git_repo, capsys)
    for _ in range(5):
        stop(capsys, monkeypatch, git_repo)
    marker.update(git_repo.root, green_failures=1)
    msg = "BLOCKED: environment broken\nneed uv"
    assert stop(capsys, monkeypatch, git_repo, message=msg) is None
    data = marker.read(git_repo.root)
    assert data["blocked_at"] and data["blocked_stop"] == "BLOCKED: environment broken"
    assert data["green_failures"] == 1  # no GREEN re-run on a BLOCKED: stop


def test_reruns_the_latest_green_command(git_repo, capsys, monkeypatch):
    ticket(git_repo, capsys)
    ok = [sys.executable, "-c", "pass"]
    main(["run", "green", "--", *ok])
    capsys.readouterr()
    assert stop(capsys, monkeypatch, git_repo) is None


def test_attended_foreign_and_pre_red_stops_pass(git_repo, capsys, monkeypatch):
    assert stop(capsys, monkeypatch, git_repo) is None  # no marker
    marker.start(git_repo.root, "demo", "T1", "goal")
    marker.claim(git_repo.root, "s1")
    assert stop(capsys, monkeypatch, git_repo) is None  # no RED yet
    git_repo.write("tests/test_sub.py", FAIL_TEST)
    main(["run", "red", "--", *CHECK])
    capsys.readouterr()
    assert stop(capsys, monkeypatch, git_repo, session="s2") is None
    marker.update(git_repo.root, mode="attended")
    assert stop(capsys, monkeypatch, git_repo) is None


def test_limit_comes_from_config(git_repo, capsys, monkeypatch):
    git_repo.write(".claude/workflow-config.json", json.dumps({"guard": {"greenFailLimit": 1}}))
    git_repo.commit("config")
    ticket(git_repo, capsys)
    assert stop(capsys, monkeypatch, git_repo)["decision"] == "block"
    assert stop(capsys, monkeypatch, git_repo) is None
