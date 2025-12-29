"""
Tests for get_versions.py - Get project versions.
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
class TestGetVersions:
    """Tests for getting project versions."""

    @patch('get_versions.get_jira_client')
    def test_get_all_versions(self, mock_get_client, mock_jira_client, sample_versions_list):
        """Test getting all versions for a project."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import get_versions

        result = get_versions('PROJ', profile=None)

        assert len(result) == 4
        mock_jira_client.get_versions.assert_called_once_with('PROJ')

    @patch('get_versions.get_jira_client')
    def test_get_version_by_id(self, mock_get_client, mock_jira_client, sample_version):
        """Test getting a specific version by ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version.return_value = copy.deepcopy(sample_version)

        from get_versions import get_version_by_id

        result = get_version_by_id('10000', profile=None)

        assert result['id'] == '10000'
        assert result['name'] == 'v1.0.0'
        mock_jira_client.get_version.assert_called_once_with('10000')

    @patch('get_versions.get_jira_client')
    def test_filter_released_versions(self, mock_get_client, mock_jira_client, sample_versions_list):
        """Test filtering for released versions."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import get_versions, filter_versions

        versions = get_versions('PROJ', profile=None)
        released = filter_versions(versions, released=True)

        # 2 released versions in sample_versions_list (v0.9.0, v0.5.0)
        assert len(released) == 2
        assert all(v['released'] is True for v in released)

    @patch('get_versions.get_jira_client')
    def test_filter_unreleased_versions(self, mock_get_client, mock_jira_client, sample_versions_list):
        """Test filtering for unreleased versions."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import get_versions, filter_versions

        versions = get_versions('PROJ', profile=None)
        unreleased = filter_versions(versions, released=False)

        # 2 unreleased versions in sample_versions_list (v1.2.0, v1.0.0)
        assert len(unreleased) == 2
        assert all(not v['released'] for v in unreleased)

    @patch('get_versions.get_jira_client')
    def test_filter_archived_versions(self, mock_get_client, mock_jira_client, sample_versions_list):
        """Test filtering for archived versions."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import get_versions, filter_versions

        versions = get_versions('PROJ', profile=None)
        archived = filter_versions(versions, archived=True)

        # 1 archived version in sample_versions_list
        assert len(archived) == 1
        assert archived[0]['archived'] is True

    @patch('get_versions.get_jira_client')
    def test_get_version_issue_counts(self, mock_get_client, mock_jira_client, sample_version_issue_counts):
        """Test getting issue counts for a version."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version_issue_counts.return_value = copy.deepcopy(sample_version_issue_counts)

        from get_versions import get_version_issue_counts

        result = get_version_issue_counts('10000', profile=None)

        assert result['issuesFixedCount'] == 45
        assert result['issuesAffectedCount'] == 12

    @patch('get_versions.get_jira_client')
    def test_get_version_unresolved_count(self, mock_get_client, mock_jira_client, sample_version_unresolved_count):
        """Test getting unresolved issue count for a version."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_version_unresolved_count.return_value = copy.deepcopy(sample_version_unresolved_count)

        from get_versions import get_version_unresolved_count

        result = get_version_unresolved_count('10000', profile=None)

        assert result['issuesUnresolvedCount'] == 3
        assert result['issuesCount'] == 48

    @patch('get_versions.get_jira_client')
    def test_versions_table_output(self, mock_get_client, mock_jira_client, sample_versions_list, capsys):
        """Test table output format for versions."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.return_value = copy.deepcopy(sample_versions_list)

        from get_versions import display_versions_table

        display_versions_table(sample_versions_list)

        captured = capsys.readouterr()
        assert 'v1.2.0' in captured.out
        assert 'v1.0.0' in captured.out
        assert 'v0.9.0' in captured.out


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetVersionsErrorHandling:
    """Test API error handling for get_versions."""

    @patch('get_versions.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = AuthenticationError("Invalid token")

        from get_versions import get_versions

        with pytest.raises(AuthenticationError):
            get_versions('PROJ', profile=None)

    @patch('get_versions.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = PermissionError("Cannot view versions")

        from get_versions import get_versions

        with pytest.raises(PermissionError):
            get_versions('PROJ', profile=None)

    @patch('get_versions.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when project doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = NotFoundError("Project", "INVALID")

        from get_versions import get_versions

        with pytest.raises(NotFoundError):
            get_versions('INVALID', profile=None)

    @patch('get_versions.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_versions import get_versions

        with pytest.raises(JiraError) as exc_info:
            get_versions('PROJ', profile=None)
        assert exc_info.value.status_code == 429

    @patch('get_versions.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_versions.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_versions import get_versions

        with pytest.raises(JiraError) as exc_info:
            get_versions('PROJ', profile=None)
        assert exc_info.value.status_code == 500
