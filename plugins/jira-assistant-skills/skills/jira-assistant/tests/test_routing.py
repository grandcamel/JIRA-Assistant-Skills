#!/usr/bin/env python3
"""
Automated routing tests for jira-assistant skill.

Runs Claude Code non-interactively and verifies correct skill routing
by checking debug logs for which skill was loaded.

Usage:
    # Run all tests
    pytest test_routing.py -v

    # Run specific category
    pytest test_routing.py -v -k "direct"

    # Run with debug output
    pytest test_routing.py -v -s

    # Run with OpenTelemetry metrics
    pytest test_routing.py -v --otel

Requirements:
    - Claude Code CLI installed and configured
    - Plugin installed: claude plugins add /path/to/jira-assistant-skills
    - pytest: pip install pytest pyyaml
    - OpenTelemetry (optional): pip install -r requirements-otel.txt
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import NamedTuple

import pytest
import yaml

# Add tests directory to path for otel_metrics import
TESTS_DIR = Path(__file__).parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

# OpenTelemetry integration (optional)
try:
    from otel_metrics import (
        init_telemetry,
        record_test_result,
        record_test_session_summary,
        shutdown as otel_shutdown,
        OTEL_AVAILABLE
    )
except ImportError:
    OTEL_AVAILABLE = False
    init_telemetry = None
    record_test_result = None
    record_test_session_summary = None
    otel_shutdown = None

# Path to the golden test set
GOLDEN_FILE = TESTS_DIR / "routing_golden.yaml"
DEBUG_DIR = Path.home() / ".claude" / "debug"


class RoutingResult(NamedTuple):
    """Result of a routing test."""
    skill_loaded: str | None
    asked_clarification: bool
    session_id: str
    duration_ms: int
    cost_usd: float


def load_golden_tests() -> list[dict]:
    """Load test cases from routing_golden.yaml."""
    with open(GOLDEN_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("tests", [])


def run_claude_routing(input_text: str, timeout: int = 60) -> RoutingResult:
    """
    Run Claude Code with input and extract routing result.

    Args:
        input_text: The user input to test
        timeout: Maximum seconds to wait

    Returns:
        RoutingResult with skill loaded and metadata
    """
    if not input_text:
        # Empty input edge case
        return RoutingResult(
            skill_loaded=None,
            asked_clarification=True,
            session_id="",
            duration_ms=0,
            cost_usd=0.0
        )

    # Run Claude non-interactively
    result = subprocess.run(
        [
            "claude",
            "--print",
            "--permission-mode", "dontAsk",
            "--output-format", "json",
            "--debug",
        ],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    # Parse JSON output
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse Claude output: {result.stdout[:500]}")

    session_id = output.get("session_id", "")
    duration_ms = output.get("duration_ms", 0)
    cost_usd = output.get("total_cost_usd", 0.0)
    response_text = output.get("result", "")
    permission_denials = output.get("permission_denials", [])

    # Check if DISAMBIGUATION was asked (not just any question)
    # "Would you like me to run this" is NOT disambiguation - it's confirmation
    response_lower = response_text.lower()
    asked_clarification = "?" in response_text and any(
        phrase in response_lower
        for phrase in [
            "which skill",
            "which would you",
            "did you mean",
            "do you want sprint details or",
            "do you want to delete them or close",
            "update fields on one issue or multiple",
        ]
    ) and not any(
        phrase in response_lower
        for phrase in [
            "would you like me to run",
            "shall i run",
            "shall i execute",
            "want me to run",
            "want me to execute",
        ]
    )

    # Detect skill from multiple sources
    skill_loaded = None

    # Method 1: Check debug log for explicit skill loading
    debug_file = DEBUG_DIR / f"{session_id}.txt"
    if debug_file.exists():
        debug_content = debug_file.read_text()

        # Look for skill loading pattern from Skill tool invocation
        skill_match = re.search(
            r'skill is loading.*?(jira-\w+)',
            debug_content,
            re.IGNORECASE
        )
        if skill_match:
            skill_loaded = normalize_skill_name(skill_match.group(1))

    # Method 2: Infer from CLI commands in response or permission denials
    if not skill_loaded:
        skill_loaded = infer_skill_from_response(response_text, permission_denials)

    return RoutingResult(
        skill_loaded=skill_loaded,
        asked_clarification=asked_clarification,
        session_id=session_id,
        duration_ms=duration_ms,
        cost_usd=cost_usd,
    )


def infer_skill_from_response(response: str, permission_denials: list) -> str | None:
    """
    Infer which skill was used based on response content and tool calls.

    This handles cases where Claude responds directly without invoking
    the Skill tool (e.g., using cached knowledge of CLI commands).
    """
    # Combine response and denied command inputs
    all_text = response.lower()
    for denial in permission_denials:
        if isinstance(denial, dict):
            cmd = denial.get("tool_input", {}).get("command", "")
            all_text += " " + cmd.lower()

    # Map CLI patterns to skills
    patterns = {
        "jira-issue": [
            r"jira\s+issue\s+(create|get|update|delete)",
            r"create.*bug",
            r"create.*task",
            r"create.*story",
        ],
        "jira-search": [
            r"jira\s+search",
            r"jql[:\s]",
            r"find\s+.*issues",
        ],
        "jira-lifecycle": [
            r"jira\s+lifecycle",
            r"transition\s+.*to",
            r"assign\s+.*to",
            r"move.*to\s+(done|progress|review)",
        ],
        "jira-agile": [
            r"jira\s+agile",
            r"sprint",
            r"epic",
            r"backlog",
            r"story\s*points?",
        ],
        "jira-collaborate": [
            r"jira\s+collaborate",
            r"add\s+comment",
            r"attach",
            r"watcher",
        ],
        "jira-relationships": [
            r"jira\s+relationships?",
            r"link\s+.*to",
            r"clone\s+",
            r"blocking",
        ],
        "jira-time": [
            r"jira\s+time",
            r"log\s+.*hours?",
            r"worklog",
            r"estimate",
        ],
        "jira-jsm": [
            r"jira\s+jsm",
            r"service\s*desk",
            r"sla",
            r"customer",
        ],
        "jira-bulk": [
            r"jira\s+bulk",
            r"bulk\s+(update|transition|assign)",
        ],
        "jira-dev": [
            r"jira\s+dev",
            r"branch\s*name",
            r"pr\s+description",
            r"commit",
        ],
        "jira-fields": [
            r"jira\s+fields?",
            r"custom\s*field",
            r"field\s*id",
        ],
        "jira-ops": [
            r"jira\s+ops",
            r"cache",
            r"warm.*cache",
        ],
        "jira-admin": [
            r"jira\s+admin",
            r"permission",
            r"project\s+settings?",
        ],
    }

    for skill, skill_patterns in patterns.items():
        for pattern in skill_patterns:
            if re.search(pattern, all_text):
                return skill

    return None


def normalize_skill_name(skill: str) -> str:
    """Normalize skill names to match golden test expectations."""
    # Map internal names to canonical names
    mappings = {
        "jira-issue-management": "jira-issue",
        "jira-issue-crud": "jira-issue",
        # Add more mappings as discovered
    }
    return mappings.get(skill, skill)


# Load tests at module level for parametrization
GOLDEN_TESTS = load_golden_tests()


def get_direct_tests():
    """Get high-certainty direct routing tests."""
    return [t for t in GOLDEN_TESTS if t.get("category") == "direct"]


def get_disambiguation_tests():
    """Get disambiguation tests (should ask for clarification)."""
    return [t for t in GOLDEN_TESTS if t.get("category") == "disambiguation"]


def get_negative_tests():
    """Get negative trigger tests (should NOT route to specific skill)."""
    return [t for t in GOLDEN_TESTS if t.get("category") == "negative"]


def get_context_tests():
    """Get context-dependent tests."""
    return [t for t in GOLDEN_TESTS if t.get("category") == "context"]


def get_workflow_tests():
    """Get multi-skill workflow tests."""
    return [t for t in GOLDEN_TESTS if t.get("category") == "workflow"]


def get_edge_tests():
    """Get edge case tests."""
    return [t for t in GOLDEN_TESTS if t.get("category") == "edge"]


# =============================================================================
# DIRECT ROUTING TESTS
# =============================================================================

@pytest.mark.parametrize(
    "test_case",
    get_direct_tests(),
    ids=lambda t: t["id"]
)
def test_direct_routing(test_case, record_otel):
    """Test high-certainty direct routing."""
    input_text = test_case["input"]
    expected_skill = test_case["expected_skill"]
    test_id = test_case["id"]

    result = run_claude_routing(input_text)

    passed = (result.skill_loaded == expected_skill and not result.asked_clarification)

    # Record to OpenTelemetry
    record_otel(
        test_id=test_id,
        category="direct",
        input_text=input_text,
        expected_skill=expected_skill,
        actual_skill=result.skill_loaded,
        passed=passed,
        duration_ms=result.duration_ms,
        cost_usd=result.cost_usd,
        asked_clarification=result.asked_clarification,
        session_id=result.session_id
    )

    assert result.skill_loaded == expected_skill, (
        f"Expected {expected_skill}, got {result.skill_loaded}\n"
        f"Input: {input_text}\n"
        f"Session: {result.session_id}"
    )

    # Direct routing should NOT ask for clarification
    assert not result.asked_clarification, (
        f"Direct routing should not ask clarification\n"
        f"Input: {input_text}"
    )


# =============================================================================
# DISAMBIGUATION TESTS
# =============================================================================

@pytest.mark.parametrize(
    "test_case",
    get_disambiguation_tests(),
    ids=lambda t: t["id"]
)
def test_disambiguation(test_case, record_otel):
    """Test that ambiguous inputs ask for clarification."""
    input_text = test_case["input"]
    expected_options = test_case.get("disambiguation_options", [])
    test_id = test_case["id"]

    result = run_claude_routing(input_text)

    passed = result.asked_clarification

    # Record to OpenTelemetry
    record_otel(
        test_id=test_id,
        category="disambiguation",
        input_text=input_text,
        expected_skill="disambiguation",
        actual_skill=result.skill_loaded if not result.asked_clarification else "asked",
        passed=passed,
        duration_ms=result.duration_ms,
        cost_usd=result.cost_usd,
        asked_clarification=result.asked_clarification,
        session_id=result.session_id
    )

    # Should ask for clarification
    assert result.asked_clarification, (
        f"Should ask for clarification\n"
        f"Input: {input_text}\n"
        f"Expected options: {expected_options}"
    )


# =============================================================================
# NEGATIVE TRIGGER TESTS
# =============================================================================

@pytest.mark.parametrize(
    "test_case",
    get_negative_tests(),
    ids=lambda t: t["id"]
)
def test_negative_triggers(test_case, record_otel):
    """Test that inputs route to correct skill, NOT to excluded skill."""
    input_text = test_case["input"]
    expected_skill = test_case["expected_skill"]
    not_skill = test_case.get("not_skill")
    test_id = test_case["id"]

    result = run_claude_routing(input_text)

    passed = (result.skill_loaded == expected_skill)
    if not_skill and result.skill_loaded == not_skill:
        passed = False

    # Record to OpenTelemetry
    record_otel(
        test_id=test_id,
        category="negative",
        input_text=input_text,
        expected_skill=expected_skill,
        actual_skill=result.skill_loaded,
        passed=passed,
        duration_ms=result.duration_ms,
        cost_usd=result.cost_usd,
        asked_clarification=result.asked_clarification,
        session_id=result.session_id
    )

    assert result.skill_loaded == expected_skill, (
        f"Expected {expected_skill}, got {result.skill_loaded}\n"
        f"Input: {input_text}"
    )

    if not_skill:
        assert result.skill_loaded != not_skill, (
            f"Should NOT route to {not_skill}\n"
            f"Input: {input_text}"
        )


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

@pytest.mark.parametrize(
    "test_case",
    get_edge_tests(),
    ids=lambda t: t["id"]
)
def test_edge_cases(test_case, record_otel):
    """Test edge cases like empty input, explicit skill mention, etc."""
    input_text = test_case["input"]
    expected_skill = test_case.get("expected_skill")
    expected_action = test_case.get("action")
    test_id = test_case["id"]

    result = run_claude_routing(input_text)

    passed = True
    if expected_skill:
        passed = (result.skill_loaded == expected_skill)
    if expected_action == "ask_for_input":
        passed = (result.skill_loaded is None or result.asked_clarification)

    # Record to OpenTelemetry
    record_otel(
        test_id=test_id,
        category="edge",
        input_text=input_text,
        expected_skill=expected_skill or expected_action or "none",
        actual_skill=result.skill_loaded,
        passed=passed,
        duration_ms=result.duration_ms,
        cost_usd=result.cost_usd,
        asked_clarification=result.asked_clarification,
        session_id=result.session_id
    )

    if expected_skill:
        assert result.skill_loaded == expected_skill, (
            f"Expected {expected_skill}, got {result.skill_loaded}\n"
            f"Input: '{input_text}'"
        )

    if expected_action == "ask_for_input":
        # Empty input should prompt for input
        assert result.skill_loaded is None or result.asked_clarification


# =============================================================================
# WORKFLOW TESTS (informational - multi-skill sequences)
# =============================================================================

@pytest.mark.parametrize(
    "test_case",
    get_workflow_tests(),
    ids=lambda t: t["id"]
)
def test_workflows(test_case, record_otel):
    """
    Test multi-skill workflow routing.

    These tests verify the FIRST skill in the workflow is triggered.
    Full workflow validation requires stateful testing.
    """
    input_text = test_case["input"]
    workflow = test_case.get("workflow", [])
    test_id = test_case["id"]

    if not workflow:
        pytest.skip("No workflow defined")

    # Check first skill in workflow is loaded
    first_skill = workflow[0].get("skill")

    result = run_claude_routing(input_text)

    passed = (result.skill_loaded == first_skill or result.asked_clarification)

    # Record to OpenTelemetry
    record_otel(
        test_id=test_id,
        category="workflow",
        input_text=input_text,
        expected_skill=first_skill,
        actual_skill=result.skill_loaded,
        passed=passed,
        duration_ms=result.duration_ms,
        cost_usd=result.cost_usd,
        asked_clarification=result.asked_clarification,
        session_id=result.session_id
    )

    # Workflow tests are informational - first skill should load
    # but we accept clarification for complex multi-skill requests
    assert result.skill_loaded == first_skill or result.asked_clarification, (
        f"Expected {first_skill} or clarification\n"
        f"Got: {result.skill_loaded}\n"
        f"Input: {input_text}"
    )


# =============================================================================
# CONTEXT TESTS (require session state - marked as expected failures)
# =============================================================================

@pytest.mark.skip(reason="Context tests require multi-turn sessions")
@pytest.mark.parametrize(
    "test_case",
    get_context_tests(),
    ids=lambda t: t["id"]
)
def test_context_dependent(test_case):
    """
    Test context-dependent routing.

    These tests require multi-turn sessions and are not yet automated.
    They should be run manually or with a session-aware test harness.
    """
    pytest.skip("Context tests require multi-turn sessions")


# =============================================================================
# SUMMARY REPORT
# =============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print routing test summary."""
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    skipped = len(terminalreporter.stats.get('skipped', []))

    print("\n" + "=" * 60)
    print("ROUTING TEST SUMMARY")
    print("=" * 60)
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total:   {passed + failed + skipped}")
    if passed + failed > 0:
        accuracy = passed / (passed + failed) * 100
        print(f"Accuracy: {accuracy:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
