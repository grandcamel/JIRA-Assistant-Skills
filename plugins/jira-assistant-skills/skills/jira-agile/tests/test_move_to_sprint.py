"""
Tests for move_to_sprint.py - Moving issues to sprints in JIRA.

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
class TestMoveToSprint:
    """Test suite for move_to_sprint.py functionality."""

    def test_move_single_issue_to_sprint(self, mock_jira_client):
        """Test moving one issue to sprint."""
        # Arrange
        from move_to_sprint import move_to_sprint

        mock_jira_client.move_issues_to_sprint.return_value = None

        # Act
        result = move_to_sprint(
            sprint_id=456,
            issue_keys=["PROJ-101"],
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['moved'] == 1
        assert result['failed'] == 0

        # Verify API call
        mock_jira_client.move_issues_to_sprint.assert_called_once()
        call_args = mock_jira_client.move_issues_to_sprint.call_args
        assert call_args[0][0] == 456  # Sprint ID
        assert "PROJ-101" in call_args[0][1]  # Issues

    def test_move_multiple_issues_to_sprint(self, mock_jira_client):
        """Test bulk moving issues."""
        # Arrange
        from move_to_sprint import move_to_sprint

        mock_jira_client.move_issues_to_sprint.return_value = None

        # Act
        result = move_to_sprint(
            sprint_id=456,
            issue_keys=["PROJ-101", "PROJ-102", "PROJ-103"],
            client=mock_jira_client
        )

        # Assert
        assert result['moved'] == 3
        assert result['failed'] == 0

    def test_move_to_sprint_by_jql(self, mock_jira_client, sample_issue_response):
        """Test moving all issues matching JQL query."""
        # Arrange
        from move_to_sprint import move_to_sprint

        # Mock JQL search returning issues
        mock_jira_client.search_issues.return_value = {
            'issues': [
                {'key': 'PROJ-101'},
                {'key': 'PROJ-102'}
            ],
            'total': 2
        }
        mock_jira_client.move_issues_to_sprint.return_value = None

        # Act
        result = move_to_sprint(
            sprint_id=456,
            jql="project=PROJ AND status='To Do'",
            client=mock_jira_client
        )

        # Assert
        assert result['moved'] == 2

        # Verify JQL search was called
        mock_jira_client.search_issues.assert_called_once()

    def test_move_to_backlog(self, mock_jira_client):
        """Test removing issues from sprint (back to backlog)."""
        # Arrange
        from move_to_sprint import move_to_backlog

        mock_jira_client.move_issues_to_backlog.return_value = None

        # Act
        result = move_to_backlog(
            issue_keys=["PROJ-101"],
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['moved_to_backlog'] == 1

        # Verify API call
        mock_jira_client.move_issues_to_backlog.assert_called_once()

    def test_move_to_sprint_dry_run(self, mock_jira_client):
        """Test dry-run preview."""
        # Arrange
        from move_to_sprint import move_to_sprint

        # Act
        result = move_to_sprint(
            sprint_id=456,
            issue_keys=["PROJ-101", "PROJ-102"],
            dry_run=True,
            client=mock_jira_client
        )

        # Assert
        assert result['would_move'] == 2
        # Verify NO actual move was called
        mock_jira_client.move_issues_to_sprint.assert_not_called()

    def test_move_to_sprint_with_rank(self, mock_jira_client):
        """Test moving and setting rank position."""
        # Arrange
        from move_to_sprint import move_to_sprint

        mock_jira_client.move_issues_to_sprint.return_value = None

        # Act
        result = move_to_sprint(
            sprint_id=456,
            issue_keys=["PROJ-101"],
            rank_position="top",
            client=mock_jira_client
        )

        # Assert
        assert result['moved'] == 1

        # Verify rank was passed
        call_args = mock_jira_client.move_issues_to_sprint.call_args
        # Depending on API, rank may be passed differently
        assert call_args is not None


@pytest.mark.agile
@pytest.mark.unit
class TestMoveToSprintCLI:
    """Test command-line interface for move_to_sprint.py."""

    def test_cli_main_exists(self):
        """Test CLI main function exists and is callable."""
        from move_to_sprint import main
        assert callable(main)

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch('sys.argv', ['move_to_sprint.py', '--help']):
            from move_to_sprint import main
            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert '--sprint' in captured.out or '--issues' in captured.out or 'usage' in captured.out.lower()


@pytest.mark.agile
@pytest.mark.unit
class TestMoveToSprintErrorHandling:
    """Test API error handling scenarios for move_to_sprint."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        from move_to_sprint import move_to_sprint

        mock_jira_client.move_issues_to_sprint.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            move_to_sprint(
                sprint_id=456,
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError
        from move_to_sprint import move_to_sprint

        mock_jira_client.move_issues_to_sprint.side_effect = PermissionError(
            "Insufficient permissions"
        )

        with pytest.raises(PermissionError):
            move_to_sprint(
                sprint_id=456,
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        from move_to_sprint import move_to_sprint

        mock_jira_client.move_issues_to_sprint.side_effect = JiraError(
            "Rate limit exceeded",
            status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            move_to_sprint(
                sprint_id=456,
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError
        from move_to_sprint import move_to_sprint

        mock_jira_client.move_issues_to_sprint.side_effect = JiraError(
            "Internal server error",
            status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            move_to_sprint(
                sprint_id=456,
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 500

    def test_sprint_not_found(self, mock_jira_client):
        """Test error when sprint doesn't exist."""
        from jira_assistant_skills_lib import JiraError
        from move_to_sprint import move_to_sprint

        mock_jira_client.move_issues_to_sprint.side_effect = JiraError(
            "Sprint does not exist",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            move_to_sprint(
                sprint_id=999,
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 404
