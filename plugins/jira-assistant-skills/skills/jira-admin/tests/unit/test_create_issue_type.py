"""
Tests for create_issue_type.py - Creating issue types in JIRA.

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
class TestCreateIssueType:
    """Test suite for create_issue_type.py functionality."""

    def test_create_issue_type_standard(self, mock_jira_client, created_issue_type_response):
        """Should create standard issue type."""
        # Arrange
        mock_jira_client.create_issue_type.return_value = created_issue_type_response

        from create_issue_type import create_issue_type

        # Act
        result = create_issue_type(
            name="Incident",
            description="An unplanned interruption",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        assert result['id'] == "10005"
        assert result['name'] == "Incident"
        mock_jira_client.create_issue_type.assert_called_once()

        # Verify call arguments
        call_args = mock_jira_client.create_issue_type.call_args
        assert call_args[1]['name'] == "Incident"
        assert call_args[1]['description'] == "An unplanned interruption"

    def test_create_issue_type_subtask(self, mock_jira_client, subtask_response):
        """Should create subtask issue type."""
        # Arrange
        mock_jira_client.create_issue_type.return_value = subtask_response

        from create_issue_type import create_issue_type

        # Act
        result = create_issue_type(
            name="Sub-bug",
            issue_type="subtask",
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        mock_jira_client.create_issue_type.assert_called_once()

        call_args = mock_jira_client.create_issue_type.call_args
        assert call_args[1]['issue_type'] == "subtask"

    def test_create_issue_type_with_hierarchy(self, mock_jira_client, epic_response):
        """Should create issue type with specific hierarchy level."""
        # Arrange
        mock_jira_client.create_issue_type.return_value = epic_response

        from create_issue_type import create_issue_type

        # Act
        result = create_issue_type(
            name="Initiative",
            hierarchy_level=2,
            client=mock_jira_client
        )

        # Assert
        assert result is not None
        mock_jira_client.create_issue_type.assert_called_once()

        call_args = mock_jira_client.create_issue_type.call_args
        assert call_args[1]['hierarchy_level'] == 2

    def test_create_issue_type_name_too_long(self, mock_jira_client):
        """Should raise ValidationError for name > 60 chars."""
        from jira_assistant_skills_lib import ValidationError
        from create_issue_type import create_issue_type

        # Act & Assert
        long_name = "A" * 61  # 61 characters
        with pytest.raises(ValidationError) as exc_info:
            create_issue_type(
                name=long_name,
                client=mock_jira_client
            )

        assert "name" in str(exc_info.value).lower() or "60" in str(exc_info.value)

    def test_create_issue_type_name_empty(self, mock_jira_client):
        """Should raise ValidationError for empty name."""
        from jira_assistant_skills_lib import ValidationError
        from create_issue_type import create_issue_type

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            create_issue_type(
                name="",
                client=mock_jira_client
            )

        assert "name" in str(exc_info.value).lower()

    def test_create_issue_type_requires_admin(self, mock_jira_client):
        """Should raise PermissionError without admin rights."""
        # Arrange
        from jira_assistant_skills_lib import PermissionError

        mock_jira_client.create_issue_type.side_effect = PermissionError(
            "Administer Jira global permission required"
        )

        from create_issue_type import create_issue_type

        # Act & Assert
        with pytest.raises(PermissionError):
            create_issue_type(
                name="Incident",
                client=mock_jira_client
            )

    def test_create_issue_type_invalid_type(self, mock_jira_client):
        """Should raise ValidationError for invalid type."""
        from jira_assistant_skills_lib import ValidationError
        from create_issue_type import create_issue_type

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            create_issue_type(
                name="Incident",
                issue_type="invalid",
                client=mock_jira_client
            )

        assert "type" in str(exc_info.value).lower()

    def test_create_issue_type_api_error(self, mock_jira_client):
        """Should propagate API errors."""
        # Arrange
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.create_issue_type.side_effect = JiraError(
            "Failed to create issue type",
            status_code=400
        )

        from create_issue_type import create_issue_type

        # Act & Assert
        with pytest.raises(JiraError) as exc_info:
            create_issue_type(
                name="Incident",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 400


@pytest.mark.admin
@pytest.mark.unit
class TestCreateIssueTypeCLI:
    """Test command-line interface for create_issue_type.py."""

    def test_cli_standard_type(self, mock_jira_client, created_issue_type_response, capsys):
        """Test CLI creating standard issue type."""
        pass

    def test_cli_subtask_type(self, mock_jira_client, subtask_response, capsys):
        """Test CLI with --type subtask."""
        pass

    def test_cli_json_output(self, mock_jira_client, created_issue_type_response, capsys):
        """Test CLI with --format json output."""
        pass
