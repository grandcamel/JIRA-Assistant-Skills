"""
Offline unit tests for tests/stream_observe.py's run_and_observe: the
Popen-based incremental reader the two-skill routing check
(skills/jira/tests/test_routing.py) uses to stop a trial the moment its
observation is complete, instead of blocking until the model finishes an
entire task or the harness's own timeout fires.

No `claude` binary is launched anywhere in this file. Each test launches
a tiny, deterministic Python subprocess (`sys.executable -c <script>`)
standing in for `claude`'s stream-json stdout, so the SUBPROCESS-
management behavior itself -- early return, process termination, and the
overall timeout -- is exercised for real. The line-parsing rules for an
actual Skill tool_use block are covered separately, on canned transcript
lines, in skills/jira/tests/test_routing.py's own offline tests.
"""

import json
import sys
import time

from tests.stream_observe import run_and_observe

SKILL_LINE = json.dumps(
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "name": "Skill",
                    "input": {"skill": "jira-assistant-skills:jira"},
                }
            ]
        },
    }
)


def _detect_skill(line: str) -> str | None:
    """Minimal stand-in for test_routing.py's own detector: returns
    "jira" the moment a line carries a Skill tool_use block, else None."""
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None
    if event.get("type") != "assistant":
        return None
    for block in event.get("message", {}).get("content", []) or []:
        if block.get("type") == "tool_use" and block.get("name") == "Skill":
            return "jira"
    return None


def test_early_observation_stops_reading_before_later_lines():
    """A line matching the detector returns immediately -- a line the
    fake process emits only after a much longer delay is never read,
    proving the harness does not keep draining stdout once it has its
    answer."""
    script = f"""
import time
print({SKILL_LINE!r}, flush=True)
time.sleep(5)
print("SHOULD_NOT_BE_SEEN", flush=True)
"""
    start = time.monotonic()
    observation = run_and_observe(
        [sys.executable, "-c", script],
        input_text="",
        detect_line=_detect_skill,
        timeout=10,
        terminate_grace=1,
    )
    elapsed = time.monotonic() - start

    assert observation.result == "jira"
    assert observation.timed_out is False
    assert "SHOULD_NOT_BE_SEEN" not in observation.lines
    assert elapsed < 4, f"took {elapsed:.1f}s -- did not stop early"


def test_no_skill_block_returns_none():
    """A process that emits ordinary (non-Skill) stream-json lines and
    exits on its own is read to completion and reported as no
    observation -- not an error, and not a timeout."""
    plain_line = json.dumps({"type": "assistant", "message": {"content": []}})
    script = f"""
print({plain_line!r}, flush=True)
print({plain_line!r}, flush=True)
"""
    observation = run_and_observe(
        [sys.executable, "-c", script],
        input_text="",
        detect_line=_detect_skill,
        timeout=10,
        terminate_grace=1,
    )

    assert observation.result is None
    assert observation.timed_out is False
    assert observation.lines == [plain_line, plain_line]


def test_stall_after_skill_block_still_returns_the_observation():
    """The fake process emits the Skill line and then hangs far longer
    than the overall timeout without exiting or closing stdout. The
    early-stop logic must fire on the Skill line itself -- proving the
    harness never blocks on process completion once it has observed
    what it needed, even when the process never voluntarily ends."""
    script = f"""
import time
print({SKILL_LINE!r}, flush=True)
time.sleep(30)
"""
    start = time.monotonic()
    observation = run_and_observe(
        [sys.executable, "-c", script],
        input_text="",
        detect_line=_detect_skill,
        timeout=10,
        terminate_grace=1,
    )
    elapsed = time.monotonic() - start

    assert observation.result == "jira"
    assert observation.timed_out is False
    assert elapsed < 5, f"took {elapsed:.1f}s -- blocked on the stalled process"


def test_overall_timeout_with_nothing_observed():
    """A process that never emits a matching line and never exits is cut
    off at the overall timeout; this -- and only this -- case reports
    timed_out=True."""
    script = "import time\ntime.sleep(30)"
    start = time.monotonic()
    observation = run_and_observe(
        [sys.executable, "-c", script],
        input_text="",
        detect_line=_detect_skill,
        timeout=1,
        terminate_grace=1,
    )
    elapsed = time.monotonic() - start

    assert observation.result is None
    assert observation.timed_out is True
    assert 0.5 < elapsed < 5, f"took {elapsed:.1f}s -- ignored the timeout"


def test_on_line_callback_receives_every_line_as_read():
    """The persistence hook (on_line) is called once per line, in order,
    matching the returned .lines -- this is what lets a caller persist
    the transcript incrementally instead of only at the end."""
    plain_line = json.dumps({"type": "user", "message": {"content": []}})
    script = f"print({plain_line!r}, flush=True)"
    seen: list[str] = []
    observation = run_and_observe(
        [sys.executable, "-c", script],
        input_text="",
        detect_line=_detect_skill,
        on_line=seen.append,
        timeout=10,
        terminate_grace=1,
    )

    assert seen == [plain_line]
    assert observation.lines == [plain_line]
