"""
Tests for update_custom_fields.py - Update custom fields on issues.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.collaborate
@pytest.mark.unit
class TestUpdateCustomFields:
    """Tests for updating custom fields."""

    @patch('update_custom_fields.get_jira_client')
    def test_update_single_field(self, mock_get_client, mock_jira_client):
        """Test updating a single custom field."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from update_custom_fields import update_custom_fields

        update_custom_fields('PROJ-123', field='customfield_10001', value='Production', profile=None)

        mock_jira_client.update_issue.assert_called_once()
        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][0] == 'PROJ-123'
        assert call_args[0][1] == {'customfield_10001': 'Production'}

    @patch('update_custom_fields.get_jira_client')
    def test_update_multiple_fields_json(self, mock_get_client, mock_jira_client):
        """Test updating multiple fields via JSON."""
        import json
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from update_custom_fields import update_custom_fields

        fields_json = json.dumps({
            'customfield_10001': 'Production',
            'customfield_10002': 'High'
        })

        update_custom_fields('PROJ-123', fields_json=fields_json, profile=None)

        call_args = mock_jira_client.update_issue.call_args
        assert 'customfield_10001' in call_args[0][1]
        assert 'customfield_10002' in call_args[0][1]

    @patch('update_custom_fields.get_jira_client')
    def test_update_field_json_value(self, mock_get_client, mock_jira_client):
        """Test updating field with JSON value (e.g., select field)."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.return_value = None

        from update_custom_fields import update_custom_fields

        # JSON value for select field
        update_custom_fields('PROJ-123', field='customfield_10001', value='{"value": "Option A"}', profile=None)

        call_args = mock_jira_client.update_issue.call_args
        assert call_args[0][1]['customfield_10001'] == {'value': 'Option A'}

    def test_update_no_fields_specified(self):
        """Test error when no fields specified."""
        from error_handler import ValidationError

        from update_custom_fields import update_custom_fields

        with pytest.raises(ValidationError):
            update_custom_fields('PROJ-123', profile=None)

    def test_update_invalid_issue_key(self):
        """Test error for invalid issue key."""
        from error_handler import ValidationError

        from update_custom_fields import update_custom_fields

        with pytest.raises(ValidationError):
            update_custom_fields('invalid', field='customfield_10001', value='test', profile=None)


@pytest.mark.collaborate
@pytest.mark.unit
class TestUpdateCustomFieldsErrorHandling:
    """Test API error handling scenarios for update_custom_fields."""

    @patch('update_custom_fields.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.side_effect = AuthenticationError("Invalid API token")

        from update_custom_fields import update_custom_fields

        with pytest.raises(AuthenticationError):
            update_custom_fields('PROJ-123', field='customfield_10001', value='test', profile=None)

    @patch('update_custom_fields.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.side_effect = PermissionError("No permission to update issue")

        from update_custom_fields import update_custom_fields

        with pytest.raises(PermissionError):
            update_custom_fields('PROJ-123', field='customfield_10001', value='test', profile=None)

    @patch('update_custom_fields.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 not found."""
        from error_handler import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.side_effect = NotFoundError("Issue PROJ-999 not found")

        from update_custom_fields import update_custom_fields

        with pytest.raises(NotFoundError):
            update_custom_fields('PROJ-999', field='customfield_10001', value='test', profile=None)

    @patch('update_custom_fields.get_jira_client')
    def test_field_not_found(self, mock_get_client, mock_jira_client):
        """Test error when field doesn't exist."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.side_effect = JiraError("Field 'customfield_99999' does not exist", status_code=400)

        from update_custom_fields import update_custom_fields

        with pytest.raises(JiraError):
            update_custom_fields('PROJ-123', field='customfield_99999', value='test', profile=None)

    @patch('update_custom_fields.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.side_effect = JiraError("Rate limit exceeded", status_code=429)

        from update_custom_fields import update_custom_fields

        with pytest.raises(JiraError) as exc_info:
            update_custom_fields('PROJ-123', field='customfield_10001', value='test', profile=None)
        assert exc_info.value.status_code == 429

    @patch('update_custom_fields.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.update_issue.side_effect = JiraError("Internal server error", status_code=500)

        from update_custom_fields import update_custom_fields

        with pytest.raises(JiraError) as exc_info:
            update_custom_fields('PROJ-123', field='customfield_10001', value='test', profile=None)
        assert exc_info.value.status_code == 500
