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
installed (this repo, plus the confluence-stub fixture) and observes which
skill loaded ONLY from a `Skill` tool_use block in the
`--output-format stream-json --verbose` transcript (review fix: the prior
version grepped a debug log for a "skill is loading" string that appears
in 0 debug logs on a real host, silently falling through to a keyword
guess over the model's answer text -- that made every one of the eight
product prompts pass whether or not either skill actually loaded, since
the prompt itself names the product and the answer echoes it). A trial
where no `Skill` tool_use block appears is treated as the skill loading
being unobserved, never guessed at: for the four jira and four confluence
prompts this correctly counts as a miss; for the two unrelated prompts
"no skill observed" is the correct, expected outcome.

Confinement (review fix): `--tools Bash,Skill` restricts the model to
exactly those two tools -- `Skill` because a plugin's SKILL.md reaches
the model only through the built-in `Skill` tool
(https://code.claude.com/docs/en/tools-reference), so without it neither
skill could ever be observed loading at all; `Bash` because the skill
itself directs the model to run `jira-as`. Each trial also runs with
`cwd` set to a fresh, empty temporary directory (no project CLAUDE.md or
other file from this repository applies) and with an environment built by
tests/harness_env.py's build_harness_env() -- the same allowlist the help-
only sufficiency arm uses, copying only PATH, HOME, TERM and LANG (the
last two if present) and forcing JIRA_AS_TRANSPORT=simulation, so a
routing trial can never inherit the operator's real Jira credentials.

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
import subprocess
import sys
import tempfile
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

# The shared, allowlist-based subprocess environment (tests/harness_env.py)
# also used by the help-only sufficiency arm.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from tests.harness_env import build_harness_env  # noqa: E402

GOLDEN_FILE = TESTS_DIR / "routing_golden.yaml"

DEFAULT_MODEL = "claude-sonnet-5"
TRIALS_PER_PROMPT = 5
MIN_CORRECT_TRIALS = 4

KNOWN_SKILLS = ("jira", "confluence")


class RoutingResult(NamedTuple):
    """Result of one cold trial."""

    skill_loaded: str | None
    observation_error: str = ""


def load_golden_tests() -> list[dict]:
    """Load the ten routing prompts from routing_golden.yaml."""
    with open(GOLDEN_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("tests", [])


def normalize_skill_name(skill: str) -> str | None:
    """Normalize a captured skill name to one of KNOWN_SKILLS, or None."""
    skill = skill.strip().lower()
    return skill if skill in KNOWN_SKILLS else None


def extract_loaded_skill(transcript_lines: list[str]) -> str | None:
    """
    Parse a `--output-format stream-json --verbose` transcript (one JSON
    object per line) and return the skill named by the FIRST `Skill`
    tool_use block, or None if the model never invoked the Skill tool.

    This is the ONLY source of truth for which skill loaded. There is no
    fallback that infers a skill from the model's answer text: a prompt
    that names its product ("Jira"/"Confluence") makes the answer text an
    unreliable signal, since the model can echo the product name whether
    or not it actually loaded the corresponding skill.
    """
    for line in transcript_lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") != "assistant":
            continue

        message = event.get("message", {})
        for block in message.get("content", []) or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if block.get("name") != "Skill":
                continue

            tool_input = block.get("input") or {}
            skill_name = (
                tool_input.get("name")
                or tool_input.get("skill_name")
                or tool_input.get("skill")
                or tool_input.get("command")
            )
            if skill_name:
                normalized = normalize_skill_name(str(skill_name))
                if normalized:
                    return normalized

    return None


def run_claude_routing(input_text: str, timeout: int = 60) -> RoutingResult:
    """
    Run Claude Code non-interactively with both plugin directories loaded,
    from a fresh empty temp directory and under the shared allowlist
    environment, and return which skill (if any) it was OBSERVED to load,
    for this one cold trial.
    """
    model = get_test_model() or DEFAULT_MODEL

    cmd = [
        "claude",
        "--print",
        "--permission-mode",
        "dontAsk",
        "--output-format",
        "stream-json",
        "--verbose",
        "--tools",
        "Bash,Skill",
        "--plugin-dir",
        str(REPO_ROOT),
        "--plugin-dir",
        str(CONFLUENCE_STUB_DIR),
        "--model",
        model,
    ]

    try:
        with tempfile.TemporaryDirectory(prefix="jas55-routing-") as scratch_dir:
            result = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=build_harness_env(),
                cwd=scratch_dir,
            )
    except subprocess.TimeoutExpired:
        return RoutingResult(
            skill_loaded=None,
            observation_error=f"claude timed out after {timeout}s",
        )

    transcript_lines = result.stdout.splitlines()
    skill_loaded = extract_loaded_skill(transcript_lines)

    observation_error = ""
    if skill_loaded is None:
        observation_error = (
            "skill load not observed (no Skill tool_use block in transcript)"
        )

    return RoutingResult(skill_loaded=skill_loaded, observation_error=observation_error)


# Load tests at module level for parametrization
GOLDEN_TESTS = load_golden_tests()


@pytest.mark.parametrize("test_case", GOLDEN_TESTS, ids=lambda t: t["id"])
def test_routing(test_case):
    """
    Run TRIALS_PER_PROMPT cold trials for one prompt.

    A prompt passes at MIN_CORRECT_TRIALS or more matching trials out of
    TRIALS_PER_PROMPT. `expected_skill: null` means the prompt should load
    neither skill -- for those prompts, "skill load not observed" IS the
    correct, expected outcome, since no Skill tool_use block should ever
    appear. The routing check as a whole (this module) passes only when
    every prompt passes.
    """
    input_text = test_case["input"]
    expected_skill = test_case.get("expected_skill")  # None means "neither"
    test_id = test_case["id"]

    correct = 0
    observed = []
    for _ in range(TRIALS_PER_PROMPT):
        result = run_claude_routing(input_text)
        observed.append(result.skill_loaded or f"<{result.observation_error}>")
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
