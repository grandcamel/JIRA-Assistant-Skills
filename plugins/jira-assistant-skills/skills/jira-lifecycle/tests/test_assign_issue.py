"""
Tests for assign_issue.py - Assign or reassign a JIRA issue.
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
class TestAssignIssue:
    """Tests for issue assignment."""

    @patch('assign_issue.get_jira_client')
    def test_assign_issue_by_account_id(self, mock_get_client, mock_jira_client):
        """Test assigning issue by account ID."""
        mock_get_client.return_value = mock_jira_client

        from assign_issue import assign_issue

        assign_issue('PROJ-123', user='5b10ac8d82e05b22cc7d4ef5', profile=None)

        mock_jira_client.assign_issue.assert_called_once_with(
            'PROJ-123', '5b10ac8d82e05b22cc7d4ef5'
        )

    @patch('assign_issue.get_jira_client')
    def test_assign_issue_to_self(self, mock_get_client, mock_jira_client):
        """Test assigning issue to current user."""
        mock_get_client.return_value = mock_jira_client

        from assign_issue import assign_issue

        assign_issue('PROJ-123', assign_to_self=True, profile=None)

        mock_jira_client.assign_issue.assert_called_once_with('PROJ-123', '-1')

    @patch('assign_issue.get_jira_client')
    def test_unassign_issue(self, mock_get_client, mock_jira_client):
        """Test removing assignee from issue."""
        mock_get_client.return_value = mock_jira_client

        from assign_issue import assign_issue

        assign_issue('PROJ-123', unassign=True, profile=None)

        mock_jira_client.assign_issue.assert_called_once_with('PROJ-123', None)

    def test_assign_requires_one_option(self):
        """Test error when no assignment option specified."""
        from assistant_skills_lib.error_handler import ValidationError
        from assign_issue import assign_issue

        with pytest.raises(ValidationError, match="Specify exactly one"):
            assign_issue('PROJ-123', profile=None)

    def test_assign_rejects_multiple_options(self):
        """Test error when multiple assignment options specified."""
        from assistant_skills_lib.error_handler import ValidationError
        from assign_issue import assign_issue

        with pytest.raises(ValidationError, match="Specify exactly one"):
            assign_issue('PROJ-123', user='test', assign_to_self=True, profile=None)

    def test_assign_rejects_user_and_unassign(self):
        """Test error when user and unassign both specified."""
        from assistant_skills_lib.error_handler import ValidationError
        from assign_issue import assign_issue

        with pytest.raises(ValidationError, match="Specify exactly one"):
            assign_issue('PROJ-123', user='test', unassign=True, profile=None)

    def test_assign_rejects_all_options(self):
        """Test error when all assignment options specified."""
        from assistant_skills_lib.error_handler import ValidationError
        from assign_issue import assign_issue

        with pytest.raises(ValidationError, match="Specify exactly one"):
            assign_issue('PROJ-123', user='test', assign_to_self=True, unassign=True, profile=None)

    def test_assign_invalid_issue_key(self):
        """Test error on invalid issue key."""
        from assistant_skills_lib.error_handler import ValidationError
        from assign_issue import assign_issue

        with pytest.raises(ValidationError):
            assign_issue('invalid', user='test', profile=None)

    @patch('assign_issue.get_jira_client')
    def test_assign_issue_with_profile(self, mock_get_client, mock_jira_client):
        """Test assigning issue with a specific profile."""
        mock_get_client.return_value = mock_jira_client

        from assign_issue import assign_issue

        assign_issue('PROJ-123', user='test-user', profile='development')

        mock_get_client.assert_called_once_with('development')


@pytest.mark.lifecycle
@pytest.mark.unit
class TestAssignIssueErrorHandling:
    """Test API error handling for assign_issue."""

    @patch('assign_issue.get_jira_client')
    def test_issue_not_found(self, mock_get_client, mock_jira_client):
        """Test handling of 404 when issue doesn't exist."""
        from jira_assistant_skills_lib import NotFoundError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.assign_issue.side_effect = NotFoundError("Issue", "PROJ-999")

        from assign_issue import assign_issue

        with pytest.raises(NotFoundError):
            assign_issue('PROJ-999', user='test', profile=None)

    @patch('assign_issue.get_jira_client')
    def test_permission_denied(self, mock_get_client, mock_jira_client):
        """Test handling of 403 when not allowed to assign."""
        from jira_assistant_skills_lib import PermissionError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.assign_issue.side_effect = PermissionError("Cannot assign")

        from assign_issue import assign_issue

        with pytest.raises(PermissionError):
            assign_issue('PROJ-123', user='test', profile=None)

    @patch('assign_issue.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.assign_issue.side_effect = AuthenticationError("Invalid token")

        from assign_issue import assign_issue

        with pytest.raises(AuthenticationError):
            assign_issue('PROJ-123', user='test', profile=None)

    @patch('assign_issue.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.assign_issue.side_effect = JiraError(
            "Rate limit exceeded", status_code=429
        )

        from assign_issue import assign_issue

        with pytest.raises(JiraError) as exc_info:
            assign_issue('PROJ-123', user='test', profile=None)
        assert exc_info.value.status_code == 429

    @patch('assign_issue.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.assign_issue.side_effect = JiraError(
            "Internal server error", status_code=500
        )

        from assign_issue import assign_issue

        with pytest.raises(JiraError) as exc_info:
            assign_issue('PROJ-123', user='test', profile=None)
        assert exc_info.value.status_code == 500

    @patch('assign_issue.get_jira_client')
    def test_user_not_found(self, mock_get_client, mock_jira_client):
        """Test handling when assignee user is not found."""
        from assistant_skills_lib.error_handler import ValidationError
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.assign_issue.side_effect = ValidationError("User not found")

        from assign_issue import assign_issue

        with pytest.raises(ValidationError, match="User not found"):
            assign_issue('PROJ-123', user='nonexistent-user', profile=None)
