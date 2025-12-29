"""
Tests for resolve_issue.py - Resolve a JIRA issue.
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
class TestResolveIssue:
    """Tests for resolving issues."""

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_success(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test resolving an issue with default resolution."""
        transitions = copy.deepcopy(sample_transitions)
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = transitions

        from resolve_issue import resolve_issue

        resolve_issue('PROJ-123', resolution='Fixed', profile=None)

        mock_jira_client.transition_issue.assert_called_once()
        call_args = mock_jira_client.transition_issue.call_args
        assert call_args[0][0] == 'PROJ-123'
        assert call_args[1]['fields']['resolution'] == {'name': 'Fixed'}

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_with_comment(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test resolving an issue with a comment."""
        transitions = copy.deepcopy(sample_transitions)
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = transitions

        from resolve_issue import resolve_issue

        resolve_issue('PROJ-123', resolution='Fixed', comment='Bug fixed', profile=None)

        call_args = mock_jira_client.transition_issue.call_args
        assert 'comment' in call_args[1]['fields']

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_picks_done_transition(self, mock_get_client, mock_jira_client):
        """Test that Done transition is selected for resolution."""
        transitions = [
            {'id': '11', 'name': 'To Do', 'to': {'name': 'To Do'}},
            {'id': '21', 'name': 'In Progress', 'to': {'name': 'In Progress'}},
            {'id': '31', 'name': 'Done', 'to': {'name': 'Done'}},
        ]
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = transitions

        from resolve_issue import resolve_issue

        resolve_issue('PROJ-123', resolution='Fixed', profile=None)

        call_args = mock_jira_client.transition_issue.call_args
        # Should pick "Done" transition (id=31)
        assert call_args[0][1] == '31'

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_no_transitions(self, mock_get_client, mock_jira_client):
        """Test error when no transitions available."""
        from jira_assistant_skills_lib import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = []

        from resolve_issue import resolve_issue

        with pytest.raises(ValidationError, match="No transitions available"):
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)

    @patch('resolve_issue.get_jira_client')
    def test_resolve_issue_no_resolve_transition(self, mock_get_client, mock_jira_client):
        """Test error when no resolution transition found."""
        from jira_assistant_skills_lib import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = [
            {'id': '11', 'name': 'To Do', 'to': {'name': 'To Do'}},
            {'id': '21', 'name': 'In Progress', 'to': {'name': 'In Progress'}}
        ]

        from resolve_issue import resolve_issue

        with pytest.raises(ValidationError, match="No resolution transition"):
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)

    def test_resolve_issue_invalid_key(self):
        """Test error on invalid issue key."""
        from jira_assistant_skills_lib import ValidationError
        from resolve_issue import resolve_issue

        with pytest.raises(ValidationError):
            resolve_issue('invalid', resolution='Fixed', profile=None)


@pytest.mark.lifecycle
@pytest.mark.unit
class TestResolveIssueErrorHandling:
    """Test API error handling for resolve_issue."""

    @patch('resolve_issue.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = AuthenticationError("Invalid token")

        from resolve_issue import resolve_issue

        with pytest.raises(AuthenticationError):
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)

    @patch('resolve_issue.get_jira_client')
    def test_permission_denied(self, mock_get_client, mock_jira_client, sample_transitions):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.return_value = copy.deepcopy(sample_transitions)
        mock_jira_client.transition_issue.side_effect = PermissionError("Cannot transition")

        from resolve_issue import resolve_issue

        with pytest.raises(PermissionError):
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)

    @patch('resolve_issue.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when issue doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = NotFoundError("Issue", "PROJ-999")

        from resolve_issue import resolve_issue

        with pytest.raises(NotFoundError):
            resolve_issue('PROJ-999', resolution='Fixed', profile=None)

    @patch('resolve_issue.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from resolve_issue import resolve_issue

        with pytest.raises(JiraError) as exc_info:
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)
        assert exc_info.value.status_code == 429

    @patch('resolve_issue.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.get_transitions.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from resolve_issue import resolve_issue

        with pytest.raises(JiraError) as exc_info:
            resolve_issue('PROJ-123', resolution='Fixed', profile=None)
        assert exc_info.value.status_code == 500
