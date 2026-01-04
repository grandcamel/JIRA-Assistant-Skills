"""
Tests for add_to_epic.py - Adding issues to epics in JIRA.

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
class TestAddToEpic:
    """Test suite for add_to_epic.py functionality."""

    def test_add_single_issue_to_epic(self, mock_jira_client, sample_epic_response, sample_issue_response):
        """Test adding one issue to epic."""
        # Arrange
        from add_to_epic import add_to_epic

        # Mock responses
        mock_jira_client.get_issue.side_effect = [
            sample_epic_response,  # Epic validation
            sample_issue_response   # Issue to add
        ]
        mock_jira_client.update_issue.return_value = None

        # Act
        result = add_to_epic(
            epic_key="PROJ-100",
            issue_keys=["PROJ-101"],
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['added'] == 1
        assert result['failed'] == 0

        # Verify API call to update issue with epic link
        mock_jira_client.update_issue.assert_called_once()
        call_args = mock_jira_client.update_issue.call_args[0]
        assert call_args[0] == "PROJ-101"  # Issue key
        assert 'customfield_10014' in call_args[1]  # Epic Link field

    def test_add_multiple_issues_to_epic(self, mock_jira_client, sample_epic_response, sample_issue_response):
        """Test bulk adding issues to epic."""
        # Arrange
        from add_to_epic import add_to_epic

        # Mock epic validation
        mock_jira_client.get_issue.return_value = sample_epic_response
        mock_jira_client.update_issue.return_value = None

        # Act
        result = add_to_epic(
            epic_key="PROJ-100",
            issue_keys=["PROJ-101", "PROJ-102", "PROJ-103"],
            client=mock_jira_client
        )

        # Assert
        assert result['added'] == 3
        assert result['failed'] == 0
        assert mock_jira_client.update_issue.call_count == 3

    def test_add_to_epic_with_dry_run(self, mock_jira_client, sample_epic_response, sample_issue_response):
        """Test dry-run mode shows preview without making changes."""
        # Arrange
        from add_to_epic import add_to_epic

        mock_jira_client.get_issue.return_value = sample_epic_response

        # Act
        result = add_to_epic(
            epic_key="PROJ-100",
            issue_keys=["PROJ-101", "PROJ-102"],
            dry_run=True,
            client=mock_jira_client
        )

        # Assert
        assert result['would_add'] == 2
        # Verify NO update calls were made
        mock_jira_client.update_issue.assert_not_called()

    def test_add_to_epic_invalid_epic(self, mock_jira_client):
        """Test error when epic doesn't exist."""
        # Arrange
        from add_to_epic import add_to_epic
        from jira_assistant_skills_lib import JiraError

        # Simulate 404 when fetching epic
        mock_jira_client.get_issue.side_effect = JiraError(
            "Issue does not exist",
            status_code=404
        )

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            add_to_epic(
                epic_key="PROJ-999",
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_add_to_epic_invalid_issue(self, mock_jira_client, sample_epic_response):
        """Test error when issue doesn't exist."""
        # Arrange
        from add_to_epic import add_to_epic
        from jira_assistant_skills_lib import JiraError

        # Epic exists, but issue update fails
        mock_jira_client.get_issue.return_value = sample_epic_response
        mock_jira_client.update_issue.side_effect = JiraError(
            "Issue does not exist",
            status_code=404
        )

        # Act
        result = add_to_epic(
            epic_key="PROJ-100",
            issue_keys=["PROJ-999"],
            client=mock_jira_client
        )

        # Assert - should track failure, not raise
        assert result['added'] == 0
        assert result['failed'] == 1
        assert result['failures'][0]['issue'] == 'PROJ-999'

    def test_add_to_epic_not_epic_type(self, mock_jira_client, sample_issue_response):
        """Test error when target is not an Epic issue type."""
        # Arrange
        from add_to_epic import add_to_epic
        from assistant_skills_lib.error_handler import ValidationError

        # Return a Story instead of Epic
        mock_jira_client.get_issue.return_value = sample_issue_response

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            add_to_epic(
                epic_key="PROJ-101",  # This is a Story, not Epic
                issue_keys=["PROJ-102"],
                client=mock_jira_client
            )

        assert "not an epic" in str(exc_info.value).lower()

    def test_remove_from_epic(self, mock_jira_client, sample_issue_response):
        """Test removing issue from epic (set to None)."""
        # Arrange
        from add_to_epic import add_to_epic

        mock_jira_client.update_issue.return_value = None

        # Act
        result = add_to_epic(
            epic_key=None,  # None means remove from epic
            issue_keys=["PROJ-101"],
            remove=True,
            client=mock_jira_client
        )

        # Assert
        assert result['removed'] == 1

        # Verify epic link set to None
        call_args = mock_jira_client.update_issue.call_args[0]
        assert call_args[1]['customfield_10014'] is None


@pytest.mark.agile
@pytest.mark.unit
class TestAddToEpicCLI:
    """Test command-line interface for add_to_epic.py."""

    def test_cli_main_exists(self):
        """Test CLI main function exists and is callable."""
        from add_to_epic import main
        assert callable(main)

    def test_cli_help_output(self, capsys):
        """Test that --help shows usage information."""
        with patch('sys.argv', ['add_to_epic.py', '--help']):
            from add_to_epic import main
            try:
                main()
            except SystemExit:
                pass  # --help causes SystemExit

        captured = capsys.readouterr()
        assert '--epic' in captured.out or 'usage' in captured.out.lower()


@pytest.mark.agile
@pytest.mark.unit
class TestAddToEpicErrorHandling:
    """Test API error handling scenarios for add_to_epic."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        from add_to_epic import add_to_epic

        mock_jira_client.get_issue.side_effect = AuthenticationError(
            "Invalid API token"
        )

        with pytest.raises(AuthenticationError):
            add_to_epic(
                epic_key="PROJ-100",
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )

    def test_forbidden_error(self, mock_jira_client, sample_epic_response):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError
        from add_to_epic import add_to_epic

        mock_jira_client.get_issue.return_value = sample_epic_response
        mock_jira_client.update_issue.side_effect = PermissionError(
            "Insufficient permissions"
        )

        # add_to_epic tracks failures rather than raising for individual issues
        result = add_to_epic(
            epic_key="PROJ-100",
            issue_keys=["PROJ-101"],
            client=mock_jira_client
        )
        assert result['failed'] == 1

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        from add_to_epic import add_to_epic

        mock_jira_client.get_issue.side_effect = JiraError(
            "Rate limit exceeded",
            status_code=429
        )

        with pytest.raises(JiraError) as exc_info:
            add_to_epic(
                epic_key="PROJ-100",
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError
        from add_to_epic import add_to_epic

        mock_jira_client.get_issue.side_effect = JiraError(
            "Internal server error",
            status_code=500
        )

        with pytest.raises(JiraError) as exc_info:
            add_to_epic(
                epic_key="PROJ-100",
                issue_keys=["PROJ-101"],
                client=mock_jira_client
            )
        assert exc_info.value.status_code == 500
