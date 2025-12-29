"""
Tests for send_notification.py - Send notifications about an issue.
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add script path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.mark.collaborate
@pytest.mark.unit
class TestSendNotification:
    """Tests for sending notifications."""

    @patch('send_notification.get_jira_client')
    def test_notify_watchers(self, mock_get_client, mock_jira_client):
        """Test notifying all watchers."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.return_value = None

        from send_notification import send_notification

        send_notification(
            'PROJ-123',
            subject='Test Subject',
            body='Test body',
            watchers=True,
            profile=None
        )

        mock_jira_client.notify_issue.assert_called_once()
        call_args = mock_jira_client.notify_issue.call_args
        assert call_args[0][0] == 'PROJ-123'
        assert call_args[1]['to']['watchers'] is True

    @patch('send_notification.get_jira_client')
    def test_notify_assignee(self, mock_get_client, mock_jira_client):
        """Test notifying assignee."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.return_value = None

        from send_notification import send_notification

        send_notification(
            'PROJ-123',
            subject='Test',
            body='Body',
            assignee=True,
            profile=None
        )

        call_args = mock_jira_client.notify_issue.call_args
        assert call_args[1]['to']['assignee'] is True

    @patch('send_notification.get_jira_client')
    def test_notify_reporter(self, mock_get_client, mock_jira_client):
        """Test notifying reporter."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.return_value = None

        from send_notification import send_notification

        send_notification(
            'PROJ-123',
            subject='Test',
            body='Body',
            reporter=True,
            profile=None
        )

        call_args = mock_jira_client.notify_issue.call_args
        assert call_args[1]['to']['reporter'] is True

    @patch('send_notification.get_jira_client')
    def test_notify_specific_users(self, mock_get_client, mock_jira_client):
        """Test notifying specific users by account ID."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.return_value = None

        from send_notification import send_notification

        send_notification(
            'PROJ-123',
            subject='Test',
            body='Body',
            users=['5b10a2844c20165700ede21g', '5b10a2844c20165700ede22h'],
            profile=None
        )

        call_args = mock_jira_client.notify_issue.call_args
        assert len(call_args[1]['to']['users']) == 2
        assert call_args[1]['to']['users'][0]['accountId'] == '5b10a2844c20165700ede21g'

    @patch('send_notification.get_jira_client')
    def test_notify_group(self, mock_get_client, mock_jira_client):
        """Test notifying a group."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.return_value = None

        from send_notification import send_notification

        send_notification(
            'PROJ-123',
            subject='Test',
            body='Body',
            groups=['developers'],
            profile=None
        )

        call_args = mock_jira_client.notify_issue.call_args
        assert len(call_args[1]['to']['groups']) == 1
        assert call_args[1]['to']['groups'][0]['name'] == 'developers'

    @patch('send_notification.get_jira_client')
    def test_custom_subject_body(self, mock_get_client, mock_jira_client):
        """Test custom notification subject and body."""
        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.return_value = None

        from send_notification import send_notification

        send_notification(
            'PROJ-123',
            subject='Action Required',
            body='Please review this issue',
            watchers=True,
            profile=None
        )

        call_args = mock_jira_client.notify_issue.call_args
        assert call_args[1]['subject'] == 'Action Required'
        assert call_args[1]['text_body'] == 'Please review this issue'

    @patch('send_notification.get_jira_client')
    def test_notify_dry_run(self, mock_get_client, mock_jira_client):
        """Test dry-run mode shows recipients."""
        mock_get_client.return_value = mock_jira_client

        from send_notification import notify_dry_run

        result = notify_dry_run(
            'PROJ-123',
            subject='Test',
            body='Body',
            watchers=True,
            assignee=True,
            profile=None
        )

        # Should return notification details without sending
        assert result['issue_key'] == 'PROJ-123'
        assert result['subject'] == 'Test'
        assert result['recipients']['watchers'] is True
        assert result['recipients']['assignee'] is True
        mock_jira_client.notify_issue.assert_not_called()


@pytest.mark.collaborate
@pytest.mark.unit
class TestSendNotificationErrorHandling:
    """Test API error handling scenarios for send_notification."""

    @patch('send_notification.get_jira_client')
    def test_authentication_error(self, mock_get_client, mock_jira_client):
        """Test handling of 401 unauthorized."""
        from jira_assistant_skills_lib import AuthenticationError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.side_effect = AuthenticationError("Invalid API token")

        from send_notification import send_notification

        with pytest.raises(AuthenticationError):
            send_notification(
                'PROJ-123',
                subject='Test',
                body='Body',
                watchers=True,
                profile=None
            )

    @patch('send_notification.get_jira_client')
    def test_permission_error(self, mock_get_client, mock_jira_client):
        """Test handling of 403 forbidden."""
        from jira_assistant_skills_lib import PermissionError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.side_effect = PermissionError("No permission to send notifications")

        from send_notification import send_notification

        with pytest.raises(PermissionError):
            send_notification(
                'PROJ-123',
                subject='Test',
                body='Body',
                watchers=True,
                profile=None
            )

    @patch('send_notification.get_jira_client')
    def test_not_found_error(self, mock_get_client, mock_jira_client):
        """Test handling of 404 not found."""
        from jira_assistant_skills_lib import NotFoundError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.side_effect = NotFoundError("Issue PROJ-999 not found")

        from send_notification import send_notification

        with pytest.raises(NotFoundError):
            send_notification(
                'PROJ-999',
                subject='Test',
                body='Body',
                watchers=True,
                profile=None
            )

    @patch('send_notification.get_jira_client')
    def test_rate_limit_error(self, mock_get_client, mock_jira_client):
        """Test handling of 429 rate limit."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.side_effect = JiraError("Rate limit exceeded", status_code=429)

        from send_notification import send_notification

        with pytest.raises(JiraError) as exc_info:
            send_notification(
                'PROJ-123',
                subject='Test',
                body='Body',
                watchers=True,
                profile=None
            )
        assert exc_info.value.status_code == 429

    @patch('send_notification.get_jira_client')
    def test_server_error(self, mock_get_client, mock_jira_client):
        """Test handling of 500 server error."""
        from jira_assistant_skills_lib import JiraError

        mock_get_client.return_value = mock_jira_client
        mock_jira_client.notify_issue.side_effect = JiraError("Internal server error", status_code=500)

        from send_notification import send_notification

        with pytest.raises(JiraError) as exc_info:
            send_notification(
                'PROJ-123',
                subject='Test',
                body='Body',
                watchers=True,
                profile=None
            )
        assert exc_info.value.status_code == 500
