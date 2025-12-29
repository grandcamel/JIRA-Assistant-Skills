"""
Tests for update_project.py - Updating JIRA project settings.

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
class TestUpdateProject:
    """Test suite for update_project.py functionality."""

    def test_update_project_name(self, mock_jira_client, sample_project_response):
        """Test updating project name."""
        from update_project import update_project

        mock_jira_client.update_project.return_value = sample_project_response

        result = update_project(
            project_key="PROJ",
            name="Updated Project Name",
            client=mock_jira_client
        )

        assert result is not None
        mock_jira_client.update_project.assert_called_once()

        # Verify name was passed
        call_kwargs = mock_jira_client.update_project.call_args
        assert 'name' in call_kwargs[1] or 'Updated Project Name' in str(call_kwargs)

    def test_update_project_description(self, mock_jira_client, sample_project_response):
        """Test updating project description."""
        from update_project import update_project

        mock_jira_client.update_project.return_value = sample_project_response

        result = update_project(
            project_key="PROJ",
            description="New description for the project",
            client=mock_jira_client
        )

        assert result is not None
        mock_jira_client.update_project.assert_called_once()

    def test_update_project_lead(self, mock_jira_client, sample_project_response):
        """Test updating project lead."""
        from update_project import update_project

        mock_jira_client.update_project.return_value = sample_project_response

        result = update_project(
            project_key="PROJ",
            lead="new-lead-account-id",
            client=mock_jira_client
        )

        assert result is not None
        mock_jira_client.update_project.assert_called_once()

        # Verify lead was passed
        call_kwargs = mock_jira_client.update_project.call_args
        assert 'lead' in str(call_kwargs).lower()

    def test_update_project_url(self, mock_jira_client, sample_project_response):
        """Test updating project URL."""
        from update_project import update_project

        mock_jira_client.update_project.return_value = sample_project_response

        result = update_project(
            project_key="PROJ",
            url="https://new-url.example.com",
            client=mock_jira_client
        )

        assert result is not None
        mock_jira_client.update_project.assert_called_once()

    def test_update_project_assignee_type(self, mock_jira_client, sample_project_response):
        """Test updating default assignee type."""
        from update_project import update_project

        mock_jira_client.update_project.return_value = sample_project_response

        result = update_project(
            project_key="PROJ",
            assignee_type="UNASSIGNED",
            client=mock_jira_client
        )

        assert result is not None
        mock_jira_client.update_project.assert_called_once()

        # Verify assignee type was passed
        call_kwargs = mock_jira_client.update_project.call_args
        assert 'assignee' in str(call_kwargs).lower() or 'UNASSIGNED' in str(call_kwargs)

    def test_update_project_category(self, mock_jira_client, sample_project_response):
        """Test updating project category."""
        from update_project import update_project

        mock_jira_client.update_project.return_value = sample_project_response

        result = update_project(
            project_key="PROJ",
            category_id=10001,
            client=mock_jira_client
        )

        assert result is not None
        mock_jira_client.update_project.assert_called_once()

    def test_update_project_multiple_fields(self, mock_jira_client, sample_project_response):
        """Test updating multiple fields at once."""
        from update_project import update_project

        mock_jira_client.update_project.return_value = sample_project_response

        result = update_project(
            project_key="PROJ",
            name="New Name",
            description="New description",
            url="https://new.example.com",
            client=mock_jira_client
        )

        assert result is not None
        mock_jira_client.update_project.assert_called_once()

    def test_update_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from update_project import update_project
        from error_handler import JiraError

        mock_jira_client.update_project.side_effect = JiraError(
            "Project not found",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            update_project(
                project_key="NOTFOUND",
                name="New Name",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_update_project_no_permission(self, mock_jira_client):
        """Test error when user lacks permission."""
        from update_project import update_project
        from error_handler import JiraError

        mock_jira_client.update_project.side_effect = JiraError(
            "You don't have permission to edit this project",
            status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            update_project(
                project_key="PROJ",
                name="New Name",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 403

    def test_update_project_invalid_assignee_type(self, mock_jira_client):
        """Test error for invalid assignee type."""
        from update_project import update_project
        from error_handler import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            update_project(
                project_key="PROJ",
                assignee_type="INVALID_TYPE",
                client=mock_jira_client
            )

        assert "invalid" in str(exc_info.value).lower()

    def test_update_project_no_changes(self, mock_jira_client):
        """Test behavior when no changes are provided."""
        from update_project import update_project
        from error_handler import ValidationError

        # Should either return early or raise an error
        with pytest.raises(ValidationError):
            update_project(
                project_key="PROJ",
                client=mock_jira_client
                # No fields to update
            )


@pytest.mark.admin
@pytest.mark.unit
class TestUpdateProjectCLI:
    """Test command-line interface for update_project.py."""

    @patch('sys.argv', ['update_project.py', 'PROJ', '--name', 'New Name'])
    def test_cli_update_name(self, mock_jira_client, sample_project_response):
        """Test CLI for updating project name."""
        mock_jira_client.update_project.return_value = sample_project_response
        pass

    @patch('sys.argv', ['update_project.py', 'PROJ', '--lead', 'alice@example.com'])
    def test_cli_update_lead(self, mock_jira_client, sample_project_response):
        """Test CLI for updating project lead."""
        mock_jira_client.update_project.return_value = sample_project_response
        pass

    @patch('sys.argv', ['update_project.py', 'PROJ', '--assignee-type', 'UNASSIGNED'])
    def test_cli_update_assignee_type(self, mock_jira_client, sample_project_response):
        """Test CLI for updating assignee type."""
        mock_jira_client.update_project.return_value = sample_project_response
        pass
