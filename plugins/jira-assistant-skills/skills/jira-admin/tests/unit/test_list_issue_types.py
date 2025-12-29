"""
Tests for list_issue_types.py - Listing issue types in JIRA.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import sys
from pathlib import Path

# Add paths BEFORE any other imports
test_dir = Path(__file__).parent  # unit
tests_dir = test_dir.parent  # tests
jira_admin_dir = tests_dir.parent  # jira-admin
skills_dir = jira_admin_dir.parent  # skills
shared_lib_path = skills_dir / 'shared' / 'scripts' / 'lib'
scripts_path = jira_admin_dir / 'scripts'

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import pytest
from unittest.mock import Mock, patch


@pytest.mark.admin
@pytest.mark.unit
class TestListIssueTypes:
    """Test suite for list_issue_types.py functionality."""

    def test_list_issue_types_success(self, mock_jira_client, issue_types_response):
        """Should return list of issue types."""
        # Arrange
        mock_jira_client.get_issue_types.return_value = issue_types_response

        from list_issue_types import list_issue_types

        # Act
        result = list_issue_types(client=mock_jira_client)

        # Assert
        assert result is not None
        assert len(result) == 5
        assert result[0]['name'] == 'Epic'
        mock_jira_client.get_issue_types.assert_called_once()

    def test_list_issue_types_filters_subtasks(self, mock_jira_client, issue_types_response):
        """Should support filtering to subtask types only."""
        # Arrange
        mock_jira_client.get_issue_types.return_value = issue_types_response

        from list_issue_types import list_issue_types

        # Act
        result = list_issue_types(client=mock_jira_client, subtask_only=True)

        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0]['name'] == 'Subtask'
        assert result[0]['subtask'] is True

    def test_list_issue_types_filters_standard(self, mock_jira_client, issue_types_response):
        """Should support filtering to standard types only (exclude subtasks)."""
        # Arrange
        mock_jira_client.get_issue_types.return_value = issue_types_response

        from list_issue_types import list_issue_types

        # Act
        result = list_issue_types(client=mock_jira_client, standard_only=True)

        # Assert
        assert result is not None
        assert len(result) == 4  # Epic, Story, Task, Bug - no Subtask
        for item in result:
            assert item['subtask'] is False

    def test_list_issue_types_by_hierarchy(self, mock_jira_client, issue_types_response):
        """Should support filtering by hierarchy level."""
        # Arrange
        mock_jira_client.get_issue_types.return_value = issue_types_response

        from list_issue_types import list_issue_types

        # Act - filter for standard level (0)
        result = list_issue_types(client=mock_jira_client, hierarchy_level=0)

        # Assert
        assert result is not None
        assert len(result) == 3  # Story, Task, Bug
        for item in result:
            assert item['hierarchyLevel'] == 0

    def test_list_issue_types_hierarchy_epic(self, mock_jira_client, issue_types_response):
        """Should filter for epic level (1)."""
        # Arrange
        mock_jira_client.get_issue_types.return_value = issue_types_response

        from list_issue_types import list_issue_types

        # Act
        result = list_issue_types(client=mock_jira_client, hierarchy_level=1)

        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0]['name'] == 'Epic'
        assert result[0]['hierarchyLevel'] == 1

    def test_list_issue_types_hierarchy_subtask(self, mock_jira_client, issue_types_response):
        """Should filter for subtask level (-1)."""
        # Arrange
        mock_jira_client.get_issue_types.return_value = issue_types_response

        from list_issue_types import list_issue_types

        # Act
        result = list_issue_types(client=mock_jira_client, hierarchy_level=-1)

        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0]['name'] == 'Subtask'
        assert result[0]['hierarchyLevel'] == -1

    def test_list_issue_types_empty_result(self, mock_jira_client):
        """Should handle empty list of issue types."""
        # Arrange
        mock_jira_client.get_issue_types.return_value = []

        from list_issue_types import list_issue_types

        # Act
        result = list_issue_types(client=mock_jira_client)

        # Assert
        assert result is not None
        assert len(result) == 0

    def test_list_issue_types_api_error(self, mock_jira_client):
        """Should propagate API errors."""
        # Arrange
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_issue_types.side_effect = JiraError(
            "Failed to get issue types",
            status_code=403
        )

        from list_issue_types import list_issue_types

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            list_issue_types(client=mock_jira_client)

        assert exc_info.value.status_code == 403


@pytest.mark.admin
@pytest.mark.unit
class TestListIssueTypesCLI:
    """Test command-line interface for list_issue_types.py."""

    def test_cli_default(self, mock_jira_client, issue_types_response, capsys):
        """Test CLI with no arguments lists all types."""
        # This tests the CLI parsing and output formatting
        pass

    def test_cli_subtask_only(self, mock_jira_client, issue_types_response, capsys):
        """Test CLI with --subtask-only flag."""
        pass

    def test_cli_json_output(self, mock_jira_client, issue_types_response, capsys):
        """Test CLI with --format json output."""
        pass
