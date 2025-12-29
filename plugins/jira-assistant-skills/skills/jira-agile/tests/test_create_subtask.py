"""
Tests for create_subtask.py - Creating subtask issues in JIRA.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import sys
from pathlib import Path

# Add paths BEFORE any other imports
test_dir = Path(__file__).parent  # tests
jira_agile_dir = test_dir.parent  # jira-agile
skills_dir = jira_agile_dir.parent  # skills
shared_lib_path = skills_dir / 'shared' / 'scripts' / 'lib'
scripts_path = jira_agile_dir / 'scripts'

sys.path.insert(0, str(shared_lib_path))
sys.path.insert(0, str(scripts_path))

import pytest
from unittest.mock import Mock, patch


@pytest.mark.agile
@pytest.mark.unit
class TestCreateSubtask:
    """Test suite for create_subtask.py functionality."""

    def test_create_subtask_minimal(self, mock_jira_client, sample_issue_response, sample_subtask_response):
        """Test creating subtask with parent and summary."""
        # Arrange
        from create_subtask import create_subtask

        # Mock parent issue fetch
        mock_jira_client.get_issue.return_value = sample_issue_response
        mock_jira_client.create_issue.return_value = sample_subtask_response

        # Act
        result = create_subtask(
            parent_key="PROJ-101",
            summary="Implement login API",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['key'] == "PROJ-102"
        assert result['fields']['issuetype']['name'] == "Sub-task"

        # Verify API call included parent
        mock_jira_client.create_issue.assert_called_once()
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args['parent'] == {'key': 'PROJ-101'}
        assert call_args['issuetype'] == {'name': 'Sub-task'}
        assert call_args['summary'] == "Implement login API"

    def test_create_subtask_with_description(self, mock_jira_client, sample_issue_response, sample_subtask_response):
        """Test subtask with markdown description."""
        # Arrange
        from create_subtask import create_subtask

        mock_jira_client.get_issue.return_value = sample_issue_response
        mock_jira_client.create_issue.return_value = sample_subtask_response

        # Act
        result = create_subtask(
            parent_key="PROJ-101",
            summary="Implement login API",
            description="## Implementation\nUse **JWT** tokens",
            client=mock_jira_client
        )

        # Assert
        assert result is not None

        # Verify description was converted to ADF
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert 'description' in call_args
        assert call_args['description']['type'] == 'doc'  # ADF format

    def test_create_subtask_inherits_project(self, mock_jira_client, sample_issue_response, sample_subtask_response):
        """Test subtask inherits project from parent."""
        # Arrange
        from create_subtask import create_subtask

        mock_jira_client.get_issue.return_value = sample_issue_response
        mock_jira_client.create_issue.return_value = sample_subtask_response

        # Act
        result = create_subtask(
            parent_key="PROJ-101",
            summary="Task",
            client=mock_jira_client
        )

        # Assert - should use parent's project
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args['project'] == {'key': 'PROJ'}

    def test_create_subtask_with_assignee(self, mock_jira_client, sample_issue_response, sample_subtask_response):
        """Test assigning subtask (including 'self')."""
        # Arrange
        from create_subtask import create_subtask

        mock_jira_client.get_issue.return_value = sample_issue_response
        mock_jira_client.create_issue.return_value = sample_subtask_response
        mock_jira_client.get_current_user_id.return_value = "557058:current-user"

        # Act
        result = create_subtask(
            parent_key="PROJ-101",
            summary="Task",
            assignee="self",
            client=mock_jira_client
        )

        # Assert
        assert result is not None

        # Verify assignee set to current user
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert call_args['assignee'] == {'accountId': '557058:current-user'}

    def test_create_subtask_with_estimate(self, mock_jira_client, sample_issue_response, sample_subtask_response):
        """Test setting time estimate on subtask."""
        # Arrange
        from create_subtask import create_subtask

        mock_jira_client.get_issue.return_value = sample_issue_response
        mock_jira_client.create_issue.return_value = sample_subtask_response

        # Act
        result = create_subtask(
            parent_key="PROJ-101",
            summary="Task",
            time_estimate="4h",
            client=mock_jira_client
        )

        # Assert
        assert result is not None

        # Verify time estimate set (in seconds: 4h = 14400s)
        call_args = mock_jira_client.create_issue.call_args[0][0]
        assert 'timetracking' in call_args
        assert call_args['timetracking']['originalEstimate'] == "4h"

    def test_create_subtask_invalid_parent(self, mock_jira_client):
        """Test error when parent doesn't exist."""
        # Arrange
        from create_subtask import create_subtask
        from error_handler import JiraError

        # Simulate 404 when fetching parent
        mock_jira_client.get_issue.side_effect = JiraError(
            "Issue does not exist",
            status_code=404
        )

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            create_subtask(
                parent_key="PROJ-999",
                summary="Task",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_create_subtask_parent_not_story(self, mock_jira_client, sample_subtask_response):
        """Test validation that some issue types can't have subtasks."""
        # Arrange
        from create_subtask import create_subtask
        from error_handler import ValidationError

        # Return a subtask as the parent (subtasks can't have subtasks)
        mock_jira_client.get_issue.return_value = sample_subtask_response

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            create_subtask(
                parent_key="PROJ-102",  # This is already a subtask
                summary="Task",
                client=mock_jira_client
            )

        assert "cannot have subtasks" in str(exc_info.value).lower() or "subtask" in str(exc_info.value).lower()


@pytest.mark.agile
@pytest.mark.unit
class TestCreateSubtaskCLI:
    """Test command-line interface for create_subtask.py."""

    def test_cli_main_exists(self):
        """Test CLI main function exists and is callable."""
        from create_subtask import main
        assert callable(main)

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch('sys.argv', ['create_subtask.py', '--help']):
            from create_subtask import main
            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert '--parent' in captured.out or '--summary' in captured.out or 'usage' in captured.out.lower()


@pytest.mark.agile
@pytest.mark.unit
class TestCreateSubtaskErrorHandling:
    """Test API error handling scenarios for create_subtask."""

    def test_authentication_error(self, mock_jira_client, sample_issue_response):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        from create_subtask import create_subtask

        mock_jira_client.get_issue.return_value = sample_issue_response
        mock_jira_client.create_issue.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            create_subtask(
                parent_key="PROJ-101",
                summary="Task",
                client=mock_jira_client
            )

    def test_forbidden_error(self, mock_jira_client, sample_issue_response):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        from create_subtask import create_subtask

        mock_jira_client.get_issue.return_value = sample_issue_response
        mock_jira_client.create_issue.side_effect = PermissionError(
            "Insufficient permissions"
        )

        with pytest.raises(PermissionError):
            create_subtask(
                parent_key="PROJ-101",
                summary="Task",
                client=mock_jira_client
            )

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        from create_subtask import create_subtask

        mock_jira_client.get_issue.side_effect = JiraError(
            "Rate limit exceeded",
            status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            create_subtask(
                parent_key="PROJ-101",
                summary="Task",
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client, sample_issue_response):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        from create_subtask import create_subtask

        mock_jira_client.get_issue.return_value = sample_issue_response
        mock_jira_client.create_issue.side_effect = JiraError(
            "Internal server error",
            status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            create_subtask(
                parent_key="PROJ-101",
                summary="Task",
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 500
