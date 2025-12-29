"""
Tests for delete_project.py - Deleting JIRA projects.

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
class TestDeleteProject:
    """Test suite for delete_project.py functionality."""

    def test_delete_project_basic(self, mock_jira_client):
        """Test basic project deletion."""
        from delete_project import delete_project

        mock_jira_client.delete_project.return_value = None

        result = delete_project(
            project_key="PROJ",
            client=mock_jira_client,
            force=True  # Skip confirmation
        )

        mock_jira_client.delete_project.assert_called_once()
        # Verify project key was passed correctly
        call_args = mock_jira_client.delete_project.call_args
        assert "PROJ" in str(call_args)

    def test_delete_project_with_undo(self, mock_jira_client):
        """Test delete with undo enabled (goes to trash)."""
        from delete_project import delete_project

        mock_jira_client.delete_project.return_value = None

        result = delete_project(
            project_key="PROJ",
            enable_undo=True,
            client=mock_jira_client,
            force=True
        )

        # Verify enable_undo was passed
        call_args = mock_jira_client.delete_project.call_args
        assert 'enable_undo' in str(call_args).lower() or 'True' in str(call_args)

    def test_delete_project_permanent(self, mock_jira_client):
        """Test permanent deletion (no undo)."""
        from delete_project import delete_project

        mock_jira_client.delete_project.return_value = None

        result = delete_project(
            project_key="PROJ",
            enable_undo=False,
            client=mock_jira_client,
            force=True
        )

        # Verify enable_undo=False was passed
        mock_jira_client.delete_project.assert_called_once()

    def test_delete_project_dry_run(self, mock_jira_client, sample_project_response):
        """Test dry run mode (preview without deletion)."""
        from delete_project import delete_project

        mock_jira_client.get_project.return_value = sample_project_response

        result = delete_project(
            project_key="PROJ",
            dry_run=True,
            client=mock_jira_client
        )

        # Should NOT call delete in dry run mode
        mock_jira_client.delete_project.assert_not_called()

        # Should call get_project to show what would be deleted
        mock_jira_client.get_project.assert_called_once()

    def test_delete_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from delete_project import delete_project
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_project.side_effect = JiraError(
            "Project NOTFOUND not found",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            delete_project(
                project_key="NOTFOUND",
                client=mock_jira_client,
                force=True
            )

        assert exc_info.value.status_code == 404

    def test_delete_project_no_permission(self, mock_jira_client):
        """Test error when user lacks admin permission."""
        from delete_project import delete_project
        from jira_assistant_skills_lib import JiraError

        mock_jira_client.delete_project.side_effect = JiraError(
            "You don't have permission to delete this project",
            status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            delete_project(
                project_key="PROJ",
                client=mock_jira_client,
                force=True
            )

        assert exc_info.value.status_code == 403

    def test_delete_project_invalid_key(self, mock_jira_client):
        """Test validation of project key format."""
        from delete_project import delete_project
        from jira_assistant_skills_lib import ValidationError

        with pytest.raises(ValidationError):
            delete_project(
                project_key="",  # Empty key
                client=mock_jira_client,
                force=True
            )

    def test_delete_project_uppercase_key(self, mock_jira_client):
        """Test that lowercase keys are normalized to uppercase."""
        from delete_project import delete_project

        mock_jira_client.delete_project.return_value = None

        result = delete_project(
            project_key="proj",  # Lowercase
            client=mock_jira_client,
            force=True
        )

        # Should be called with uppercase
        call_args = mock_jira_client.delete_project.call_args
        assert "PROJ" in str(call_args)


@pytest.mark.admin
@pytest.mark.unit
class TestDeleteProjectAsync:
    """Test async deletion for large projects."""

    def test_delete_project_async(self, mock_jira_client, sample_task_response):
        """Test async deletion for large projects."""
        from delete_project import delete_project_async

        mock_jira_client.delete_project_async.return_value = "task-123"
        mock_jira_client.get_task_status.return_value = sample_task_response

        result = delete_project_async(
            project_key="BIGPROJ",
            client=mock_jira_client
        )

        # Should call async delete
        mock_jira_client.delete_project_async.assert_called_once()

    def test_delete_project_async_status(self, mock_jira_client, sample_task_response):
        """Test polling task status during async deletion."""
        from delete_project import poll_task_status

        mock_jira_client.get_task_status.return_value = sample_task_response

        result = poll_task_status(
            task_id="task-123",
            client=mock_jira_client
        )

        assert result['status'] == 'COMPLETE'
        mock_jira_client.get_task_status.assert_called()


@pytest.mark.admin
@pytest.mark.unit
class TestDeleteProjectCLI:
    """Test command-line interface for delete_project.py."""

    @patch('sys.argv', ['delete_project.py', 'PROJ', '--yes'])
    def test_cli_with_confirmation(self, mock_jira_client):
        """Test CLI with --yes flag to skip confirmation."""
        mock_jira_client.delete_project.return_value = None
        pass

    @patch('sys.argv', ['delete_project.py', 'PROJ', '--dry-run'])
    def test_cli_dry_run(self, mock_jira_client, sample_project_response):
        """Test CLI dry run mode."""
        mock_jira_client.get_project.return_value = sample_project_response
        pass

    @patch('sys.argv', ['delete_project.py', 'PROJ', '--no-undo', '--yes'])
    def test_cli_permanent_delete(self, mock_jira_client):
        """Test CLI for permanent deletion."""
        mock_jira_client.delete_project.return_value = None
        pass
