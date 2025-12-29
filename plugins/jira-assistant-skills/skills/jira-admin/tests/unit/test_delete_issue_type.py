"""
Tests for delete_issue_type.py - Deleting issue types in JIRA.

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
class TestDeleteIssueType:
    """Test suite for delete_issue_type.py functionality."""

    def test_delete_issue_type_success(self, mock_jira_client):
        """Should delete issue type successfully."""
        # Arrange
        mock_jira_client.delete_issue_type.return_value = None

        from delete_issue_type import delete_issue_type

        # Act
        result = delete_issue_type(
            issue_type_id="10005",
            client=mock_jira_client
        )

        # Assert
        assert result is True
        mock_jira_client.delete_issue_type.assert_called_once_with(
            "10005",
            alternative_issue_type_id=None
        )

    def test_delete_issue_type_with_alternative(self, mock_jira_client):
        """Should delete and migrate issues to alternative type."""
        # Arrange
        mock_jira_client.delete_issue_type.return_value = None

        from delete_issue_type import delete_issue_type

        # Act
        result = delete_issue_type(
            issue_type_id="10005",
            alternative_id="10001",
            client=mock_jira_client
        )

        # Assert
        assert result is True
        mock_jira_client.delete_issue_type.assert_called_once_with(
            "10005",
            alternative_issue_type_id="10001"
        )

    def test_delete_issue_type_not_found(self, mock_jira_client):
        """Should raise NotFoundError for invalid ID."""
        # Arrange
        from error_handler import NotFoundError

        mock_jira_client.delete_issue_type.side_effect = NotFoundError(
            "Issue type", "10999"
        )

        from delete_issue_type import delete_issue_type

        # Act & Assert
        with pytest.raises(NotFoundError):
            delete_issue_type(
                issue_type_id="10999",
                client=mock_jira_client
            )

    def test_delete_issue_type_in_use(self, mock_jira_client):
        """Should raise error if type is in use and no alternative given."""
        # Arrange
        from error_handler import JiraError

        mock_jira_client.delete_issue_type.side_effect = JiraError(
            "Cannot delete issue type. Issues exist that use this issue type.",
            status_code=400
        )

        from delete_issue_type import delete_issue_type

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            delete_issue_type(
                issue_type_id="10001",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 400

    def test_delete_issue_type_requires_admin(self, mock_jira_client):
        """Should raise PermissionError without admin rights."""
        # Arrange
        from error_handler import PermissionError

        mock_jira_client.delete_issue_type.side_effect = PermissionError(
            "Administer Jira global permission required"
        )

        from delete_issue_type import delete_issue_type

        # Act & Assert
        with pytest.raises(PermissionError):
            delete_issue_type(
                issue_type_id="10005",
                client=mock_jira_client
            )

    def test_delete_issue_type_invalid_alternative(self, mock_jira_client):
        """Should raise error for invalid alternative issue type."""
        # Arrange
        from error_handler import JiraError

        mock_jira_client.delete_issue_type.side_effect = JiraError(
            "The alternative issue type does not exist",
            status_code=400
        )

        from delete_issue_type import delete_issue_type

        # Act & Assert
        with pytest.raises(JiraError):
            delete_issue_type(
                issue_type_id="10005",
                alternative_id="99999",
                client=mock_jira_client
            )

    def test_delete_issue_type_get_alternatives(
        self, mock_jira_client, alternatives_response
    ):
        """Should support getting alternatives before delete."""
        # Arrange
        mock_jira_client.get_issue_type_alternatives.return_value = alternatives_response

        from delete_issue_type import get_alternatives_for_type

        # Act
        result = get_alternatives_for_type(
            issue_type_id="10005",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert len(result) == 2
        assert result[0]['name'] == 'Story'
        mock_jira_client.get_issue_type_alternatives.assert_called_once_with("10005")

    def test_delete_issue_type_dry_run(self, mock_jira_client):
        """Should support dry run without actual deletion."""
        from delete_issue_type import delete_issue_type

        # Act
        result = delete_issue_type(
            issue_type_id="10005",
            client=mock_jira_client,
            dry_run=True
        )

        # Assert
        assert result is True
        mock_jira_client.delete_issue_type.assert_not_called()


@pytest.mark.admin
@pytest.mark.unit
class TestDeleteIssueTypeCLI:
    """Test command-line interface for delete_issue_type.py."""

    def test_cli_delete(self, mock_jira_client, capsys):
        """Test CLI delete."""
        pass

    def test_cli_with_alternative(self, mock_jira_client, capsys):
        """Test CLI with --alternative-id."""
        pass

    def test_cli_dry_run(self, mock_jira_client, capsys):
        """Test CLI with --dry-run flag."""
        pass

    def test_cli_show_alternatives(self, mock_jira_client, alternatives_response, capsys):
        """Test CLI with --show-alternatives flag."""
        pass
