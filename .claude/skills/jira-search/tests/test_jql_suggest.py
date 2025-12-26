"""
Tests for jql_suggest.py - Get JQL field value suggestions.
"""

import pytest
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.search
@pytest.mark.unit
class TestSuggestValues:
    """Tests for JQL field value suggestions."""

    def test_suggest_project_values(self, mock_jira_client):
        """Test getting project name suggestions."""
        mock_jira_client.get_jql_suggestions.return_value = {
            'results': [
                {'value': 'PROJ', 'displayName': 'Test Project'},
                {'value': 'DEV', 'displayName': 'Development'}
            ]
        }

        from jql_suggest import get_suggestions

        suggestions = get_suggestions(mock_jira_client, 'project', use_cache=False)

        assert len(suggestions) == 2
        assert suggestions[0]['value'] == 'PROJ'
        mock_jira_client.get_jql_suggestions.assert_called_once_with('project', '')

    def test_suggest_status_values(self, mock_jira_client, sample_jql_suggestions):
        """Test getting status value suggestions."""
        mock_jira_client.get_jql_suggestions.return_value = sample_jql_suggestions

        from jql_suggest import get_suggestions

        suggestions = get_suggestions(mock_jira_client, 'status')

        assert len(suggestions) == 5
        assert any(s['value'] == 'Open' for s in suggestions)
        assert any(s['value'] == 'In Progress' for s in suggestions)

    def test_suggest_user_values(self, mock_jira_client):
        """Test getting user suggestions."""
        mock_jira_client.get_jql_suggestions.return_value = {
            'results': [
                {'value': 'john.smith', 'displayName': 'John Smith'},
                {'value': 'jane.doe', 'displayName': 'Jane Doe'}
            ]
        }

        from jql_suggest import get_suggestions

        suggestions = get_suggestions(mock_jira_client, 'assignee')

        assert len(suggestions) == 2
        assert any(s['value'] == 'john.smith' for s in suggestions)

    def test_suggest_with_prefix(self, mock_jira_client):
        """Test suggestions filtered by partial input."""
        mock_jira_client.get_jql_suggestions.return_value = {
            'results': [
                {'value': 'In Progress', 'displayName': 'In Progress'}
            ]
        }

        from jql_suggest import get_suggestions

        suggestions = get_suggestions(mock_jira_client, 'status', prefix='In Pr', use_cache=False)

        assert len(suggestions) == 1
        assert suggestions[0]['value'] == 'In Progress'
        mock_jira_client.get_jql_suggestions.assert_called_once_with('status', 'In Pr')

    def test_suggest_custom_field_values(self, mock_jira_client):
        """Test suggestions for custom select fields."""
        mock_jira_client.get_jql_suggestions.return_value = {
            'results': [
                {'value': 'Option A', 'displayName': 'Option A'},
                {'value': 'Option B', 'displayName': 'Option B'}
            ]
        }

        from jql_suggest import get_suggestions

        suggestions = get_suggestions(mock_jira_client, 'customfield_10000')

        assert len(suggestions) == 2

    def test_empty_suggestions(self, mock_jira_client):
        """Test handling fields with no suggestions."""
        mock_jira_client.get_jql_suggestions.return_value = {
            'results': []
        }

        from jql_suggest import get_suggestions

        suggestions = get_suggestions(mock_jira_client, 'summary')

        assert len(suggestions) == 0


@pytest.mark.search
@pytest.mark.unit
class TestJqlSuggestErrorHandling:
    """Test API error handling scenarios for jql_suggest."""

    def test_authentication_error(self, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_jira_client.get_jql_suggestions.side_effect = AuthenticationError(
            "Invalid API token"
        )

        from jql_suggest import get_suggestions

        with pytest.raises(AuthenticationError):
            get_suggestions(mock_jira_client, 'status', use_cache=False)

    def test_forbidden_error(self, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        mock_jira_client.get_jql_suggestions.side_effect = PermissionError(
            "You don't have permission to access this resource"
        )

        from jql_suggest import get_suggestions

        with pytest.raises(PermissionError):
            get_suggestions(mock_jira_client, 'status', use_cache=False)

    def test_rate_limit_error(self, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_jira_client.get_jql_suggestions.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from jql_suggest import get_suggestions

        with pytest.raises(JiraError) as exc_info:
            get_suggestions(mock_jira_client, 'status', use_cache=False)
        assert exc_info.value.status_code == 429

    def test_server_error(self, mock_jira_client):
        """Test handling of 500 internal server error."""
        from error_handler import JiraError
        mock_jira_client.get_jql_suggestions.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from jql_suggest import get_suggestions

        with pytest.raises(JiraError) as exc_info:
            get_suggestions(mock_jira_client, 'status', use_cache=False)
        assert exc_info.value.status_code == 500
