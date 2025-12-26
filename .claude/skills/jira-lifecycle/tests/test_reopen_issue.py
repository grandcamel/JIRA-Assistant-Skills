"""
Tests for reopen_issue.py - Reopen a closed/resolved issue.
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
class TestReopenIssue:
    """Tests for reopening issues."""

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_success(self, mock_get_client, mock_jira_client):
        """Test reopening a resolved issue."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'Reopen', 'to': {'name': 'Open'}},
            {'id': '21', 'name': 'Start Progress', 'to': {'name': 'In Progress'}}
        ]

        from reopen_issue import reopen_issue

        reopen_issue('PROJ-123', profile=None)

        mock_jira_client.transition_issue.assert_called_once()
        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[0][1] == '11'  # Reopen transition ID

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_with_comment(self, mock_get_client, mock_jira_client):
        """Test reopening with a comment."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'Reopen', 'to': {'name': 'Open'}}
        ]

        from reopen_issue import reopen_issue

        reopen_issue('PROJ-123', comment='Regression found', profile=None)

        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[1]['fields'] is not None

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_uses_todo_fallback(self, mock_get_client, mock_jira_client):
        """Test falling back to To Do transition when no Reopen."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'To Do', 'to': {'name': 'To Do'}},
            {'id': '21', 'name': 'Done', 'to': {'name': 'Done'}}
        ]

        from reopen_issue import reopen_issue

        reopen_issue('PROJ-123', profile=None)

        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[0][1] == '11'  # To Do transition ID

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_uses_backlog_fallback(self, mock_get_client, mock_jira_client):
        """Test falling back to Backlog transition when no Reopen or To Do."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'Backlog', 'to': {'name': 'Backlog'}},
            {'id': '21', 'name': 'Done', 'to': {'name': 'Done'}}
        ]

        from reopen_issue import reopen_issue

        reopen_issue('PROJ-123', profile=None)

        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[0][1] == '11'  # Backlog transition ID

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_no_transitions(self, mock_get_client, mock_jira_client):
        """Test error when no transitions available."""
        from error_handler import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = []

        from reopen_issue import reopen_issue

        with pytest.raises(ValidationError, match="No transitions available"):
            reopen_issue('PROJ-123', profile=None)

    @patch('reopen_issue.get_jira_client')
    def test_reopen_issue_no_reopen_transition(self, mock_get_client, mock_jira_client):
        """Test error when no reopen transition found."""
        from error_handler import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '21', 'name': 'Done', 'to': {'name': 'Done'}},
            {'id': '31', 'name': 'Close', 'to': {'name': 'Closed'}}
        ]

        from reopen_issue import reopen_issue

        with pytest.raises(ValidationError, match="No reopen transition"):
            reopen_issue('PROJ-123', profile=None)

    def test_reopen_issue_invalid_key(self):
        """Test error on invalid issue key."""
        from error_handler import ValidationError
        from reopen_issue import reopen_issue

        with pytest.raises(ValidationError):
            reopen_issue('invalid', profile=None)


@pytest.mark.lifecycle
@pytest.mark.unit
class TestReopenIssueErrorHandling:
    """Test API error handling for reopen_issue."""

    @patch('reopen_issue.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from error_handler import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = AuthenticationError("Invalid token")

        from reopen_issue import reopen_issue

        with pytest.raises(AuthenticationError):
            reopen_issue('PROJ-123', profile=None)

    @patch('reopen_issue.get_jira_client')
    def test_permission_denied(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from error_handler import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'Reopen', 'to': {'name': 'Open'}}
        ]
        mock_jira_client.transition_issue.side_effect = PermissionError("Cannot transition")

        from reopen_issue import reopen_issue

        with pytest.raises(PermissionError):
            reopen_issue('PROJ-123', profile=None)

    @patch('reopen_issue.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when issue doesn't exist."""
        from error_handler import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = NotFoundError("Issue", "PROJ-999")

        from reopen_issue import reopen_issue

        with pytest.raises(NotFoundError):
            reopen_issue('PROJ-999', profile=None)

    @patch('reopen_issue.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from reopen_issue import reopen_issue

        with pytest.raises(JiraError) as exc_info:
            reopen_issue('PROJ-123', profile=None)
        assert exc_info.value.status_code == 429

    @patch('reopen_issue.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from error_handler import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from reopen_issue import reopen_issue

        with pytest.raises(JiraError) as exc_info:
            reopen_issue('PROJ-123', profile=None)
        assert exc_info.value.status_code == 500
