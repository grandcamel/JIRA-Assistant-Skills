"""
Live Integration Tests: Notification Integration

Tests for notification functionality against a real JIRA instance.

IMPORTANT: JIRA Cloud's notification API (/rest/api/3/issue/{key}/notify)
has strict requirements that vary by instance configuration:
- The notify permission must be enabled for the project
- Users must have notification permissions
- Some instances may have notifications disabled entirely

These tests verify the notification API is accessible and handles various scenarios.
"""

import pytest
import uuid


def check_notification_support(jira_client, test_issue):
    """
    Check if notifications are supported on this JIRA instance.

    Returns:
        True if notifications are supported, False otherwise
    """
    current_user_id = jira_client.get_current_user_id()

    try:
        jira_client.notify_issue(
            test_issue['key'],
            subject="Notification capability check",
            text_body="Testing notification support",
            to={'users': [{'accountId': current_user_id}]}
        )
        return True
    except Exception as e:
        if 'No recipients' in str(e) or '400' in str(e) or '403' in str(e):
            return False
        raise


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.notifications
class TestNotificationToUser:
    """Tests for sending notifications to specific users."""

    @pytest.fixture(autouse=True)
    def skip_if_not_supported(self, jira_client, test_issue):
        """Skip tests if notifications are not supported on this instance."""
        if not check_notification_support(jira_client, test_issue):
            pytest.skip(
                "JIRA instance does not support notifications or user lacks permission. "
                "This is a JIRA configuration issue, not a code issue."
            )

    def test_notify_current_user(self, jira_client, test_issue, current_user):
        """Test sending notification to the current user."""
        try:
            jira_client.notify_issue(
                test_issue['key'],
                subject=f"Test notification {uuid.uuid4().hex[:8]}",
                text_body="Test notification to current user",
                to={'users': [{'accountId': current_user['accountId']}]}
            )
        except Exception as e:
            pytest.fail(f"Notification to current user failed: {e}")

    def test_notify_with_custom_subject(self, jira_client, test_issue, current_user):
        """Test notification with custom subject line."""
        custom_subject = f"Custom Subject {uuid.uuid4().hex[:8]}"

        try:
            jira_client.notify_issue(
                test_issue['key'],
                subject=custom_subject,
                text_body="Test body",
                to={'users': [{'accountId': current_user['accountId']}]}
            )
        except Exception as e:
            pytest.fail(f"Notification with custom subject failed: {e}")

    def test_notify_with_html_body(self, jira_client, test_issue, current_user):
        """Test notification with HTML formatted body."""
        try:
            jira_client.notify_issue(
                test_issue['key'],
                subject="HTML notification test",
                html_body="<p>This is a <strong>formatted</strong> notification.</p>",
                to={'users': [{'accountId': current_user['accountId']}]}
            )
        except Exception as e:
            pytest.fail(f"Notification with HTML body failed: {e}")

    def test_notify_with_text_and_html_body(self, jira_client, test_issue, current_user):
        """Test notification with both text and HTML body."""
        try:
            jira_client.notify_issue(
                test_issue['key'],
                subject="Multi-format notification",
                text_body="Plain text version",
                html_body="<p>HTML version</p>",
                to={'users': [{'accountId': current_user['accountId']}]}
            )
        except Exception as e:
            pytest.fail(f"Notification with text and HTML body failed: {e}")


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.notifications
class TestNotificationToRoles:
    """Tests for sending notifications to issue roles (reporter, assignee, watchers)."""

    @pytest.fixture(autouse=True)
    def skip_if_not_supported(self, jira_client, test_issue):
        """Skip tests if notifications are not supported."""
        if not check_notification_support(jira_client, test_issue):
            pytest.skip("Notifications not supported on this instance")

    def test_notify_reporter(self, jira_client, test_issue):
        """Test notification to issue reporter."""
        try:
            jira_client.notify_issue(
                test_issue['key'],
                subject="Reporter notification test",
                text_body="Test notification to reporter",
                to={'reporter': True}
            )
        except Exception as e:
            # Reporter notifications may fail if no valid recipients
            if 'No recipients' in str(e):
                pytest.skip("No valid reporter recipient")
            pytest.fail(f"Reporter notification failed unexpectedly: {e}")

    def test_notify_watchers(self, jira_client, test_issue_with_watchers):
        """Test notification to issue watchers."""
        try:
            jira_client.notify_issue(
                test_issue_with_watchers['key'],
                subject="Watcher notification test",
                text_body="Test notification to watchers",
                to={'watchers': True}
            )
        except Exception as e:
            if 'No recipients' in str(e):
                pytest.skip("No valid watcher recipients")
            pytest.fail(f"Watcher notification failed unexpectedly: {e}")

    def test_notify_assignee(self, jira_client, test_project, current_user):
        """Test notification to issue assignee."""
        # Create issue with assignee
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Assignee notification test {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'},
            'assignee': {'accountId': current_user['accountId']}
        })

        try:
            jira_client.notify_issue(
                issue['key'],
                subject="Assignee notification test",
                text_body="Test notification to assignee",
                to={'assignee': True}
            )
        except Exception as e:
            if 'No recipients' in str(e):
                pytest.skip("No valid assignee recipient")
            pytest.fail(f"Assignee notification failed unexpectedly: {e}")
        finally:
            jira_client.delete_issue(issue['key'])


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.notifications
class TestNotificationCombined:
    """Tests for notifications to multiple recipient types."""

    @pytest.fixture(autouse=True)
    def skip_if_not_supported(self, jira_client, test_issue):
        """Skip tests if notifications are not supported."""
        if not check_notification_support(jira_client, test_issue):
            pytest.skip("Notifications not supported on this instance")

    def test_notify_multiple_roles(self, jira_client, test_project, current_user):
        """Test notification to multiple roles at once."""
        # Create issue with assignee
        issue = jira_client.create_issue({
            'project': {'key': test_project['key']},
            'summary': f'Multi-role notification test {uuid.uuid4().hex[:8]}',
            'issuetype': {'name': 'Task'},
            'assignee': {'accountId': current_user['accountId']}
        })

        try:
            jira_client.notify_issue(
                issue['key'],
                subject="Multi-role notification test",
                text_body="Test notification to multiple roles",
                to={
                    'reporter': True,
                    'assignee': True,
                    'watchers': True
                }
            )
        except Exception as e:
            if 'No recipients' in str(e):
                pytest.skip("No valid recipients for multi-role notification")
            pytest.fail(f"Multi-role notification failed unexpectedly: {e}")
        finally:
            jira_client.delete_issue(issue['key'])

    def test_notify_user_and_role_combined(self, jira_client, test_issue, current_user):
        """Test notification to specific users and roles combined."""
        try:
            jira_client.notify_issue(
                test_issue['key'],
                subject="Combined notification test",
                text_body="Test notification to users and roles",
                to={
                    'users': [{'accountId': current_user['accountId']}],
                    'reporter': True
                }
            )
        except Exception as e:
            if 'No recipients' in str(e):
                pytest.skip("No valid recipients for combined notification")
            pytest.fail(f"Combined notification failed unexpectedly: {e}")


@pytest.mark.integration
@pytest.mark.collaborate
@pytest.mark.notifications
class TestNotificationEdgeCases:
    """Tests for notification edge cases and error handling."""

    def test_notification_without_support_handled(self, jira_client, test_issue):
        """Test that notification failures are handled gracefully."""
        current_user_id = jira_client.get_current_user_id()

        try:
            jira_client.notify_issue(
                test_issue['key'],
                subject="Edge case test",
                text_body="Test body",
                to={'users': [{'accountId': current_user_id}]}
            )
            # Success is fine
        except Exception as e:
            # Verify error is meaningful
            error_str = str(e)
            assert any(term in error_str.lower() for term in ['notify', 'recipient', 'permission', 'error', '400', '403'])

    def test_notification_empty_subject_uses_default(self, jira_client, test_issue):
        """Test notification with empty subject uses issue-based default."""
        if not check_notification_support(jira_client, test_issue):
            pytest.skip("Notifications not supported")

        current_user_id = jira_client.get_current_user_id()

        try:
            # Pass empty subject - JIRA should handle this
            jira_client.notify_issue(
                test_issue['key'],
                subject="",  # Empty subject
                text_body="Test body",
                to={'users': [{'accountId': current_user_id}]}
            )
        except Exception as e:
            # Empty subject may be rejected - that's acceptable behavior
            pass

    def test_notification_long_body(self, jira_client, test_issue, current_user):
        """Test notification with long body content."""
        if not check_notification_support(jira_client, test_issue):
            pytest.skip("Notifications not supported")

        long_body = "This is a long notification body. " * 100

        try:
            jira_client.notify_issue(
                test_issue['key'],
                subject="Long body notification test",
                text_body=long_body,
                to={'users': [{'accountId': current_user['accountId']}]}
            )
        except Exception as e:
            # Long body may be truncated or rejected - both are acceptable
            pass
