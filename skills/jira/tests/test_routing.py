#!/usr/bin/env python3
"""
Two-skill routing check for the jira skill.

With one skill per plugin, disambiguating among the thirteen retired domain
skills inside a single plugin is moot. What remains worth checking is
*inter-plugin* discrimination: given a prompt, does Claude Code load the
`jira` skill from this plugin, the `confluence` skill from the non-shipped
`tests/fixtures/confluence-stub/` fixture plugin, or neither -- and does it
get this right consistently across cold trials?

This runs Claude Code non-interactively with BOTH plugin directories
installed (this repo, plus the confluence-stub fixture) and inspects the
debug log to see which skill loaded, the same mechanism the retired
intra-plugin routing test used.

Usage:
    # Run the full routing check (five cold trials per prompt)
    pytest test_routing.py -v

Requirements:
    - Claude Code CLI installed and configured
    - pytest: pip install pytest pyyaml

Not run in CI: this launches the `claude` binary directly. See
.github/workflows/ci.yml, which deselects this file, and
tests/e2e/README.md for the host-triggered process this check belongs to.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import pytest
import yaml

# Mark all tests in this module as 'live' - they require the Claude CLI
pytestmark = pytest.mark.live

TESTS_DIR = Path(__file__).parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

# Import model config from conftest (after sys.path modification)
from conftest import get_test_model  # noqa: E402

# The plugin under test (this repo) and the non-shipped fixture plugin used
# only to give the routing check a second skill to discriminate against.
REPO_ROOT = TESTS_DIR.parents[2]
CONFLUENCE_STUB_DIR = REPO_ROOT / "tests" / "fixtures" / "confluence-stub"

GOLDEN_FILE = TESTS_DIR / "routing_golden.yaml"
DEBUG_DIR = Path.home() / ".claude" / "debug"

DEFAULT_MODEL = "claude-sonnet-5"
TRIALS_PER_PROMPT = 5
MIN_CORRECT_TRIALS = 4

KNOWN_SKILLS = ("jira", "confluence")


class RoutingResult(NamedTuple):
    """Result of one cold trial."""

    skill_loaded: str | None
    session_id: str
    response_text: str


def load_golden_tests() -> list[dict]:
    """Load the ten routing prompts from routing_golden.yaml."""
    with open(GOLDEN_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("tests", [])


def normalize_skill_name(skill: str) -> str | None:
    """Normalize a captured skill name to one of KNOWN_SKILLS, or None."""
    skill = skill.strip().lower()
    return skill if skill in KNOWN_SKILLS else None


def infer_skill_from_response(response_text: str) -> str | None:
    """
    Fallback: infer the loaded skill from response content when the debug
    log doesn't show an explicit Skill-tool invocation.

    Only two candidate skills exist now, so this just needs to discriminate
    jira content from confluence content in what Claude actually said/ran.
    """
    text = response_text.lower()
    jira_hit = bool(re.search(r"\bjira-as\b|\bjira\b", text))
    confluence_hit = bool(re.search(r"\bconfluence\b", text))
    if jira_hit and not confluence_hit:
        return "jira"
    if confluence_hit and not jira_hit:
        return "confluence"
    return None


def run_claude_routing(input_text: str, timeout: int = 60) -> RoutingResult:
    """
    Run Claude Code non-interactively with both plugin directories loaded
    and return which skill (if any) it routed to for this one cold trial.
    """
    model = get_test_model() or DEFAULT_MODEL

    cmd = [
        "claude",
        "--print",
        "--permission-mode",
        "dontAsk",
        "--output-format",
        "json",
        "--debug",
        "--plugin-dir",
        str(REPO_ROOT),
        "--plugin-dir",
        str(CONFLUENCE_STUB_DIR),
        "--model",
        model,
    ]

    result = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse Claude output: {result.stdout[:500]}")

    session_id = output.get("session_id", "")
    response_text = output.get("result", "")

    skill_loaded = None

    # Method 1 (kept from the retired intra-plugin routing test): look for
    # an explicit Skill-tool invocation in the debug log.
    debug_file = DEBUG_DIR / f"{session_id}.txt"
    if debug_file.exists():
        debug_content = debug_file.read_text()
        skill_match = re.search(
            r"skill is loading.*?\b(jira|confluence)\b",
            debug_content,
            re.IGNORECASE,
        )
        if skill_match:
            skill_loaded = normalize_skill_name(skill_match.group(1))

    # Method 2: infer from response content when the debug log is silent
    # (e.g. Claude answered from cached knowledge without the Skill tool).
    if not skill_loaded:
        skill_loaded = infer_skill_from_response(response_text)

    return RoutingResult(
        skill_loaded=skill_loaded,
        session_id=session_id,
        response_text=response_text,
    )


# Load tests at module level for parametrization
GOLDEN_TESTS = load_golden_tests()


@pytest.mark.parametrize("test_case", GOLDEN_TESTS, ids=lambda t: t["id"])
def test_routing(test_case):
    """
    Run TRIALS_PER_PROMPT cold trials for one prompt.

    A prompt passes at MIN_CORRECT_TRIALS or more matching trials out of
    TRIALS_PER_PROMPT. `expected_skill: null` means the prompt should load
    neither skill. The routing check as a whole (this module) passes only
    when every prompt passes.
    """
    input_text = test_case["input"]
    expected_skill = test_case.get("expected_skill")  # None means "neither"
    test_id = test_case["id"]

    correct = 0
    observed = []
    for _ in range(TRIALS_PER_PROMPT):
        result = run_claude_routing(input_text)
        observed.append(result.skill_loaded)
        if result.skill_loaded == expected_skill:
            correct += 1

    assert correct >= MIN_CORRECT_TRIALS, (
        f"[{test_id}] expected skill {expected_skill!r} in >= "
        f"{MIN_CORRECT_TRIALS}/{TRIALS_PER_PROMPT} cold trials, "
        f"got {correct}/{TRIALS_PER_PROMPT}\n"
        f"Input: {input_text}\nObserved: {observed}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
