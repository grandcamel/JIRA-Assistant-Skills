"""Verify source coverage and the public local-citation audit command."""

import hashlib
import json
import subprocess  # nosec B404: offline Python audit subprocesses only
import sys
from pathlib import Path

HERE = Path(__file__).parent


def test_inventory_preserves_all_hypotheses():
    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    facts = inventory["facts"]
    assert len(facts) == 153
    assert {f["id"] for f in facts} == {f"G{n:03}" for n in range(1, 154)}
    assert {f["inventory_item"] for f in facts} == set(range(1, 154))
    assert len({f["question"] for f in facts}) == 153
    for fact in facts:
        assert fact["expected"] == fact["wrong_hypothesis_quote"]
        assert fact["question"].startswith(
            "Answer from your own knowledge only, in at most 3 sentences. Do not use tools. "
        )
        assert fact["citations"]
        assert fact["repo"] in ("jira", "confluence")
        for citation in fact["citations"]:
            assert citation["file"].startswith("skills/")
            assert ".." not in Path(citation["file"]).parts
            assert citation["lines"]
            assert len(citation["source_sha256"]) == 64
            if citation["audit_status"] == "out_of_range":
                assert fact["citation_review_required"]


def test_audit_reports_missing_out_of_range_and_changed_sources(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "source.md"
    source.write_text("a fact\n", encoding="utf-8")
    citation = {
        "repo": "jira",
        "file": "source.md",
        "lines": [[1, 1]],
        "excerpt_lines": [[1, 1]],
        "excerpt": "a fact",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    facts = [
        {"id": f"G{n:03}", "inventory_item": n, "citations": [dict(citation)]}
        for n in range(1, 154)
    ]
    inventory = tmp_path / "inventory.json"
    report = tmp_path / "audit.json"

    def invoke():
        inventory.write_text(json.dumps({"schema_version": 1, "facts": facts}))
        result = subprocess.run(  # nosec B603: fixed Python audit script; no network or model CLI
            [
                sys.executable,
                str(HERE / "audit_inventory.py"),
                "--inventory",
                str(inventory),
                "--jira-root",
                str(root),
                "--confluence-root",
                str(root),
                "--output",
                str(report),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result, json.loads(report.read_text())

    result, data = invoke()
    assert result.returncode == 0, result.stderr
    assert data["counts"]["resolves"] == 153
    facts[0]["citations"][0]["file"] = "absent.md"
    facts[1]["citations"][0]["lines"] = [[2, 2]]
    result, data = invoke()
    assert result.returncode == 1
    assert data["counts"]["missing_file"] == 1
    assert data["counts"]["out_of_range"] == 1
    source.write_text("different fact\n", encoding="utf-8")
    result, data = invoke()
    assert result.returncode == 1
    assert data["changed_source_citations"] == 152
    assert data["excerpt_mismatches"] == 152


def test_explicit_snapshot_only_replaces_marked_citations(tmp_path):
    repo = tmp_path / "repo"
    snapshot = tmp_path / "snapshot"
    repo.mkdir()
    snapshot.mkdir()
    (repo / "source.md").write_text("old\n")
    snap_source = snapshot / "source.md"
    snap_source.write_text("research version\n")
    facts = [
        {
            "id": f"G{n:03}",
            "inventory_item": n,
            "citations": [
                {
                    "repo": "jira",
                    "file": "source.md",
                    "lines": [[1, 1]],
                    "excerpt_lines": [[1, 1]],
                    "excerpt": "research version",
                    "source_sha256": hashlib.sha256(
                        snap_source.read_bytes()
                    ).hexdigest(),
                    "audit_status": "uncommitted_main_snapshot",
                }
            ],
        }
        for n in range(1, 154)
    ]
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"schema_version": 1, "facts": facts}))
    report = tmp_path / "report.json"
    command = [
        sys.executable,
        str(HERE / "audit_inventory.py"),
        "--inventory",
        str(inventory),
        "--jira-root",
        str(repo),
        "--confluence-root",
        str(repo),
        "--output",
        str(report),
    ]
    baseline = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603: local audit only
    assert baseline.returncode == 1
    assert json.loads(report.read_text())["changed_source_citations"] == 153
    resolved = subprocess.run(  # nosec B603: local audit only
        command + ["--jira-snapshot", str(snapshot)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resolved.returncode == 0, resolved.stderr
    assert json.loads(report.read_text())["counts"]["resolves"] == 153
    facts[0]["citations"][0]["audit_status"] = "context_resolves"
    inventory.write_text(json.dumps({"schema_version": 1, "facts": facts}))
    partial = subprocess.run(  # nosec B603: local audit only
        command + ["--jira-snapshot", str(snapshot)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert partial.returncode == 1
    assert json.loads(report.read_text())["changed_source_citations"] == 1
