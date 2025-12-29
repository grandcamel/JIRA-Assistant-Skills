"""
Unit Tests: list_fields.py

Tests for listing JIRA custom fields.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Path setup
_this_dir = Path(__file__).parent
_tests_dir = _this_dir.parent
_jira_fields_dir = _tests_dir.parent
_scripts_dir = _jira_fields_dir / 'scripts'
_shared_lib_dir = _jira_fields_dir.parent / 'shared' / 'scripts' / 'lib'

for path in [str(_shared_lib_dir), str(_scripts_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from list_fields import list_fields, AGILE_PATTERNS
from jira_assistant_skills_lib import JiraError, AuthenticationError


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsBasic:
    """Test basic list_fields functionality."""

    def test_list_all_custom_fields(self, mock_jira_client, sample_fields_response):
        """Test listing all custom fields."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(client=mock_jira_client)

        assert result is not None
        assert isinstance(result, list)
        # Should only return custom fields (5 of 7)
        assert len(result) == 5
        mock_jira_client.get.assert_called_once_with('/rest/api/3/field')

    def test_list_includes_system_fields(self, mock_jira_client, sample_fields_response):
        """Test listing all fields including system fields."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(custom_only=False, client=mock_jira_client)

        assert result is not None
        # Should return all 7 fields
        assert len(result) == 7
        system_fields = [f for f in result if not f['id'].startswith('customfield_')]
        assert len(system_fields) == 2

    def test_list_fields_structure(self, mock_jira_client, sample_fields_response):
        """Test that returned fields have correct structure."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(client=mock_jira_client)

        for field in result:
            assert 'id' in field
            assert 'name' in field
            assert 'type' in field
            assert 'custom' in field
            assert 'searchable' in field
            assert 'navigable' in field

    def test_list_fields_sorted_by_name(self, mock_jira_client, sample_fields_response):
        """Test that fields are sorted alphabetically by name."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(client=mock_jira_client)

        names = [f['name'] for f in result]
        assert names == sorted(names, key=str.lower)


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsFiltering:
    """Test list_fields filtering options."""

    def test_filter_by_pattern(self, mock_jira_client, sample_fields_response):
        """Test filtering fields by name pattern."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(filter_pattern='epic', client=mock_jira_client)

        assert len(result) == 2  # Epic Link and Epic Name
        for field in result:
            assert 'epic' in field['name'].lower()

    def test_filter_case_insensitive(self, mock_jira_client, sample_fields_response):
        """Test that filtering is case-insensitive."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(filter_pattern='SPRINT', client=mock_jira_client)

        assert len(result) == 1
        assert result[0]['name'] == 'Sprint'

    def test_filter_no_matches(self, mock_jira_client, sample_fields_response):
        """Test filtering with no matches returns empty list."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(filter_pattern='nonexistent', client=mock_jira_client)

        assert result == []

    def test_agile_only_filter(self, mock_jira_client, sample_fields_response):
        """Test filtering for Agile-related fields only."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(agile_only=True, client=mock_jira_client)

        # Sprint, Story Points, Epic Link, Epic Name, Rank
        assert len(result) == 5
        for field in result:
            name_lower = field['name'].lower()
            assert any(pattern in name_lower for pattern in AGILE_PATTERNS)

    def test_combined_filters(self, mock_jira_client, sample_fields_response):
        """Test combining filter pattern with agile_only."""
        mock_jira_client.get.return_value = sample_fields_response

        result = list_fields(filter_pattern='sprint', agile_only=True, client=mock_jira_client)

        assert len(result) == 1
        assert result[0]['name'] == 'Sprint'


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsEmptyResults:
    """Test list_fields with empty or no results."""

    def test_empty_fields_response(self, mock_jira_client):
        """Test handling of empty fields response."""
        mock_jira_client.get.return_value = []

        result = list_fields(client=mock_jira_client)

        assert result == []

    def test_no_custom_fields(self, mock_jira_client):
        """Test when no custom fields exist."""
        mock_jira_client.get.return_value = [
            {'id': 'summary', 'name': 'Summary', 'custom': False,
             'searchable': True, 'navigable': True, 'schema': {'type': 'string'}}
        ]

        result = list_fields(custom_only=True, client=mock_jira_client)

        assert result == []


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsErrorHandling:
    """Test error handling in list_fields."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 authentication error."""
        mock_jira_client.get.side_effect = AuthenticationError("Invalid token")

        with pytest.raises(AuthenticationError):
            list_fields(client=mock_jira_client)

    def test_permission_denied_error(self, mock_jira_client):
        """Test handling of 403 permission denied."""
        mock_jira_client.get.side_effect = JiraError("Permission denied", status_code=403)

        with pytest.raises(JiraError) as exc_info:
            list_fields(client=mock_jira_client)
        assert exc_info.value.status_code == 403

    def test_not_found_error(self, mock_jira_client):
        """Test handling of 404 not found."""
        mock_jira_client.get.side_effect = JiraError("Not found", status_code=404)

        with pytest.raises(JiraError) as exc_info:
            list_fields(client=mock_jira_client)
        assert exc_info.value.status_code == 404

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        mock_jira_client.get.side_effect = JiraError("Rate limit exceeded", status_code=429)

        with pytest.raises(JiraError) as exc_info:
            list_fields(client=mock_jira_client)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 server error."""
        mock_jira_client.get.side_effect = JiraError("Server error", status_code=500)

        with pytest.raises(JiraError) as exc_info:
            list_fields(client=mock_jira_client)
        assert exc_info.value.status_code == 500


@pytest.mark.fields
@pytest.mark.unit
class TestListFieldsClientManagement:
    """Test client lifecycle management."""

    def test_closes_client_on_success(self, sample_fields_response):
        """Test that client is closed after successful operation."""
        mock_client = MagicMock()
        mock_client.get.return_value = sample_fields_response

        with patch('list_fields.get_jira_client', return_value=mock_client):
            list_fields()

        mock_client.close.assert_called_once()

    def test_closes_client_on_error(self):
        """Test that client is closed even when operation fails."""
        mock_client = MagicMock()
        mock_client.get.side_effect = JiraError("Test error")

        with patch('list_fields.get_jira_client', return_value=mock_client):
            with pytest.raises(JiraError):
                list_fields()

        mock_client.close.assert_called_once()

    def test_does_not_close_provided_client(self, mock_jira_client, sample_fields_response):
        """Test that provided client is not closed."""
        mock_jira_client.get.return_value = sample_fields_response

        list_fields(client=mock_jira_client)

        mock_jira_client.close.assert_not_called()
