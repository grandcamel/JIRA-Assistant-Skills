"""Black-box tests for the floor evaluator's public command-line interface."""

import fcntl
import hashlib
import json
import shutil
import subprocess  # nosec B404: local offline CLI fixtures only
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent
DRIVER = ROOT / "run_eval.py"


def fact(identifier: str = "G001") -> dict:
    return {
        "id": identifier,
        "repo": "jira",
        "inventory_item": 1,
        "topic": "fixture",
        "question": "Answer from your own knowledge only, in at most 3 sentences. Do not use tools. Fixture question?",
        "expected": "Fixture expected fact.",
        "citations": [
            {
                "repo": "jira",
                "file": "skills/example/SKILL.md",
                "lines": [[1, 1]],
                "excerpt": "fixture",
            }
        ],
        "wrong_hypothesis_quote": "Fixture was originally treated as a gotcha.",
        "source_line": 1,
    }


def setup(tmp_path: Path, scenario: str) -> tuple[Path, Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps({"schema_version": 1, "facts": [fact()]}), encoding="utf-8"
    )
    fixtures = tmp_path / "fixtures"
    shutil.copytree(ROOT / "fake_models", fixtures)
    scenarios = json.loads((fixtures / "scenarios.json").read_text(encoding="utf-8"))
    scenarios["facts"] = {"G001": scenario}
    (fixtures / "scenarios.json").write_text(json.dumps(scenarios), encoding="utf-8")
    return inventory, fixtures, tmp_path / "output"


def invoke(
    inventory: Path, fixtures: Path, output: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "--inventory",
            str(inventory),
            "--output",
            str(output),
            "--fake-models",
            str(fixtures),
            "--workers",
            "2",
            "--retry-backoff",
            "0",
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def result(output: Path) -> dict:
    return json.loads((output / "classification.json").read_text(encoding="utf-8"))


def test_complete_floor_and_zero_call_resume(tmp_path: Path) -> None:
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    first = invoke(inventory, fixtures, output)
    assert first.returncode == 0, first.stderr
    classified = result(output)
    assert classified["complete"] is True
    assert classified["facts"][0]["verdict"] == "floor"
    first_log = (output / "fake-invocations.jsonl").read_text(encoding="utf-8")
    assert len(first_log.splitlines()) == 12
    resumed = invoke(inventory, fixtures, output, "--resume")
    assert resumed.returncode == 0, resumed.stderr
    assert (output / "fake-invocations.jsonl").read_text(encoding="utf-8") == first_log


def test_four_of_five_passes_and_three_of_five_keeps(tmp_path: Path) -> None:
    inventory, fixtures, output = setup(tmp_path, "four_of_five")
    assert invoke(inventory, fixtures, output).returncode == 0
    assert result(output)["facts"][0]["verdict"] == "floor"
    inventory, fixtures, output = setup(tmp_path / "three", "three_of_five")
    assert invoke(inventory, fixtures, output).returncode == 0
    assert result(output)["facts"][0]["verdict"] == "gotcha"


def test_contradiction_is_stale_and_malformed_judge_is_retryable(
    tmp_path: Path,
) -> None:
    inventory, fixtures, output = setup(tmp_path, "confident_contradiction")
    assert invoke(inventory, fixtures, output).returncode == 0
    row = result(output)["facts"][0]
    assert row["stale_candidate"] is True
    assert row["verdict"] == "gotcha"
    inventory, fixtures, output = setup(tmp_path / "malformed", "all_correct")
    scenarios = json.loads((fixtures / "scenarios.json").read_text(encoding="utf-8"))
    scenarios["facts"]["G001"] = {
        "correct": [True] * 5,
        "inject": "malformed_judge_once",
    }
    (fixtures / "scenarios.json").write_text(json.dumps(scenarios), encoding="utf-8")
    failed = invoke(inventory, fixtures, output)
    assert failed.returncode == 0
    assert result(output)["facts"][0]["verdict"] == "floor"
    resumed = invoke(inventory, fixtures, output, "--resume")
    assert resumed.returncode == 0, resumed.stderr
    assert result(output)["facts"][0]["verdict"] == "floor"


def configure(fixtures, spec):
    path = fixtures / "scenarios.json"
    data = json.loads(path.read_text())
    data["facts"]["G001"] = spec
    path.write_text(json.dumps(data))


def summary(output):
    return json.loads((output / "run_summary.json").read_text())


@pytest.mark.parametrize(
    "response", [[], {"correct": [1, 1, 1, 1, 1]}, {"correct": [True] * 4}, None]
)
def test_well_formed_but_invalid_judge_is_incomplete(tmp_path, response):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    configure(fixtures, {"correct": [True] * 5, "judge_response": response})
    run = invoke(inventory, fixtures, output)
    assert run.returncode == 1, run.stdout
    assert result(output)["facts"][0]["verdict"] == "incomplete"
    assert summary(output)["incomplete_fact_ids"] == ["G001"]
    assert summary(output)["trial_calls"] == 10
    assert summary(output)["judge_calls"] == 4


@pytest.mark.parametrize(
    "scenario,stale,consistent",
    [
        ("uncertain", False, False),
        (
            {
                "correct": [True, True, True, True, False],
                "contradictions": [False] * 4 + [True],
            },
            True,
            False,
        ),
        (
            {
                "correct": [False] * 5,
                "contradiction": True,
                "consistent_contradiction": False,
            },
            True,
            False,
        ),
        ("confident_contradiction", True, True),
    ],
)
def test_contradiction_distinguished_from_uncertainty(
    tmp_path, scenario, stale, consistent
):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    configure(fixtures, scenario)
    run = invoke(inventory, fixtures, output)
    assert run.returncode == 0, run.stdout + run.stderr
    row = result(output)["facts"][0]
    assert row["stale_candidate"] is stale
    assert row["consistent_stale_candidate"] is consistent
    if stale:
        assert "jira:skills/example/SKILL.md" in (output / "stale-facts.md").read_text()
        assert row["review_required"]


def test_any_floor_model_below_threshold_keeps_fact(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    configure(fixtures, {"models": {"sonnet": "three_of_five", "terra": "all_correct"}})
    assert invoke(inventory, fixtures, output).returncode == 0
    row = result(output)["facts"][0]
    assert row["models"]["sonnet"]["correct"] == 3
    assert row["models"]["terra"]["correct"] == 5
    assert row["verdict"] == "gotcha"
    assert row["review_required"]


def test_failure_retries_once_and_other_facts_complete(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    configure(
        fixtures,
        {
            "correct": [True] * 5,
            "inject": "failure",
            "inject_kind": "trial",
            "inject_trial": 1,
        },
    )
    data = json.loads(inventory.read_text())
    data["facts"].append(fact("G002"))
    inventory.write_text(json.dumps(data))
    run = invoke(inventory, fixtures, output)
    assert run.returncode == 1
    rows = result(output)["facts"]
    assert [row["verdict"] for row in rows] == ["incomplete", "floor"]
    assert summary(output)["trial_calls"] == 22
    assert summary(output)["judge_calls"] == 2
    assert summary(output)["incomplete_fact_ids"] == ["G001"]
    attempts = list((output / "raw" / "attempts").rglob("*.json"))
    before = {str(path): path.read_bytes() for path in attempts}
    assert invoke(inventory, fixtures, output, "--resume").returncode == 1
    assert all(Path(path).read_bytes() == content for path, content in before.items())
    assert summary(output)["trial_calls"] == 4
    assert summary(output)["judge_calls"] == 0
    assert summary(output)["reused"] == 20


def test_transient_failure_recovers_in_same_run(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    configure(
        fixtures,
        {
            "correct": [True] * 5,
            "inject": "failure_once",
            "inject_kind": "trial",
            "inject_trial": 1,
        },
    )
    run = invoke(inventory, fixtures, output)
    assert run.returncode == 0
    assert summary(output)["trial_calls"] == 12
    assert summary(output)["failed"] == 0
    assert summary(output)["incomplete_fact_ids"] == []


def test_timeouts_preserve_partial_output_and_retry(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    configure(
        fixtures,
        {
            "correct": [True] * 5,
            "inject": "timeout",
            "inject_kind": "trial",
            "inject_trial": 1,
            "seconds": 2,
        },
    )
    run = invoke(inventory, fixtures, output, "--timeout", "0.25")
    assert run.returncode == 1
    receipt = json.loads((output / "raw/sonnet/G001_t1.meta.json").read_text())
    assert receipt["timeout"] is True
    assert "fixture partial stdout" in receipt["stdout"]
    assert "fixture partial stderr" in receipt["stderr"]
    assert summary(output)["trial_calls"] == 12


@pytest.mark.parametrize(
    "damage", ["trial_missing", "trial_corrupt", "judge_missing", "judge_parsed"]
)
def test_resume_recovers_completed_attempts_without_new_calls(tmp_path, damage):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    assert invoke(inventory, fixtures, output).returncode == 0
    before = (output / "fake-invocations.jsonl").read_bytes()
    if damage == "trial_missing":
        (output / "raw/sonnet/G001_t1.meta.json").unlink()
    elif damage == "trial_corrupt":
        (output / "raw/sonnet/G001_t1.txt").write_text("corrupted")
    elif damage == "judge_missing":
        (output / "raw/judge/G001_sonnet.raw.txt").unlink()
    else:
        path = output / "raw/judge/G001_sonnet.json"
        data = json.loads(path.read_text())
        data["parsed"]["correct"] = [False] * 5
        path.write_text(json.dumps(data))
    resumed = invoke(inventory, fixtures, output, "--resume")
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert (output / "fake-invocations.jsonl").read_bytes() == before
    assert result(output)["facts"][0]["verdict"] == "floor"
    assert summary(output)["total_calls"] == 0


def test_changed_trial_invalidates_judge_dependency(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    assert invoke(inventory, fixtures, output).returncode == 0
    path = output / "raw/sonnet/G001_t1.txt"
    path.write_text("A different answer.")
    meta = path.with_name("G001_t1.meta.json")
    data = json.loads(meta.read_text())
    data["answer_hash"] = hashlib.sha256(path.read_bytes()).hexdigest()
    meta.write_text(json.dumps(data))
    assert invoke(inventory, fixtures, output, "--resume").returncode == 0
    assert summary(output)["trial_calls"] == 0
    assert summary(output)["judge_calls"] == 1
    prompt = json.loads((output / "raw/judge/G001_sonnet.json").read_text())["prompt"]
    assert "A different answer." in prompt


@pytest.mark.parametrize("mismatch", ["inventory", "commands", "fake", "selection"])
def test_resume_refuses_mismatched_inputs_without_calls(tmp_path, mismatch):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    assert invoke(inventory, fixtures, output).returncode == 0
    before = (output / "fake-invocations.jsonl").read_bytes()
    extras = []
    if mismatch == "inventory":
        data = json.loads(inventory.read_text())
        data["facts"][0]["expected"] = "changed reference"
        inventory.write_text(json.dumps(data))
    elif mismatch == "commands":
        path = tmp_path / "commands.json"
        data = json.loads((ROOT / "commands.json").read_text())
        data["models"]["sonnet"]["model_id"] = "new-model"
        path.write_text(json.dumps(data))
        extras = ["--commands", str(path)]
    elif mismatch == "fake":
        configure(fixtures, "three_of_five")
    else:
        extras = ["--limit", "1"]
    run = invoke(inventory, fixtures, output, "--resume", *extras)
    assert run.returncode == 2
    assert "incompatible" in run.stderr
    assert (output / "fake-invocations.jsonl").read_bytes() == before


def test_filters_include_cross_repo_citations_and_relative_fake_path(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    data = json.loads(inventory.read_text())
    data["facts"].append(fact("G002"))
    data["facts"][1]["citations"][0]["repo"] = "confluence"
    inventory.write_text(json.dumps(data))
    run = subprocess.run(  # nosec B603: local fake only
        [
            sys.executable,
            str(DRIVER.resolve()),
            "--inventory",
            str(inventory),
            "--fake-models",
            "fixtures",
            "--output",
            str(output),
            "--repo",
            "confluence",
            "--facts",
            "G001,G002",
            "--limit",
            "1",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert [row["id"] for row in result(output)["facts"]] == ["G002"]
    assert result(output)["full_inventory"] is False
    assert "FILTERED RUN" in (output / "flipped-to-floor.md").read_text()


def test_lock_and_workers_refusals(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    assert invoke(inventory, fixtures, output, "--workers", "5").returncode == 2
    output.mkdir()
    with (output / ".floor-eval.lock").open("w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = invoke(inventory, fixtures, output)
        assert run.returncode == 2
        assert "another run owns" in run.stderr
    assert not (output / "fake-invocations.jsonl").exists()


def test_concurrency_never_exceeds_four(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    configure(fixtures, {"correct": [True] * 5, "delay": 0.08})
    assert invoke(inventory, fixtures, output, "--workers", "4").returncode == 0
    calls = [
        json.loads(line)
        for line in (output / "fake-completions.jsonl").read_text().splitlines()
    ]
    events = sorted(
        [(c["started"], 1) for c in calls] + [(c["finished"], -1) for c in calls]
    )
    running, peak = 0, 0
    for _, delta in events:
        running += delta
        peak = max(peak, running)
    assert 1 < peak <= 4


def test_custom_command_model_placeholder_and_required_output(tmp_path):
    inventory, fixtures, output = setup(tmp_path, "all_correct")
    script = tmp_path / "command.py"
    log = tmp_path / "argv.jsonl"
    script.write_text(
        "import json,sys\nfrom pathlib import Path\n"
        f"with open({str(log)!r}, 'a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')\n"
        "print('non-answer CLI banner')\n"
    )
    commands = json.loads((ROOT / "commands.json").read_text())
    for command in commands["models"].values():
        command["argv"] = [
            sys.executable,
            str(script),
            "{model_id}",
            "{outfile}",
            "{prompt}",
        ]
    commands["models"]["sonnet"]["model_id"] = "changed-once"
    path = tmp_path / "commands.json"
    path.write_text(json.dumps(commands))
    run = subprocess.run(  # nosec B603: configured commands point exclusively at local Python stub
        [
            sys.executable,
            str(DRIVER),
            "--inventory",
            str(inventory),
            "--commands",
            str(path),
            "--output",
            str(output),
            "--retry-backoff",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 1
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert sum(call[0] == "changed-once" for call in calls) == 5
    assert sum(call[0] == "gpt-5.6-terra" for call in calls) == 10
    row = json.loads((output / "raw/terra/G001_t1.meta.json").read_text())
    assert row["complete"] is False
    assert "missing required outfile" in row["stderr"]
    assert (output / "raw/terra/G001_t1.txt").read_text() == ""
    trial_prompt = next(call[-1] for call in calls if call[0] == "changed-once")
    assert "Fixture expected fact." not in trial_prompt
    assert "CITATION SNAPSHOTS" not in trial_prompt


def test_interrupt_marks_run_incomplete_and_resumes_collected_calls(tmp_path):
    import signal
    import time

    inventory, fixtures, output = setup(tmp_path, "all_correct")
    configure(fixtures, {"correct": [True] * 5, "delay": 0.3})
    child = subprocess.Popen(  # nosec B603: owned offline evaluator process
        [
            sys.executable,
            str(DRIVER),
            "--inventory",
            str(inventory),
            "--fake-models",
            str(fixtures),
            "--output",
            str(output),
            "--workers",
            "2",
            "--retry-backoff",
            "0",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while (
            not (output / "fake-invocations.jsonl").exists()
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        assert (output / "fake-invocations.jsonl").exists()
        assert result(output)["status"] == "running"
        assert result(output)["complete"] is False
        child.send_signal(signal.SIGINT)
        stdout, stderr = child.communicate(timeout=10)
        assert child.returncode == 1, stdout + stderr
        assert result(output)["complete"] is False
        assert "interrupted" in " ".join(result(output)["failures"])
        before = len((output / "fake-invocations.jsonl").read_text().splitlines())
        assert before < 10
        resumed = invoke(inventory, fixtures, output, "--resume")
        assert resumed.returncode == 0, resumed.stderr
        assert summary(output)["total_calls"] == 12 - before
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=10)
