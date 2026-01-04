"""
Unit Tests: configure_agile_fields.py

Tests for configuring Agile fields for projects.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Path setup
_this_dir = Path(__file__).parent
_tests_dir = _this_dir.parent
_jira_fields_dir = _tests_dir.parent
_scripts_dir = _jira_fields_dir / 'scripts'
_shared_lib_dir = _jira_fields_dir.parent / 'shared' / 'scripts' / 'lib'

for path in [str(_shared_lib_dir), str(_scripts_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from configure_agile_fields import (
    configure_agile_fields,
    find_agile_fields,
    find_project_screens,
    add_field_to_screen
)
from jira_assistant_skills_lib import JiraError, AuthenticationError
from assistant_skills_lib.error_handler import ValidationError


@pytest.mark.fields
@pytest.mark.unit
class TestFindAgileFields:
    """Test find_agile_fields helper function."""

    def test_find_all_agile_fields(self, mock_jira_client, sample_fields_response):
        """Test finding all Agile fields."""
        mock_jira_client.get.return_value = sample_fields_response

        result = find_agile_fields(mock_jira_client)

        assert result['story_points'] == 'customfield_10002'
        assert result['epic_link'] == 'customfield_10003'
        assert result['sprint'] == 'customfield_10001'
        assert result['epic_name'] == 'customfield_10004'

    def test_find_no_agile_fields(self, mock_jira_client):
        """Test when no Agile fields exist."""
        mock_jira_client.get.return_value = [
            {'id': 'summary', 'name': 'Summary', 'custom': False}
        ]

        result = find_agile_fields(mock_jira_client)

        assert result['story_points'] is None
        assert result['epic_link'] is None
        assert result['sprint'] is None
        assert result['epic_name'] is None

    def test_find_partial_agile_fields(self, mock_jira_client):
        """Test finding only some Agile fields."""
        mock_jira_client.get.return_value = [
            {'id': 'customfield_10001', 'name': 'Sprint', 'custom': True}
        ]

        result = find_agile_fields(mock_jira_client)

        assert result['sprint'] == 'customfield_10001'
        assert result['story_points'] is None


@pytest.mark.fields
@pytest.mark.unit
class TestFindProjectScreens:
    """Test find_project_screens helper function."""

    def test_find_screens_with_scheme(
        self,
        mock_jira_client,
        sample_project_response,
        sample_screen_schemes_response,
        sample_screen_scheme_mapping,
        sample_screen_scheme,
        sample_screen
    ):
        """Test finding screens when project has screen scheme."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_screen_schemes_response,
            sample_screen_scheme_mapping,
            sample_screen_scheme,
            sample_screen,
            sample_screen,
            sample_screen
        ]

        result = find_project_screens(mock_jira_client, 'TEST')

        assert isinstance(result, list)
        assert len(result) > 0

    def test_find_screens_no_scheme_uses_default(self, mock_jira_client, sample_project_response, sample_all_screens):
        """Test fallback to default screen when no scheme found."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            {'values': []},  # No screen schemes
            sample_all_screens   # All screens
        ]

        result = find_project_screens(mock_jira_client, 'TEST')

        assert isinstance(result, list)


@pytest.mark.fields
@pytest.mark.unit
class TestAddFieldToScreen:
    """Test add_field_to_screen helper function."""

    def test_add_field_success(self, mock_jira_client, sample_screen_tabs, sample_screen_fields):
        """Test successfully adding a field to a screen."""
        mock_jira_client.get.side_effect = [sample_screen_tabs, sample_screen_fields]
        mock_jira_client.post.return_value = {}

        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002')

        assert result is True
        mock_jira_client.post.assert_called_once()

    def test_add_field_already_exists(self, mock_jira_client, sample_screen_tabs):
        """Test adding a field that already exists on screen."""
        fields_with_target = [{'id': 'customfield_10002', 'name': 'Story Points'}]
        mock_jira_client.get.side_effect = [sample_screen_tabs, fields_with_target]

        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002')

        assert result is True
        mock_jira_client.post.assert_not_called()

    def test_add_field_dry_run(self, mock_jira_client):
        """Test dry-run mode does not make changes."""
        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002', dry_run=True)

        assert result is True
        mock_jira_client.get.assert_not_called()
        mock_jira_client.post.assert_not_called()

    def test_add_field_no_tabs(self, mock_jira_client):
        """Test handling when screen has no tabs."""
        mock_jira_client.get.return_value = []

        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002')

        assert result is False

    def test_add_field_api_error(self, mock_jira_client, sample_screen_tabs, sample_screen_fields):
        """Test handling of API error when adding field."""
        mock_jira_client.get.side_effect = [sample_screen_tabs, sample_screen_fields]
        mock_jira_client.post.side_effect = JiraError("Failed to add field")

        result = add_field_to_screen(mock_jira_client, 10001, 'customfield_10002')

        assert result is False


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsBasic:
    """Test basic configure_agile_fields functionality."""

    def test_configure_agile_fields_success(
        self,
        sample_project_response,
        sample_fields_response,
        sample_all_screens
    ):
        """Test successful Agile field configuration."""
        # Use a fresh MagicMock with a dynamic side_effect function
        # to return appropriate responses based on the URL
        mock_client = MagicMock()
        call_count = [0]

        def get_side_effect(url, params=None):
            call_count[0] += 1
            if '/rest/api/3/project/' in url and '/issuetypescreenscheme' not in url:
                return sample_project_response
            if url == '/rest/api/3/field':
                return sample_fields_response
            if '/issuetypescreenscheme/project' in url:
                return {'values': []}  # No screen schemes, use default
            if url == '/rest/api/3/screens':
                return sample_all_screens
            if '/screens/' in url and '/tabs' in url:
                return [{'id': 10001, 'name': 'Field Tab'}]
            if '/fields' in url:
                return [{'id': 'summary', 'name': 'Summary'}]  # No conflicting fields
            return {}

        mock_client.get.side_effect = get_side_effect
        mock_client.post.return_value = {}
        mock_client.close = MagicMock()

        result = configure_agile_fields(project_key='TEST', client=mock_client)

        assert result is not None
        assert result['project'] == 'TEST'
        assert result['dry_run'] is False
        assert 'fields_found' in result
        assert 'screens_found' in result
        assert 'fields_added' in result


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsDryRun:
    """Test dry-run functionality."""

    def test_configure_dry_run_no_changes(
        self,
        mock_jira_client,
        sample_project_response,
        sample_fields_response,
        sample_screen_schemes_response,
        sample_screen_scheme_mapping,
        sample_screen_scheme,
        sample_screen
    ):
        """Test dry-run mode shows preview without changes."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            sample_fields_response,
            sample_project_response,
            sample_screen_schemes_response,
            sample_screen_scheme_mapping,
            sample_screen_scheme,
            sample_screen,
            sample_screen,
            sample_screen
        ]

        result = configure_agile_fields(
            project_key='TEST',
            dry_run=True,
            client=mock_jira_client
        )

        assert result['dry_run'] is True
        # No POST calls should be made in dry-run
        mock_jira_client.post.assert_not_called()


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsValidation:
    """Test validation in configure_agile_fields."""

    def test_reject_team_managed_project(self, mock_jira_client, sample_project_team_managed):
        """Test that team-managed projects are rejected."""
        mock_jira_client.get.return_value = sample_project_team_managed

        with pytest.raises(ValidationError) as exc_info:
            configure_agile_fields(project_key='TEAM', client=mock_jira_client)

        assert 'team-managed' in str(exc_info.value).lower()

    def test_no_agile_fields_found(self, mock_jira_client, sample_project_response):
        """Test error when no Agile fields exist in instance."""
        mock_jira_client.get.side_effect = [
            sample_project_response,
            [{'id': 'summary', 'name': 'Summary', 'custom': False}]  # No agile fields
        ]

        with pytest.raises(ValidationError) as exc_info:
            configure_agile_fields(project_key='TEST', client=mock_jira_client)

        assert 'no agile fields' in str(exc_info.value).lower()


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsErrorHandling:
    """Test error handling in configure_agile_fields."""

    def test_project_not_found(self, mock_jira_client):
        """Test handling of non-existent project."""
        mock_jira_client.get.side_effect = JiraError("Project not found", status_code=404)

        with pytest.raises(JiraError) as exc_info:
            configure_agile_fields(project_key='NOTEXIST', client=mock_jira_client)
        assert exc_info.value.status_code == 404

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        mock_jira_client.get.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            configure_agile_fields(project_key='TEST', client=mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        mock_jira_client.get.side_effect = JiraError("Permission denied", status_code=403)

        with pytest.raises(JiraError) as exc_info:
            configure_agile_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 403

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        mock_jira_client.get.side_effect = JiraError("Rate limit exceeded", status_code=429)

        with pytest.raises(JiraError) as exc_info:
            configure_agile_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        mock_jira_client.get.side_effect = JiraError("Server error", status_code=500)

        with pytest.raises(JiraError) as exc_info:
            configure_agile_fields(project_key='TEST', client=mock_jira_client)
        assert exc_info.value.status_code == 500


@pytest.mark.fields
@pytest.mark.unit
class TestConfigureAgileFieldsClientManagement:
    """Test client lifecycle management."""

    def test_does_not_close_provided_client(
        self,
        sample_project_response,
        sample_fields_response,
        sample_all_screens
    ):
        """Test that provided client is not closed."""
        # Use a fresh MagicMock with a dynamic side_effect function
        mock_client = MagicMock()

        def get_side_effect(url, params=None):
            if '/rest/api/3/project/' in url and '/issuetypescreenscheme' not in url:
                return sample_project_response
            if url == '/rest/api/3/field':
                return sample_fields_response
            if '/issuetypescreenscheme/project' in url:
                return {'values': []}  # No screen schemes, use default
            if url == '/rest/api/3/screens':
                return sample_all_screens
            if '/screens/' in url and '/tabs' in url:
                return [{'id': 10001, 'name': 'Field Tab'}]
            if '/fields' in url:
                return [{'id': 'summary', 'name': 'Summary'}]
            return {}

        mock_client.get.side_effect = get_side_effect
        mock_client.post.return_value = {}
        mock_client.close = MagicMock()

        configure_agile_fields(project_key='TEST', client=mock_client)

        mock_client.close.assert_not_called()
