"""
Tests for project archive and restore operations - archive_project.py, restore_project.py.

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
class TestArchiveProject:
    """Test suite for archive_project.py functionality."""

    def test_archive_project_success(self, mock_jira_client, sample_project_response):
        """Test archiving a project successfully."""
        from archive_project import archive_project

        # archive_project returns None on success (204)
        mock_jira_client.archive_project.return_value = None

        result = archive_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        assert result is not None
        assert result['success'] is True

        mock_jira_client.archive_project.assert_called_once_with("PROJ")

    def test_archive_project_dry_run(self, mock_jira_client, sample_project_response):
        """Test dry-run mode doesn't actually archive."""
        from archive_project import archive_project

        mock_jira_client.get_project.return_value = sample_project_response

        result = archive_project(
            project_key="PROJ",
            dry_run=True,
            client=mock_jira_client
        )

        assert result is not None
        assert result['dry_run'] is True

        # Should NOT call archive_project
        mock_jira_client.archive_project.assert_not_called()

    def test_archive_project_already_archived(self, mock_jira_client):
        """Test error when project is already archived."""
        from archive_project import archive_project
        from error_handler import JiraError

        mock_jira_client.archive_project.side_effect = JiraError(
            "Project is already archived",
            status_code=400
        )

        with pytest.raises(JiraError) as exc_info:
            archive_project(
                project_key="PROJ",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 400

    def test_archive_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from archive_project import archive_project
        from error_handler import JiraError

        mock_jira_client.archive_project.side_effect = JiraError(
            "Project not found",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            archive_project(
                project_key="NOTFOUND",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_archive_project_no_permission(self, mock_jira_client):
        """Test error when user lacks admin permission."""
        from archive_project import archive_project
        from error_handler import JiraError

        mock_jira_client.archive_project.side_effect = JiraError(
            "You don't have permission to archive projects",
            status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            archive_project(
                project_key="PROJ",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 403

    def test_archive_project_invalid_key(self, mock_jira_client):
        """Test error for invalid project key."""
        from archive_project import archive_project
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            archive_project(
                project_key="",
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestRestoreProject:
    """Test suite for restore_project.py functionality."""

    def test_restore_archived_project(self, mock_jira_client, sample_project_response):
        """Test restoring an archived project."""
        from restore_project import restore_project

        mock_jira_client.restore_project.return_value = sample_project_response

        result = restore_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        assert result is not None
        assert result['key'] == "PROJ"

        mock_jira_client.restore_project.assert_called_once_with("PROJ")

    def test_restore_trashed_project(self, mock_jira_client, sample_project_response):
        """Test restoring a project from trash."""
        from restore_project import restore_project

        mock_jira_client.restore_project.return_value = sample_project_response

        result = restore_project(
            project_key="OLD",
            client=mock_jira_client
        )

        assert result is not None

        mock_jira_client.restore_project.assert_called_once_with("OLD")

    def test_restore_active_project_error(self, mock_jira_client):
        """Test error when trying to restore an active project."""
        from restore_project import restore_project
        from error_handler import JiraError

        mock_jira_client.restore_project.side_effect = JiraError(
            "Project is not archived or deleted",
            status_code=400
        )

        with pytest.raises(JiraError) as exc_info:
            restore_project(
                project_key="ACTIVE",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 400

    def test_restore_project_not_found(self, mock_jira_client):
        """Test error when project doesn't exist."""
        from restore_project import restore_project
        from error_handler import JiraError

        mock_jira_client.restore_project.side_effect = JiraError(
            "Project not found",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            restore_project(
                project_key="NOTFOUND",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_restore_project_no_permission(self, mock_jira_client):
        """Test error when user lacks admin permission."""
        from restore_project import restore_project
        from error_handler import JiraError

        mock_jira_client.restore_project.side_effect = JiraError(
            "You don't have permission to restore projects",
            status_code=403
        )

        with pytest.raises(JiraError) as exc_info:
            restore_project(
                project_key="PROJ",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 403

    def test_restore_project_expired(self, mock_jira_client):
        """Test error when project has expired from trash."""
        from restore_project import restore_project
        from error_handler import JiraError

        mock_jira_client.restore_project.side_effect = JiraError(
            "Project has been permanently deleted",
            status_code=404
        )

        with pytest.raises(JiraError) as exc_info:
            restore_project(
                project_key="EXPIRED",
                client=mock_jira_client
            )

        assert exc_info.value.status_code == 404

    def test_restore_project_invalid_key(self, mock_jira_client):
        """Test error for invalid project key."""
        from restore_project import restore_project
        from error_handler import ValidationError

        with pytest.raises(ValidationError):
            restore_project(
                project_key="",
                client=mock_jira_client
            )


@pytest.mark.admin
@pytest.mark.unit
class TestArchiveRestoreOutput:
    """Test output formatting for archive/restore operations."""

    def test_archive_format_text_output(self, mock_jira_client, sample_project_response):
        """Test text output for archive operation."""
        from archive_project import archive_project, format_output

        mock_jira_client.archive_project.return_value = None
        mock_jira_client.get_project.return_value = sample_project_response

        result = archive_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        output = format_output(result, "PROJ", output_format="text")

        assert "PROJ" in output
        assert "archived" in output.lower()

    def test_archive_format_json_output(self, mock_jira_client, sample_project_response):
        """Test JSON output for archive operation."""
        from archive_project import archive_project, format_output
        import json

        mock_jira_client.archive_project.return_value = None
        mock_jira_client.get_project.return_value = sample_project_response

        result = archive_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        output = format_output(result, "PROJ", output_format="json")

        # Should be valid JSON
        data = json.loads(output)
        assert 'success' in data or 'project_key' in data

    def test_restore_format_text_output(self, mock_jira_client, sample_project_response):
        """Test text output for restore operation."""
        from restore_project import restore_project, format_output

        mock_jira_client.restore_project.return_value = sample_project_response

        result = restore_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        output = format_output(result, output_format="text")

        assert "PROJ" in output
        assert "restored" in output.lower()

    def test_restore_format_json_output(self, mock_jira_client, sample_project_response):
        """Test JSON output for restore operation."""
        from restore_project import restore_project, format_output
        import json

        mock_jira_client.restore_project.return_value = sample_project_response

        result = restore_project(
            project_key="PROJ",
            client=mock_jira_client
        )

        output = format_output(result, output_format="json")

        # Should be valid JSON
        data = json.loads(output)
        assert data is not None


@pytest.mark.admin
@pytest.mark.unit
class TestArchiveRestoreCLI:
    """Test command-line interfaces for archive/restore operations."""

    @patch('sys.argv', ['archive_project.py', 'PROJ', '--yes'])
    def test_cli_archive_project(self, mock_jira_client, sample_project_response):
        """Test CLI for archiving project."""
        mock_jira_client.archive_project.return_value = None
        # CLI test placeholder - would need to mock main()
        pass

    @patch('sys.argv', ['archive_project.py', 'PROJ', '--dry-run'])
    def test_cli_archive_project_dry_run(self, mock_jira_client, sample_project_response):
        """Test CLI for dry-run archive."""
        mock_jira_client.get_project.return_value = sample_project_response
        # CLI test placeholder
        pass

    @patch('sys.argv', ['restore_project.py', 'PROJ'])
    def test_cli_restore_project(self, mock_jira_client, sample_project_response):
        """Test CLI for restoring project."""
        mock_jira_client.restore_project.return_value = sample_project_response
        # CLI test placeholder
        pass
