import io
import json
from pathlib import Path
import sys

import pytest
from ticket_guard import evidence, marker
from ticket_guard.__main__ import main

FAIL_TEST = "def test_sub():\n    from src.app import sub\n    assert sub(3, 1) == 2\n"
RED_CMD = [sys.executable, "-c", "import sys; sys.exit(1)"]


def hook(capsys, monkeypatch, name, payload):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    code = main(["hook", name])
    return code, capsys.readouterr().out


def started(git_repo, mode="goal"):
    marker.start(git_repo.root, "demo", "T1", mode)
    marker.claim(git_repo.root, "s1")


def red(git_repo, capsys, *extra):
    git_repo.write("tests/test_sub.py", FAIL_TEST)
    code = main(["run", "red", *extra, "--", *RED_CMD])
    capsys.readouterr()
    return code


# RED and GREEN wrappers ---------------------------------------------------------


def test_red_records_a_failing_run_of_new_tests(git_repo, capsys):
    started(git_repo)
    assert red(git_repo, capsys) == 0
    rec = [r for r in evidence.records(git_repo.root, "T1") if r["event"] == "run"][-1]
    assert rec["phase"] == "red" and rec["valid"] is True
    assert rec["exit_code"] == 1
    assert rec["test_files"] == ["tests/test_sub.py"]
    for key in ("command", "cwd", "head_sha", "tree_hash", "test_files_digest"):
        assert rec[key]
    assert rec["log_sha256"]
    assert Path(rec["log_path"]).is_file()


def test_red_is_invalid_when_the_tests_pass(git_repo, capsys):
    started(git_repo)
    git_repo.write("tests/test_sub.py", FAIL_TEST)
    assert main(["run", "red", "--", sys.executable, "-c", "pass"]) == 1
    assert "RED needs a failing" in capsys.readouterr().err


def test_red_is_invalid_after_a_source_change(git_repo, capsys):
    started(git_repo)
    git_repo.write("src/app.py", "def sub(a, b):\n    return a - b\n")
    assert red(git_repo, capsys) == 1
    rec = evidence.records(git_repo.root, "T1")[-1]
    assert rec["valid"] is False and "src/app.py" in rec["reason"]


def test_red_is_invalid_on_a_collection_error(git_repo, capsys):
    started(git_repo)
    git_repo.write("tests/test_sub.py", FAIL_TEST)
    cmd = [
        sys.executable,
        "-c",
        "import sys; print('ERROR collecting tests'); sys.exit(2)",
    ]
    assert main(["run", "red", "--", *cmd]) == 1
    assert "collection" in capsys.readouterr().err


@pytest.mark.parametrize(
    "script, kind",
    [
        (
            "import sys; print('/usr/bin/python3: No module named pytest'); sys.exit(1)",
            "test",
        ),
        (
            "import sys; print('bash: line 1: pytest: command not found'); sys.exit(1)",
            "test",
        ),
        ("import sys; print('sh: 1: pytest: not found'); sys.exit(1)", "stand-in"),
        ("import sys; sys.exit(127)", "test"),
    ],
)
def test_red_is_invalid_when_the_runner_is_missing(git_repo, capsys, script, kind):
    started(git_repo)
    git_repo.write("tests/test_sub.py", FAIL_TEST)
    cmd = [sys.executable, "-c", script]
    assert main(["run", "red", "--type", kind, "--", *cmd]) == 1
    assert "test runner did not start" in capsys.readouterr().err


def test_red_accepts_a_missing_module_inside_a_test(git_repo, capsys):
    started(git_repo)
    git_repo.write("tests/test_sub.py", FAIL_TEST)
    script = "import sys; print(\"E   ModuleNotFoundError: No module named 'src.app'\"); sys.exit(1)"
    assert main(["run", "red", "--", sys.executable, "-c", script]) == 0


def test_red_stand_in_needs_only_a_failure(git_repo, capsys):
    started(git_repo)
    assert main(["run", "red", "--type", "stand-in", "--", *RED_CMD]) == 0


def test_red_refactor_needs_a_passing_suite_and_freezes_every_test(git_repo, capsys):
    started(git_repo)
    ok = [sys.executable, "-c", "pass"]
    assert main(["run", "red", "--type", "refactor", "--", *ok]) == 0
    rec = evidence.records(git_repo.root, "T1")[-1]
    assert rec["test_files"] == ["tests/test_app.py"]
    assert main(["run", "red", "--type", "refactor", "--", *RED_CMD]) == 1


def test_green_records_and_flags_changed_tests(git_repo, capsys):
    started(git_repo)
    red(git_repo, capsys)
    ok = [sys.executable, "-c", "pass"]
    assert main(["run", "green", "--", *ok]) == 0
    rec = evidence.records(git_repo.root, "T1")[-1]
    assert (rec["phase"], rec["exit_code"], rec["tests_changed"]) == ("green", 0, False)
    git_repo.write("tests/test_sub.py", "def test_sub():\n    pass\n")
    assert main(["run", "green", "--", *ok]) == 1
    assert evidence.records(git_repo.root, "T1")[-1]["tests_changed"] is True
    assert "changed since RED" in capsys.readouterr().err


def test_green_needs_a_red_record(git_repo, capsys):
    started(git_repo)
    assert main(["run", "green", "--", sys.executable, "-c", "pass"]) == 1
    assert "no valid RED record" in capsys.readouterr().err


@pytest.mark.parametrize("phase", ["red", "green"])
@pytest.mark.parametrize("shell", ["sh", "bash", "/bin/zsh", "dash"])
def test_run_refuses_an_unquoted_shell_c_command(git_repo, capsys, phase, shell):
    started(git_repo)
    argv = [shell, "-c", "test", "-f", "docs/units.md"]
    assert main(["run", phase, "--", *argv]) == 1
    err = capsys.readouterr().err
    assert "one quoted string" in err and '-- "test -f docs/units.md"' in err
    assert all(r["event"] != "run" for r in evidence.records(git_repo.root, "T1"))


def test_run_accepts_a_quoted_shell_string_and_sh_c_with_one_script(git_repo, capsys):
    started(git_repo)
    assert main(["run", "red", "--type", "stand-in", "--", "test -f docs/units.md && grep -q x docs/units.md"]) == 0
    assert main(["run", "red", "--type", "stand-in", "--", "sh", "-c", "test -f docs/units.md"]) == 0


def test_run_needs_a_marker(git_repo, capsys):
    assert main(["run", "red", "--", *RED_CMD]) == 1
    assert "no marker" in capsys.readouterr().err


# PreToolUse ---------------------------------------------------------------------


def edit(git_repo, rel, session="s1", tool="Edit"):
    return {
        "session_id": session,
        "hook_event_name": "PreToolUse",
        "cwd": str(git_repo.root),
        "tool_name": tool,
        "tool_input": {"file_path": str(git_repo.root / rel)},
    }


def decision(out):
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


def test_pre_tool_use_exits_0_silently_without_a_marker(git_repo, capsys, monkeypatch):
    assert hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/x.py")) == (
        0,
        "",
    )


def test_freeze_denies_frozen_tests_in_goal_mode(git_repo, capsys, monkeypatch):
    started(git_repo)
    red(git_repo, capsys)
    code, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py"))
    assert code == 0 and decision(out) == "deny"
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "T1" in reason and "marker.json" in reason and "guard marker clear" in reason
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "src/app.py"))
    assert out == ""
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py", "s2"))
    assert out == ""  # another session: stand down


def test_freeze_asks_attended_and_records_the_amendment(git_repo, capsys, monkeypatch):
    started(git_repo, "attended")
    red(git_repo, capsys)
    payload = edit(git_repo, "tests/test_sub.py", tool="Write")
    _, out = hook(capsys, monkeypatch, "pre-tool-use", payload)
    assert decision(out) == "ask"
    assert evidence.records(git_repo.root, "T1")[-1]["event"] == "amendment_requested"


def next_ticket(git_repo, mode="goal"):
    marker.clear(git_repo.root)
    marker.start(git_repo.root, "demo", "T2", mode)
    marker.claim(git_repo.root, "s1")


def earlier_ticket(git_repo, capsys, mode="goal"):
    """On a spec branch, T1 records RED on tests/test_sub.py and commits; then T2 starts in the same session."""
    git_repo.git("checkout", "-q", "-b", "spec/demo")
    started(git_repo, mode)
    red(git_repo, capsys)
    git_repo.commit("T1")
    next_ticket(git_repo, mode)


def test_freeze_skips_an_earlier_ticket_started_on_another_branch(git_repo, capsys, monkeypatch):
    git_repo.git("checkout", "-q", "-b", "spec/demo")
    git_repo.write("docs/specs/todo/demo/notes.md", "spec branch commit\n")
    git_repo.commit("spec")
    started(git_repo)
    red(git_repo, capsys)
    git_repo.commit("T1")
    marker.clear(git_repo.root)
    git_repo.git("checkout", "-q", "main")
    git_repo.git("checkout", "-q", "-b", "spec/other")
    next_ticket(git_repo)
    assert hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py")) == (0, "")


def test_freeze_skips_an_earlier_ticket_started_before_the_fork_point(git_repo, capsys, monkeypatch):
    started(git_repo)
    red(git_repo, capsys)
    git_repo.commit("T1 on main")
    marker.clear(git_repo.root)
    git_repo.git("checkout", "-q", "-b", "spec/demo")
    next_ticket(git_repo)
    assert hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py")) == (0, "")


def test_freeze_skips_an_earlier_tickets_refactor_red(git_repo, capsys, monkeypatch):
    git_repo.git("checkout", "-q", "-b", "spec/demo")
    started(git_repo)
    assert main(["run", "red", "--type", "refactor", "--", sys.executable, "-c", "pass"]) == 0
    capsys.readouterr()
    next_ticket(git_repo)
    assert hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_app.py")) == (0, "")


def test_freeze_skips_an_earlier_ticket_without_a_start_sha(git_repo, capsys, monkeypatch):
    earlier_ticket(git_repo, capsys)
    path = evidence.path(git_repo.root, "T1")
    recs = [{k: v for k, v in r.items() if k != "start_sha"} for r in evidence.records(git_repo.root, "T1")]
    path.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    assert hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py")) == (0, "")


def test_freeze_keeps_the_current_tickets_refactor_red(git_repo, capsys, monkeypatch):
    started(git_repo)
    assert main(["run", "red", "--type", "refactor", "--", sys.executable, "-c", "pass"]) == 0
    capsys.readouterr()
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_app.py"))
    assert decision(out) == "deny"


def test_freeze_denies_an_earlier_tickets_red_tests_in_goal_mode(git_repo, capsys, monkeypatch):
    earlier_ticket(git_repo, capsys)
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py"))
    assert decision(out) == "deny"
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "ticket T1" in reason and "guard block" in reason
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_app.py"))
    assert out == ""


def test_freeze_asks_attended_for_an_earlier_tickets_tests_and_names_the_owner(git_repo, capsys, monkeypatch):
    earlier_ticket(git_repo, capsys, "attended")
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py", tool="Write"))
    assert decision(out) == "ask"
    assert "ticket T1" in json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    rec = evidence.records(git_repo.root, "T2")[-1]
    assert (rec["event"], rec["file"], rec["tool"], rec["owner_ticket"]) == (
        "amendment_requested",
        "tests/test_sub.py",
        "Write",
        "T1",
    )
    owner = evidence.records(git_repo.root, "T1")[-1]
    assert (owner["event"], owner["file"], owner["from_ticket"]) == ("amendment_requested", "tests/test_sub.py", "T2")


# PostToolUse --------------------------------------------------------------------


def applied(git_repo, rel, tool="Edit"):
    return edit(git_repo, rel, tool=tool) | {"hook_event_name": "PostToolUse", "tool_response": {}}


def test_post_tool_use_records_an_applied_amendment_to_the_current_tickets_tests(git_repo, capsys, monkeypatch):
    started(git_repo, "attended")
    red(git_repo, capsys)
    assert hook(capsys, monkeypatch, "post-tool-use", applied(git_repo, "tests/test_sub.py")) == (0, "")
    rec = evidence.records(git_repo.root, "T1")[-1]
    assert (rec["event"], rec["file"], rec["tool"], rec["owner_ticket"]) == (
        "amendment_applied",
        "tests/test_sub.py",
        "Edit",
        "T1",
    )


def test_post_tool_use_records_an_applied_amendment_to_an_earlier_tickets_tests(git_repo, capsys, monkeypatch):
    earlier_ticket(git_repo, capsys, "attended")
    hook(capsys, monkeypatch, "post-tool-use", applied(git_repo, "tests/test_sub.py", "MultiEdit"))
    rec = evidence.records(git_repo.root, "T2")[-1]
    assert (rec["event"], rec["tool"], rec["owner_ticket"]) == ("amendment_applied", "MultiEdit", "T1")
    owner = evidence.records(git_repo.root, "T1")[-1]
    assert (owner["event"], owner["from_ticket"]) == ("amendment_applied", "T2")


def test_post_tool_use_ignores_files_that_are_not_frozen(git_repo, capsys, monkeypatch):
    started(git_repo, "attended")
    red(git_repo, capsys)
    before = evidence.records(git_repo.root, "T1")
    for rel in ("src/app.py", "tests/test_app.py"):
        assert hook(capsys, monkeypatch, "post-tool-use", applied(git_repo, rel)) == (0, "")
    assert evidence.records(git_repo.root, "T1") == before


def test_post_tool_use_exits_0_silently_without_a_marker(git_repo, capsys, monkeypatch):
    assert hook(capsys, monkeypatch, "post-tool-use", applied(git_repo, "tests/x.py")) == (0, "")


def test_no_freeze_before_red(git_repo, capsys, monkeypatch):
    started(git_repo)
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_app.py"))
    assert out == ""


def test_goal_mode_blocks_the_text_ticket_folder(git_repo, capsys, monkeypatch):
    git_repo.write(".claude/workflow-config.json", json.dumps({"text": {"ticketsDir": "tickets"}}))
    git_repo.commit("config")
    started(git_repo)
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tickets/T9.md"))
    assert decision(out) == "deny"
    marker.update(git_repo.root, mode="attended")
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tickets/T9.md"))
    assert out == ""


def test_hooks_survive_bad_input(git_repo, capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert main(["hook", "pre-tool-use"]) == 0


# SessionStart -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        ("none", "guard run red"),
        ("red", "guard run green"),
        ("green", "ticket:complete T1"),
    ],
)
def test_session_start_after_compact_prints_next_step(git_repo, capsys, monkeypatch, setup, expected):
    started(git_repo)
    if setup in ("red", "green"):
        red(git_repo, capsys)
    if setup == "green":
        main(["run", "green", "--", sys.executable, "-c", "pass"])
        capsys.readouterr()
    payload = {"session_id": "s1", "source": "compact", "cwd": str(git_repo.root)}
    code, out = hook(capsys, monkeypatch, "session-start", payload)
    assert code == 0
    assert "T1" in out and "goal" in out and expected in out
    assert "docs/specs/todo/demo/goal-prompt.md" in out


def test_session_start_is_silent_for_other_sources_and_no_marker(git_repo, capsys, monkeypatch):
    payload = {"session_id": "s1", "source": "compact", "cwd": str(git_repo.root)}
    assert hook(capsys, monkeypatch, "session-start", payload) == (0, "")
    started(git_repo)
    payload["source"] = "startup"
    assert hook(capsys, monkeypatch, "session-start", payload) == (0, "")


def test_a_rerun_after_block_judges_only_its_own_evidence(git_repo, capsys, monkeypatch):
    started(git_repo)
    red(git_repo, capsys)
    assert main(["block", "T1", "the tests were wrong"]) == 0
    capsys.readouterr()
    started(git_repo)
    _, out = hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py"))
    assert out == ""  # the old attempt's RED no longer freezes this attempt's tests
    git_repo.write("tests/test_sub.py", "def test_sub():\n    from src.app import sub\n    assert sub(5, 2) == 3\n")
    assert main(["run", "red", "--", *RED_CMD]) == 0
    capsys.readouterr()
    reds = [r for r in evidence.current(git_repo.root, "T1") if r["event"] == "run" and r["phase"] == "red"]
    assert len(reds) == 1
    assert len([r for r in evidence.records(git_repo.root, "T1") if r["event"] == "run"]) == 2  # the file keeps both


# Approved amendments and GREEN (eval repo #7) ------------------------------------

OK = [sys.executable, "-c", "pass"]
AMENDED = "def test_sub():\n    from src.app import sub\n    assert sub(4, 1) == 3\n"


def test_green_accepts_a_frozen_test_changed_by_an_approved_amendment(git_repo, capsys, monkeypatch):
    started(git_repo, "attended")
    red(git_repo, capsys)
    git_repo.write("tests/test_sub.py", AMENDED)
    hook(capsys, monkeypatch, "post-tool-use", applied(git_repo, "tests/test_sub.py"))
    assert main(["run", "green", "--", *OK]) == 0
    rec = evidence.records(git_repo.root, "T1")[-1]
    assert (rec["tests_changed"], rec["amended_tests"]) == (False, ["tests/test_sub.py"])


def test_green_still_refuses_a_frozen_test_changed_without_an_amendment(git_repo, capsys, monkeypatch):
    started(git_repo, "attended")
    git_repo.write("tests/test_other.py", FAIL_TEST.replace("test_sub", "test_other"))
    red(git_repo, capsys)
    git_repo.write("tests/test_sub.py", AMENDED)
    git_repo.write("tests/test_other.py", "def test_other():\n    pass\n")
    hook(capsys, monkeypatch, "post-tool-use", applied(git_repo, "tests/test_sub.py"))
    assert main(["run", "green", "--", *OK]) == 1
    assert evidence.records(git_repo.root, "T1")[-1]["tests_changed"] is True


def test_green_ignores_an_amendment_recorded_before_red(git_repo, capsys, monkeypatch):
    started(git_repo, "attended")
    evidence.append(git_repo.root, "T1", "amendment_applied", file="tests/test_sub.py", tool="Edit", owner_ticket="T1")
    red(git_repo, capsys)
    git_repo.write("tests/test_sub.py", AMENDED)
    assert main(["run", "green", "--", *OK]) == 1


def test_green_accepts_a_legacy_red_with_an_attended_amendment_request(git_repo, capsys, monkeypatch):
    """RED records from builds before per-file digests, with only amendment_requested logged."""
    started(git_repo, "attended")
    red(git_repo, capsys)
    log = evidence.path(git_repo.root, "T1")
    recs = [json.loads(line) for line in log.read_text().splitlines()]
    for r in recs:
        r.pop("test_file_digests", None)
    log.write_text("".join(json.dumps(r) + "\n" for r in recs))
    hook(capsys, monkeypatch, "pre-tool-use", edit(git_repo, "tests/test_sub.py"))
    git_repo.write("tests/test_sub.py", AMENDED)
    assert main(["run", "green", "--", *OK]) == 0
    assert evidence.records(git_repo.root, "T1")[-1]["amended_tests"] == ["tests/test_sub.py"]


def test_summary_names_the_amended_tests(git_repo, capsys, monkeypatch):
    from ticket_guard import boundary

    started(git_repo, "attended")
    red(git_repo, capsys)
    git_repo.write("tests/test_sub.py", AMENDED)
    hook(capsys, monkeypatch, "post-tool-use", applied(git_repo, "tests/test_sub.py"))
    main(["run", "green", "--", *OK])
    notes, missing = boundary.summary(git_repo.root)
    assert not [m for m in missing if m.startswith("GREEN")]
    assert "tests amended after RED with approval: tests/test_sub.py" in notes
