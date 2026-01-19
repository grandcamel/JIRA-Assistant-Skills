#!/usr/bin/env python3
"""
Sandbox validation tests for jira-assistant skill.

Verifies that sandboxed profiles correctly restrict tool access.
Run these tests with specific sandbox profiles to validate restrictions.

Usage:
    # Test read-only profile (should block creates)
    SANDBOX_PROFILE=read-only CLAUDE_ALLOWED_TOOLS="Read Glob Grep WebFetch WebSearch Bash(jira-as issue get:*) Bash(jira-as search:*)" \
        pytest test_sandbox_validation.py -v -k "readonly"

    # Test via run_sandboxed.sh
    ./run_sandboxed.sh --profile read-only --validate

    # Run all validation tests
    pytest test_sandbox_validation.py -v

Requirements:
    - Same as test_routing.py
    - SANDBOX_PROFILE environment variable indicates current profile
    - CLAUDE_ALLOWED_TOOLS environment variable sets restrictions
"""

import json
import os
import subprocess

import pytest

# Mark all tests in this module as 'live' - they require the Claude CLI
pytestmark = pytest.mark.live

# Import shared fixtures from conftest
from conftest import get_test_model


def get_current_profile() -> str:
    """Get the current sandbox profile from environment."""
    return os.environ.get("SANDBOX_PROFILE", "full")


def run_claude_with_prompt(prompt: str, timeout: int = 60) -> dict:
    """
    Run Claude Code with a prompt and return the full output.

    Returns:
        Dict with keys: result, permission_denials, exit_code, stderr
    """
    cmd = [
        "claude",
        "--print",
        "--permission-mode",
        "dontAsk",
        "--output-format",
        "json",
    ]

    # Add plugin-dir if specified
    plugin_dir = os.environ.get("CLAUDE_PLUGIN_DIR")
    if plugin_dir:
        cmd.extend(["--plugin-dir", plugin_dir])

    # Add allowed tools if specified (for sandboxed testing)
    allowed_tools = os.environ.get("CLAUDE_ALLOWED_TOOLS")
    if allowed_tools:
        cmd.extend(["--allowedTools", allowed_tools])

    # Add model if specified
    model = get_test_model()
    if model:
        cmd.extend(["--model", model])

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Parse JSON output
        try:
            output = json.loads(result.stdout)
            return {
                "result": output.get("result", ""),
                "permission_denials": output.get("permission_denials", []),
                "exit_code": result.returncode,
                "stderr": result.stderr,
            }
        except json.JSONDecodeError:
            return {
                "result": result.stdout,
                "permission_denials": [],
                "exit_code": result.returncode,
                "stderr": result.stderr,
            }
    except subprocess.TimeoutExpired:
        return {
            "result": "",
            "permission_denials": [],
            "exit_code": -1,
            "stderr": "Timeout",
        }


def has_permission_denial(denials: list, pattern: str) -> bool:
    """
    Check if any permission denial matches the given pattern.

    Args:
        denials: List of permission denial dicts from Claude output
        pattern: String to search for in denied commands

    Returns:
        True if pattern found in any denied command
    """
    pattern_lower = pattern.lower()
    for denial in denials:
        if isinstance(denial, dict):
            cmd = denial.get("tool_input", {}).get("command", "")
            if pattern_lower in cmd.lower():
                return True
            # Also check tool name
            tool = denial.get("tool", "")
            if pattern_lower in tool.lower():
                return True
    return False


def response_indicates_blocked(response: str) -> bool:
    """Check if response indicates the operation was blocked or not allowed."""
    indicators = [
        "not allowed",
        "cannot",
        "can't",
        "unable to",
        "don't have permission",
        "not permitted",
        "restricted",
        "blocked",
        "denied",
    ]
    response_lower = response.lower()
    return any(ind in response_lower for ind in indicators)


# =============================================================================
# Read-Only Profile Tests
# =============================================================================


@pytest.mark.skipif(
    get_current_profile() not in ("read-only", "full"),
    reason="Test requires read-only or full profile",
)
class TestReadOnlyProfile:
    """Tests for read-only sandbox profile."""

    def test_readonly_allows_get(self):
        """Read-only profile should allow viewing issues."""
        output = run_claude_with_prompt("show me details of issue TES-1")

        # Should attempt jira-as issue get (or similar read operation)
        # In read-only, this should be allowed
        assert not response_indicates_blocked(output["result"]), (
            "Read operation should be allowed in read-only profile"
        )

    def test_readonly_allows_search(self):
        """Read-only profile should allow search operations."""
        output = run_claude_with_prompt("search for open bugs in TES project")

        # Search should be allowed
        assert not response_indicates_blocked(output["result"]), (
            "Search operation should be allowed in read-only profile"
        )

    @pytest.mark.skipif(
        get_current_profile() != "read-only",
        reason="Only run denial tests in read-only profile",
    )
    def test_readonly_denies_create(self):
        """Read-only profile should deny create operations."""
        output = run_claude_with_prompt("create a new bug in TES: Test sandbox")

        # Should either have permission denial or response indicating blocked
        blocked = (
            has_permission_denial(output["permission_denials"], "create")
            or has_permission_denial(output["permission_denials"], "issue")
            or response_indicates_blocked(output["result"])
        )

        assert blocked, (
            f"Create operation should be blocked in read-only profile. "
            f"Response: {output['result'][:200]}"
        )

    @pytest.mark.skipif(
        get_current_profile() != "read-only",
        reason="Only run denial tests in read-only profile",
    )
    def test_readonly_denies_update(self):
        """Read-only profile should deny update operations."""
        output = run_claude_with_prompt("update TES-1 priority to High")

        blocked = has_permission_denial(
            output["permission_denials"], "update"
        ) or response_indicates_blocked(output["result"])

        assert blocked, (
            f"Update operation should be blocked in read-only profile. "
            f"Response: {output['result'][:200]}"
        )

    @pytest.mark.skipif(
        get_current_profile() != "read-only",
        reason="Only run denial tests in read-only profile",
    )
    def test_readonly_denies_delete(self):
        """Read-only profile should deny delete operations."""
        output = run_claude_with_prompt("delete issue TES-1")

        blocked = has_permission_denial(
            output["permission_denials"], "delete"
        ) or response_indicates_blocked(output["result"])

        assert blocked, (
            f"Delete operation should be blocked in read-only profile. "
            f"Response: {output['result'][:200]}"
        )


# =============================================================================
# Search-Only Profile Tests
# =============================================================================


@pytest.mark.skipif(
    get_current_profile() not in ("search-only", "full"),
    reason="Test requires search-only or full profile",
)
class TestSearchOnlyProfile:
    """Tests for search-only sandbox profile."""

    def test_searchonly_allows_search(self):
        """Search-only profile should allow JQL searches."""
        output = run_claude_with_prompt("find all bugs with priority = High")

        # Search should work
        assert not response_indicates_blocked(output["result"]), (
            "Search operation should be allowed in search-only profile"
        )

    @pytest.mark.skipif(
        get_current_profile() != "search-only",
        reason="Only run denial tests in search-only profile",
    )
    def test_searchonly_denies_issue_get(self):
        """Search-only profile should deny individual issue retrieval."""
        output = run_claude_with_prompt("show me issue TES-1")

        blocked = (
            has_permission_denial(output["permission_denials"], "issue get")
            or has_permission_denial(output["permission_denials"], "issue")
            or response_indicates_blocked(output["result"])
        )

        assert blocked, (
            f"Issue get should be blocked in search-only profile. "
            f"Response: {output['result'][:200]}"
        )

    @pytest.mark.skipif(
        get_current_profile() != "search-only",
        reason="Only run denial tests in search-only profile",
    )
    def test_searchonly_denies_create(self):
        """Search-only profile should deny create operations."""
        output = run_claude_with_prompt("create a bug: Test sandbox")

        blocked = has_permission_denial(
            output["permission_denials"], "create"
        ) or response_indicates_blocked(output["result"])

        assert blocked, (
            f"Create should be blocked in search-only profile. "
            f"Response: {output['result'][:200]}"
        )


# =============================================================================
# Issue-Only Profile Tests
# =============================================================================


@pytest.mark.skipif(
    get_current_profile() not in ("issue-only", "full"),
    reason="Test requires issue-only or full profile",
)
class TestIssueOnlyProfile:
    """Tests for issue-only sandbox profile."""

    def test_issueonly_allows_issue_operations(self):
        """Issue-only profile should allow issue CRUD."""
        output = run_claude_with_prompt("show me details of TES-1")

        # Issue operations should work
        assert not response_indicates_blocked(output["result"]), (
            "Issue operations should be allowed in issue-only profile"
        )

    @pytest.mark.skipif(
        get_current_profile() != "issue-only",
        reason="Only run denial tests in issue-only profile",
    )
    def test_issueonly_denies_search(self):
        """Issue-only profile should deny JQL search operations."""
        output = run_claude_with_prompt("run JQL: project = TES AND type = Bug")

        blocked = has_permission_denial(
            output["permission_denials"], "search"
        ) or response_indicates_blocked(output["result"])

        assert blocked, (
            f"JQL search should be blocked in issue-only profile. "
            f"Response: {output['result'][:200]}"
        )


# =============================================================================
# Full Profile Tests (Baseline)
# =============================================================================


@pytest.mark.skipif(
    get_current_profile() != "full", reason="Test requires full profile"
)
class TestFullProfile:
    """Tests for full (unrestricted) sandbox profile."""

    def test_full_allows_all_operations(self):
        """Full profile should allow all operations."""
        # Just verify we can run without restrictions
        output = run_claude_with_prompt("what JIRA operations can you help with?")

        # Should not be blocked
        assert not response_indicates_blocked(output["result"]), (
            "Full profile should not block any operations"
        )

    def test_full_no_permission_denials(self):
        """Full profile should not have permission denials."""
        output = run_claude_with_prompt("list available JIRA skills")

        # No denials expected
        assert len(output["permission_denials"]) == 0, (
            f"Full profile should not have denials: {output['permission_denials']}"
        )


# =============================================================================
# Profile Detection Tests
# =============================================================================


class TestProfileDetection:
    """Tests that profile is correctly detected and applied."""

    def test_profile_environment_set(self):
        """Verify SANDBOX_PROFILE environment variable is set."""
        profile = get_current_profile()
        # In container tests, this should be set
        # Locally, defaults to "full"
        assert profile in ("read-only", "search-only", "issue-only", "full"), (
            f"Invalid profile: {profile}"
        )

    def test_allowed_tools_matches_profile(self):
        """Verify CLAUDE_ALLOWED_TOOLS matches the profile expectations."""
        profile = get_current_profile()
        allowed_tools = os.environ.get("CLAUDE_ALLOWED_TOOLS", "")

        if profile == "full":
            # Full profile has no restrictions (empty or not set)
            assert allowed_tools == "", "Full profile should have no tool restrictions"
        elif profile == "read-only":
            # Should include Read, Glob, Grep, and read-only jira commands
            assert "Read" in allowed_tools or allowed_tools == "", (
                "Read-only profile should allow Read tool"
            )
            assert (
                "jira-as issue get" in allowed_tools
                or "Bash(jira-as issue get" in allowed_tools
            ), "Read-only profile should allow jira-as issue get"
        elif profile == "search-only":
            # Should only allow search
            assert (
                "jira-as search" in allowed_tools
                or "Bash(jira-as search" in allowed_tools
            ), "Search-only profile should allow jira-as search"
        elif profile == "issue-only":
            # Should allow all issue operations
            assert (
                "jira-as issue" in allowed_tools
                or "Bash(jira-as issue" in allowed_tools
            ), "Issue-only profile should allow jira-as issue"
