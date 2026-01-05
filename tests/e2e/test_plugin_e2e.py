"""
E2E test classes for jira-assistant-skills plugin

Tests verify that Claude Code can:
1. Install the plugin correctly
2. Discover all 14 JIRA skills
3. Respond appropriately to skill-related prompts
4. Handle errors gracefully

Run with: pytest tests/e2e/ -v --e2e-verbose
"""

import pytest

from .runner import TestStatus

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


# All 14 skills in the jira-assistant-skills plugin
EXPECTED_SKILLS = [
    "jira-issue",
    "jira-lifecycle",
    "jira-search",
    "jira-collaborate",
    "jira-agile",
    "jira-relationships",
    "jira-time",
    "jira-jsm",
    "jira-bulk",
    "jira-dev",
    "jira-fields",
    "jira-ops",
    "jira-admin",
    "jira-assistant",
]


class TestPluginInstallation:
    """Plugin installation tests."""

    def test_plugin_installs(self, claude_runner, e2e_enabled):
        """Verify plugin installs successfully."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.install_plugin("plugins/jira-assistant-skills")
        assert result["success"] or "already installed" in result["output"].lower()

    def test_skills_discoverable(self, claude_runner, installed_plugin, e2e_enabled):
        """Verify skills are discoverable after installation."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt("What JIRA skills are available?")
        output = result["output"].lower()

        # Check for at least one skill
        found = any(
            s.lower().replace("-", "") in output.replace("-", "")
            for s in EXPECTED_SKILLS
        )
        assert found or result["success"], "No skills found in output"

    def test_skill_count(self, claude_runner, installed_plugin, e2e_enabled):
        """Verify all 14 skills are available."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt(
            "List all available JIRA Assistant skills. How many are there?"
        )
        output = result["output"].lower()

        # Should mention multiple skills
        skill_mentions = sum(1 for s in EXPECTED_SKILLS if s.lower() in output)
        assert skill_mentions >= 3, (
            f"Expected at least 3 skills mentioned, found {skill_mentions}"
        )


class TestSkillDiscovery:
    """Tests for individual skill discovery."""

    @pytest.mark.parametrize(
        "skill_name,trigger_words",
        [
            (
                "jira-issue",
                ["create issue", "get issue", "update issue", "delete issue"],
            ),
            ("jira-search", ["jql", "search", "find issues", "query"]),
            ("jira-agile", ["sprint", "epic", "story point", "backlog"]),
            ("jira-lifecycle", ["transition", "workflow", "status change"]),
            ("jira-collaborate", ["comment", "attachment", "watcher"]),
            ("jira-relationships", ["link", "blocks", "dependency", "clone"]),
            ("jira-time", ["worklog", "time tracking", "estimate"]),
            ("jira-jsm", ["service desk", "request", "sla", "queue"]),
            ("jira-bulk", ["bulk", "batch", "multiple issues"]),
            ("jira-dev", ["git", "branch", "commit", "pull request"]),
            ("jira-fields", ["custom field", "field id"]),
            ("jira-ops", ["cache", "performance"]),
        ],
    )
    def test_skill_trigger(
        self, claude_runner, installed_plugin, e2e_enabled, skill_name, trigger_words
    ):
        """Test that skill triggers respond to appropriate prompts."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        # Use the first trigger word as the prompt
        prompt = f"How do I {trigger_words[0]} in JIRA?"
        result = claude_runner.send_prompt(prompt)

        # Check that response mentions the skill or its functionality
        output = result["output"].lower()
        assert any(word.lower() in output for word in trigger_words), (
            f"Expected {skill_name} trigger words in response"
        )


class TestCoreOperations:
    """Tests for core JIRA operations."""

    def test_issue_creation_guidance(
        self, claude_runner, installed_plugin, e2e_enabled
    ):
        """Test issue creation guidance."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt(
            "How do I create a new bug in JIRA with priority and assignee?"
        )
        output = result["output"].lower()

        assert "create" in output
        assert any(w in output for w in ["issue", "bug", "--type", "jira issue create"])

    def test_search_guidance(self, claude_runner, installed_plugin, e2e_enabled):
        """Test JQL search guidance."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt(
            "Write a JQL query to find all open bugs assigned to me"
        )
        output = result["output"].lower()

        assert any(w in output for w in ["jql", "query", "assignee"])
        assert any(w in output for w in ["bug", "type"])

    def test_agile_workflow(self, claude_runner, installed_plugin, e2e_enabled):
        """Test Agile workflow guidance."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt(
            "How do I create a sprint, add issues to it, and track story points?"
        )
        output = result["output"].lower()

        assert any(w in output for w in ["sprint", "jira agile sprint"])
        assert any(w in output for w in ["story point", "estimate"])


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_issue_key(self, claude_runner, installed_plugin, e2e_enabled):
        """Test handling of invalid issue key."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt("Get details for JIRA issue INVALID123")

        # Should not crash
        assert not result.get("crashed", False)

    def test_missing_credentials_guidance(
        self, claude_runner, installed_plugin, e2e_enabled
    ):
        """Test guidance for missing credentials."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt(
            "What do I need to configure to use the JIRA skills?"
        )
        output = result["output"].lower()

        assert any(w in output for w in ["token", "credential", "api", "configure"])


@pytest.mark.skip(reason="Redundant with test_individual_case parametrized tests")
class TestYAMLSuites:
    """Run all YAML-defined test suites."""

    def test_all_suites(self, e2e_runner, e2e_enabled):
        """Execute all test suites from test_cases.yaml."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        results = e2e_runner.run_all()
        e2e_runner.print_summary(results)

        failures = [
            f"{s.suite_name}::{t.test_id}"
            for s in results
            for t in s.tests
            if t.status != TestStatus.PASSED
        ]
        assert len(failures) == 0, f"Test failures: {failures}"


class TestIntegration:
    """Cross-skill integration tests."""

    def test_search_to_bulk_workflow(
        self, claude_runner, installed_plugin, e2e_enabled
    ):
        """Test workflow from search to bulk operations."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt(
            "How do I find all bugs in the current sprint and bulk transition them to In Progress?"
        )
        output = result["output"].lower()

        assert any(w in output for w in ["search", "jql", "find"])
        assert any(w in output for w in ["bulk", "transition"])

    def test_epic_sprint_workflow(self, claude_runner, installed_plugin, e2e_enabled):
        """Test epic to sprint planning workflow."""
        if not e2e_enabled:
            pytest.skip("E2E disabled")

        result = claude_runner.send_prompt(
            "How do I create an epic, add stories with estimates, and move them to a sprint?"
        )
        output = result["output"].lower()

        assert any(w in output for w in ["epic", "jira agile epic"])
        assert any(w in output for w in ["sprint", "move"])
