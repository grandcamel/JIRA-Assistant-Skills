"""
Tests for remove_notification.py - TDD approach.

Test cases per implementation plan:
1. test_remove_notification_by_id - Test removing notification by ID
2. test_remove_by_event_and_recipient - Test removing by event name and recipient type
3. test_validate_notification_exists - Test error when notification doesn't exist
4. test_confirm_before_remove - Test confirmation prompt before removal
5. test_force_remove_no_confirm - Test --force flag bypasses confirmation
6. test_format_text_output - Test human-readable success output
7. test_dry_run_mode - Test dry-run shows what would be removed
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Add scripts and shared lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib'))


class TestRemoveNotificationById:
    """Test removing notification by ID."""

    def test_remove_notification_by_id(self, mock_jira_client, sample_notification_scheme_detail):
        """Test removing notification by ID."""
        from remove_notification import remove_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.delete_notification_from_scheme.return_value = None

        # Execute
        result = remove_notification(
            client=mock_jira_client,
            scheme_id='10000',
            notification_id='10',
            force=True
        )

        # Verify
        assert result['success'] is True
        mock_jira_client.delete_notification_from_scheme.assert_called_once_with('10000', '10')


class TestRemoveByEventAndRecipient:
    """Test removing by event name and recipient type."""

    def test_remove_by_event_and_recipient(self, mock_jira_client, sample_notification_scheme_detail):
        """Test removing by event name and recipient type."""
        from remove_notification import remove_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.delete_notification_from_scheme.return_value = None

        # Execute - remove Group:jira-administrators from Issue created
        result = remove_notification(
            client=mock_jira_client,
            scheme_id='10000',
            event_name='Issue created',
            recipient='Group:jira-administrators',
            force=True
        )

        # Verify
        assert result['success'] is True
        # Should find notification ID 12 (Group:jira-administrators on Issue created)
        mock_jira_client.delete_notification_from_scheme.assert_called_once_with('10000', '12')


class TestValidateNotificationExists:
    """Test error when notification doesn't exist."""

    def test_validate_notification_exists(self, mock_jira_client, sample_notification_scheme_detail):
        """Test error when notification doesn't exist."""
        from remove_notification import remove_notification
        from error_handler import NotFoundError

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail

        # Execute with non-existent notification ID
        with pytest.raises(NotFoundError):
            remove_notification(
                client=mock_jira_client,
                scheme_id='10000',
                notification_id='99999',
                force=True
            )


class TestConfirmBeforeRemove:
    """Test confirmation prompt before removal."""

    def test_confirm_before_remove(self, mock_jira_client, sample_notification_scheme_detail):
        """Test confirmation prompt before removal."""
        from remove_notification import remove_notification
        from error_handler import ValidationError

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail

        # Execute without force should raise if not confirmed
        with pytest.raises(ValidationError) as exc_info:
            remove_notification(
                client=mock_jira_client,
                scheme_id='10000',
                notification_id='10',
                force=False,
                confirmed=False
            )

        assert 'confirm' in str(exc_info.value).lower()


class TestForceRemoveNoConfirm:
    """Test --force flag bypasses confirmation."""

    def test_force_remove_no_confirm(self, mock_jira_client, sample_notification_scheme_detail):
        """Test --force flag bypasses confirmation."""
        from remove_notification import remove_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.delete_notification_from_scheme.return_value = None

        # Execute with force=True
        result = remove_notification(
            client=mock_jira_client,
            scheme_id='10000',
            notification_id='10',
            force=True
        )

        # Verify deletion proceeded
        assert result['success'] is True
        mock_jira_client.delete_notification_from_scheme.assert_called_once()


class TestFormatTextOutput:
    """Test human-readable success output."""

    def test_format_text_output(self, mock_jira_client, sample_notification_scheme_detail):
        """Test human-readable success output."""
        from remove_notification import remove_notification, format_text_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.delete_notification_from_scheme.return_value = None

        # Execute
        result = remove_notification(
            client=mock_jira_client,
            scheme_id='10000',
            notification_id='10',
            force=True
        )
        output = format_text_output(result)

        # Verify output contains expected content
        assert '10000' in output
        assert 'removed' in output.lower() or 'success' in output.lower()


class TestDryRunMode:
    """Test dry-run shows what would be removed."""

    def test_dry_run_mode(self, mock_jira_client, sample_notification_scheme_detail):
        """Test dry-run shows what would be removed."""
        from remove_notification import remove_notification

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail

        # Execute with dry_run=True
        result = remove_notification(
            client=mock_jira_client,
            scheme_id='10000',
            notification_id='10',
            dry_run=True
        )

        # Verify API was NOT called
        mock_jira_client.delete_notification_from_scheme.assert_not_called()

        # Verify result indicates dry run
        assert result['dry_run'] is True
        assert 'would_remove' in result


class TestFormatJsonOutput:
    """Test JSON output formatting."""

    def test_format_json_output(self, mock_jira_client, sample_notification_scheme_detail):
        """Test JSON output is valid and contains expected fields."""
        import json
        from remove_notification import remove_notification, format_json_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail
        mock_jira_client.delete_notification_from_scheme.return_value = None

        # Execute
        result = remove_notification(
            client=mock_jira_client,
            scheme_id='10000',
            notification_id='10',
            force=True
        )
        output = format_json_output(result)

        # Verify output is valid JSON with expected fields
        parsed = json.loads(output)
        assert parsed['success'] is True
        assert parsed['scheme_id'] == '10000'
        assert parsed['notification_id'] == '10'

    def test_format_json_output_dry_run(self, mock_jira_client, sample_notification_scheme_detail):
        """Test JSON output for dry-run mode."""
        import json
        from remove_notification import remove_notification, format_json_output

        # Setup mock
        mock_jira_client.get_notification_scheme.return_value = sample_notification_scheme_detail

        # Execute with dry_run=True
        result = remove_notification(
            client=mock_jira_client,
            scheme_id='10000',
            notification_id='10',
            dry_run=True
        )
        output = format_json_output(result)

        # Verify output is valid JSON with dry_run indicator
        parsed = json.loads(output)
        assert parsed['dry_run'] is True
        assert parsed['scheme_id'] == '10000'
        assert 'would_remove' in parsed
