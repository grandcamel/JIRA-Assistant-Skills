"""
Unit tests for issue CLI commands.

Tests cover:
- get_issue: Retrieving issue details, fields, links, time tracking
- create_issue: Creating issues with various options
- update_issue: Updating issue fields
- delete_issue: Deleting issues with/without confirmation
"""

import json
from copy import deepcopy
from unittest.mock import patch

import pytest

from jira_assistant_skills.cli.commands.issue_cmds import (
    _create_issue_impl,
    _delete_issue_impl,
    _get_issue_impl,
    _update_issue_impl,
    issue,
)
from jira_assistant_skills_lib import format_issue, format_json


# =============================================================================
# Tests for _get_issue_impl
# =============================================================================


@pytest.mark.unit
class TestGetIssueImpl:
    """Tests for the _get_issue_impl implementation function."""

    def test_get_issue_success(self, mock_jira_client, sample_issue):
        """Test retrieving an issue successfully."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_issue_impl(issue_key="PROJ-123")

        mock_jira_client.get_issue.assert_called_once_with("PROJ-123", fields=None)
        assert result["key"] == "PROJ-123"
        assert result["fields"]["summary"] == "Test Issue Summary"

    def test_get_issue_normalizes_key(self, mock_jira_client, sample_issue):
        """Test that issue key is normalized to uppercase."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_issue_impl(issue_key="proj-123")

        mock_jira_client.get_issue.assert_called_once_with("PROJ-123", fields=None)
        assert result["key"] == "PROJ-123"

    def test_get_issue_with_specific_fields(
        self, mock_jira_client, sample_issue_minimal
    ):
        """Test retrieving an issue with specific fields."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_minimal)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_issue_impl(issue_key="PROJ-124", fields=["summary", "status"])

        mock_jira_client.get_issue.assert_called_once_with(
            "PROJ-124", fields=["summary", "status"]
        )
        assert result["key"] == "PROJ-124"

    def test_get_issue_with_links(self, mock_jira_client, sample_issue_with_links):
        """Test retrieving an issue with issue links."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue_with_links)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_issue_impl(issue_key="PROJ-126")

        assert "issuelinks" in result["fields"]
        assert len(result["fields"]["issuelinks"]) == 2

    def test_get_issue_with_time_tracking(
        self, mock_jira_client, sample_issue_with_time_tracking
    ):
        """Test retrieving an issue with time tracking information."""
        mock_jira_client.get_issue.return_value = deepcopy(
            sample_issue_with_time_tracking
        )

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _get_issue_impl(issue_key="PROJ-125")

        tt = result["fields"]["timetracking"]
        assert tt["originalEstimate"] == "2d"
        assert tt["remainingEstimate"] == "1d 4h"
        assert tt["timeSpent"] == "4h"

    def test_get_issue_not_found(self, mock_jira_client):
        """Test handling issue not found error."""
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_issue.side_effect = NotFoundError("Issue", "PROJ-999")

        with (
            patch(
                "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
                return_value=mock_jira_client,
            ),
            pytest.raises(NotFoundError) as exc_info,
        ):
            _get_issue_impl(issue_key="PROJ-999")

        assert "not found" in str(exc_info.value).lower()

    def test_get_issue_closes_client(self, mock_jira_client, sample_issue):
        """Test that client is closed after operation."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _get_issue_impl(issue_key="PROJ-123")

        mock_jira_client.close.assert_called_once()


# =============================================================================
# Tests for _create_issue_impl
# =============================================================================


@pytest.mark.unit
class TestCreateIssueImpl:
    """Tests for the _create_issue_impl implementation function."""

    def test_create_issue_basic(self, mock_jira_client, sample_created_issue):
        """Test creating a basic issue."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.issue_cmds.has_project_context",
            return_value=False,
        ):
            result = _create_issue_impl(
                project="PROJ",
                issue_type="Bug",
                summary="Test bug",
            )

        assert result["key"] == "PROJ-130"
        mock_jira_client.create_issue.assert_called_once()

    def test_create_issue_with_description(self, mock_jira_client, sample_created_issue):
        """Test creating an issue with description."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.issue_cmds.has_project_context",
            return_value=False,
        ):
            result = _create_issue_impl(
                project="PROJ",
                issue_type="Bug",
                summary="Test bug",
                description="This is a test description",
            )

        assert result["key"] == "PROJ-130"
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert "description" in call_args

    def test_create_issue_with_labels(self, mock_jira_client, sample_created_issue):
        """Test creating an issue with labels."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.issue_cmds.has_project_context",
            return_value=False,
        ):
            result = _create_issue_impl(
                project="PROJ",
                issue_type="Bug",
                summary="Test bug",
                labels=["urgent", "backend"],
            )

        assert result["key"] == "PROJ-130"
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args["labels"] == ["urgent", "backend"]

    def test_create_issue_closes_client(self, mock_jira_client, sample_created_issue):
        """Test that client is closed after operation."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.issue_cmds.has_project_context",
            return_value=False,
        ):
            _create_issue_impl(
                project="PROJ",
                issue_type="Bug",
                summary="Test bug",
            )

        mock_jira_client.close.assert_called()


# =============================================================================
# Tests for _update_issue_impl
# =============================================================================


@pytest.mark.unit
class TestUpdateIssueImpl:
    """Tests for the _update_issue_impl implementation function."""

    def test_update_issue_summary(self, mock_jira_client):
        """Test updating issue summary."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _update_issue_impl(issue_key="PROJ-123", summary="New summary")

        mock_jira_client.update_issue.assert_called_once()
        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][0] == "PROJ-123"
        assert call_args[0][1]["summary"] == "New summary"

    def test_update_issue_priority(self, mock_jira_client):
        """Test updating issue priority."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _update_issue_impl(issue_key="PROJ-123", priority="High")

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["priority"] == {"name": "High"}

    def test_update_issue_labels(self, mock_jira_client):
        """Test updating issue labels."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _update_issue_impl(issue_key="PROJ-123", labels=["bug", "urgent"])

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]["labels"] == ["bug", "urgent"]

    def test_update_issue_no_fields_raises_error(self, mock_jira_client):
        """Test that updating with no fields raises ValueError."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), pytest.raises(ValueError, match="No fields specified"):
            _update_issue_impl(issue_key="PROJ-123")

    def test_update_issue_closes_client(self, mock_jira_client):
        """Test that client is closed after operation."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _update_issue_impl(issue_key="PROJ-123", summary="New summary")

        mock_jira_client.close.assert_called_once()


# =============================================================================
# Tests for _delete_issue_impl
# =============================================================================


@pytest.mark.unit
class TestDeleteIssueImpl:
    """Tests for the _delete_issue_impl implementation function."""

    def test_delete_issue_force(self, mock_jira_client):
        """Test force deleting an issue."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _delete_issue_impl(issue_key="PROJ-123", force=True)

        mock_jira_client.delete_issue.assert_called_once_with("PROJ-123")
        assert result is None

    def test_delete_issue_no_force_returns_info(self, mock_jira_client, sample_issue):
        """Test deleting without force returns issue info for confirmation."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = _delete_issue_impl(issue_key="PROJ-123", force=False)

        mock_jira_client.delete_issue.assert_not_called()
        assert result is not None
        assert result["key"] == "PROJ-123"
        assert result["summary"] == "Test Issue Summary"

    def test_delete_issue_closes_client(self, mock_jira_client):
        """Test that client is closed after operation."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            _delete_issue_impl(issue_key="PROJ-123", force=True)

        mock_jira_client.close.assert_called_once()


# =============================================================================
# Tests for CLI Commands
# =============================================================================


@pytest.mark.unit
class TestGetIssueCommand:
    """Tests for the get_issue Click command."""

    def test_get_issue_cli_success(self, cli_runner, mock_jira_client, sample_issue):
        """Test CLI get issue command success."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(issue, ["get", "PROJ-123"])

        assert result.exit_code == 0
        assert "PROJ-123" in result.output

    def test_get_issue_cli_json_output(self, cli_runner, mock_jira_client, sample_issue):
        """Test CLI get issue command with JSON output."""
        mock_jira_client.get_issue.return_value = deepcopy(sample_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(issue, ["get", "PROJ-123", "--output", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["key"] == "PROJ-123"


@pytest.mark.unit
class TestCreateIssueCommand:
    """Tests for the create_issue Click command."""

    def test_create_issue_cli_success(
        self, cli_runner, mock_jira_client, sample_created_issue
    ):
        """Test CLI create issue command success."""
        mock_jira_client.create_issue.return_value = deepcopy(sample_created_issue)

        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ), patch(
            "jira_assistant_skills.cli.commands.issue_cmds.has_project_context",
            return_value=False,
        ):
            result = cli_runner.invoke(
                issue,
                [
                    "create",
                    "--project", "PROJ",
                    "--type", "Bug",
                    "--summary", "Test bug",
                ],
            )

        assert result.exit_code == 0
        assert "PROJ-130" in result.output


@pytest.mark.unit
class TestUpdateIssueCommand:
    """Tests for the update_issue Click command."""

    def test_update_issue_cli_success(self, cli_runner, mock_jira_client):
        """Test CLI update issue command success."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                issue,
                ["update", "PROJ-123", "--summary", "Updated summary"],
            )

        assert result.exit_code == 0
        assert "Updated" in result.output


@pytest.mark.unit
class TestDeleteIssueCommand:
    """Tests for the delete_issue Click command."""

    def test_delete_issue_cli_force(self, cli_runner, mock_jira_client):
        """Test CLI delete issue command with force flag."""
        with patch(
            "jira_assistant_skills.cli.commands.issue_cmds.get_jira_client",
            return_value=mock_jira_client,
        ):
            result = cli_runner.invoke(
                issue,
                ["delete", "PROJ-123", "--force"],
            )

        assert result.exit_code == 0
        assert "Deleted" in result.output
        mock_jira_client.delete_issue.assert_called_once()
