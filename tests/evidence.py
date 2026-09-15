"""
Shared evidence-persistence helpers for the two live harnesses: the
help-only sufficiency arm (tests/e2e/) and the two-skill routing check
(skills/jira/tests/test_routing.py).

Run 2 of the sufficiency arm and manual reproductions showed the model
completing tasks while the harness's scoring silently disagreed. Without
a persisted record of what actually happened -- the raw transcript, every
command the model ran, which ones the harness thought matched, and every
replay's exit code/output -- diagnosing a harness defect versus a real
model failure requires re-running the (expensive, non-deterministic) live
arm. This module makes each run write that record to disk once, so it
never has to be reconstructed after the fact.
"""

import json
import os
import time
from pathlib import Path


def new_run_dir(prefix: str) -> Path:
    """
    Create and return a fresh evidence directory
    `${TMPDIR:-/tmp}/<prefix>-<UTC timestamp>/`, created once per
    pytest session (call this at import time or from a session-scoped
    fixture/singleton, not per trial).
    """
    base = Path(os.environ.get("TMPDIR") or "/tmp")
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_dir = base / f"{prefix}-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_json(path: Path, data) -> None:
    """Write `data` as indented JSON, tolerating non-JSON-native values
    (e.g. dataclasses) via str() fallback."""
    path.write_text(json.dumps(data, indent=2, default=_json_default))


def write_transcript(path: Path, transcript_lines: list[str]) -> None:
    """Write the raw stream-json transcript, one JSON object per line,
    exactly as captured (no reformatting -- this is the primary source
    of truth for diagnosing a harness defect after the fact)."""
    text = "\n".join(transcript_lines)
    if transcript_lines:
        text += "\n"
    path.write_text(text)


def _json_default(value):
    if hasattr(value, "__dict__"):
        return value.__dict__
    return str(value)
