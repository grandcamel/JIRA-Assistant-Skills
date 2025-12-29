"""
Tests for get_issue_type.py - Getting issue type details in JIRA.

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
class TestGetIssueType:
    """Test suite for get_issue_type.py functionality."""

    def test_get_issue_type_success(self, mock_jira_client, epic_response):
        """Should return issue type details."""
        # Arrange
        mock_jira_client.get_issue_type.return_value = epic_response

        from get_issue_type import get_issue_type

        # Act
        result = get_issue_type(issue_type_id="10000", client=mock_jira_client)

        # Assert
        assert result is not None
        assert result['id'] == "10000"
        assert result['name'] == "Epic"
        assert result['hierarchyLevel'] == 1
        mock_jira_client.get_issue_type.assert_called_once_with("10000")

    def test_get_issue_type_not_found(self, mock_jira_client):
        """Should raise NotFoundError for invalid ID."""
        # Arrange
        from jira_assistant_skills_lib import NotFoundError

        mock_jira_client.get_issue_type.side_effect = NotFoundError(
            "Issue type", "10999"
        )

        from get_issue_type import get_issue_type

        # Act & Assert
        with pytest.raises(NotFoundError):
            get_issue_type(issue_type_id="10999", client=mock_jira_client)

    def test_get_issue_type_shows_hierarchy(self, mock_jira_client, epic_response):
        """Should display hierarchy level information."""
        # Arrange
        mock_jira_client.get_issue_type.return_value = epic_response

        from get_issue_type import get_issue_type

        # Act
        result = get_issue_type(issue_type_id="10000", client=mock_jira_client)

        # Assert
        assert 'hierarchyLevel' in result
        assert result['hierarchyLevel'] == 1

    def test_get_issue_type_shows_subtask_flag(self, mock_jira_client, subtask_response):
        """Should show subtask flag correctly."""
        # Arrange
        mock_jira_client.get_issue_type.return_value = subtask_response

        from get_issue_type import get_issue_type

        # Act
        result = get_issue_type(issue_type_id="10004", client=mock_jira_client)

        # Assert
        assert result['subtask'] is True
        assert result['hierarchyLevel'] == -1

    def test_get_issue_type_shows_scope(self, mock_jira_client, project_scoped_issue_type):
        """Should display scope (global vs project-specific)."""
        # Arrange
        mock_jira_client.get_issue_type.return_value = project_scoped_issue_type

        from get_issue_type import get_issue_type

        # Act
        result = get_issue_type(issue_type_id="10100", client=mock_jira_client)

        # Assert
        assert 'scope' in result
        assert result['scope']['type'] == 'PROJECT'
        assert result['scope']['project']['id'] == '10000'

    def test_get_issue_type_with_alternatives(
        self, mock_jira_client, epic_response, alternatives_response
    ):
        """Should show alternative issue types when requested."""
        # Arrange
        mock_jira_client.get_issue_type.return_value = epic_response
        mock_jira_client.get_issue_type_alternatives.return_value = alternatives_response

        from get_issue_type import get_issue_type

        # Act
        result = get_issue_type(
            issue_type_id="10000",
            client=mock_jira_client,
            show_alternatives=True
        )

        # Assert
        assert result is not None
        mock_jira_client.get_issue_type_alternatives.assert_called_once_with("10000")

    def test_get_issue_type_api_error(self, mock_jira_client):
        """Should propagate API errors."""
        # Arrange
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.get_issue_type.side_effect = JiraError(
            "Server error",
            status_code=500
        )

        from get_issue_type import get_issue_type

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            get_issue_type(issue_type_id="10000", client=mock_jira_client)

        assert exc_info.value.status_code == 500


@pytest.mark.admin
@pytest.mark.unit
class TestGetIssueTypeCLI:
    """Test command-line interface for get_issue_type.py."""

    def test_cli_with_id(self, mock_jira_client, epic_response, capsys):
        """Test CLI with issue type ID."""
        pass

    def test_cli_json_output(self, mock_jira_client, epic_response, capsys):
        """Test CLI with --format json output."""
        pass

    def test_cli_show_alternatives(self, mock_jira_client, epic_response, capsys):
        """Test CLI with --show-alternatives flag."""
        pass
