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

# Import model config from conftest
from conftest import get_test_model

# Path to the golden test set
GOLDEN_FILE = TESTS_DIR / "routing_golden.yaml"
DEBUG_DIR = Path.home() / ".claude" / "debug"


class CommandMatch(NamedTuple):
    """Result of matching a single expected command pattern."""
    pattern: str
    is_regex: bool
    matched: bool


class ToolUseResult(NamedTuple):
    """Result of tool use accuracy check."""
    total_patterns: int
    matched_patterns: int
    accuracy: float  # 0.0 to 1.0
    matches: list[CommandMatch]


class RoutingResult(NamedTuple):
    """Result of a routing test."""
    skill_loaded: str | None
    asked_clarification: bool
    session_id: str
    duration_ms: int
    cost_usd: float
    # Enhanced fields for tool use accuracy
    response_text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    tool_use: ToolUseResult | None = None


def load_golden_tests() -> list[dict]:
    """Load test cases from routing_golden.yaml."""
    with open(GOLDEN_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("tests", [])


def validate_tool_use(response_text: str, expected_commands: list[dict] | None) -> ToolUseResult:
    """
    Validate that expected command patterns appear in the response.

    Args:
        response_text: The full response text from Claude
        expected_commands: List of expected command patterns, each with:
            - pattern: Literal string to match
            - pattern_regex: Regex pattern to match (alternative to pattern)

    Returns:
        ToolUseResult with accuracy metrics and individual match results
    """
    if not expected_commands:
        return ToolUseResult(
            total_patterns=0,
            matched_patterns=0,
            accuracy=1.0,  # No expectations = 100% by default
            matches=[]
        )

    matches = []
    matched_count = 0

    # Normalize response for matching (handle code blocks)
    response_lower = response_text.lower()

    for cmd in expected_commands:
        if "pattern" in cmd:
            # Literal string match (case-insensitive)
            pattern = cmd["pattern"]
            is_regex = False
            matched = pattern.lower() in response_lower
        elif "pattern_regex" in cmd:
            # Regex match
            pattern = cmd["pattern_regex"]
            is_regex = True
            try:
                matched = bool(re.search(pattern, response_text, re.IGNORECASE))
            except re.error:
                matched = False
        else:
            continue

        matches.append(CommandMatch(
            pattern=pattern,
            is_regex=is_regex,
            matched=matched
        ))

        if matched:
            matched_count += 1

    total = len(matches)
    accuracy = matched_count / total if total > 0 else 1.0

    return ToolUseResult(
        total_patterns=total,
        matched_patterns=matched_count,
        accuracy=accuracy,
        matches=matches
    )


def run_claude_routing(
    input_text: str,
    expected_commands: list[dict] | None = None,
    timeout: int = 60
) -> RoutingResult:
    """
    Run Claude Code with input and extract routing result.

    Args:
        input_text: The user input to test
        expected_commands: Optional list of expected command patterns for tool use validation
        timeout: Maximum seconds to wait

    Returns:
        RoutingResult with skill loaded, response text, and tool use metrics
    """
    if not input_text:
        # Empty input edge case
        return RoutingResult(
            skill_loaded=None,
            asked_clarification=True,
            session_id="",
            duration_ms=0,
            cost_usd=0.0,
            response_text="",
            input_tokens=0,
            output_tokens=0,
            tool_use=None
        )

    # Build command with optional model
    cmd = [
        "claude",
        "--print",
        "--permission-mode", "dontAsk",
        "--output-format", "json",
        "--debug",
    ]

    # Add plugin-dir if specified via environment (for container testing)
    plugin_dir = os.environ.get("CLAUDE_PLUGIN_DIR")
    if plugin_dir:
        cmd.extend(["--plugin-dir", plugin_dir])

    # Add model flag if specified (e.g., --model haiku for faster tests)
    model = get_test_model()
    if model:
        cmd.extend(["--model", model])

    # Run Claude non-interactively
    result = subprocess.run(
        cmd,
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

    # Extract token counts
    input_tokens = output.get("num_turns", 0)  # Fallback if not available
    output_tokens = 0
    if "usage" in output:
        input_tokens = output["usage"].get("input_tokens", 0)
        output_tokens = output["usage"].get("output_tokens", 0)

    # Validate tool use accuracy if expected commands provided
    tool_use_result = validate_tool_use(response_text, expected_commands)

    return RoutingResult(
        skill_loaded=skill_loaded,
        asked_clarification=asked_clarification,
        session_id=session_id,
        duration_ms=duration_ms,
        cost_usd=cost_usd,
        response_text=response_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        tool_use=tool_use_result,
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
    expected_commands = test_case.get("expected_commands")
    test_id = test_case["id"]

    result = run_claude_routing(input_text, expected_commands=expected_commands)

    routing_passed = (result.skill_loaded == expected_skill and not result.asked_clarification)
    tool_use_passed = result.tool_use is None or result.tool_use.accuracy >= 0.5

    # Record to OpenTelemetry with enhanced context
    record_otel(
        test_id=test_id,
        category="direct",
        input_text=input_text,
        expected_skill=expected_skill,
        actual_skill=result.skill_loaded,
        passed=routing_passed and tool_use_passed,
        duration_ms=result.duration_ms,
        cost_usd=result.cost_usd,
        asked_clarification=result.asked_clarification,
        session_id=result.session_id,
        tokens_input=result.input_tokens,
        tokens_output=result.output_tokens,
        response_text=result.response_text,
        tool_use_accuracy=result.tool_use.accuracy if result.tool_use else None,
        tool_use_matched=result.tool_use.matched_patterns if result.tool_use else None,
        tool_use_total=result.tool_use.total_patterns if result.tool_use else None,
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

    # Validate tool use accuracy if expected commands specified
    if expected_commands and result.tool_use:
        # Report unmatched patterns for debugging
        unmatched = [m for m in result.tool_use.matches if not m.matched]
        if unmatched:
            unmatched_patterns = [m.pattern for m in unmatched]
            print(f"  Unmatched command patterns: {unmatched_patterns}")

        # Warn but don't fail if tool use accuracy is low (< 50%)
        if result.tool_use.accuracy < 0.5:
            print(
                f"  WARNING: Low tool use accuracy {result.tool_use.accuracy:.0%} "
                f"({result.tool_use.matched_patterns}/{result.tool_use.total_patterns})"
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
