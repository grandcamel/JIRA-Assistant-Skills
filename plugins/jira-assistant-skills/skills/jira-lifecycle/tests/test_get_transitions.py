"""
Tests for get_transitions.py - Get available transitions for an issue.
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
class TestGetTransitions:
    """Tests for getting issue transitions."""

    @patch('get_transitions.get_jira_client')
    def test_get_transitions_success(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test getting transitions for an issue."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = copy.deepcopy(sample_transitions)

        from get_transitions import get_transitions

        result = get_transitions('PROJ-123', profile=None)

        assert len(result) == 3
        assert any(t['name'] == 'In Progress' for t in result)
        mock_jira_client.get_transitions.assert_called_once_with('PROJ-123')

    @patch('get_transitions.get_jira_client')
    def test_get_transitions_empty(self, mock_get_client, mock_jira_client):
        """Test handling when no transitions available."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = []

        from get_transitions import get_transitions

        result = get_transitions('PROJ-123', profile=None)

        assert result == []

    def test_get_transitions_invalid_issue_key(self):
        """Test error on invalid issue key."""
        from error_handler import ValidationError
        from get_transitions import get_transitions

        with pytest.raises(ValidationError):
            get_transitions('invalid', profile=None)

    @patch('get_transitions.get_jira_client')
    def test_get_transitions_with_profile(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test getting transitions with a specific profile."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = copy.deepcopy(sample_transitions)

        from get_transitions import get_transitions

        result = get_transitions('PROJ-123', profile='development')

        assert len(result) == 3
        mock_get_client.assert_called_once_with('development')


@pytest.mark.lifecycle
@pytest.mark.unit
class TestGetTransitionsErrorHandling:
    """Test API error handling for get_transitions."""

    @patch('get_transitions.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = AuthenticationError("Invalid token")

        from get_transitions import get_transitions

        with pytest.raises(AuthenticationError):
            get_transitions('PROJ-123', profile=None)

    @patch('get_transitions.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = PermissionError("Access denied")

        from get_transitions import get_transitions

        with pytest.raises(PermissionError):
            get_transitions('PROJ-123', profile=None)

    @patch('get_transitions.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when issue doesn't exist."""
        from error_handler import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = NotFoundError("Issue", "PROJ-999")

        from get_transitions import get_transitions

        with pytest.raises(NotFoundError):
            get_transitions('PROJ-999', profile=None)

    @patch('get_transitions.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from get_transitions import get_transitions

        with pytest.raises(JiraError) as exc_info:
            get_transitions('PROJ-123', profile=None)
        assert exc_info.value.status_code == 429

    @patch('get_transitions.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from get_transitions import get_transitions

        with pytest.raises(JiraError) as exc_info:
            get_transitions('PROJ-123', profile=None)
        assert exc_info.value.status_code == 500
