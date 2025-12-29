"""
Tests for update_issue_type.py - Updating issue types in JIRA.

Following TDD: These tests are written FIRST and should FAIL initially.
Implementation comes after tests are defined.
"""

import copy
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
class TestUpdateIssueType:
    """Test suite for update_issue_type.py functionality."""

    def test_update_issue_type_name(self, mock_jira_client, story_response):
        """Should update issue type name."""
        # Arrange
        updated_response = copy.deepcopy(story_response)
        updated_response['name'] = 'User Story'
        mock_jira_client.update_issue_type.return_value = updated_response

        from update_issue_type import update_issue_type

        # Act
        result = update_issue_type(
            issue_type_id="10001",
            name="User Story",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['name'] == "User Story"
        mock_jira_client.update_issue_type.assert_called_once()

        call_args = mock_jira_client.update_issue_type.call_args
        assert call_args[1]['name'] == "User Story"

    def test_update_issue_type_description(self, mock_jira_client, story_response):
        """Should update issue type description."""
        # Arrange
        updated_response = copy.deepcopy(story_response)
        updated_response['description'] = 'Updated description'
        mock_jira_client.update_issue_type.return_value = updated_response

        from update_issue_type import update_issue_type

        # Act
        result = update_issue_type(
            issue_type_id="10001",
            description="Updated description",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        mock_jira_client.update_issue_type.assert_called_once()

        call_args = mock_jira_client.update_issue_type.call_args
        assert call_args[1]['description'] == "Updated description"

    def test_update_issue_type_avatar(self, mock_jira_client, story_response):
        """Should update issue type avatar."""
        # Arrange
        updated_response = copy.deepcopy(story_response)
        updated_response['avatarId'] = 10400
        mock_jira_client.update_issue_type.return_value = updated_response

        from update_issue_type import update_issue_type

        # Act
        result = update_issue_type(
            issue_type_id="10001",
            avatar_id=10400,
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        mock_jira_client.update_issue_type.assert_called_once()

        call_args = mock_jira_client.update_issue_type.call_args
        assert call_args[1]['avatar_id'] == 10400

    def test_update_issue_type_multiple_fields(self, mock_jira_client, story_response):
        """Should update multiple fields at once."""
        # Arrange
        updated_response = copy.deepcopy(story_response)
        updated_response['name'] = 'Feature Request'
        updated_response['description'] = 'A request for new functionality'
        mock_jira_client.update_issue_type.return_value = updated_response

        from update_issue_type import update_issue_type

        # Act
        result = update_issue_type(
            issue_type_id="10001",
            name="Feature Request",
            description="A request for new functionality",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        mock_jira_client.update_issue_type.assert_called_once()

        call_args = mock_jira_client.update_issue_type.call_args
        assert call_args[1]['name'] == "Feature Request"
        assert call_args[1]['description'] == "A request for new functionality"

    def test_update_issue_type_not_found(self, mock_jira_client):
        """Should raise NotFoundError for invalid ID."""
        # Arrange
        from error_handler import NotFoundError

        mock_jira_client.update_issue_type.side_effect = NotFoundError(
            "Issue type", "10999"
        )

        from update_issue_type import update_issue_type

        # Act & Assert
        with pytest.raises(NotFoundError):
            update_issue_type(
                issue_type_id="10999",
                name="New Name",
                client=mock_jira_client
            )

    def test_update_issue_type_name_too_long(self, mock_jira_client):
        """Should raise ValidationError for name > 60 chars."""
        from error_handler import ValidationError
        from update_issue_type import update_issue_type

        # Act & Assert
        long_name = "A" * 61
        with pytest.raises(ValidationError) as exc_info:
            update_issue_type(
                issue_type_id="10001",
                name=long_name,
                client=mock_jira_client
            )

        assert "name" in str(exc_info.value).lower() or "60" in str(exc_info.value)

    def test_update_issue_type_requires_admin(self, mock_jira_client):
        """Should raise PermissionError without admin rights."""
        # Arrange
        from error_handler import PermissionError

        mock_jira_client.update_issue_type.side_effect = PermissionError(
            "Administer Jira global permission required"
        )

        from update_issue_type import update_issue_type

        # Act & Assert
        with pytest.raises(PermissionError):
            update_issue_type(
                issue_type_id="10001",
                name="New Name",
                client=mock_jira_client
            )

    def test_update_issue_type_no_changes(self, mock_jira_client, story_response):
        """Should handle update with no fields specified."""
        from error_handler import ValidationError
        from update_issue_type import update_issue_type

        # Act & Assert - should require at least one field
        with pytest.raises(ValidationError) as exc_info:
            update_issue_type(
                issue_type_id="10001",
                client=mock_jira_client
            )

        assert "at least one" in str(exc_info.value).lower()


@pytest.mark.admin
@pytest.mark.unit
class TestUpdateIssueTypeCLI:
    """Test command-line interface for update_issue_type.py."""

    def test_cli_update_name(self, mock_jira_client, story_response, capsys):
        """Test CLI with --name."""
        pass

    def test_cli_update_description(self, mock_jira_client, story_response, capsys):
        """Test CLI with --description."""
        pass

    def test_cli_json_output(self, mock_jira_client, story_response, capsys):
        """Test CLI with --format json output."""
        pass
