"""
Tests for archive_version.py - Archive a project version.
"""

import copy
import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestArchiveVersion:
    """Tests for archiving project versions."""

    @patch('archive_version.get_jira_client')
    def test_archive_version_by_id(self, mock_get_client, mock_jira_client, sample_version_archived):
        """Test archiving a version by ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.return_value = sample_version_archived

        from archive_version import archive_version

        result = archive_version(version_id='10002', profile=None)

        assert result['archived'] is True
        mock_jira_client.update_version.assert_called_once()
        call_args = mock_jira_client.update_version.call_args
        assert call_args[1]['archived'] is True

    @patch('archive_version.get_jira_client')
    def test_archive_version_by_name(self, mock_get_client, mock_jira_client, sample_versions_list, sample_version_archived):
        """Test archiving version by name."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = sample_versions_list
        mock_jira_client.update_version.return_value = sample_version_archived

        from archive_version import archive_version_by_name

        result = archive_version_by_name(
            project='PROJ',
            version_name='v0.5.0',
            profile=None
        )

        assert result['archived'] is True
        mock_jira_client.get_versions.assert_called_once_with('PROJ')
        mock_jira_client.update_version.assert_called_once()

    @patch('archive_version.get_jira_client')
    def test_archive_version_not_found(self, mock_get_client, mock_jira_client, sample_versions_list):
        """Test error when version name not found."""
        from error_handler import ValidationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = sample_versions_list

        from archive_version import archive_version_by_name

        with pytest.raises(ValidationError, match="Version.*not found"):
            archive_version_by_name(
                project='PROJ',
                version_name='v99.0.0',
                profile=None
            )

    @patch('archive_version.get_jira_client')
    def test_archive_version_dry_run(self, mock_get_client, mock_jira_client):
        """Test dry-run mode shows what would be archived."""
        mock_get_client.return_value = mock_jira_client

        from archive_version import archive_version_dry_run

        result = archive_version_dry_run(version_id='10002')

        # Dry run should return data without calling API
        assert result['version_id'] == '10002'
        assert result['archived'] is True
        mock_jira_client.update_version.assert_not_called()


@pytest.mark.lifecycle
@pytest.mark.unit
class TestArchiveVersionErrorHandling:
    """Test API error handling for archive_version."""

    @patch('archive_version.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = AuthenticationError("Invalid token")

        from archive_version import archive_version

        with pytest.raises(AuthenticationError):
            archive_version(version_id='10002', profile=None)

    @patch('archive_version.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = PermissionError("Cannot archive version")

        from archive_version import archive_version

        with pytest.raises(PermissionError):
            archive_version(version_id='10002', profile=None)

    @patch('archive_version.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when version doesn't exist."""
        from error_handler import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = NotFoundError("Version", "99999")

        from archive_version import archive_version

        with pytest.raises(NotFoundError):
            archive_version(version_id='99999', profile=None)

    @patch('archive_version.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from archive_version import archive_version

        with pytest.raises(JiraError) as exc_info:
            archive_version(version_id='10002', profile=None)
        assert exc_info.value.status_code == 429

    @patch('archive_version.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from archive_version import archive_version

        with pytest.raises(JiraError) as exc_info:
            archive_version(version_id='10002', profile=None)
        assert exc_info.value.status_code == 500
