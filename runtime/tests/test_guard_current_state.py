import json

from ticket_guard import currentstate
from ticket_guard.__main__ import main

SD = """---
command: intake:create-system-description
verified: {sha}
---
# System Description

Billing for small teams.

**Sources:** intake docs. **Last updated:** 2026-11-20 at {sha}

## 1. Purpose and scope

Scope.

## 2. Components

```mermaid
flowchart TD
  api --> db
```

| Component | What it does | Status |
|-----------|--------------|--------|
| API | Serves `src/app.py::add` | `wired` |
| Exporter | CSV export, no caller yet | built, not wired |
| Billing v2 | Named by spec billing-v2 | `planned` |

## 3. Data flow

Flows.
"""

FINDINGS = """# Intake Findings

## Summary

| ID | Finding | Severity | Area | Status | Surfaced by |
|----|---------|----------|------|--------|-------------|
| F-001 | Any user sees any invoice | High | access | open | intake:document-authorization |
| F-002 | Typo in a label | Low | ui | fixed | intake:document-features |
| F-003 | Rounding drops cents | Medium | billing | ticketed | intake:testing-features |

## Open questions
"""


def with_state(git_repo, sd=SD, findings=FINDINGS):
    sha = git_repo.git("rev-parse", "--short", "HEAD")
    git_repo.write("docs/system-description.md", sd.format(sha=sha))
    if findings is not None:
        git_repo.write("docs/intake-findings.md", findings)
    git_repo.commit("docs: system description\n\nIntake: intake:create-system-description")
    return sha


def test_compiles_components_findings_drift_and_build_point(git_repo, capsys):
    sha = with_state(git_repo)
    assert main(["current-state"]) == 0
    data = json.loads((git_repo.root / "docs/current-state.json").read_text())
    assert data["schema"] == 1
    assert data["built_at"] == {"head": git_repo.head(), "system_description": sha, "date": "2026-11-20"}
    assert [(c["name"], c["status"]) for c in data["components"]] == [
        ("API", "wired"),
        ("Exporter", "built, not wired"),
        ("Billing v2", "planned"),
    ]
    assert data["components"][0]["does"] == "Serves `src/app.py::add`"
    assert data["components"][0]["source"] == "docs/system-description.md#2-components"
    assert [f["id"] for f in data["findings"]] == ["F-001", "F-003"]  # fixed and invalid rows are not current
    assert data["findings"][0]["source"] == "docs/intake-findings.md#F-001"
    assert data["drift"] == []
    assert "docs/current-state.json" in capsys.readouterr().out


def test_drift_rows_name_their_source(git_repo):
    with_state(git_repo)
    sha = git_repo.git("rev-parse", "--short", "HEAD")
    git_repo.write("docs/api.md", f"---\nverified: {sha}\n---\n# API\n\n`src/app.py::add`\n")
    git_repo.commit("docs: api")
    git_repo.write("src/app.py", "def add(a, b):\n    return b + a\n")
    git_repo.commit("change add")
    data = currentstate.build(git_repo.root)
    rows = {d["doc"]: d for d in data["drift"]}
    assert "api.md" in rows and rows["api.md"]["source"] == "guard docs-drift"


def test_no_findings_file_means_no_findings(git_repo):
    with_state(git_repo, findings=None)
    assert currentstate.build(git_repo.root)["findings"] == []


def test_unknown_status_fails_loudly(git_repo, capsys):
    with_state(git_repo, sd=SD.replace("| `planned` |", "| maybe |"))
    assert main(["current-state"]) == 1
    assert "Billing v2: unknown status 'maybe'" in capsys.readouterr().err
    assert not (git_repo.root / "docs/current-state.json").exists()


def test_missing_component_table_fails_loudly(git_repo, capsys):
    with_state(git_repo, sd=SD.split("| Component")[0] + "\n## 3. Data flow\n")
    assert main(["current-state"]) == 1
    assert "no component table" in capsys.readouterr().err


def test_missing_system_description_fails_loudly(git_repo, capsys):
    assert main(["current-state"]) == 1
    assert "docs/system-description.md" in capsys.readouterr().err


def test_malformed_findings_table_fails_loudly(git_repo, capsys):
    with_state(git_repo, findings="# Intake Findings\n\n## Summary\n\n| ID | What |\n|----|------|\n| F-001 | x |\n")
    assert main(["current-state"]) == 1
    assert "intake-findings.md" in capsys.readouterr().err


def test_validate_rejects_a_hand_edited_shape():
    assert currentstate.validate({"schema": 1}) != []
    good = {
        "schema": 1,
        "built_at": {"head": "a", "system_description": "b", "date": "c"},
        "components": [{"name": "A", "does": "", "status": "wired", "source": "s"}],
        "findings": [],
        "drift": [],
    }
    assert currentstate.validate(good) == []
    good["components"][0]["status"] = "maybe"
    assert currentstate.validate(good) != []


def test_code_at_a_cell_edge_keeps_its_backticks(git_repo):
    rows = "| F-004 | Rate limiting is off unless `NODE_ENV=production` | Medium | auth | open | x |\n| F-005 | `requireAdmin` is dead code | Low | auth | open | x |\n"
    with_state(git_repo, findings=FINDINGS.replace("\n## Open questions", rows + "\n## Open questions"))
    found = {f["id"]: f["finding"] for f in currentstate.build(git_repo.root)["findings"]}
    assert found["F-004"] == "Rate limiting is off unless `NODE_ENV=production`"
    assert found["F-005"] == "`requireAdmin` is dead code"
    assert currentstate.build(git_repo.root)["components"][0]["status"] == "wired"  # a fully quoted cell is unquoted
