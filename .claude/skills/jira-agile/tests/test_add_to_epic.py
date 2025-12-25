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
from unittest.mock import Mock, patch, MagicMock


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
        from error_handler import JiraError

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
        from error_handler import JiraError

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
        from error_handler import ValidationError

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

    @patch('sys.argv', ['add_to_epic.py', '--epic', 'PROJ-100', '--issues', 'PROJ-101,PROJ-102'])
    def test_cli_multiple_issues(self, mock_jira_client, sample_epic_response):
        """Test CLI with multiple issues."""
        # This will fail initially - tests the CLI parsing
        mock_jira_client.get_issue.return_value = sample_epic_response
        mock_jira_client.update_issue.return_value = None

        # from add_to_epic import main
        # This is a placeholder - will implement when script exists
        pass

    @patch('sys.argv', ['add_to_epic.py', '--epic', 'PROJ-100', '--jql', 'project=PROJ'])
    def test_cli_with_jql(self, mock_jira_client, sample_epic_response):
        """Test CLI with JQL query instead of issue keys."""
        # This will fail initially
        # from add_to_epic import main
        pass
