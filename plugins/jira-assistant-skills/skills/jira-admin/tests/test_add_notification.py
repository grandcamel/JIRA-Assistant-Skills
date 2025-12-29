"""
Tests for add_notification.py - TDD approach.

Test cases per implementation plan:
1. test_add_notification_current_assignee - Test adding CurrentAssignee notification
2. test_add_notification_group - Test adding Group notification with parameter
3. test_add_notification_project_role - Test adding ProjectRole notification
4. test_add_notification_user - Test adding User notification with account ID
5. test_add_notification_all_watchers - Test adding AllWatchers notification
6. test_add_multiple_notifications - Test adding multiple notifications to same event
7. test_validate_event_id - Test validation of event ID
8. test_validate_recipient_type - Test validation of notification type
9. test_validate_required_parameters - Test validation of required parameters
10. test_format_text_output - Test human-readable success output
11. test_format_json_output - Test JSON output
12. test_dry_run_mode - Test dry-run shows what would be added
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch
import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))


class TestAddNotificationCurrentAssignee:
    """Test adding CurrentAssignee notification to event."""

    def test_add_notification_current_assignee(self, mock_jira_client, sample_notification_scheme_detail):
        """Test adding CurrentAssignee notification to event."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='1',
            recipients=['CurrentAssignee']
        )

        # Verify
        assert result['success'] is True
        mock_jira_client.add_notification_to_scheme.assert_called_once()


class TestAddNotificationGroup:
    """Test adding Group notification with parameter."""

    def test_add_notification_group(self, mock_jira_client, sample_notification_scheme_detail):
        """Test adding Group notification with parameter."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='1',
            recipients=['Group:developers']
        )

        # Verify
        assert result['success'] is True
        call_args = mock_jira_client.add_notification_to_scheme.call_args[0][1]
        events = call_args.get('notificationSchemeEvents', [])
        assert any(
            n.get('parameter') == 'developers'
            for e in events
            for n in e.get('notifications', [])
        )


class TestAddNotificationProjectRole:
    """Test adding ProjectRole notification with role ID."""

    def test_add_notification_project_role(self, mock_jira_client, sample_notification_scheme_detail):
        """Test adding ProjectRole notification with role ID."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='3',
            recipients=['ProjectRole:10002']
        )

        # Verify
        assert result['success'] is True
        call_args = mock_jira_client.add_notification_to_scheme.call_args[0][1]
        events = call_args.get('notificationSchemeEvents', [])
        assert any(
            n.get('notificationType') == 'ProjectRole' and n.get('parameter') == '10002'
            for e in events
            for n in e.get('notifications', [])
        )


class TestAddNotificationUser:
    """Test adding User notification with user account ID."""

    def test_add_notification_user(self, mock_jira_client, sample_notification_scheme_detail):
        """Test adding User notification with user account ID."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='4',
            recipients=['User:5b10ac8d82e05b22cc7d4ef5']
        )

        # Verify
        assert result['success'] is True


class TestAddNotificationAllWatchers:
    """Test adding AllWatchers notification."""

    def test_add_notification_all_watchers(self, mock_jira_client, sample_notification_scheme_detail):
        """Test adding AllWatchers notification."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='6',
            recipients=['AllWatchers']
        )

        # Verify
        assert result['success'] is True


class TestAddMultipleNotifications:
    """Test adding multiple notifications to same event."""

    def test_add_multiple_notifications(self, mock_jira_client, sample_notification_scheme_detail):
        """Test adding multiple notifications to same event."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute with multiple recipients
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='4',
            recipients=['CurrentAssignee', 'Reporter', 'AllWatchers']
        )

        # Verify
        assert result['success'] is True
        call_args = mock_jira_client.add_notification_to_scheme.call_args[0][1]
        events = call_args.get('notificationSchemeEvents', [])
        notifications = events[0].get('notifications', [])
        assert len(notifications) == 3


class TestValidateEventId:
    """Test validation of event ID."""

    def test_validate_event_id(self, mock_jira_client, sample_notification_scheme_detail):
        """Test validation of event ID."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute with valid event ID
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='1',
            recipients=['CurrentAssignee']
        )

        # Verify success
        assert result['success'] is True

    def test_event_by_name(self, mock_jira_client, sample_notification_scheme_detail):
        """Test specifying event by name instead of ID."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute with event name
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_name='Issue created',
            recipients=['CurrentAssignee']
        )

        # Verify event ID was resolved
        assert result['success'] is True
        call_args = mock_jira_client.add_notification_to_scheme.call_args[0][1]
        events = call_args.get('notificationSchemeEvents', [])
        assert events[0]['event']['id'] == '1'


class TestValidateRecipientType:
    """Test validation of notification type."""

    def test_validate_recipient_type(self, mock_jira_client):
        """Test validation of notification type."""
        from add_notification import add_notification
        from error_handler import ValidationError

        # Execute with invalid recipient type
        with pytest.raises(ValidationError) as exc_info:
            add_notification(
                client=mock_jira_client,
                scheme_id='10000',
                event_id='1',
                recipients=['InvalidRecipientType']
            )

        assert 'InvalidRecipientType' in str(exc_info.value)


class TestValidateRequiredParameters:
    """Test validation of required parameters."""

    def test_validate_required_parameters(self, mock_jira_client):
        """Test validation of required parameters (group name, role ID, etc.)."""
        from add_notification import add_notification
        from error_handler import ValidationError

        # Execute with Group without parameter
        with pytest.raises(ValidationError) as exc_info:
            add_notification(
                client=mock_jira_client,
                scheme_id='10000',
                event_id='1',
                recipients=['Group']  # Missing parameter
            )

        assert 'parameter' in str(exc_info.value).lower()


class TestFormatTextOutput:
    """Test human-readable success output."""

    def test_format_text_output(self, mock_jira_client, sample_notification_scheme_detail):
        """Test human-readable success output."""
        from add_notification import add_notification, format_text_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='1',
            recipients=['CurrentAssignee', 'Group:developers']
        )
        output = format_text_output(result)

        # Verify output contains expected content
        assert '10000' in output
        assert 'Current Assignee' in output or 'CurrentAssignee' in output
        assert 'developers' in output


class TestFormatJsonOutput:
    """Test JSON output."""

    def test_format_json_output(self, mock_jira_client, sample_notification_scheme_detail):
        """Test JSON output."""
        from add_notification import add_notification, format_json_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.add_notification_to_scheme.return_value = {}

        # Execute
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='1',
            recipients=['CurrentAssignee']
        )
        output = format_json_output(result)

        # Verify valid JSON
        parsed = json.loads(output)
        assert parsed['success'] is True


class TestDryRunMode:
    """Test dry-run shows what would be added."""

    def test_dry_run_mode(self, mock_jira_client, sample_notification_scheme_detail):
        """Test dry-run shows what would be added."""
        from add_notification import add_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail

        # Execute with dry_run=True
        result = add_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_id='1',
            recipients=['CurrentAssignee', 'Reporter'],
            dry_run=True
        )

        # Verify API was NOT called
        mock_jira_client.add_notification_to_scheme.assert_not_called()

        # Verify result shows what would be added
        assert result['dry_run'] is True
        assert 'would_add' in result
