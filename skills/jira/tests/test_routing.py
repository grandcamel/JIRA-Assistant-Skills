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

Confinement, refined against authorized live-CLI probes: `--tools
Bash,Skill` restricts the model to exactly those two tools -- `Skill`
because a plugin's SKILL.md reaches the model only through the built-in
`Skill` tool (https://code.claude.com/docs/en/tools-reference), so
without it neither skill could ever be observed loading at all; `Bash`
because the skill itself directs the model to run `jira-as`.
`--allowedTools "Bash,Skill"` is passed alongside `--tools`: a probe
found that under `--permission-mode dontAsk`, the Skill tool call is
itself DENIED unless also pre-approved this way. `--strict-mcp-config
--mcp-config <empty-mcp.json>` keeps the operator's own configured MCP
servers (which a probe found still load and expose tools otherwise) out
of a routing trial entirely. Each trial also runs with `cwd` set to a
fresh, empty temporary directory (no project CLAUDE.md or other file
from this repository applies) and with an environment built by
tests/harness_env.py's build_harness_env() -- the same allowlist the
help-only sufficiency arm uses, copying only PATH, HOME, USER, LOGNAME,
TERM and LANG (the last two if present) and forcing
JIRA_AS_TRANSPORT=simulation, so a routing trial can never inherit the
operator's real Jira credentials.

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

# Same empty MCP config the sufficiency arm uses, so the operator's own
# configured MCP servers (found by a live probe to still load and expose
# tools otherwise) never enter a routing trial either.
EMPTY_MCP_CONFIG = (REPO_ROOT / "tests" / "e2e" / "empty-mcp.json").resolve()

# Same evidence-persistence helpers the sufficiency arm uses (see
# tests/evidence.py): every trial's transcript and observed skill is
# written to disk, so a scoring question never requires re-running the
# live check.
from tests.evidence import new_run_dir, write_json, write_transcript  # noqa: E402

GOLDEN_FILE = TESTS_DIR / "routing_golden.yaml"

DEFAULT_MODEL = "claude-sonnet-5"
TRIALS_PER_PROMPT = 5
MIN_CORRECT_TRIALS = 4

KNOWN_SKILLS = ("jira", "confluence")

# One evidence directory per pytest session (this module is imported
# once per run): every trial's transcript lands here, plus a running
# summary of the observed skill per trial.
_ROUTING_RUN_DIR = new_run_dir("jas55-routing")
_ROUTING_TRIAL_COUNTERS: dict[str, int] = {}
_ROUTING_SUMMARY: dict = {"run_dir": str(_ROUTING_RUN_DIR), "prompts": {}}


def _next_routing_trial_number(test_id: str) -> int:
    _ROUTING_TRIAL_COUNTERS[test_id] = _ROUTING_TRIAL_COUNTERS.get(test_id, 0) + 1
    return _ROUTING_TRIAL_COUNTERS[test_id]


def _persist_routing_trial(
    test_id: str,
    trial_number: int,
    transcript_lines: list[str],
    result: "RoutingResult",
) -> None:
    """Write this trial's transcript and record the observed skill in the
    run-wide summary.json, so the evidence is on disk even if a later
    trial or the process itself is interrupted."""
    base_name = f"{test_id}-{trial_number}"
    write_transcript(
        _ROUTING_RUN_DIR / f"{base_name}.transcript.jsonl", transcript_lines
    )
    _ROUTING_SUMMARY["prompts"].setdefault(test_id, []).append(
        {
            "trial": trial_number,
            "skill_loaded": result.skill_loaded,
            "observation_error": result.observation_error,
        }
    )
    write_json(_ROUTING_RUN_DIR / "summary.json", _ROUTING_SUMMARY)


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

    A live probe showed the tool_use input is `{"skill":
    "jira-assistant-skills:jira"}` -- the plugin-namespaced skill name
    under the key `skill`, normalized here to the segment after the last
    colon. Other field names once checked defensively (`name`,
    `skill_name`, `command`) are not what the CLI actually sends and have
    been dropped.
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

            skill_value = (block.get("input") or {}).get("skill")
            if skill_value:
                normalized = normalize_skill_name(str(skill_value).rsplit(":", 1)[-1])
                if normalized:
                    return normalized

    return None


def run_claude_routing(
    test_id: str, input_text: str, timeout: int = 60
) -> RoutingResult:
    """
    Run Claude Code non-interactively with both plugin directories loaded,
    from a fresh empty temp directory and under the shared allowlist
    environment, and return which skill (if any) it was OBSERVED to load,
    for this one cold trial. Persists the trial's transcript and the
    observed skill to _ROUTING_RUN_DIR (see tests/evidence.py).
    """
    model = get_test_model() or DEFAULT_MODEL
    trial_number = _next_routing_trial_number(test_id)

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
        "--allowedTools",
        "Bash,Skill",
        "--strict-mcp-config",
        "--mcp-config",
        str(EMPTY_MCP_CONFIG),
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
        timeout_result = RoutingResult(
            skill_loaded=None,
            observation_error=f"claude timed out after {timeout}s",
        )
        _persist_routing_trial(test_id, trial_number, [], timeout_result)
        return timeout_result

    transcript_lines = result.stdout.splitlines()
    skill_loaded = extract_loaded_skill(transcript_lines)

    observation_error = ""
    if skill_loaded is None:
        observation_error = (
            "skill load not observed (no Skill tool_use block in transcript)"
        )

    routing_result = RoutingResult(
        skill_loaded=skill_loaded, observation_error=observation_error
    )
    _persist_routing_trial(test_id, trial_number, transcript_lines, routing_result)
    return routing_result


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
        result = run_claude_routing(test_id, input_text)
        observed.append(result.skill_loaded or f"<{result.observation_error}>")
        if result.skill_loaded == expected_skill:
            correct += 1

    print(f"[{test_id}] evidence: {_ROUTING_RUN_DIR}")

    assert correct >= MIN_CORRECT_TRIALS, (
        f"[{test_id}] expected skill {expected_skill!r} in >= "
        f"{MIN_CORRECT_TRIALS}/{TRIALS_PER_PROMPT} cold trials, "
        f"got {correct}/{TRIALS_PER_PROMPT}\n"
        f"Evidence directory: {_ROUTING_RUN_DIR}\n"
        f"Input: {input_text}\nObserved: {observed}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
