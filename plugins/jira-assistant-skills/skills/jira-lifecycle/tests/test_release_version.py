"""
Tests for release_version.py - Release a project version.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.mark.lifecycle
@pytest.mark.unit
class TestReleaseVersion:
    """Tests for releasing project versions."""

    @patch("release_version.get_jira_client")
    def test_release_version_by_id(
        self, mock_get_client, mock_jira_client, sample_version_released
    ):
        """Test releasing a version by ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.return_value = sample_version_released

        from release_version import release_version

        result = release_version(version_id="10001")

        assert result["released"] is True
        mock_jira_client.update_version.assert_called_once()
        call_args = mock_jira_client.update_version.call_args
        assert call_args[1]["released"] is True

    @patch("release_version.get_jira_client")
    def test_release_version_with_date(self, mock_get_client, mock_jira_client):
        """Test releasing version with specific release date."""
        mock_get_client.return_value = mock_jira_client
        released_with_date = {
            "id": "10001",
            "name": "v1.0.0",
            "released": True,
            "releaseDate": "2025-02-15",
            "archived": False,
        }
        mock_jira_client.update_version.return_value = released_with_date

        from release_version import release_version

        result = release_version(
            version_id="10001", release_date="2025-02-15"
        )

        assert result["released"] is True
        assert result["releaseDate"] == "2025-02-15"

    @patch("release_version.get_jira_client")
    def test_release_version_by_name(
        self,
        mock_get_client,
        mock_jira_client,
        sample_versions_list,
        sample_version_released,
    ):
        """Test releasing version by name."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = sample_versions_list
        mock_jira_client.update_version.return_value = sample_version_released

        from release_version import release_version_by_name

        result = release_version_by_name(
            project="PROJ", version_name="v1.0.0"
        )

        assert result["released"] is True
        mock_jira_client.get_versions.assert_called_once_with("PROJ")
        mock_jira_client.update_version.assert_called_once()

    @patch("release_version.get_jira_client")
    def test_release_version_not_found(
        self, mock_get_client, mock_jira_client, sample_versions_list
    ):
        """Test error when version name not found."""
        from assistant_skills_lib.error_handler import ValidationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = sample_versions_list

        from release_version import release_version_by_name

        with pytest.raises(ValidationError, match="Version.*not found"):
            release_version_by_name(
                project="PROJ", version_name="v99.0.0"
            )

    @patch("release_version.get_jira_client")
    def test_release_with_description(self, mock_get_client, mock_jira_client):
        """Test releasing version with updated description."""
        mock_get_client.return_value = mock_jira_client
        released_with_desc = {
            "id": "10001",
            "name": "v1.0.0",
            "description": "Released version",
            "released": True,
            "archived": False,
        }
        mock_jira_client.update_version.return_value = released_with_desc

        from release_version import release_version

        result = release_version(
            version_id="10001", description="Released version"
        )

        assert result["description"] == "Released version"

    @patch("release_version.get_jira_client")
    def test_release_version_dry_run(self, mock_get_client, mock_jira_client):
        """Test dry-run mode shows what would be released."""
        mock_get_client.return_value = mock_jira_client

        from release_version import release_version_dry_run

        result = release_version_dry_run(version_id="10001", release_date="2025-03-01")

        # Dry run should return data without calling API
        assert result["version_id"] == "10001"
        assert result["released"] is True
        assert result["releaseDate"] == "2025-03-01"
        mock_jira_client.update_version.assert_not_called()


@pytest.mark.lifecycle
@pytest.mark.unit
class TestReleaseVersionErrorHandling:
    """Test API error handling for release_version."""

    @patch("release_version.get_jira_client")
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = AuthenticationError(
            "Invalid token"
        )

        from release_version import release_version

        with pytest.raises(AuthenticationError):
            release_version(version_id="10001")

    @patch("release_version.get_jira_client")
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = PermissionError(
            "Cannot release version"
        )

        from release_version import release_version

        with pytest.raises(PermissionError):
            release_version(version_id="10001")

    @patch("release_version.get_jira_client")
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when version doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = NotFoundError("Version", "99999")

        from release_version import release_version

        with pytest.raises(NotFoundError):
            release_version(version_id="99999")

    @patch("release_version.get_jira_client")
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from release_version import release_version

        with pytest.raises(JiraError) as exc_info:
            release_version(version_id="10001")
        assert exc_info.value.status_code == 429

    @patch("release_version.get_jira_client")
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_version.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from release_version import release_version

        with pytest.raises(JiraError) as exc_info:
            release_version(version_id="10001")
        assert exc_info.value.status_code == 500
