"""
Tests for jira-as bulk commands.

Tests cover:
- Constants and helper functions
- Implementation functions for all bulk operations
- Formatting functions
- CLI commands
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from jira_assistant_skills.cli.commands.bulk_cmds import (
    # Constants
    CLONE_FIELDS,
    STANDARD_PRIORITIES,
    # Helper functions
    _find_transition,
    _get_issues_to_process,
    _resolve_user_id,
    _validate_priority,
    # Implementation functions
    _bulk_assign_impl,
    _bulk_clone_impl,
    _bulk_delete_impl,
    _bulk_set_priority_impl,
    _bulk_transition_impl,
    _clone_issue,
    # Formatting functions
    _format_bulk_result,
    # Click commands
    bulk,
)
from jira_assistant_skills_lib import JiraError, ValidationError


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_client():
    """Create mock JIRA client."""
    client = MagicMock()
    client.close = MagicMock()
    return client


@pytest.fixture
def sample_issues():
    """Sample issues for bulk testing."""
    return [
        {
            "key": "TEST-1",
            "fields": {
                "summary": "First issue",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "assignee": {"displayName": "John Doe", "accountId": "user123"},
                "issuetype": {"name": "Bug"},
                "subtasks": [],
                "issuelinks": [],
            },
        },
        {
            "key": "TEST-2",
            "fields": {
                "summary": "Second issue",
                "status": {"name": "In Progress"},
                "priority": {"name": "Medium"},
                "assignee": None,
                "issuetype": {"name": "Task"},
                "subtasks": [{"key": "TEST-3"}],
                "issuelinks": [],
            },
        },
        {
            "key": "TEST-4",
            "fields": {
                "summary": "Fourth issue",
                "status": {"name": "Open"},
                "priority": {"name": "Low"},
                "assignee": {"displayName": "Jane Smith"},
                "issuetype": {"name": "Story"},
                "subtasks": [],
                "issuelinks": [
                    {"type": {"name": "Blocks"}, "outwardIssue": {"key": "TEST-5"}}
                ],
            },
        },
    ]


@pytest.fixture
def sample_transitions():
    """Sample transitions for testing."""
    return [
        {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
        {"id": "21", "name": "Done", "to": {"name": "Done"}},
        {"id": "31", "name": "Reopen", "to": {"name": "Open"}},
    ]


# =============================================================================
# Test Constants
# =============================================================================


class TestConstants:
    """Tests for constants."""

    def test_standard_priorities_contains_expected(self):
        """Test STANDARD_PRIORITIES contains expected values."""
        assert "Highest" in STANDARD_PRIORITIES
        assert "High" in STANDARD_PRIORITIES
        assert "Medium" in STANDARD_PRIORITIES
        assert "Low" in STANDARD_PRIORITIES
        assert "Lowest" in STANDARD_PRIORITIES

    def test_clone_fields_contains_expected(self):
        """Test CLONE_FIELDS contains expected fields."""
        assert "summary" in CLONE_FIELDS
        assert "description" in CLONE_FIELDS
        assert "priority" in CLONE_FIELDS
        assert "labels" in CLONE_FIELDS


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_issue_key")
    def test_get_issues_to_process_with_keys(self, mock_validate, mock_client):
        """Test getting issues from issue keys."""
        mock_validate.side_effect = lambda x: x

        result = _get_issues_to_process(
            mock_client,
            issue_keys=["TEST-1", "TEST-2"],
            max_issues=100,
        )

        assert len(result) == 2
        assert result[0]["key"] == "TEST-1"
        assert result[1]["key"] == "TEST-2"

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_get_issues_to_process_with_jql(self, mock_validate, mock_client, sample_issues):
        """Test getting issues from JQL."""
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = _get_issues_to_process(
            mock_client,
            jql="project = TEST",
            max_issues=100,
        )

        assert len(result) == 3

    def test_get_issues_to_process_no_input(self, mock_client):
        """Test getting issues with no input raises error."""
        with pytest.raises(ValidationError, match="Either --issues or --jql"):
            _get_issues_to_process(mock_client)

    def test_find_transition_exact_name(self, sample_transitions):
        """Test finding transition by exact name."""
        result = _find_transition(sample_transitions, "Done")
        assert result["id"] == "21"

    def test_find_transition_by_status(self, sample_transitions):
        """Test finding transition by target status."""
        result = _find_transition(sample_transitions, "In Progress")
        assert result["id"] == "11"

    def test_find_transition_case_insensitive(self, sample_transitions):
        """Test finding transition is case insensitive."""
        result = _find_transition(sample_transitions, "DONE")
        assert result["id"] == "21"

    def test_find_transition_partial_match(self, sample_transitions):
        """Test finding transition with partial match."""
        result = _find_transition(sample_transitions, "Progress")
        assert result["id"] == "11"

    def test_find_transition_not_found(self, sample_transitions):
        """Test finding transition that doesn't exist."""
        result = _find_transition(sample_transitions, "Invalid")
        assert result is None

    def test_resolve_user_id_self(self, mock_client):
        """Test resolving 'self' user."""
        mock_client.get_current_user_id.return_value = "current-user-123"

        result = _resolve_user_id(mock_client, "self")

        assert result == "current-user-123"

    def test_resolve_user_id_email(self, mock_client):
        """Test resolving user by email."""
        mock_client.get.return_value = [
            {"accountId": "user123", "emailAddress": "john@example.com"},
        ]

        result = _resolve_user_id(mock_client, "john@example.com")

        assert result == "user123"

    def test_resolve_user_id_account_id(self, mock_client):
        """Test resolving when account ID is provided."""
        result = _resolve_user_id(mock_client, "user123")
        assert result == "user123"

    def test_resolve_user_id_none(self, mock_client):
        """Test resolving None returns None."""
        result = _resolve_user_id(mock_client, None)
        assert result is None

    def test_validate_priority_valid(self):
        """Test validating valid priority."""
        assert _validate_priority("High") == "High"
        assert _validate_priority("HIGH") == "High"
        assert _validate_priority("high") == "High"

    def test_validate_priority_invalid(self):
        """Test validating invalid priority."""
        with pytest.raises(ValidationError, match="Invalid priority"):
            _validate_priority("Invalid")


# =============================================================================
# Test Implementation Functions
# =============================================================================


class TestBulkTransitionImplementation:
    """Tests for bulk transition implementation."""

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_transition_dry_run(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk transition dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = _bulk_transition_impl(
            jql="project = TEST",
            target_status="Done",
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert result["would_process"] == 3
        assert len(result["issues"]) == 3
        mock_client.transition_issue.assert_not_called()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_transition_execute(self, mock_validate, mock_get_client, mock_client, sample_issues, sample_transitions):
        """Test bulk transition execution."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}
        mock_client.get_transitions.return_value = sample_transitions

        result = _bulk_transition_impl(
            jql="project = TEST",
            target_status="Done",
            dry_run=False,
        )

        assert result["success"] == 3
        assert result["failed"] == 0
        assert mock_client.transition_issue.call_count == 3

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_transition_with_comment(self, mock_validate, mock_get_client, mock_client, sample_issues, sample_transitions):
        """Test bulk transition with comment."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues[:1]}
        mock_client.get_transitions.return_value = sample_transitions

        result = _bulk_transition_impl(
            jql="project = TEST",
            target_status="Done",
            comment="Completed",
            dry_run=False,
        )

        assert result["success"] == 1
        mock_client.add_comment.assert_called_once()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_transition_no_transition_available(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk transition when target not available."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues[:1]}
        mock_client.get_transitions.return_value = []

        result = _bulk_transition_impl(
            jql="project = TEST",
            target_status="InvalidStatus",
            dry_run=False,
        )

        assert result["failed"] == 1
        assert "TEST-1" in result["errors"]

    def test_bulk_transition_no_target_status(self):
        """Test bulk transition requires target status."""
        with pytest.raises(ValidationError, match="Target status is required"):
            _bulk_transition_impl(jql="project = TEST")


class TestBulkAssignImplementation:
    """Tests for bulk assign implementation."""

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_assign_dry_run(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk assign dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}
        mock_client.get_current_user_id.return_value = "self-user-id"

        result = _bulk_assign_impl(
            jql="project = TEST",
            assignee="self",
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert result["would_process"] == 3
        mock_client.assign_issue.assert_not_called()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_assign_execute(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk assign execution."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = _bulk_assign_impl(
            jql="project = TEST",
            assignee="user123",
            dry_run=False,
        )

        assert result["success"] == 3
        assert mock_client.assign_issue.call_count == 3

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_unassign(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk unassign."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues[:1]}

        result = _bulk_assign_impl(
            jql="project = TEST",
            unassign=True,
            dry_run=False,
        )

        assert result["success"] == 1
        mock_client.assign_issue.assert_called_with("TEST-1", None)

    def test_bulk_assign_no_assignee_or_unassign(self):
        """Test bulk assign requires assignee or unassign."""
        with pytest.raises(ValidationError, match="Either --assignee or --unassign"):
            _bulk_assign_impl(jql="project = TEST")


class TestBulkSetPriorityImplementation:
    """Tests for bulk set priority implementation."""

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_set_priority_dry_run(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk set priority dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = _bulk_set_priority_impl(
            jql="project = TEST",
            priority="High",
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert result["would_process"] == 3
        mock_client.update_issue.assert_not_called()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_set_priority_execute(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk set priority execution."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = _bulk_set_priority_impl(
            jql="project = TEST",
            priority="Highest",
            dry_run=False,
        )

        assert result["success"] == 3
        assert mock_client.update_issue.call_count == 3

    def test_bulk_set_priority_no_priority(self):
        """Test bulk set priority requires priority."""
        with pytest.raises(ValidationError, match="Priority is required"):
            _bulk_set_priority_impl(jql="project = TEST")

    def test_bulk_set_priority_invalid_priority(self):
        """Test bulk set priority rejects invalid priority."""
        with pytest.raises(ValidationError, match="Invalid priority"):
            _bulk_set_priority_impl(jql="project = TEST", priority="Invalid")


class TestBulkCloneImplementation:
    """Tests for bulk clone implementation."""

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_clone_dry_run(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk clone dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = _bulk_clone_impl(
            jql="project = TEST",
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert result["would_create"] == 3
        mock_client.create_issue.assert_not_called()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_clone_execute(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk clone execution."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}
        mock_client.create_issue.return_value = {"key": "TEST-NEW", "id": "99"}

        result = _bulk_clone_impl(
            jql="project = TEST",
            dry_run=False,
        )

        assert result["success"] == 3
        assert len(result["created_issues"]) == 3

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_clone_with_prefix(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk clone with prefix."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues[:1]}
        mock_client.create_issue.return_value = {"key": "TEST-NEW", "id": "99"}

        result = _bulk_clone_impl(
            jql="project = TEST",
            prefix="[Clone]",
            dry_run=False,
        )

        call_args = mock_client.create_issue.call_args
        assert "[Clone]" in call_args[0][0]["summary"]

    def test_clone_issue_basic(self, mock_client):
        """Test cloning a single issue."""
        source = {
            "key": "TEST-1",
            "fields": {
                "summary": "Original",
                "project": {"key": "TEST"},
                "issuetype": {"name": "Bug"},
                "priority": {"name": "High"},
                "description": "Description",
                "labels": ["label1"],
            },
        }
        mock_client.create_issue.return_value = {"key": "TEST-NEW", "id": "99"}

        result = _clone_issue(mock_client, source)

        assert result["key"] == "TEST-NEW"
        assert result["source"] == "TEST-1"

    def test_clone_issue_with_subtasks(self, mock_client):
        """Test cloning issue with subtasks."""
        source = {
            "key": "TEST-1",
            "fields": {
                "summary": "Parent",
                "project": {"key": "TEST"},
                "issuetype": {"name": "Story"},
                "subtasks": [{"key": "TEST-2"}],
            },
        }
        mock_client.create_issue.side_effect = [
            {"key": "TEST-NEW-1", "id": "99"},
            {"key": "TEST-NEW-2", "id": "100"},
        ]
        mock_client.get_issue.return_value = {
            "key": "TEST-2",
            "fields": {
                "summary": "Subtask",
                "issuetype": {"name": "Sub-task"},
            },
        }

        result = _clone_issue(mock_client, source, include_subtasks=True)

        assert result["key"] == "TEST-NEW-1"
        assert "TEST-NEW-2" in result["subtasks"]


class TestBulkDeleteImplementation:
    """Tests for bulk delete implementation."""

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_delete_dry_run(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk delete dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = _bulk_delete_impl(
            jql="project = TEST",
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert result["would_delete"] == 3
        mock_client.delete_issue.assert_not_called()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_delete_execute(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk delete execution."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = _bulk_delete_impl(
            jql="project = TEST",
            dry_run=False,
        )

        assert result["success"] == 3
        assert mock_client.delete_issue.call_count == 3

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_bulk_delete_without_subtasks(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test bulk delete without subtasks."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues[:1]}

        result = _bulk_delete_impl(
            jql="project = TEST",
            delete_subtasks=False,
            dry_run=False,
        )

        mock_client.delete_issue.assert_called_with("TEST-1", delete_subtasks=False)


# =============================================================================
# Test Formatting Functions
# =============================================================================


class TestFormattingFunctions:
    """Tests for formatting functions."""

    def test_format_bulk_result_dry_run(self):
        """Test formatting dry run result."""
        result = {
            "dry_run": True,
            "would_process": 5,
            "issues": [
                {"key": "TEST-1", "from": "Open", "to": "Done"},
                {"key": "TEST-2", "from": "Open", "to": "Done"},
            ],
        }

        output = _format_bulk_result(result, "transition")

        assert "[DRY RUN]" in output
        assert "5 issue(s)" in output
        assert "TEST-1" in output
        assert "Use --yes" in output

    def test_format_bulk_result_success(self):
        """Test formatting success result."""
        result = {
            "success": 5,
            "failed": 0,
        }

        output = _format_bulk_result(result, "transition")

        assert "5 succeeded" in output
        assert "0 failed" in output

    def test_format_bulk_result_with_errors(self):
        """Test formatting result with errors."""
        result = {
            "success": 3,
            "failed": 2,
            "errors": {
                "TEST-4": "Transition not available",
                "TEST-5": "Permission denied",
            },
        }

        output = _format_bulk_result(result, "transition")

        assert "3 succeeded" in output
        assert "2 failed" in output
        assert "Errors:" in output
        assert "TEST-4" in output

    def test_format_bulk_result_cancelled(self):
        """Test formatting cancelled result."""
        result = {"cancelled": True}

        output = _format_bulk_result(result, "operation")

        assert "cancelled" in output.lower()

    def test_format_bulk_result_created_issues(self):
        """Test formatting result with created issues."""
        result = {
            "success": 2,
            "failed": 0,
            "created_issues": [
                {"source": "TEST-1", "key": "TEST-NEW-1"},
                {"source": "TEST-2", "key": "TEST-NEW-2"},
            ],
        }

        output = _format_bulk_result(result, "clone")

        assert "Created issues:" in output
        assert "TEST-1 -> TEST-NEW-1" in output


# =============================================================================
# Test CLI Commands
# =============================================================================


class TestBulkTransitionCommand:
    """Tests for bulk transition command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_transition_command_dry_run(self, mock_validate, mock_get_client, runner, mock_client, sample_issues):
        """Test transition command dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = runner.invoke(bulk, [
            "transition",
            "--jql", "project = TEST",
            "--to", "Done",
        ])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_transition_command_execute(self, mock_validate, mock_get_client, runner, mock_client, sample_issues, sample_transitions):
        """Test transition command execution."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}
        mock_client.get_transitions.return_value = sample_transitions

        result = runner.invoke(bulk, [
            "transition",
            "--jql", "project = TEST",
            "--to", "Done",
            "--yes",
        ])

        assert result.exit_code == 0
        assert "succeeded" in result.output

    def test_transition_command_missing_input(self, runner):
        """Test transition command requires JQL or issues."""
        result = runner.invoke(bulk, ["transition", "--to", "Done", "--yes"])

        assert result.exit_code != 0
        assert "required" in result.output.lower()


class TestBulkAssignCommand:
    """Tests for bulk assign command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_assign_command(self, mock_validate, mock_get_client, runner, mock_client, sample_issues):
        """Test assign command."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = runner.invoke(bulk, [
            "assign",
            "--jql", "project = TEST",
            "--assignee", "user123",
            "--yes",
        ])

        assert result.exit_code == 0

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_unassign_command(self, mock_validate, mock_get_client, runner, mock_client, sample_issues):
        """Test unassign command."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = runner.invoke(bulk, [
            "assign",
            "--jql", "project = TEST",
            "--unassign",
            "--yes",
        ])

        assert result.exit_code == 0

    def test_assign_requires_action(self, runner):
        """Test assign requires assignee or unassign."""
        result = runner.invoke(bulk, [
            "assign",
            "--jql", "project = TEST",
            "--yes",
        ])

        assert result.exit_code != 0


class TestBulkSetPriorityCommand:
    """Tests for bulk set-priority command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_set_priority_command(self, mock_validate, mock_get_client, runner, mock_client, sample_issues):
        """Test set-priority command."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = runner.invoke(bulk, [
            "set-priority",
            "--jql", "project = TEST",
            "--priority", "High",
            "--yes",
        ])

        assert result.exit_code == 0


class TestBulkCloneCommand:
    """Tests for bulk clone command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_clone_command(self, mock_validate, mock_get_client, runner, mock_client, sample_issues):
        """Test clone command."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}
        mock_client.create_issue.return_value = {"key": "TEST-NEW", "id": "99"}

        result = runner.invoke(bulk, [
            "clone",
            "--jql", "project = TEST",
            "--yes",
        ])

        assert result.exit_code == 0


class TestBulkDeleteCommand:
    """Tests for bulk delete command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_delete_command_dry_run(self, mock_validate, mock_get_client, runner, mock_client, sample_issues):
        """Test delete command dry run."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = runner.invoke(bulk, [
            "delete",
            "--jql", "project = TEST",
            "--dry-run",
        ])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_delete_command_execute(self, mock_validate, mock_get_client, runner, mock_client, sample_issues):
        """Test delete command execution."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}

        result = runner.invoke(bulk, [
            "delete",
            "--jql", "project = TEST",
            "--yes",
        ])

        assert result.exit_code == 0
        assert "succeeded" in result.output

    def test_delete_shows_warning(self, runner):
        """Test delete shows warning without yes."""
        result = runner.invoke(bulk, [
            "delete",
            "--jql", "project = TEST",
        ])

        assert "WARNING" in result.output


# =============================================================================
# Test Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    def test_jira_error_handling(self, mock_get_client, runner):
        """Test JiraError is handled properly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search_issues.side_effect = JiraError("API Error")

        result = runner.invoke(bulk, [
            "transition",
            "--jql", "project = TEST",
            "--to", "Done",
            "--yes",
        ])

        assert result.exit_code == 1

    @patch("jira_assistant_skills.cli.commands.bulk_cmds.get_jira_client")
    @patch("jira_assistant_skills.cli.commands.bulk_cmds.validate_jql")
    def test_partial_failure(self, mock_validate, mock_get_client, mock_client, sample_issues):
        """Test partial failures in bulk operation."""
        mock_get_client.return_value = mock_client
        mock_validate.return_value = "project = TEST"
        mock_client.search_issues.return_value = {"issues": sample_issues}
        mock_client.get_transitions.side_effect = [
            [{"id": "21", "name": "Done", "to": {"name": "Done"}}],
            JiraError("Failed"),
            [{"id": "21", "name": "Done", "to": {"name": "Done"}}],
        ]

        result = _bulk_transition_impl(
            jql="project = TEST",
            target_status="Done",
            dry_run=False,
        )

        assert result["success"] == 2
        assert result["failed"] == 1
        assert "TEST-2" in result["errors"]
