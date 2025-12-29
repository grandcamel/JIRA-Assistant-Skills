"""
Tests for get_activity.py - Get issue activity/changelog.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.collaborate
@pytest.mark.unit
class TestGetActivity:
    """Tests for getting issue activity/changelog."""

    @patch('get_activity.get_jira_client')
    def test_get_all_activity(self, mock_get_client, mock_jira_client, sample_changelog):
        """Test getting all activity for an issue."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.return_value = sample_changelog

        from get_activity import get_activity

        result = get_activity('PROJ-123', profile=None)

        assert result['total'] == 5
        assert len(result['values']) == 5
        mock_jira_client.get_changelog.assert_called_once()

    @patch('get_activity.get_jira_client')
    def test_activity_pagination(self, mock_get_client, mock_jira_client, sample_changelog):
        """Test pagination of activity."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.return_value = sample_changelog

        from get_activity import get_activity

        result = get_activity('PROJ-123', limit=2, offset=1, profile=None)

        call_args = mock_jira_client.get_changelog.call_args
        assert call_args[1]['max_results'] == 2
        assert call_args[1]['start_at'] == 1

    @patch('get_activity.get_jira_client')
    def test_parse_status_change(self, mock_get_client, mock_jira_client, sample_changelog):
        """Test parsing status change in activity."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.return_value = sample_changelog

        from get_activity import parse_changelog

        parsed = parse_changelog(sample_changelog)

        # First change is status change (In Progress → Done)
        status_change = parsed[0]
        assert status_change['type'] == 'status'
        assert status_change['field'] == 'status'
        assert status_change['from'] == 'In Progress'
        assert status_change['to'] == 'Done'

    @patch('get_activity.get_jira_client')
    def test_parse_assignee_change(self, mock_get_client, mock_jira_client, sample_changelog):
        """Test parsing assignee change in activity."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.return_value = sample_changelog

        from get_activity import parse_changelog

        parsed = parse_changelog(sample_changelog)

        # Third change is assignee change (None → Alice Smith)
        assignee_change = parsed[2]
        assert assignee_change['type'] == 'assignee'
        assert assignee_change['field'] == 'assignee'
        assert assignee_change['from'] == ''
        assert assignee_change['to'] == 'Alice Smith'

    @patch('get_activity.get_jira_client')
    def test_parse_priority_change(self, mock_get_client, mock_jira_client, sample_changelog):
        """Test parsing priority change in activity."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.return_value = sample_changelog

        from get_activity import parse_changelog

        parsed = parse_changelog(sample_changelog)

        # Last change is priority change (Medium → High)
        priority_change = parsed[5]
        assert priority_change['type'] == 'priority'
        assert priority_change['field'] == 'priority'
        assert priority_change['from'] == 'Medium'
        assert priority_change['to'] == 'High'

    @patch('get_activity.get_jira_client')
    def test_filter_by_change_type(self, mock_get_client, mock_jira_client, sample_changelog):
        """Test filtering activity by change type."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.return_value = sample_changelog

        from get_activity import get_activity, parse_changelog

        result = get_activity('PROJ-123', profile=None)
        parsed = parse_changelog(result)

        # Filter only status changes (there are 2 in the fixture)
        status_changes = [c for c in parsed if c['type'] == 'status']
        assert len(status_changes) == 2
        assert status_changes[0]['field'] == 'status'

    @patch('get_activity.get_jira_client')
    def test_activity_table_output(self, mock_get_client, mock_jira_client, sample_changelog, capsys):
        """Test table output format for activity."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.return_value = sample_changelog

        from get_activity import display_activity_table, parse_changelog

        parsed = parse_changelog(sample_changelog)
        display_activity_table(parsed)

        captured = capsys.readouterr()
        assert 'status' in captured.out
        assert 'Done' in captured.out
        assert 'In Progress' in captured.out

    @patch('get_activity.get_jira_client')
    def test_activity_json_output(self, mock_get_client, mock_jira_client, sample_changelog):
        """Test JSON output format for activity."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.return_value = sample_changelog

        from get_activity import parse_changelog
        import json

        parsed = parse_changelog(sample_changelog)
        json_output = json.dumps(parsed, indent=2)

        # Should be valid JSON with 6 individual changes
        parsed_json = json.loads(json_output)
        assert len(parsed_json) == 6
        assert parsed_json[0]['field'] == 'status'


@pytest.mark.collaborate
@pytest.mark.unit
class TestGetActivityErrorHandling:
    """Test API error handling scenarios for get_activity."""

    @patch('get_activity.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.side_effect = AuthenticationError("Invalid API token")

        from get_activity import get_activity

        with pytest.raises(AuthenticationError):
            get_activity('PROJ-123', profile=None)

    @patch('get_activity.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.side_effect = PermissionError("No permission to view activity")

        from get_activity import get_activity

        with pytest.raises(PermissionError):
            get_activity('PROJ-123', profile=None)

    @patch('get_activity.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.side_effect = NotFoundError("Issue PROJ-999 not found")

        from get_activity import get_activity

        with pytest.raises(NotFoundError):
            get_activity('PROJ-999', profile=None)

    @patch('get_activity.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.side_effect = JiraError("Rate limit exceeded", status_code=429)

        from get_activity import get_activity

        with pytest.raises(JiraError) as exc_info:
            get_activity('PROJ-123', profile=None)
        assert exc_info.value.status_code == 429

    @patch('get_activity.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_changelog.side_effect = JiraError("Internal server error", status_code=500)

        from get_activity import get_activity

        with pytest.raises(JiraError) as exc_info:
            get_activity('PROJ-123', profile=None)
        assert exc_info.value.status_code == 500
